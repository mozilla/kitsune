from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class KBCategoryPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """Locators belonging to the KB Category page."""
        self.article_from_list = lambda article_name: page.locator(
            "ul[class='documents'] li").get_by_role("link", name=article_name, exact=True)
