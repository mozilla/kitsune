const STORAGE_KEY = 'sumo-theme';
const COOKIE_NAME = 'sumo-theme';
// 1 year in seconds
const COOKIE_MAX_AGE = 31536000;

function getSystemTheme() {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function getSavedTheme() {
  const saved = localStorage.getItem(STORAGE_KEY);
  return (saved === 'dark' || saved === 'light') ? saved : null;
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  // Persist as a cookie so Django can pre-render data-theme server-side,
  // eliminating the navigation flash before any JS runs.
  document.cookie = `${COOKIE_NAME}=${theme};path=/;max-age=${COOKIE_MAX_AGE};SameSite=Lax`;
}

/**
 * Alpine component for the theme toggle button.
 * Register via: Alpine.data('themeToggle', themeToggle)
 */
export function themeToggle() {
  return {
    theme: getSavedTheme() || getSystemTheme(),

    get isDark() {
      return this.theme === 'dark';
    },

    toggle() {
      this.theme = this.isDark ? 'light' : 'dark';
      localStorage.setItem(STORAGE_KEY, this.theme);
      applyTheme(this.theme);
    },

    init() {
      // Sync with what the server-rendered data-theme (from cookie) already set.
      const htmlTheme = document.documentElement.getAttribute('data-theme');
      if (htmlTheme === 'dark' || htmlTheme === 'light') {
        this.theme = htmlTheme;
      } else {
        // No server-side cookie yet (e.g. first visit) — apply and set cookie now.
        applyTheme(this.theme);
      }

      // Stay in sync when the user changes preference in another tab.
      window.addEventListener('storage', (e) => {
        if (e.key === STORAGE_KEY) {
          this.theme = (e.newValue === 'dark' || e.newValue === 'light')
            ? e.newValue
            : getSystemTheme();
          applyTheme(this.theme);
        }
      });
    },
  };
}