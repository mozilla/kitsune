from playwright.sync_api import Page, ElementHandle
from playwright_tests.core.basepage import BasePage


class FooterSection(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        # Footer section locators.
        self.all_footer_links = page.locator("footer a")
        self.language_selector = page.locator("select#mzp-c-language-switcher-select")
        self.language_selector_options = page.locator(
            "select#mzp-c-language-switcher-select option").all()

    # Footer section actions.
    def get_all_footer_links(self) -> list[ElementHandle]:
        """Returns all footer links."""
        return self._get_element_handles(self.all_footer_links)

    def get_all_footer_locales(self) -> list[str]:
        """Returns all footer locales."""
        return self._get_element_attribute_value(self.language_selector_options, "value")

    def switch_to_a_locale(self, locale: str):
        """Switches to a locale."""
        self._select_option_by_value(self.language_selector, locale)
