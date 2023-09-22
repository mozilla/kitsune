from selenium.webdriver.common.by import By
from selenium_tests.core.base_page import BasePage
from selenium.webdriver.remote.webdriver import WebDriver


class KBArticlePage(BasePage):
    __kb_article_heading = (By.XPATH, "//h1[@class='sumo-page-heading']")
    # Editing Tools options
    __editing_tools_show_history_option = (By.XPATH, "//a[text()='Show History']")

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    def click_on_show_history_option(self):
        super()._click(self.__editing_tools_show_history_option)

    def get_text_of_article_title(self) -> str:
        return super()._get_text_of_element(self.__kb_article_heading)
