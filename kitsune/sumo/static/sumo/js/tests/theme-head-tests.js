import { expect } from "chai";
import sinon from "sinon";
import { parse } from "acorn";

// Matching the file as .txt keeps babel from rewriting it, so the text is the shipped bytes.
import headScript from "theme_head.txt!=!../../../../theme_head.js";
import { themeResolutionCases } from "sumo/js/tests/theme-resolution-cases";

const DARK_QUERY = "(prefers-color-scheme: dark)";
const STORAGE_KEY = "sumo-theme-preference";
const LIGHT_COLOR = "#FFFFFF";
const DARK_COLOR = "#101318";

const storageFailures = [
  {
    label: "access to localStorage throws",
    descriptor: {
      get() {
        throw new window.DOMException("Storage is blocked", "SecurityError");
      },
    },
  },
  {
    label: "getItem throws",
    descriptor: {
      value: {
        getItem() {
          throw new window.DOMException("Storage is unavailable", "QuotaExceededError");
        },
      },
    },
  },
];

describe("theme head script", () => {
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

  function stubStorage(storedValue) {
    const get = sandbox.stub().returns({
      getItem: (key) => (key === STORAGE_KEY ? storedValue : null),
    });
    stubProperty(window, "localStorage", { get });
    return get;
  }

  function stubMatchMedia(prefersDark) {
    const matchMedia = sandbox.spy((query) => ({
      matches: prefersDark && query === DARK_QUERY,
      addEventListener: sandbox.spy(),
      addListener: sandbox.spy(),
    }));
    stubProperty(window, "matchMedia", { value: matchMedia });
    return matchMedia;
  }

  function runHeadScript() {
    new Function(headScript)();
  }

  function themeColors() {
    return document.head.querySelectorAll('meta[name="theme-color"]');
  }

  beforeEach(() => {
    sandbox = sinon.createSandbox();
    originalAttributes = Array.from(root.attributes, ({ name, value }) => [name, value]);
    originalHead = Array.from(document.head.childNodes);
    originalAttributes.forEach(([name]) => root.removeAttribute(name));
    document.head.replaceChildren();
  });

  afterEach(() => {
    restorers.splice(0).reverse().forEach((restore) => restore());
    sandbox.restore();
    Array.from(root.attributes).forEach(({ name }) => root.removeAttribute(name));
    originalAttributes.forEach(([name, value]) => root.setAttribute(name, value));
    document.head.replaceChildren(...originalHead);
  });

  describe("resolution", () => {
    themeResolutionCases.forEach((testCase) => {
      const failures = testCase.storageThrows ? storageFailures : [null];

      failures.forEach((failure) => {
        it(failure ? `${testCase.name} (${failure.label})` : testCase.name, () => {
          if (testCase.loggedIn) {
            root.setAttribute("data-theme-owner", "owner-key");
          }
          if (testCase.serverPreference !== null) {
            root.setAttribute("data-theme-preference", testCase.serverPreference);
          }
          let storageAccess = null;
          if (failure) {
            stubProperty(window, "localStorage", failure.descriptor);
          } else {
            storageAccess = stubStorage(testCase.storedPreference);
          }
          if (testCase.matchMediaMissing) {
            stubProperty(window, "matchMedia", { value: undefined });
          } else {
            stubMatchMedia(testCase.prefersDark);
          }

          runHeadScript();

          const { theme, preference } = testCase.expected;
          expect(root.getAttribute("data-theme")).to.equal(theme);
          expect(root.getAttribute("data-theme-preference")).to.equal(preference);
          expect(themeColors()).to.have.length(1);
          expect(themeColors()[0].getAttribute("content")).to.equal(
            theme === "dark" ? DARK_COLOR : LIGHT_COLOR
          );
          if (testCase.loggedIn) {
            expect(storageAccess.called, "logged-in pages never read localStorage").to.equal(false);
          }
        });
      });
    });

    it("updates an existing theme-color meta instead of adding a second", () => {
      stubStorage("dark");
      stubMatchMedia(false);
      const meta = document.createElement("meta");
      meta.setAttribute("name", "theme-color");
      meta.setAttribute("content", LIGHT_COLOR);
      document.head.appendChild(meta);

      runHeadScript();

      expect(themeColors()).to.have.length(1);
      expect(themeColors()[0]).to.equal(meta);
      expect(meta.getAttribute("content")).to.equal(DARK_COLOR);
    });
  });

  describe("constraints", () => {
    it("registers no listeners and makes no network requests", () => {
      stubStorage("system");
      const matchMedia = stubMatchMedia(true);
      const addEventListener = sandbox.spy(window.EventTarget.prototype, "addEventListener");
      const windowFetch = sandbox.stub(window, "fetch");
      const globalFetch = sandbox.stub(global, "fetch");

      runHeadScript();

      const query = matchMedia.firstCall.returnValue;
      expect(query.addEventListener.called).to.equal(false);
      expect(query.addListener.called).to.equal(false);
      expect(addEventListener.called).to.equal(false);
      expect(windowFetch.called).to.equal(false);
      expect(globalFetch.called).to.equal(false);
    });

    it("is plain ES5 under 1 KB", () => {
      expect(() => parse(headScript, { ecmaVersion: 5 })).to.not.throw();
      expect(Buffer.byteLength(headScript, "utf8")).to.be.below(1024);
    });
  });
});
