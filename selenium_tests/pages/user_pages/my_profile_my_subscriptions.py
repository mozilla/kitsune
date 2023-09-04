from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium_tests.core.base_page import BasePage


class MyProfileMySubscriptions(BasePage):
    __my_profile_user_navbar_options = (By.XPATH, "//ul[@id='user-nav']/li/a")
    __my_profile_user_navbar_selected_element = (By.XPATH, "//a[@class='selected']")

    def __init__(self, driver: WebDriver):
        super().__init__(driver)
