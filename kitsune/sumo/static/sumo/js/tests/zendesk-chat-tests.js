import { expect } from "chai";
import sinon from "sinon";

import { SIGN_OUT_KEY } from "sumo/js/sign-out-sync";
import {
  removeChat,
  removeChatOnSignOut,
  signInToChat,
  SIGNED_IN_USER_KEY,
} from "sumo/js/zendesk-chat";

const JWT_URL = "/support-chat/jwt/firefox-enterprise";

function textResponse(body) {
  return {
    ok: true,
    status: 200,
    headers: { get: () => "text/plain" },
    text: async () => body,
  };
}

function loginCall() {
  return window.zE.getCalls().find((call) => call.args[1] === "loginUser");
}

describe("zendesk-chat", () => {
  beforeEach(() => {
    window.zE = sinon.stub();
    sinon.stub(window, "fetch").resolves(textResponse("a.signed.token"));
    window.localStorage.removeItem(SIGNED_IN_USER_KEY);
    sinon.stub(console, "error");
  });

  afterEach(() => {
    window.fetch.restore();
    console.error.restore();
    window.localStorage.removeItem(SIGNED_IN_USER_KEY);
    delete window.zE;
  });

  it("does nothing without the html data attributes", () => {
    signInToChat(null, null);

    expect(window.zE.called).to.equal(false);
  });

  it("signs in again even when the widget already knows this user", () => {
    // The widget doesn't restore an authenticated session itself, so skipping
    // the login leaves it anonymous with a fresh, empty conversation.
    window.localStorage.setItem(SIGNED_IN_USER_KEY, "ringo");

    signInToChat(JWT_URL, "ringo");

    const commands = window.zE.getCalls().map((call) => call.args[1]);
    expect(commands).to.eql(["loginUser"]);
  });

  it("signs the previous user out and forgets them before signing a different one in", () => {
    window.localStorage.setItem(SIGNED_IN_USER_KEY, "paul");

    signInToChat(JWT_URL, "ringo");

    const commands = window.zE.getCalls().map((call) => call.args[1]);
    expect(commands).to.eql(["logoutUser", "loginUser"]);
    expect(window.localStorage.getItem(SIGNED_IN_USER_KEY)).to.equal(null);
  });

  it("signs out first when it can't confirm who the widget has", () => {
    signInToChat(JWT_URL, "ringo");

    const commands = window.zE.getCalls().map((call) => call.args[1]);
    expect(commands).to.eql(["logoutUser", "loginUser"]);
  });

  it("posts to the token url and hands the token back to Zendesk", async () => {
    signInToChat(JWT_URL, "ringo");

    const jwtCallback = loginCall().args[2];
    const token = await new Promise((resolve) => jwtCallback(resolve));

    expect(token).to.equal("a.signed.token");
    expect(window.fetch.calledOnce).to.equal(true);
    expect(window.fetch.firstCall.args[0]).to.equal(JWT_URL);
    expect(window.fetch.firstCall.args[1].method).to.equal("POST");
  });

  it("fetches a fresh token every time Zendesk asks", async () => {
    signInToChat(JWT_URL, "ringo");

    const jwtCallback = loginCall().args[2];
    await new Promise((resolve) => jwtCallback(resolve));
    await new Promise((resolve) => jwtCallback(resolve));

    expect(window.fetch.callCount).to.equal(2);
  });

  const REFUSALS = [
    // Refusing access is the system working as intended, so it isn't worth logging.
    { status: 401, logs: false },
    { status: 403, logs: false },
    { status: 404, logs: false },
    // A 429 means our own rate limits may be too tight, which we want to hear about.
    { status: 429, logs: true },
  ];

  for (const { status, logs } of REFUSALS) {
    it(`removes the chat on a ${status} and ${logs ? "logs it" : "stays quiet"}`, async () => {
      window.fetch.resolves({
        ok: false,
        status,
        headers: { get: () => "text/plain" },
        text: async () => "",
      });

      signInToChat(JWT_URL, "ringo");

      const handToZendesk = sinon.spy();
      loginCall().args[2](handToZendesk);
      // Waiting on the callback would hang. We never answer Zendesk now,
      // because the widget is going away.
      await new Promise((resolve) => setTimeout(resolve, 0));

      const commands = window.zE.getCalls().map((call) => call.args[1]);
      expect(commands).to.include.members(["resetWidget", "hide"]);
      expect(handToZendesk.called).to.equal(false);
      expect(console.error.called).to.equal(logs);
    });
  }

  it("removes the chat when the token request fails outright", async () => {
    window.fetch.rejects(new Error("network down"));

    signInToChat(JWT_URL, "ringo");

    loginCall().args[2](sinon.spy());
    await new Promise((resolve) => setTimeout(resolve, 0));

    const commands = window.zE.getCalls().map((call) => call.args[1]);
    expect(commands).to.include.members(["resetWidget", "hide"]);
    expect(console.error.called).to.equal(true);
  });

  it("remembers the user once login succeeds", () => {
    signInToChat(JWT_URL, "ringo");

    loginCall().args[3](null);

    expect(window.localStorage.getItem(SIGNED_IN_USER_KEY)).to.equal("ringo");
  });

  it("forgets the user, removes the chat, and logs it when login fails", () => {
    signInToChat(JWT_URL, "ringo");

    loginCall().args[3]({ type: "LoginFailedError" });

    const commands = window.zE.getCalls().map((call) => call.args[1]);
    expect(window.localStorage.getItem(SIGNED_IN_USER_KEY)).to.equal(null);
    // Leaving the widget up would let the user chat anonymously.
    expect(commands).to.include.members(["resetWidget", "hide"]);
    // Zendesk rejected a token we just created, so chat is broken for everyone.
    expect(console.error.called).to.equal(true);
  });

  describe("removeChat", () => {
    it("logs out, clears local state, then hides", () => {
      removeChat();

      const commands = window.zE.getCalls().map((call) => call.args[1]);
      expect(commands).to.eql(["logoutUser", "resetWidget", "hide"]);
    });
  });

  describe("removeChatOnSignOut", () => {
    let form;
    let stopListening;

    beforeEach(() => {
      form = document.createElement("form");
      form.id = "sign-out";
      document.body.appendChild(form);
      stopListening = () => {};
    });

    // jsdom shares one window across tests.
    afterEach(() => {
      stopListening();
      form.remove();
    });

    function listen() {
      stopListening = removeChatOnSignOut();
    }

    function storageEvent(key, newValue) {
      // Real storage events only fire in the other tabs.
      return new window.StorageEvent("storage", { key, newValue });
    }

    it("removes the chat when this tab signs out", () => {
      listen();

      form.dispatchEvent(new window.Event("submit"));

      const commands = window.zE.getCalls().map((call) => call.args[1]);
      expect(commands).to.eql(["logoutUser", "resetWidget", "hide"]);
    });

    it("lets the sign-out go ahead", () => {
      listen();

      const event = new window.Event("submit", { cancelable: true });
      form.dispatchEvent(event);

      expect(event.defaultPrevented).to.equal(false);
    });

    it("covers every sign-out form on the page", () => {
      // The profile page renders its own, sharing the id with the one in the nav.
      const second = document.createElement("form");
      second.id = "sign-out";
      document.body.appendChild(second);

      listen();
      second.dispatchEvent(new window.Event("submit"));

      expect(window.zE.called).to.equal(true);
      second.remove();
    });

    it("removes the chat when another tab signs out", () => {
      listen();

      window.dispatchEvent(storageEvent(SIGN_OUT_KEY, "1758000000000"));

      const commands = window.zE.getCalls().map((call) => call.args[1]);
      expect(commands).to.eql(["logoutUser", "resetWidget", "hide"]);
    });

    it("ignores changes to other keys", () => {
      listen();

      window.dispatchEvent(storageEvent("something-else", "1758000000000"));

      expect(window.zE.called).to.equal(false);
    });

    it("does nothing on a page without the widget", () => {
      delete window.zE;
      listen();

      window.zE = sinon.stub();
      form.dispatchEvent(new window.Event("submit"));
      window.dispatchEvent(storageEvent(SIGN_OUT_KEY, "1758000000000"));

      expect(window.zE.called).to.equal(false);
    });
  });
});
