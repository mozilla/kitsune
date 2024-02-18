from playwright_tests.core.basepage import BasePage
from playwright.sync_api import Page


class EditKBArticlePage(BasePage):
    # KB Article edit page locators.
    __edit_article_page_header = "//h1"

    # KB Article edit page field locators.
    __edit_article_keywords_field = "//input[@id='id_keywords']"
    __edit_article_search_result_summary_field = "//textarea[@id='id_summary']"
    __edit_article_content_textarea_field = "//textarea[@id='id_content']"
    __edit_article_toggle_syntax_highlight = "//a[text()='Toggle syntax highlighting']"
    __edit_article_expiry_date_field = "//input[@id='id_expires']"
    __edit_article_submit_for_review_button = ("//article[@id='edit-document']//button[text("
                                               ")='Submit for Review']")

    # Submit your changes locators.
    __edit_article_submit_changes_panel_comment_field = "//input[@id='id_comment']"
    __edit_article_submit_changes_panel_submit_button = "//button[@id='submit-document-form']"

    def __init__(self, page: Page):
        super().__init__(page)

    # Edit kb article page actions.
    def _get_edit_article_page_header(self) -> str:
        return super()._get_text_of_element(self.__edit_article_page_header)

    # Edit kb article page field actions.
    def _get_edit_article_keywords_field_value(self) -> str:
        return super()._get_element_input_value(self.__edit_article_keywords_field)

    def _fill_edit_article_keywords_field(self, text: str):
        super()._clear_field(self.__edit_article_keywords_field)
        super()._fill(self.__edit_article_keywords_field, text)

    def _get_edit_article_search_result_summary_text(self) -> str:
        return super()._get_text_of_element(self.__edit_article_search_result_summary_field)

    def _fill_edit_article_search_result_summary_field(self, text: str):
        super()._clear_field(self.__edit_article_search_result_summary_field)
        super()._fill(self.__edit_article_search_result_summary_field, text)

    def _get_edit_article_content_field_text(self) -> str:
        return super()._get_text_of_element(self.__edit_article_content_textarea_field)

    def _fill_edit_article_content_field(self, text: str):
        # We need to toggle the content field from syntax highlighting to make interaction easier.
        super()._click(self.__edit_article_toggle_syntax_highlight)
        super()._clear_field(self.__edit_article_content_textarea_field)
        super()._fill(self.__edit_article_content_textarea_field, text)

    def _get_edit_article_expiry_date_value(self) -> str:
        return super()._get_element_attribute_value(self.__edit_article_expiry_date_field)

    def _fill_edit_article_expiry_date(self, text: str):
        super()._type(self.__edit_article_expiry_date_field, text, 0)

    # Edit kb button actions.
    def _click_submit_for_review_button(self):
        super()._click_on_first_item(self.__edit_article_submit_for_review_button)

    # Submit you changes panel actions.
    def _fill_edit_article_changes_panel_comment(self, text: str):
        super()._fill(self.__edit_article_submit_changes_panel_comment_field, text)

    def _click_edit_article_changes_panel_submit_button(self):
        super()._click(self.__edit_article_submit_changes_panel_submit_button)
