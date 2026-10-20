import { expect } from "chai";
import sinon from "sinon";

import { getPreference, initTheme, setPreference } from "sumo/js/theme";
import { removeCookie, setCookie } from "sumo/js/utils/cookie";

const ENDPOINT = "/en-US/users/theme";
const CONSOLE_METHODS = ["debug", "error", "info", "log", "warn"];

function fakeResponse(status, body = {}) {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: { get: () => "application/json" },
    text: async () => (typeof body === "string" ? body : JSON.stringify(body)),
  };
}

function settle() {
  return new Promise((resolve) => setTimeout(resolve, 0));
}

describe("theme persistence", () => {
  const root = document.documentElement;
  let sandbox;
  let originalAttributes;
  let originalHead;
  let rejections;
  let requests;
  let pageCount = 0;
  let pageOwner;

  function onUnhandledRejection(reason) {
    rejections.push(reason);
  }

  // A new owner per page, because the save queue outlives a test whose request never settles.
  function startPage({ owner, endpoint = ENDPOINT } = {}) {
    pageCount += 1;
    pageOwner = owner ?? `owner-${pageCount}`;
    Array.from(root.attributes).forEach(({ name }) => root.removeAttribute(name));
    root.setAttribute("data-theme", "light");
    root.setAttribute("data-theme-preference", "system");
    root.setAttribute("data-theme-owner", pageOwner);
    if (endpoint !== null) {
      root.setAttribute("data-theme-endpoint", endpoint);
    }
    initTheme();
  }

  function sent() {
    return requests.map(({ params }) => params.get("preference"));
  }

  beforeEach(() => {
    sandbox = sinon.createSandbox();
    rejections = [];
    requests = [];
    process.on("unhandledRejection", onUnhandledRejection);
    sandbox.stub(window, "fetch").callsFake(
      (url, init) =>
        new Promise((resolve, reject) => {
          requests.push({
            url,
            init,
            params: new URLSearchParams(init.body),
            respond: (status, body) => resolve(fakeResponse(status, body)),
            fail: reject,
          });
        })
    );
    originalAttributes = Array.from(root.attributes, ({ name, value }) => [name, value]);
    originalHead = Array.from(document.head.childNodes);
    originalAttributes.forEach(([name]) => root.removeAttribute(name));
  });

  afterEach(() => {
    process.off("unhandledRejection", onUnhandledRejection);
    Array.from(root.attributes).forEach(({ name }) => root.removeAttribute(name));
    initTheme();
    removeCookie("csrftoken");
    sandbox.restore();
    originalAttributes.forEach(([name, value]) => root.setAttribute(name, value));
    document.head.replaceChildren(...originalHead);
  });

  it("posts at once with the preference, the owner, the CSRF token and keepalive", () => {
    setCookie("csrftoken", "token-123");
    startPage();

    setPreference("dark");

    expect(requests).to.have.length(1);
    const [{ url, init, params }] = requests;
    expect(url).to.equal(ENDPOINT);
    expect(init.method).to.equal("POST");
    expect(init.keepalive).to.equal(true);
    expect(init.headers["X-CSRFToken"]).to.equal("token-123");
    expect(params.get("preference")).to.equal("dark");
    expect(params.get("owner")).to.equal(pageOwner);
  });

  describe("one request in flight", () => {
    it("holds changes made meanwhile, sends only the latest, then posts new changes at once", async () => {
      startPage();

      setPreference("dark");
      setPreference("light");
      setPreference("system");
      await settle();

      expect(sent()).to.deep.equal(["dark"]);

      requests[0].respond(200);
      await settle();

      expect(sent()).to.deep.equal(["dark", "system"]);
      expect(requests[1].params.get("owner")).to.equal(pageOwner);
      expect(requests[1].init.keepalive).to.equal(true);

      requests[1].respond(200);
      await settle();
      setPreference("light");

      expect(sent()).to.deep.equal(["dark", "system", "light"]);
    });

    it("sends nothing more when the latest choice is the one already sent", async () => {
      startPage();

      setPreference("dark");
      setPreference("light");
      setPreference("dark");
      requests[0].respond(200);
      await settle();

      expect(sent()).to.deep.equal(["dark"]);
      expect(getPreference()).to.equal("dark");
    });
  });

  it("keeps a failed choice on the page, logs nothing, and sends the queued choice without retrying", async () => {
    const logged = CONSOLE_METHODS.map((method) => sandbox.stub(console, method));
    const failures = [
      ["a network error", (request) => request.fail(new TypeError("Failed to fetch"))],
      ["a rejection that is not an Error", (request) => request.fail(null)],
      ["a 400 response", (request) => request.respond(400)],
      ["a 403 response", (request) => request.respond(403)],
      ["a 404 response", (request) => request.respond(404)],
      ["a 500 response", (request) => request.respond(500)],
      ["a 200 response with an unreadable body", (request) => request.respond(200, "<html>")],
    ];

    for (const [label, fail] of failures) {
      requests = [];
      startPage();

      setPreference("dark");
      setPreference("light");
      fail(requests[0]);
      await settle();

      expect(sent(), label).to.deep.equal(["dark", "light"]);
      expect(getPreference(), label).to.equal("light");
      expect(root.getAttribute("data-theme"), label).to.equal("light");
    }
    expect(rejections).to.deep.equal([]);
    logged.forEach((method) => expect(method.called).to.equal(false));
  });

  it("stops saving from the page after a 409, dropping a queued choice and logging nothing", async () => {
    const logged = CONSOLE_METHODS.map((method) => sandbox.stub(console, method));
    startPage();

    setPreference("dark");
    setPreference("light");
    requests[0].respond(409);
    await settle();
    setPreference("system");
    await settle();

    expect(sent()).to.deep.equal(["dark"]);
    expect(getPreference()).to.equal("system");
    expect(rejections).to.deep.equal([]);
    logged.forEach((method) => expect(method.called).to.equal(false));
  });

  it("starts a fresh queue when the page is prepared again with another owner or endpoint", async () => {
    startPage();
    setPreference("dark");
    requests[0].respond(409);
    await settle();
    const owner = `${pageOwner}-next`;

    [ENDPOINT, "/fr/users/theme"].forEach((endpoint) => {
      startPage({ owner, endpoint });

      setPreference("dark");

      expect(requests.at(-1).url).to.equal(endpoint);
      expect(requests.at(-1).params.get("owner")).to.equal(owner);
    });
    expect(requests).to.have.length(3);
  });

  it("posts nothing without an endpoint", () => {
    [null, ""].forEach((endpoint) => {
      startPage({ endpoint });

      setPreference("dark");
    });

    expect(requests).to.have.length(0);
  });
});
