from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium_tests.core.base_page import BasePage


class KbArticle(BasePage):
    __kb_article_heading = (By.XPATH, "//h1[@class='sumo-page-heading']")

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    def get_text_of_article_title(self) -> str:
        return super()._get_text_of_element(self.__kb_article_heading)
