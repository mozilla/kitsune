from playwright.sync_api import Page, Locator
from playwright_tests.core.basepage import BasePage


class KBArticleShowHistoryPage(BasePage):
    # Show History page locators.
    __show_history_page_header = "//h1[@class='title sumo-page-subheading']"
    __show_history_category_link = "//dt[text()='Category:']/following-sibling::dd/a"
    __show_history_revision_history_for = ("//dt[text()='Revision history "
                                           "for:']/following-sibling::dd[1]")
    __ready_for_l10_modal_submit_button = "//button[@id='submit-l10n']"
    __l10n_modal = "//div[@class='mzp-c-modal-window']"

    # Document contributors locators
    __show_history_page_banner = "//li[@class='mzp-c-notification-bar mzp-t-success']/p"
    __all_contributors_list_items = "//ul[@class='avatar-wrap']/li"
    __all_contributors_usernames = "//ul[@class='avatar-wrap']//a/span"
    __edit_contributors_option = "//section[@id='contributors']//a[@class='edit']"
    __add_contributor_input_field = "//input[@id='token-input-id_users']"
    __add_contributor_button = "//input[@value='Add Contributor']"
    __delete_contributor_confirmation_page_header = "//h1[@class='title sumo-page-subheading']"
    __delete_contributor_confirmation_page_cancel_button = "//a[text()='Cancel']"
    __delete_contributor_confirmation_page_submit_button = "//input[@value='Remove contributor']"

    # Show History delete document section locators.
    __delete_this_document_button = "//div[@id='delete-doc']/a"
    __delete_this_document_confirmation_delete_button = "//div[@class='submit']/input"
    __delete_this_document_confirmation_cancel_button = "//div[@class='submit']/a"
    __article_deleted_confirmation_message = "//article[@id='delete-document']/h1"
    __article_revision_list_items = ("//div[@id='revision-list']//tbody/tr[contains(@id,"
                                     "'rev-list')]")
    __unable_to_delete_revision_page_header = "//article[@id='delete-revision']/h1"
    __unable_to_delete_revision_page_subheader = "//article[@id='delete-revision']/p"
    __unable_to_delete_revision_page_go_back_to_document_history = "//div[@class='submit']/a"

    def __init__(self, page: Page):
        super().__init__(page)

    # Page actions.
    def get_l10n_modal_locator(self) -> Locator:
        return self._get_element_locator(self.__l10n_modal)

    def get_show_history_page_banner(self) -> str:
        return self._get_text_of_element(self.__show_history_page_banner)

    def get_show_history_page_title(self) -> str:
        return self._get_text_of_element(self.__show_history_page_header)

    def get_show_history_category_text(self) -> str:
        return self._get_text_of_element(self.__show_history_category_link)

    def click_on_show_history_category(self):
        self._click(self.__show_history_category_link)

    def get_show_history_revision_for_locale_text(self) -> str:
        return self._get_text_of_element(self.__show_history_revision_history_for)

    def click_on_a_particular_revision_editor(self, revision_id: str, username: str):
        self._click(f"//tr[@id='{revision_id}']//a[contains(text(),'{username}')]")

    def click_on_ready_for_l10n_option(self, revision_id: str):
        self._click(f"//tr[@id='{revision_id}']/td[@class='l10n']/a")

    def get_ready_for_localization_status(self, revision_id: str) -> Locator:
        return self._get_element_locator(f"//tr[@id='{revision_id}']/td[@class='l10n']/"
                                         f"a[@class='yes']")

    def click_on_submit_l10n_readiness_button(self):
        self._click(self.__ready_for_l10_modal_submit_button)

    # Delete document actions.
    def click_on_delete_this_document_button(self):
        self._click(self.__delete_this_document_button)

    def get_delete_this_document_button_locator(self) -> Locator:
        return self._get_element_locator(self.__delete_this_document_button)

    def is_delete_button_displayed(self) -> bool:
        return self._is_element_visible(self.__delete_this_document_button)

    def click_on_confirmation_delete_button(self):
        self._click(self.__delete_this_document_confirmation_delete_button)

    def click_on_confirmation_cancel_button(self):
        self._click(self.__delete_this_document_confirmation_cancel_button)

    def is_article_deleted_confirmation_messages_displayed(self) -> Locator:
        self._wait_for_selector(self.__article_deleted_confirmation_message)
        return self._get_element_locator(self.__article_deleted_confirmation_message)

    def get_last_revision_id(self) -> str:
        self._wait_for_selector(self.__article_revision_list_items)
        revisions = self._get_elements_locators(self.__article_revision_list_items)
        return self._get_element_attribute_value(
            revisions[0], "id"
        )

    # For unreviewed revisions but user session doesn't permit review.
    def click_on_a_revision_date(self, revision_id):
        self._click(f"//tr[@id='{revision_id}']/td[@class='date']/a")

    def get_revision_time(self, revision_id) -> str:
        return self._get_text_of_element(f"//tr[@id='{revision_id}']/td[@class='date']/a/time")

    def get_revision_status(self, revision_id) -> str:
        return self._get_text_of_element(f"//tr[@id='{revision_id}']/td[@class='status']/span")

    def get_a_particular_revision_locator(self, revision_id) -> Locator:
        return self._get_element_locator(f"//tr[@id='{revision_id}']")

    # For unreviewed revisions but user session permits review.
    def get_status_of_reviewable_revision(self, revision_id):
        return self._get_text_of_element(f"//tr[@id='{revision_id}']/td[@class='status']/a")

    def click_on_review_revision(self, revision_id):
        self._click(f"//tr[@id='{revision_id}']/td[@class='status']/a")

    def get_delete_revision_button_locator(self, revision_id) -> Locator:
        return self._get_element_locator(f"//tr[@id='{revision_id}']/td[@class='delete']/a")

    def click_on_delete_revision_button(self, revision_id):
        return self._click(f"//tr[@id='{revision_id}']/td[@class='delete']/a")

    def get_unable_to_delete_revision_header(self) -> str:
        return self._get_text_of_element(self.__unable_to_delete_revision_page_header)

    def get_unable_to_delete_revision_subheader(self) -> str:
        return self._get_text_of_element(self.__unable_to_delete_revision_page_subheader)

    def click_go_back_to_document_history_option(self):
        self._click(self.__unable_to_delete_revision_page_go_back_to_document_history)

    # Article contribution actions.
    def click_on_edit_contributors_option(self):
        self._click(self.__edit_contributors_option)

    def get_edit_contributors_option_locator(self) -> Locator:
        return self._get_element_locator(self.__edit_contributors_option)

    def add_a_new_contributor_inside_the_contributor_field(self, text: str):
        # Adding contributor username inside the contributor field.
        self._type(self.__add_contributor_input_field, text, 100)

    def click_on_new_contributor_search_result(self, username: str):
        self._click(f"//div[@class='name_search']/b[contains(text(), '{username}')]")

    def click_on_add_contributor_button(self):
        self._click(self.__add_contributor_button)

    def click_on_a_particular_contributor(self, username: str):
        self._click(f"//span[text()='{username}']/..")

    def click_on_delete_button_for_a_particular_contributor(self, username: str):
        self._click(f"//span[text()='{username}']/../..//a[@class='remove-button']")

    def get_list_of_all_contributors(self) -> list[str]:
        return self._get_text_of_elements(self.__all_contributors_usernames)

    def get_delete_contributor_confirmation_page_header(self) -> str:
        return self._get_text_of_element(self.__delete_contributor_confirmation_page_header)

    def click_on_delete_contributor_confirmation_page_cancel_button(self):
        self._click(self.__delete_contributor_confirmation_page_cancel_button)

    def click_on_delete_contributor_confirmation_page_confirm_button(self):
        self._click(self.__delete_contributor_confirmation_page_submit_button)

    def get_all_contributors_locator(self) -> Locator:
        return self._get_element_locator(self.__all_contributors_list_items)

    def get_revision_significance(self, revision_id: str) -> str:
        return self._get_text_of_element(f"//tr[@id='{revision_id}']"
                                         f"/td[@class='significance']").strip()
