from playwright.sync_api import Page, ElementHandle
from playwright_tests.core.basepage import BasePage


class FooterSection(BasePage):

    # Footer section locators.
    __all_footer_links = "//footer//a"
    __language_selector = "//select[@id='mzp-c-language-switcher-select']"
    __language_selector_options = "//select[@id='mzp-c-language-switcher-select']/option"

    def __init__(self, page: Page):
        super().__init__(page)

    # Footer section actions.
    def _get_all_footer_links(self) -> list[ElementHandle]:
        return super()._get_element_handles(self.__all_footer_links)

    def _get_all_footer_locales(self) -> list[str]:
        return super()._get_element_attribute_value(super()._get_elements_locators(
            self.__language_selector_options), "value")

    def _switch_to_a_locale(self, locale: str):
        super()._select_option_by_value(self.__language_selector, locale)
