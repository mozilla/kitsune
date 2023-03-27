from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium_tests.core.base_page import BasePage


class ContributePage(BasePage):
    __breadcrumbs = (By.XPATH, "//ol[@id='breadcrumbs']/li")
    __way_to_contribute_cards = (By.XPATH, "//ul[@class='svelte-5c0h9n']/a")

    def __init__(self, driver: WebDriver):
        super().__init__(driver)
