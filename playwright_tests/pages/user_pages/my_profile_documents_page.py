from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class MyProfileDocumentsPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """Locators belonging to the my profile documents page."""
        self.documents_link_list = page.locator("main a")
        self.document_by_name = lambda document_name: page.locator("main").get_by_role(
            "link").filter(has_text=document_name)

    """Actions against the my profile documents page locators."""
    def click_on_a_particular_document(self, document_name: str):
        """Click on a particular document"""
        self._click(self.document_by_name(document_name))

    def get_text_of_document_links(self) -> list[str]:
        """Get text of all document links"""
        return self._get_text_of_elements(self.documents_link_list)
