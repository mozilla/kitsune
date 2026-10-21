import { savePreference } from "sumo/js/theme-persistence";

const PREFERENCES = ["system", "light", "dark"];
const STORAGE_KEY = "sumo-theme-preference";
const CHANNEL_NAME = "sumo-theme";
const CHANGE_EVENT = "sumo:themechange";
const DARK_QUERY = "(prefers-color-scheme: dark)";
const THEME_COLORS = { light: "#FFFFFF", dark: "#101318" };

let active = false;
let owner = null;
let currentPreference = "system";
let currentTheme = "light";
let darkQuery = null;
let channel = null;
let teardown = null;

function isPreference(value) {
  return PREFERENCES.includes(value);
}

export function resolveTheme(preference, prefersDark) {
  if (preference === "light" || preference === "dark") {
    return preference;
  }
  return prefersDark === true ? "dark" : "light";
}

export function getPreference() {
  return currentPreference;
}

export function getTheme() {
  return currentTheme;
}

export function isActive() {
  return active;
}

function applyPreference(preference) {
  const theme = resolveTheme(preference, darkQuery?.matches === true);
  if (preference === currentPreference && theme === currentTheme) {
    return false;
  }
  currentPreference = preference;
  currentTheme = theme;

  const root = document.documentElement;
  root.setAttribute("data-theme", theme);
  root.setAttribute("data-theme-preference", preference);
  let meta = document.querySelector('meta[name="theme-color"]');
  if (!meta) {
    meta = document.createElement("meta");
    meta.name = "theme-color";
    document.head.appendChild(meta);
  }
  meta.content = THEME_COLORS[theme];

  document.dispatchEvent(new CustomEvent(CHANGE_EVENT, { detail: { theme, preference } }));
  return true;
}

export function setPreference(preference) {
  if (!active || !isPreference(preference) || !applyPreference(preference)) {
    return;
  }

  if (owner === null) {
    try {
      window.localStorage.setItem(STORAGE_KEY, preference);
    } catch {
      // Blocked or full storage must not undo a choice that is already applied.
    }
    return;
  }

  if (channel) {
    try {
      channel.postMessage({ owner, preference });
    } catch {
      // A closed channel throws; other tabs just keep their theme.
    }
  }
  savePreference(preference);
}

// Runs once on load; exported so tests can re-run it against a prepared page.
export function initTheme() {
  if (teardown) {
    teardown();
    teardown = null;
  }
  active = false;
  owner = null;
  currentPreference = "system";
  currentTheme = "light";
  darkQuery = null;
  channel = null;

  const root = document.documentElement;
  const preference = root.getAttribute("data-theme-preference");
  const theme = root.getAttribute("data-theme");
  // Without the head script's attributes the feature is off for this page.
  if (!isPreference(preference) || (theme !== "light" && theme !== "dark")) {
    return;
  }
  active = true;
  currentPreference = preference;
  currentTheme = theme;
  owner = root.getAttribute("data-theme-owner");

  const cleanups = [];

  try {
    const query = window.matchMedia(DARK_QUERY);
    if (query) {
      darkQuery = query;
      const onSystemChange = () => {
        if (currentPreference === "system") {
          applyPreference("system");
        }
      };
      if (typeof query.addEventListener === "function") {
        query.addEventListener("change", onSystemChange);
        cleanups.push(() => query.removeEventListener("change", onSystemChange));
      } else if (typeof query.addListener === "function") {
        query.addListener(onSystemChange);
        cleanups.push(() => query.removeListener(onSystemChange));
      }
    }
  } catch {
    // matchMedia is missing or unsupported: system resolves to light.
  }

  if (owner === null) {
    const onStorage = (event) => {
      if (event.key === STORAGE_KEY && isPreference(event.newValue)) {
        applyPreference(event.newValue);
      }
    };
    window.addEventListener("storage", onStorage);
    cleanups.push(() => window.removeEventListener("storage", onStorage));
  } else {
    try {
      const ownChannel = new window.BroadcastChannel(CHANNEL_NAME);
      const onMessage = ({ data }) => {
        if (data?.owner === owner && isPreference(data.preference)) {
          applyPreference(data.preference);
        }
      };
      ownChannel.addEventListener("message", onMessage);
      channel = ownChannel;
      cleanups.push(() => {
        ownChannel.removeEventListener("message", onMessage);
        ownChannel.close();
      });
    } catch {
      // BroadcastChannel is missing or blocked: tabs only sync after a reload.
    }
  }

  teardown = () => cleanups.forEach((cleanup) => cleanup());

  // The OS setting may have changed since the head script resolved it.
  if (darkQuery !== null && currentPreference === "system") {
    applyPreference("system");
  }
}

initTheme();
