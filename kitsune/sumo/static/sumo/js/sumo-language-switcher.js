/**
 * Custom language switcher implementation that handles document translations
 */
export default class SumoLanguageSwitcher {
  constructor() {
    this.currentLocale = this._getCurrentLocale();
    this.isDocumentPage = this._isDocumentPage();
    this.currentSlug = this.isDocumentPage ? this._getCurrentSlug() : null;
  }

  /**
   * @param {Function} callback - Optional callback to be called after language switch
   */
  init(callback) {
    const langSwitcher = document.querySelector('.mzp-c-language-switcher');
    if (!langSwitcher) return;

    langSwitcher.addEventListener('change', async (event) => {
      event.preventDefault();
      const targetLocale = event.target.value;
      
      if (this.isDocumentPage) {
        try {
          const response = await fetch(`/translate-url?current_slug=${this.currentSlug}&current_locale=${this.currentLocale}&target_locale=${targetLocale}`);
          const data = await response.json();

          if (data.found) {
            if (callback) {
              callback(this.currentLocale, targetLocale);
            }
            window.location.href = data.url;
            return;
          }
        } catch (error) {
          console.error('Error finding translation:', error);
        }
      }

      if (callback) {
        callback(this.currentLocale, targetLocale);
      }
      const newPath = window.location.pathname.replace(
        new RegExp(`^/${this.currentLocale}/`),
        `/${targetLocale}/`
      );
      window.location.href = newPath + window.location.search + window.location.hash;
    });
  }

  _isDocumentPage() {
    return /\/(kb|wiki)\//.test(window.location.pathname);
  }

  _getCurrentSlug() {
    const pathParts = window.location.pathname.split('/');
    return pathParts[pathParts.length - 1] || pathParts[pathParts.length - 2];
  }

  _getCurrentLocale() {
    return window.location.pathname.split('/')[1];
  }
} 