from playwright.sync_api import Locator, Page

from playwright_tests.core.basepage import BasePage


class WhatLinksHerePage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.what_links_here_list = self.page.locator("article[id] li a")
        self.what_links_here_for_article = lambda article_name: self.page.locator(
            "article[id] li").get_by_role("link").filter(has_text=article_name)

    def get_a_particular_what_links_here_article_locator(self, article_name: str) -> Locator:
        return self.what_links_here_for_article(article_name)
