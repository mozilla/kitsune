from playwright_tests.core.basepage import BasePage
from playwright.sync_api import Page, Locator


class ArticleDiscussionsPage(BasePage):

    def __init__(self, page: Page):
        super().__init__(page)

    def _is_title_for_article_discussion_displayed(self, article_title: str) -> Locator:
        xpath = f"//td[@class='title']/a[text()='{article_title}']"
        return super()._get_element_locator(xpath)
