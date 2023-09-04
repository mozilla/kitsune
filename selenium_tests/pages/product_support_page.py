from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium_tests.core.base_page import BasePage


class ProductSupportPage(BasePage):
    __product_title = (By.XPATH, "//span[@class='product-title-text']")

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    def get_product_title_text(self) -> str:
        return super()._get_text_of_element(self.__product_title)

    def is_product_product_title_displayed(self) -> bool:
        return super()._is_element_displayed(self.__product_title)
