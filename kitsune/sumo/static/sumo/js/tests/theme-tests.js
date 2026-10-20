import { expect } from "chai";
import sinon from "sinon";

import {
  getPreference,
  getTheme,
  initTheme,
  isActive,
  resolveTheme,
  setPreference,
} from "sumo/js/theme";
import { themeResolutionCases } from "sumo/js/tests/theme-resolution-cases";

const DARK_QUERY = "(prefers-color-scheme: dark)";
const STORAGE_KEY = "sumo-theme-preference";
const CHANNEL_NAME = "sumo-theme";
const CHANGE_EVENT = "sumo:themechange";
const LIGHT_COLOR = "#FFFFFF";
const DARK_COLOR = "#101318";
const OWNER = "owner-key";
const ENDPOINT = "/en-US/users/theme";

describe("theme runtime", () => {
  const root = document.documentElement;
  const restorers = [];
  let sandbox;
  let originalAttributes;
  let originalHead;

  function stubProperty(target, name, descriptor) {
    const original = Object.getOwnPropertyDescriptor(target, name);
    Object.defineProperty(target, name, { configurable: true, ...descriptor });
    restorers.push(() => {
      if (original) {
        Object.defineProperty(target, name, original);
      } else {
        delete target[name];
      }
    });
  }

  function stubStorage() {
    const storage = { setItem: sandbox.spy() };
    const get = sandbox.stub().returns(storage);
    stubProperty(window, "localStorage", { get });
    return { storage, get };
  }

  function stubMatchMedia(prefersDark, { legacy = false } = {}) {
    const listeners = new Set();
    const query = {
      matches: prefersDark,
      listeners,
      setMatches(matches) {
        query.matches = matches;
        listeners.forEach((listener) => listener({ matches, media: DARK_QUERY }));
      },
    };
    if (legacy) {
      query.addListener = sandbox.spy((listener) => listeners.add(listener));
      query.removeListener = sandbox.spy((listener) => listeners.delete(listener));
    } else {
      query.addEventListener = sandbox.spy((type, listener) => listeners.add(listener));
      query.removeEventListener = sandbox.spy((type, listener) => listeners.delete(listener));
    }
    const matchMedia = sandbox.spy((text) => (text === DARK_QUERY ? query : { matches: false }));
    stubProperty(window, "matchMedia", { value: matchMedia });
    return { query, matchMedia };
  }

  function stubBroadcastChannel({ failingPost = false } = {}) {
    const instances = [];
    class FakeBroadcastChannel {
      constructor(name) {
        this.name = name;
        this.listeners = new Set();
        this.postMessage = sandbox.spy(() => {
          if (failingPost) {
            throw new window.DOMException("Channel is closed", "InvalidStateError");
          }
        });
        this.close = sandbox.spy();
        instances.push(this);
      }

      addEventListener(type, listener) {
        this.listeners.add(listener);
      }

      removeEventListener(type, listener) {
        this.listeners.delete(listener);
      }

      receive(data) {
        this.listeners.forEach((listener) => listener({ data }));
      }
    }
    stubProperty(window, "BroadcastChannel", { value: FakeBroadcastChannel });
    return instances;
  }

  // Resolves at once, so the save queue is idle again before the next test.
  function stubFetch() {
    return sandbox.stub(window, "fetch").resolves({
      ok: true,
      status: 200,
      headers: { get: () => "application/json" },
      text: async () => "{}",
    });
  }

  function startPage({
    preference = "system",
    theme = "light",
    owner = null,
    endpoint = null,
    themeColor = true,
  } = {}) {
    root.setAttribute("data-theme", theme);
    root.setAttribute("data-theme-preference", preference);
    if (owner !== null) {
      root.setAttribute("data-theme-owner", owner);
    }
    if (endpoint !== null) {
      root.setAttribute("data-theme-endpoint", endpoint);
    }
    if (themeColor) {
      const meta = document.createElement("meta");
      meta.name = "theme-color";
      meta.content = theme === "dark" ? DARK_COLOR : LIGHT_COLOR;
      document.head.appendChild(meta);
    }
    initTheme();
  }

  function listenForChanges() {
    const listener = sandbox.spy();
    document.addEventListener(CHANGE_EVENT, listener);
    restorers.push(() => document.removeEventListener(CHANGE_EVENT, listener));
    return listener;
  }

  function details(listener) {
    return listener.getCalls().map((call) => call.args[0].detail);
  }

  function dispatchStorage(key, newValue) {
    window.dispatchEvent(new window.StorageEvent("storage", { key, newValue }));
  }

  function expectPage(theme, preference) {
    const themeColors = document.head.querySelectorAll('meta[name="theme-color"]');
    expect(root.getAttribute("data-theme")).to.equal(theme);
    expect(root.getAttribute("data-theme-preference")).to.equal(preference);
    expect(themeColors).to.have.length(1);
    expect(themeColors[0].getAttribute("content")).to.equal(
      theme === "dark" ? DARK_COLOR : LIGHT_COLOR
    );
    expect(getTheme()).to.equal(theme);
    expect(getPreference()).to.equal(preference);
  }

  beforeEach(() => {
    sandbox = sinon.createSandbox();
    originalAttributes = Array.from(root.attributes, ({ name, value }) => [name, value]);
    originalHead = Array.from(document.head.childNodes);
    originalAttributes.forEach(([name]) => root.removeAttribute(name));
    document.head.replaceChildren();
  });

  afterEach(() => {
    Array.from(root.attributes).forEach(({ name }) => root.removeAttribute(name));
    initTheme();
    restorers.splice(0).reverse().forEach((restore) => restore());
    sandbox.restore();
    originalAttributes.forEach(([name, value]) => root.setAttribute(name, value));
    document.head.replaceChildren(...originalHead);
  });

  describe("resolveTheme", () => {
    themeResolutionCases.forEach(({ name, prefersDark, matchMediaMissing, expected }) => {
      it(name, () => {
        expect(resolveTheme(expected.preference, prefersDark && !matchMediaMissing)).to.equal(
          expected.theme
        );
      });
    });

    it("treats an unknown preference as system and only a true OS answer as dark", () => {
      expect(resolveTheme("sepia", true)).to.equal("dark");
      expect(resolveTheme("sepia", false)).to.equal("light");
      [undefined, null, 1, "dark", {}].forEach((prefersDark) => {
        expect(resolveTheme("system", prefersDark), String(prefersDark)).to.equal("light");
      });
    });
  });

  describe("following the OS", () => {
    it("updates the page while the preference is system, without broadcasting or saving", () => {
      const { query } = stubMatchMedia(false);
      const channels = stubBroadcastChannel();
      const fetch = stubFetch();
      startPage({ owner: OWNER, endpoint: ENDPOINT });
      const changes = listenForChanges();

      query.setMatches(true);

      expectPage("dark", "system");
      expect(details(changes)).to.deep.equal([{ theme: "dark", preference: "system" }]);
      expect(changes.firstCall.args[0].target).to.equal(document);

      query.setMatches(false);

      expectPage("light", "system");
      expect(details(changes)).to.have.length(2);
      expect(channels[0].postMessage.called).to.equal(false);
      expect(fetch.called).to.equal(false);
    });

    it("ignores the OS while the preference is explicit and follows it again after system", () => {
      const { query } = stubMatchMedia(false);
      stubStorage();
      startPage();
      setPreference("light");
      const changes = listenForChanges();

      query.setMatches(true);

      expectPage("light", "light");
      expect(changes.called).to.equal(false);

      setPreference("system");
      query.setMatches(false);
      query.setMatches(true);

      expectPage("dark", "system");
    });

    it("uses addListener when the media query has no addEventListener", () => {
      const { query } = stubMatchMedia(false, { legacy: true });
      startPage();

      query.setMatches(true);

      expect(query.addListener.calledOnce).to.equal(true);
      expectPage("dark", "system");
    });

    it("applies an OS change that happened after the head script ran", () => {
      stubMatchMedia(true);
      const changes = listenForChanges();

      startPage({ preference: "system", theme: "light" });

      expectPage("dark", "system");
      expect(details(changes)).to.deep.equal([{ theme: "dark", preference: "system" }]);
    });

    [
      { label: "is missing", matchMedia: undefined, theme: "light" },
      { label: "returns nothing", matchMedia: () => null, theme: "light" },
      { label: "can't be subscribed to", matchMedia: () => ({ matches: true }), theme: "dark" },
    ].forEach(({ label, matchMedia, theme }) => {
      it(`still resolves system when matchMedia ${label}`, () => {
        stubProperty(window, "matchMedia", { value: matchMedia });
        stubStorage();
        const consoleError = sandbox.spy(console, "error");
        startPage({ preference: "light", theme: "light" });

        expect(() => setPreference("system")).to.not.throw();

        expectPage(theme, "system");
        expect(consoleError.called).to.equal(false);
      });
    });

    it("replaces the previous listeners when initialised again", () => {
      const { query } = stubMatchMedia(false);
      stubStorage();
      const channels = stubBroadcastChannel();
      const addEventListener = sandbox.spy(window, "addEventListener");
      const removeEventListener = sandbox.spy(window, "removeEventListener");
      startPage();

      initTheme();

      expect(query.listeners.size).to.equal(1);
      const added = addEventListener.withArgs("storage");
      const removed = removeEventListener.withArgs("storage");
      expect(added.callCount).to.equal(2);
      expect(removed.callCount).to.equal(1);
      expect(removed.firstCall.args[1]).to.equal(added.firstCall.args[1]);

      root.setAttribute("data-theme-owner", OWNER);
      initTheme();
      initTheme();

      expect(channels).to.have.length(2);
      expect(channels[0].close.calledOnce).to.equal(true);
      expect(channels[0].listeners.size).to.equal(0);
      expect(channels[1].listeners.size).to.equal(1);
    });
  });

  describe("setPreference", () => {
    it("dispatches a preference-only change, as from system to dark on a dark OS", () => {
      stubMatchMedia(true);
      stubStorage();
      startPage({ preference: "system", theme: "dark" });
      const changes = listenForChanges();

      setPreference("dark");

      expectPage("dark", "dark");
      expect(details(changes)).to.deep.equal([{ theme: "dark", preference: "dark" }]);
    });

    it("does nothing for the current preference or a value that isn't a preference", () => {
      const channels = stubBroadcastChannel();
      const fetch = stubFetch();
      startPage({ preference: "light", theme: "light", owner: OWNER, endpoint: ENDPOINT });
      const changes = listenForChanges();

      [
        "light",
        undefined,
        null,
        "",
        "sepia",
        "Dark",
        " dark",
        1,
        true,
        ["dark"],
        { toString: () => "dark" },
      ].forEach((value) => setPreference(value));

      expectPage("light", "light");
      expect(changes.called).to.equal(false);
      expect(channels[0].postMessage.called).to.equal(false);
      expect(fetch.called).to.equal(false);
    });

    it("creates the theme-color meta when the page has none", () => {
      stubStorage();
      startPage({ preference: "light", theme: "light", themeColor: false });

      setPreference("dark");

      expectPage("dark", "dark");
    });
  });

  describe("anonymous pages", () => {
    it("writes the choice to localStorage and neither broadcasts nor posts", () => {
      const { storage } = stubStorage();
      const channels = stubBroadcastChannel();
      const fetch = stubFetch();
      startPage({ endpoint: ENDPOINT });

      setPreference("dark");

      expect(storage.setItem.calledOnceWithExactly(STORAGE_KEY, "dark")).to.equal(true);
      expect(channels).to.have.length(0);
      expect(fetch.called).to.equal(false);
    });

    it("applies a valid storage event for the theme key without writing or posting it", () => {
      const { storage } = stubStorage();
      const fetch = stubFetch();
      startPage({ endpoint: ENDPOINT });
      const changes = listenForChanges();

      dispatchStorage("sumo-signed-out", "dark");
      [null, "", "sepia", "Dark", " dark"].forEach((value) => dispatchStorage(STORAGE_KEY, value));
      expect(changes.called).to.equal(false);

      dispatchStorage(STORAGE_KEY, "dark");

      expectPage("dark", "dark");
      expect(details(changes)).to.deep.equal([{ theme: "dark", preference: "dark" }]);
      expect(storage.setItem.called).to.equal(false);
      expect(fetch.called).to.equal(false);
    });

    [
      {
        label: "access to localStorage throws",
        descriptor: {
          get() {
            throw new window.DOMException("Storage is blocked", "SecurityError");
          },
        },
      },
      {
        label: "setItem throws",
        descriptor: {
          value: {
            setItem() {
              throw new window.DOMException("Storage is full", "QuotaExceededError");
            },
          },
        },
      },
    ].forEach(({ label, descriptor }) => {
      it(`still applies the choice when ${label}`, () => {
        stubProperty(window, "localStorage", descriptor);
        const consoleError = sandbox.spy(console, "error");
        startPage();
        const changes = listenForChanges();

        expect(() => setPreference("dark")).to.not.throw();

        expectPage("dark", "dark");
        expect(details(changes)).to.deep.equal([{ theme: "dark", preference: "dark" }]);
        expect(consoleError.called).to.equal(false);
      });
    });
  });

  describe("logged-in pages", () => {
    it("broadcasts and posts a local change, and never touches localStorage", () => {
      const channels = stubBroadcastChannel();
      const fetch = stubFetch();
      const { get } = stubStorage();
      startPage({ owner: OWNER, endpoint: ENDPOINT });

      setPreference("dark");
      dispatchStorage(STORAGE_KEY, "light");

      expect(channels).to.have.length(1);
      expect(channels[0].name).to.equal(CHANNEL_NAME);
      expect(
        channels[0].postMessage.calledOnceWithExactly({ owner: OWNER, preference: "dark" })
      ).to.equal(true);
      expect(fetch.calledOnce).to.equal(true);
      const [url, init] = fetch.firstCall.args;
      const params = new URLSearchParams(init.body);
      expect(url).to.equal(ENDPOINT);
      expect(params.get("preference")).to.equal("dark");
      expect(params.get("owner")).to.equal(OWNER);
      expectPage("dark", "dark");
      expect(get.called).to.equal(false);
    });

    it("applies a valid message from the page's owner without broadcasting or posting it", () => {
      const channels = stubBroadcastChannel();
      const fetch = stubFetch();
      startPage({ owner: OWNER, endpoint: ENDPOINT });
      const changes = listenForChanges();

      [
        { owner: "other-owner", preference: "dark" },
        null,
        "dark",
        [OWNER, "dark"],
        { owner: OWNER, preference: "sepia" },
        { owner: OWNER, preference: "Dark" },
        { owner: OWNER, preference: ["dark"] },
        { owner: OWNER },
        { preference: "dark" },
        { owner: [OWNER], preference: "dark" },
      ].forEach((data) => channels[0].receive(data));
      expect(changes.called).to.equal(false);

      channels[0].receive({ owner: OWNER, preference: "dark" });

      expectPage("dark", "dark");
      expect(details(changes)).to.deep.equal([{ theme: "dark", preference: "dark" }]);
      expect(channels[0].postMessage.called).to.equal(false);
      expect(fetch.called).to.equal(false);
    });

    [
      {
        label: "BroadcastChannel is missing",
        install: () => stubProperty(window, "BroadcastChannel", { value: undefined }),
      },
      {
        label: "the BroadcastChannel constructor throws",
        install: () =>
          stubProperty(window, "BroadcastChannel", {
            value: function BroadcastChannel() {
              throw new window.DOMException("Blocked", "SecurityError");
            },
          }),
      },
      {
        label: "postMessage throws",
        install: () => stubBroadcastChannel({ failingPost: true }),
      },
    ].forEach(({ label, install }) => {
      it(`still applies and posts the choice when ${label}`, () => {
        install();
        const fetch = stubFetch();
        const consoleError = sandbox.spy(console, "error");
        startPage({ owner: OWNER, endpoint: ENDPOINT });

        expect(() => setPreference("dark")).to.not.throw();

        expectPage("dark", "dark");
        expect(fetch.calledOnce).to.equal(true);
        expect(consoleError.called).to.equal(false);
      });
    });
  });

  it("is inert on a page without the head script's attributes", () => {
    const { matchMedia } = stubMatchMedia(true);
    const channels = stubBroadcastChannel();
    const { storage, get } = stubStorage();
    const fetch = stubFetch();
    const addEventListener = sandbox.spy(window.EventTarget.prototype, "addEventListener");
    const changes = listenForChanges();
    addEventListener.resetHistory();

    [
      {},
      { "data-theme": "light", "data-theme-preference": "sepia" },
      { "data-theme-preference": "dark" },
      { "data-theme": "sepia", "data-theme-preference": "dark" },
    ].forEach((attributes) => {
      Array.from(root.attributes).forEach(({ name }) => root.removeAttribute(name));
      Object.entries(attributes).forEach(([name, value]) => root.setAttribute(name, value));
      root.setAttribute("data-theme-owner", OWNER);
      root.setAttribute("data-theme-endpoint", ENDPOINT);
      const before = Array.from(root.attributes, ({ name, value }) => [name, value]);

      initTheme();
      setPreference("dark");
      setPreference("light");

      expect(isActive()).to.equal(false);
      expect(getPreference()).to.equal("system");
      expect(getTheme()).to.equal("light");
      expect(Array.from(root.attributes, ({ name, value }) => [name, value])).to.deep.equal(before);
    });

    expect(addEventListener.called).to.equal(false);
    expect(matchMedia.called).to.equal(false);
    expect(channels).to.have.length(0);
    expect(get.called).to.equal(false);
    expect(storage.setItem.called).to.equal(false);
    expect(fetch.called).to.equal(false);
    expect(changes.called).to.equal(false);
    expect(document.head.querySelectorAll("meta")).to.have.length(0);
  });
});
