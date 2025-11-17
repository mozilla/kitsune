from playwright.sync_api import Locator, Page
from playwright_tests.core.basepage import BasePage


class ArticleDiscussionsPage(BasePage):

    def __init__(self, page: Page):
        super().__init__(page)

        """Locators belonging to the Article Discussions page."""
        self.article_discussion_title = lambda article_title: page.locator(
            "td[class='title']").get_by_role("link", name=article_title, exact=True)
