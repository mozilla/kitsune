from playwright.sync_api import Page, ElementHandle
from playwright_tests.core.basepage import BasePage


class FooterSection(BasePage):
    __all_footer_links = "//footer//a"
    __language_selector = "mzp-c-language-switcher-select"

    def __init__(self, page: Page):
        super().__init__(page)

    def get_all_footer_links(self) -> list[ElementHandle]:
        return super()._get_element_handles(self.__all_footer_links)
