from playwright.sync_api import Locator, Page

from playwright_tests.core.basepage import BasePage


class UnreviewedLocalizationPage(BasePage):

    def __init__(self, page: Page):
        super().__init__(page)
        self.listed_article = lambda title: page.locator("td[class='doc-title']").get_by_role(
            "link", name=title, exact=True)
        self.modified_by_text = lambda title: page.locator(
            "td[class='doc-title']").get_by_role("link", name=title, exact=True).locator(
            "+ div[class='users']")

    def get_listed_article(self, title: str) -> Locator:
        return self.listed_article(title)

    def click_on_a_listed_article(self, title: str):
        self._click(self.listed_article(title))

    def get_modified_by_text(self, title: str) -> str:
        return self._get_text_of_element(self.modified_by_text(title))
