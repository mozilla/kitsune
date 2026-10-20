import Alpine from "@alpinejs/csp";
import { expect } from "chai";

import { getPreference, initTheme, setPreference } from "sumo/js/theme";
import "sumo/js/theme-switcher";

const STORAGE_KEY = "sumo-theme-preference";
const CHANGE_EVENT = "sumo:themechange";
// DOM constructors the Alpine CSP evaluator checks against that mocha's jsdom setup doesn't expose.
const ALPINE_GLOBALS = ["Node", "ShadowRoot", "HTMLIFrameElement", "HTMLScriptElement"];

// Mirrors the markup of the theme_switcher macro in common_macros.html.
function switcherMarkup(prefix, { field = false, checked = null } = {}) {
  const name = field ? "theme_preference" : `${prefix}-theme`;
  const options = ["system", "light", "dark"]
    .map(
      (value) => `
      <input type="radio" id="${prefix}-theme-${value}" name="${name}" value="${value}"
        ${value === checked ? "checked" : ""}>
      <label for="${prefix}-theme-${value}">${value}</label>`
    )
    .join("");
  return `
    <fieldset class="sumo-theme-switcher" x-data="themeSwitcher" @change="choose"${field ? "" : " hidden"}>
      <legend class="sumo-theme-switcher--legend">Appearance</legend>
      <div class="sumo-theme-switcher--options">${options}</div>
    </fieldset>`;
}

describe("theme switcher", () => {
  const root = document.documentElement;
  const originalGlobals = {};
  let container;
  let originalAttributes;
  let originalHead;

  function startPage({ preference = "system", theme = "light" } = {}) {
    root.setAttribute("data-theme", theme);
    root.setAttribute("data-theme-preference", preference);
    initTheme();
  }

  // Returns the mounted switchers, keyed by prefix.
  function mount(switchers) {
    container = document.createElement("div");
    container.innerHTML = Object.entries(switchers)
      .map(([prefix, options]) => switcherMarkup(prefix, options))
      .join("");
    document.body.appendChild(container);
    Alpine.initTree(container);
    return Object.fromEntries(
      Object.keys(switchers).map((prefix) => [
        prefix,
        container.querySelector(`#${prefix}-theme-system`).closest("fieldset"),
      ])
    );
  }

  function radio(switcher, value) {
    return switcher.querySelector(`input[value="${value}"]`);
  }

  function checkedValues(switcher) {
    return Array.from(switcher.querySelectorAll("input:checked"), (input) => input.value);
  }

  function dispatchThemeChange(detail) {
    document.dispatchEvent(new window.CustomEvent(CHANGE_EVENT, { detail }));
  }

  before(() => {
    ALPINE_GLOBALS.forEach((name) => {
      originalGlobals[name] = Object.getOwnPropertyDescriptor(global, name);
      global[name] = window[name];
    });
    document.dispatchEvent(new window.CustomEvent("alpine:init"));
  });

  after(() => {
    ALPINE_GLOBALS.forEach((name) => {
      if (originalGlobals[name]) {
        Object.defineProperty(global, name, originalGlobals[name]);
      } else {
        delete global[name];
      }
    });
  });

  beforeEach(() => {
    originalAttributes = Array.from(root.attributes, ({ name, value }) => [name, value]);
    originalHead = Array.from(document.head.childNodes);
    originalAttributes.forEach(([name]) => root.removeAttribute(name));
  });

  afterEach(() => {
    if (container) {
      Alpine.destroyTree(container);
      container.remove();
      container = null;
    }
    Array.from(root.attributes).forEach(({ name }) => root.removeAttribute(name));
    initTheme();
    window.localStorage.removeItem(STORAGE_KEY);
    originalAttributes.forEach(([name, value]) => root.setAttribute(name, value));
    document.head.replaceChildren(...originalHead);
  });

  it("reveals every switcher and checks the current preference, whatever the server checked", () => {
    startPage({ preference: "light" });

    const { footer, menu, settings } = mount({
      footer: {},
      menu: {},
      settings: { field: true, checked: "dark" },
    });

    [footer, menu, settings].forEach((switcher) => {
      expect(switcher.hidden).to.equal(false);
      expect(checkedValues(switcher)).to.deep.equal(["light"]);
    });
  });

  it("leaves switchers to the markup while the runtime is inactive", () => {
    initTheme();
    const { footer, settings } = mount({ footer: {}, settings: { field: true, checked: "light" } });
    const events = [];
    const listener = (event) => events.push(event.detail);
    document.addEventListener(CHANGE_EVENT, listener);

    radio(settings, "dark").click();
    document.removeEventListener(CHANGE_EVENT, listener);

    expect(footer.hidden).to.equal(true);
    expect(checkedValues(footer)).to.deep.equal([]);
    expect(settings.hidden).to.equal(false);
    expect(checkedValues(settings)).to.deep.equal(["dark"]);
    expect(getPreference()).to.equal("system");
    expect(events).to.deep.equal([]);
    expect(window.localStorage.getItem(STORAGE_KEY)).to.equal(null);
  });

  it("applies a choice and shows it in every switcher on the page", () => {
    startPage();
    const { footer, menu } = mount({ footer: {}, menu: {} });

    radio(menu, "dark").click();

    expect(getPreference()).to.equal("dark");
    expect(root.getAttribute("data-theme")).to.equal("dark");
    expect(window.localStorage.getItem(STORAGE_KEY)).to.equal("dark");
    expect(checkedValues(footer)).to.deep.equal(["dark"]);
    expect(checkedValues(menu)).to.deep.equal(["dark"]);
  });

  it("puts the radio back when the runtime rejects the chosen value", () => {
    startPage();
    const { footer } = mount({ footer: {} });
    const tampered = radio(footer, "dark");
    tampered.value = "sepia";

    tampered.click();

    expect(getPreference()).to.equal("system");
    expect(checkedValues(footer)).to.deep.equal(["system"]);
  });

  it("ignores an event without a known preference", () => {
    startPage({ preference: "light" });
    const { footer } = mount({ footer: {} });

    dispatchThemeChange({ theme: "dark", preference: "sepia" });
    dispatchThemeChange(null);
    dispatchThemeChange({ theme: "dark" });

    expect(checkedValues(footer)).to.deep.equal(["light"]);
  });

  it("stops following changes once destroyed", () => {
    startPage();
    const { footer } = mount({ footer: {} });

    Alpine.destroyTree(container);
    setPreference("dark");

    expect(checkedValues(footer)).to.deep.equal(["system"]);
  });
});
