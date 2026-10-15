(function () {
  var root = document.documentElement;
  var preference = null;
  try {
    preference = root.hasAttribute("data-theme-owner")
      ? root.getAttribute("data-theme-preference")
      : window.localStorage.getItem("sumo-theme-preference");
  } catch (e) {}
  if (preference !== "light" && preference !== "dark") {
    preference = "system";
  }
  var theme = preference;
  if (theme === "system") {
    theme = "light";
    try {
      if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
        theme = "dark";
      }
    } catch (e) {}
  }
  root.setAttribute("data-theme", theme);
  root.setAttribute("data-theme-preference", preference);
  var meta = document.querySelector('meta[name="theme-color"]');
  if (!meta) {
    meta = document.createElement("meta");
    meta.name = "theme-color";
    document.head.appendChild(meta);
  }
  meta.content = theme === "dark" ? "#101318" : "#FFFFFF";
})();
