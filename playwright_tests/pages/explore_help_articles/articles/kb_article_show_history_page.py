from playwright.sync_api import Page, Locator
from playwright_tests.core.basepage import BasePage


class KBArticleShowHistoryPage(BasePage):
    # Show History delete document section locators.
    __delete_this_document_button = "//div[@id='delete-doc']/a"
    __delete_this_document_confirmation_delete_button = "//div[@class='submit']/input"
    __delete_this_document_confirmation_cancel_button = "//div[@class='submit']/a"
    __article_deleted_confirmation_message = "//article[@id='delete-document']/h1"
    __article_revision_list_items = ("//div[@id='revision-list']//tbody/tr[contains(@id,"
                                     "'rev-list')]")

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

    def _get_last_revision_id(self) -> str:
        revisions = super()._get_elements_locators(self.__article_revision_list_items)
        return super()._get_element_locator_attribute_value(
            revisions[0], "id"
        )

    # For unreviewed revisions but user session doesn't permit review.
    def _get_revision_status(self, revision_id) -> str:
        xpath = f"//tr[@id='{revision_id}']/td[@class='status']/span"
        return super()._get_text_of_element(xpath)

    # For unreviewed revisions but user session permits review.
    def _get_status_of_reviewable_revision(self, revision_id):
        xpath = f"//tr[@id='{revision_id}']/td[@class='status']/a"
        return super()._get_text_of_element(xpath)

    def _click_on_review_revision(self, revision_id):
        xpath = f"//tr[@id='{revision_id}']/td[@class='status']/a"
        super()._click(xpath)
