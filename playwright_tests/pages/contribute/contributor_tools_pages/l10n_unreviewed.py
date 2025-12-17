from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class UnreviewedLocalizationPage(BasePage):

    def __init__(self, page: Page):
        super().__init__(page)

        """Locators belonging to the unreviewed localization page."""
        self.listed_article = lambda title: page.locator("td[class='doc-title']").get_by_role(
            "link", name=title, exact=True)
        self.modified_by_text = lambda title: page.locator(
            "td[class='doc-title']").get_by_role("link", name=title, exact=True).locator(
            "+ div[class='users']")


    """Actions against the unreviewed localization page locators."""
    def click_on_a_listed_article(self, title: str):
        self._click(self.listed_article(title))

    def get_modified_by_text(self, title: str) -> str:
        return self._get_text_of_element(self.modified_by_text(title))
