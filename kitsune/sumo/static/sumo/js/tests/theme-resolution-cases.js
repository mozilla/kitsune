// Shared by the head script and runtime tests so their resolution can't drift apart.
// Each case starts from an anonymous page with nothing stored on a light OS.
const base = {
  loggedIn: false,
  serverPreference: null,
  storedPreference: null,
  storageThrows: false,
  prefersDark: false,
  matchMediaMissing: false,
};

const loggedIn = { loggedIn: true };

// [name, page, expected theme, expected preference]
const cases = [
  ["logged in, server dark, OS light", { ...loggedIn, serverPreference: "dark" }, "dark", "dark"],
  ["logged in, server light, OS dark", { ...loggedIn, serverPreference: "light", prefersDark: true }, "light", "light"],
  ["logged in, server system, OS light", { ...loggedIn, serverPreference: "system" }, "light", "system"],
  ["logged in, server system, OS dark", { ...loggedIn, serverPreference: "system", prefersDark: true }, "dark", "system"],
  ["logged in, server value in the wrong case", { ...loggedIn, serverPreference: "Dark", prefersDark: true }, "dark", "system"],
  ["logged in, no server preference", { ...loggedIn, prefersDark: true }, "dark", "system"],
  ["logged in, server light wins over stored dark", { ...loggedIn, serverPreference: "light", storedPreference: "dark" }, "light", "light"],
  ["logged in, no server preference ignores stored dark", { ...loggedIn, storedPreference: "dark" }, "light", "system"],
  ["anonymous, nothing stored, OS light", {}, "light", "system"],
  ["anonymous, stored light, OS dark", { storedPreference: "light", prefersDark: true }, "light", "light"],
  ["anonymous, stored dark, OS light", { storedPreference: "dark" }, "dark", "dark"],
  ["anonymous, stored system, OS dark", { storedPreference: "system", prefersDark: true }, "dark", "system"],
  ["anonymous, unknown stored value, OS dark", { storedPreference: "sepia", prefersDark: true }, "dark", "system"],
  ["anonymous, stray server preference is ignored", { serverPreference: "dark" }, "light", "system"],
  ["anonymous, storage throws, OS dark", { storageThrows: true, prefersDark: true }, "dark", "system"],
  ["anonymous, matchMedia missing, stored system", { storedPreference: "system", matchMediaMissing: true }, "light", "system"],
  ["anonymous, matchMedia missing, stored dark", { storedPreference: "dark", matchMediaMissing: true }, "dark", "dark"],
];

export const themeResolutionCases = cases.map(([name, page, theme, preference]) => ({
  ...base,
  ...page,
  name,
  expected: { theme, preference },
}));
