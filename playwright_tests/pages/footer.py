from playwright.sync_api import ElementHandle, Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

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

    def switch_to_a_locale(self, locale: str, max_retries=3) -> None:
        """Switches to a locale with a retry mechanism."""
        print("Trying to switch the locale")
        attempts = 0
        while attempts < max_retries:
            self._select_option_by_value(self.language_selector, locale)
            try:
                self.page.wait_for_url("**/" + locale + "/**", timeout=4000)
                return
            except PlaywrightTimeoutError:
                print("Switching to locale failed, retrying...")
                self.page.reload()
                if locale in self.page.url:
                    return
            attempts += 1
            raise PlaywrightTimeoutError(
                f"Failed to switch to locale '{locale}' after {max_retries} attempts.")
