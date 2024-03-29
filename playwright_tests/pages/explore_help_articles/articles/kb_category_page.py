from playwright.sync_api import Locator

from playwright_tests.core.basepage import BasePage


class KBCategoryPage(BasePage):

    def _get_a_particular_article_locator_from_list(self, article_name: str) -> Locator:
        xpath = f"//ul[@class='documents']/li/a[text()='{article_name}']"
        return super()._get_element_locator(xpath)
