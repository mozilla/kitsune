from playwright.sync_api import Locator, Page

from playwright_tests.core.basepage import BasePage


class ArticleDiscussionsPage(BasePage):

    def __init__(self, page: Page):
        super().__init__(page)
        self.article_discussion_title = lambda article_title: page.locator(
            "td[class='title']").get_by_role("link", name=article_title, exact=True)

    def is_title_for_article_discussion_displayed(self, article_title: str) -> Locator:
        return self.article_discussion_title(article_title)
