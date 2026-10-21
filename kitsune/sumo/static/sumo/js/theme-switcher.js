import Alpine from "@alpinejs/csp";

import { getPreference, isActive, setPreference } from "sumo/js/theme";

export function themeSwitcher() {
  let onThemeChange = null;

  return {
    init() {
      onThemeChange = (event) => this.check(event.detail?.preference);
      document.addEventListener("sumo:themechange", onThemeChange);
      if (isActive()) {
        this.check(getPreference());
        this.$root.hidden = false;
      }
    },

    destroy() {
      document.removeEventListener("sumo:themechange", onThemeChange);
    },

    choose(event) {
      // Without the runtime a field is a plain form control, so the native choice stands.
      if (!isActive()) {
        return;
      }
      setPreference(event.target.value);
      // The runtime ignores a choice it can't apply; show what is actually in effect.
      this.check(getPreference());
    },

    check(preference) {
      const radio = Array.from(this.$root.querySelectorAll('input[type="radio"]')).find(
        (input) => input.value === preference
      );
      if (radio) {
        radio.checked = true;
      }
    },
  };
}

document.addEventListener("alpine:init", () => {
  Alpine.data("themeSwitcher", themeSwitcher);
});
