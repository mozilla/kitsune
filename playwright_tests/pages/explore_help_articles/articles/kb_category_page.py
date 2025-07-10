from playwright.sync_api import Locator, Page

from playwright_tests.core.basepage import BasePage


class KBCategoryPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.article_from_list = lambda article_name: page.locator(
            "ul[class='documents'] li").get_by_role("link", name=article_name, exact=True)

    def get_a_particular_article_locator_from_list(self, article_name: str) -> Locator:
        return self.article_from_list(article_name)
