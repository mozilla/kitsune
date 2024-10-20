from playwright.sync_api import Page, Locator
from playwright_tests.core.basepage import BasePage


class MyProfileDocumentsPage(BasePage):
    # My profile documents locators.
    MY_PROFILE_DOCUMENTS_LOCATORS = {
        "documents_link_list": "//main//a"
    }

    def __init__(self, page: Page):
        super().__init__(page)

    # My profile documents actions.
    def click_on_a_particular_document(self, document_name: str):
        """Click on a particular document"""
        self._click(f"//main//a[contains(text(),'{document_name}')]")

    def get_text_of_document_links(self) -> list[str]:
        """Get text of all document links"""
        return self._get_text_of_elements(self.MY_PROFILE_DOCUMENTS_LOCATORS["documents_link_"
                                                                             "list"])

    def get_a_particular_document_locator(self, document_name: str) -> Locator:
        """Get a particular document locator"""
        return self._get_element_locator(f"//main//a[contains(text(),'{document_name}')]")
