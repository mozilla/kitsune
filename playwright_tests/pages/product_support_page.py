from playwright.sync_api import Page, Locator
from playwright_tests.core.basepage import BasePage


class ProductSupportPage(BasePage):
    __product_title = "//span[@class='product-title-text']"

    def __init__(self, page: Page):
        super().__init__(page)

    def get_product_title_text(self) -> str:
        return super()._get_text_of_element(self.__product_title)

    def product_product_title_element(self) -> Locator:
        return super()._get_element_locator(self.__product_title)
