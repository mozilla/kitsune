from playwright.sync_api import Page, Locator
from playwright_tests.core.basepage import BasePage


class KBArticleShowHistoryPage(BasePage):
    # Show History delete document section locators.
    __delete_this_document_button = "//div[@id='delete-doc']/a"
    __delete_this_document_confirmation_delete_button = "//div[@class='submit']/input"
    __delete_this_document_confirmation_cancel_button = "//div[@class='submit']/a"
    __article_deleted_confirmation_message = "//article[@id='delete-document']/h1"

    def __init__(self, page: Page):
        super().__init__(page)

    # Delete document actions.
    def _click_on_delete_this_document_button(self):
        super()._click(self.__delete_this_document_button)

    def _click_on_confirmation_delete_button(self):
        super()._click(self.__delete_this_document_confirmation_delete_button)

    def _is_article_deleted_confirmation_messages_displayed(self) -> Locator:
        super()._wait_for_selector(self.__article_deleted_confirmation_message)
        return super()._get_element_locator(self.__article_deleted_confirmation_message)
