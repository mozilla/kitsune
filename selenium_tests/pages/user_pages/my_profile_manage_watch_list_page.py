from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium_tests.core.base_page import BasePage


class MyProfileManageWatchListPage(BasePage):
    __my_profile_user_navbar = (By.XPATH, "//ul[@id='user-nav']/li")
    __my_profile_user_navbar_selected_element = (By.XPATH, "//a[@class='selected']")
    __my_profile_manage_watch_list_page_heading = (By.XPATH, "//h1[@class='sumo-page-heading']")

    def __init__(self, driver: WebDriver):
        super().__init__(driver)
