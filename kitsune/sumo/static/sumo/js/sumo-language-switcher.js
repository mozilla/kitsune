/**
 * Custom language switcher implementation that handles document translations
 */
export default class SumoLanguageSwitcher {
  constructor() {
    this.langSwitcher = document.querySelector('.mzp-c-language-switcher');
  }

  /**
   * @param {Function} callback - Optional callback to be called after language switch
   */
  init(callback) {
    if (!this.langSwitcher) return;

    this.langSwitcher.addEventListener('change', async (event) => {
      event.preventDefault();
      const targetLocale = event.target.value;
      const currentLocale = this.getCurrentLocale();
      
      if (this.isDocumentPage()) {
        const currentSlug = this.getCurrentSlug();
        try {
          const response = await fetch(`/kb/translate-url?current_slug=${currentSlug}&current_locale=${currentLocale}&target_locale=${targetLocale}`);
          const data = await response.json();

          if (data.found) {
            if (callback) {
              callback(currentLocale, targetLocale);
            }
            window.location.href = data.url;
            return;
          }
        } catch (error) {
          console.error('Error finding translation:', error);
        }
      }

      if (callback) {
        callback(currentLocale, targetLocale);
      }
      const newPath = window.location.pathname.replace(
        new RegExp(`^/${currentLocale}/`),
        `/${targetLocale}/`
      );
      window.location.href = newPath + window.location.search + window.location.hash;
    });
  }

  isDocumentPage() {
    const path = window.location.pathname;
    // Check if it's a KB path but not a special page
    return /\/kb\//.test(path) && 
           !/(\/kb\/(all|revisions|new|category|json|locales|preview-wiki-content|save_draft))$/.test(path);
  }

  getCurrentSlug() {
    const path = window.location.pathname;
    // Extract the slug from KB URLs, handling both direct and sub-paths
    const matches = path.match(/\/kb\/([^\/]+)/);
    return matches && matches.length > 1 ? matches[1] : '';
  }

  getCurrentLocale() {
    return window.location.pathname.split('/')[1];
  }
} 