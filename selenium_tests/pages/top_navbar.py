from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium_tests.core.base_page import BasePage


class TopNavbar(BasePage):
    __menu_titles = (
        By.XPATH,
        "//div[@id='main-navigation']//a[contains(@class,'mzp-c-menu-title')]",
    )
    __contribute_option = (By.XPATH, "//a[contains(text(),'Contribute')]")

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    def get_available_menu_titles(self):
        super()._get_text_of_elements(self.__menu_titles)

    def click_on_contribute_top_navbar_option(self):
        super()._click(self.__contribute_option)
