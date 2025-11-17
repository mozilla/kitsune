from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class MostVisitedTranslations(BasePage):

    def __init__(self, page: Page):
        super().__init__(page)

        """Locators belonging to the most visited translations page."""
        self.article_title = lambda article_name: page.locator("td").get_by_role(
            "link", name=article_name, exact=True)
        self.updated_localization_status = lambda article_name: page.locator(
            f"//td/a[text()='{article_name}']/../following-sibling::td[@class='status']/span")
        self.translation_status = lambda article_name: page.locator(
            f"//td/a[text()='{article_name}']/../following-sibling::td[@class='status']/a")


    """Actions against the most visited translations page locators."""
    def get_updated_localization_status(self, article_name: str) -> str:
        return self._get_text_of_element(self.updated_localization_status(article_name))

    def click_on_a_particular_article_status(self, article_name: str):
        self._click(self.translation_status(article_name))

    def get_a_particular_translation_status(self, article_name: str) -> str:
        return self._get_text_of_element(self.translation_status(article_name)).strip()
