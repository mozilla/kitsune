from playwright.sync_api import Locator, Page

from playwright_tests.core.basepage import BasePage


class WhatLinksHerePage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """Locators belonging to the 'What links here' page."""
        self.what_links_here_list = self.page.locator("article[id] li a")
        self.what_links_here_for_article = lambda article_name: self.page.locator(
            "article[id] li").get_by_role("link").filter(has_text=article_name)
