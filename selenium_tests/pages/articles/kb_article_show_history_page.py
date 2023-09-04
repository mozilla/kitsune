from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium_tests.core.base_page import BasePage


class KBArticleShowHistoryPage(BasePage):
    __delete_this_document_button = (By.XPATH, "//div[@id='delete-doc']/a")
    __delete_this_document_confirmation_delete_button = (By.XPATH, "//div[@class='submit']/input")
    __delete_this_document_confirmation_cancel_button = (By.XPATH, "//div[@class='submit']/a")
    __article_deleted_confirmation_message = (By.XPATH, "//article[@id='delete-document']/h1")

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    def click_on_delete_this_document_button(self):
        super()._click(self.__delete_this_document_button)

    def click_on_confirmation_delete_button(self):
        super()._click(self.__delete_this_document_confirmation_delete_button)

    def is_article_deleted_confirmation_messages_displayed(self) -> bool:
        return super()._is_element_displayed(self.__article_deleted_confirmation_message)
