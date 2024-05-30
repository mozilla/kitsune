from playwright_tests.core.basepage import BasePage
from playwright.sync_api import Page, Locator


class UnreviewedLocalizationPage(BasePage):

    def __init__(self, page: Page):
        super().__init__(page)

    def _get_listed_article(self, title: str) -> Locator:
        return super()._get_element_locator(f"//td[@class='doc-title']/a[text()='{title}']")

    def _click_on_a_listed_article(self, title: str):
        super()._click(f"//td[@class='doc-title']/a[text()='{title}']")

    def _get_modified_by_text(self, title: str) -> str:
        return super()._get_text_of_element(f"//td[@class='doc-title']/a[text()='{title}']/"
                                            f"following-sibling::div[@class='users']")
