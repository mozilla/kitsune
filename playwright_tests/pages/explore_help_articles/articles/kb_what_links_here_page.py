from playwright_tests.core.basepage import BasePage
from playwright.sync_api import Page, Locator


class WhatLinksHerePage(BasePage):
    __what_links_here_list = "//article[@id]//li/a"

    def __init__(self, page: Page):
        super().__init__(page)

    def _get_a_particular_what_links_here_article_locator(self, article_name: str) -> Locator:
        return super()._get_element_locator(f"//article[@id]//li/"
                                            f"a[contains(text(), '{article_name}')]")
