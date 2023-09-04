from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium_tests.core.base_page import BasePage


class FooterSection(BasePage):
    __all_footer_links = (By.XPATH, "//footer//a")
    __language_selector = (By.ID, "mzp-c-language-switcher-select")

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    def get_all_footer_links(self) -> list[WebElement]:
        return super()._find_elements(self.__all_footer_links)
