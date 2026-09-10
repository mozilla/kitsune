import { expect } from "chai";
import sinon from "sinon";

import { signInToChat, STORAGE_KEY } from "sumo/js/zendesk-chat";

const JWT_URL = "/support-chat/jwt/firefox-enterprise";

function textResponse(body) {
  return {
    ok: true,
    status: 200,
    headers: { get: () => "text/plain" },
    text: async () => body,
  };
}

// Signing a different user in makes two zE calls, so don't assume which is which.
function loginCall() {
  return window.zE.getCalls().find((call) => call.args[1] === "loginUser");
}

describe("zendesk-chat", () => {
  beforeEach(() => {
    window.zE = sinon.stub();
    sinon.stub(window, "fetch").resolves(textResponse("a.signed.token"));
    window.localStorage.removeItem(STORAGE_KEY);
    sinon.stub(console, "error");
  });

  afterEach(() => {
    window.fetch.restore();
    console.error.restore();
    window.localStorage.removeItem(STORAGE_KEY);
    delete window.zE;
  });

  it("does nothing without the html data attributes", () => {
    signInToChat(null, null);

    expect(window.zE.called).to.equal(false);
  });

  it("signs in again even when the widget already knows this user", () => {
    // The widget doesn't restore an authenticated session itself, so skipping the
    // login leaves them anonymous with a fresh, empty conversation. Checked on dev.
    window.localStorage.setItem(STORAGE_KEY, "ringo");

    signInToChat(JWT_URL, "ringo");

    const commands = window.zE.getCalls().map((call) => call.args[1]);
    expect(commands).to.eql(["loginUser"]);
  });

  it("signs the previous user out before signing a different one in", () => {
    // Otherwise their conversation carries over on a shared browser.
    window.localStorage.setItem(STORAGE_KEY, "paul");

    signInToChat(JWT_URL, "ringo");

    const commands = window.zE.getCalls().map((call) => call.args[1]);
    expect(commands).to.eql(["logoutUser", "loginUser"]);
  });

  it("forgets the previous user as soon as they are signed out", () => {
    // A failed login would otherwise leave us claiming they're still signed in.
    window.localStorage.setItem(STORAGE_KEY, "paul");

    signInToChat(JWT_URL, "ringo");

    expect(window.localStorage.getItem(STORAGE_KEY)).to.equal(null);
  });

  it("signs nobody out when the widget has no user", () => {
    signInToChat(JWT_URL, "ringo");

    const commands = window.zE.getCalls().map((call) => call.args[1]);
    expect(commands).to.eql(["loginUser"]);
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
    // Reusing one would loop: Zendesk 401s an expired token, re-runs this, and
    // gets the same dead token back.
    signInToChat(JWT_URL, "ringo");

    const jwtCallback = loginCall().args[2];
    await new Promise((resolve) => jwtCallback(resolve));
    await new Promise((resolve) => jwtCallback(resolve));

    expect(window.fetch.callCount).to.equal(2);
  });

  it("remembers the user once login succeeds", () => {
    signInToChat(JWT_URL, "ringo");

    loginCall().args[3](null);

    expect(window.localStorage.getItem(STORAGE_KEY)).to.equal("ringo");
  });

  it("does not remember the user when login fails", () => {
    signInToChat(JWT_URL, "ringo");

    loginCall().args[3]({ type: "LoginFailedError" });

    expect(window.localStorage.getItem(STORAGE_KEY)).to.equal(null);
  });
});
