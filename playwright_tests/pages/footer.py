from playwright.sync_api import Page, ElementHandle
from playwright_tests.core.basepage import BasePage


class FooterSection(BasePage):
    # Footer section locators.
    FOOTER_SECTION_LOCATORS = {
        "all_footer_links": "//footer//a",
        "language_selector": "//select[@id='mzp-c-language-switcher-select']",
        "language_selector_options": "//select[@id='mzp-c-language-switcher-select']/option"
    }

    def __init__(self, page: Page):
        super().__init__(page)

    # Footer section actions.
    def get_all_footer_links(self) -> list[ElementHandle]:
        """Returns all footer links."""
        return self._get_element_handles(self.FOOTER_SECTION_LOCATORS["all_footer_links"])

    def get_all_footer_locales(self) -> list[str]:
        """Returns all footer locales."""
        return self._get_element_attribute_value(self._get_elements_locators(
            self.FOOTER_SECTION_LOCATORS["language_selector_options"]), "value")

    def switch_to_a_locale(self, locale: str):
        """Switches to a locale."""
        self._select_option_by_value(self.FOOTER_SECTION_LOCATORS["language_selector"], locale)
