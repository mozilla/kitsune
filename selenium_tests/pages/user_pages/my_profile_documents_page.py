from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium_tests.core.base_page import BasePage


class MyProfileDocumentsPage(BasePage):
    __documents_link_list = (By.XPATH, "//main//a")

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    def click_on_a_particular_document(self, document_name: str):
        xpath = (By.XPATH, f"//main//a[contains(text(),'{document_name}')]")
        super()._click(xpath)

    def get_text_of_document_links(self) -> list[str]:
        return super()._get_text_of_elements(self.__documents_link_list)
