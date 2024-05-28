from playwright_tests.core.basepage import BasePage
from playwright.sync_api import Page, Locator


class MostVisitedTranslations(BasePage):

    def __init__(self, page: Page):
        super().__init__(page)

    def _get_a_particular_article_title_locator(self, article_name: str) -> Locator:
        xpath = f"//td/a[text()='{article_name}']"
        return super()._get_element_locator(xpath)

    def _get_updated_localization_status(self, article_name: str) -> str:
        return super()._get_text_of_element(f"//td/a[text()='{article_name}']/../"
                                            f"following-sibling::td[@class='status']/span")

    def _click_on_a_particular_article_status(self, article_name: str):
        super()._click(f"//td/a[text()='{article_name}']/../following-sibling::td[@class='status']"
                       f"/a")

    def _get_a_particular_translation_status(self, article_name: str) -> str:
        return super()._get_text_of_element(f"//td/a[text()='{article_name}']/../"
                                            f"following-sibling::td[@class='status']/a").strip()
