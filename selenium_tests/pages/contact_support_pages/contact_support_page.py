from selenium.webdriver.common.by import By
from selenium_tests.core.base_page import BasePage
from selenium.webdriver.remote.webdriver import WebDriver


class ContactSupportPage(BasePage):
    __contact_support_page_heading = (By.XPATH, "//article/h1")
    __contact_support_page_second_heading = (By.XPATH, "//article/h2")
    __contact_support_firefox_card = (By.XPATH, "//a[@data-event-label='Firefox']")

    def __init__(self, driver: WebDriver):
        super().__init__(driver)
