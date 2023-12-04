from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class MyProfileDocumentsPage(BasePage):
    __documents_link_list = "//main//a"

    def __init__(self, page: Page):
        super().__init__(page)

    def click_on_a_particular_document(self, document_name: str):
        xpath = f"//main//a[contains(text(),'{document_name}')]"
        super()._click(xpath)

    def get_text_of_document_links(self) -> list[str]:
        return super()._get_text_of_elements(self.__documents_link_list)
