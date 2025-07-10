from playwright.sync_api import Page

from playwright_tests.core.basepage import BasePage, Locator


class EditKBArticlePage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        # KB Article edit page locators.
        self.edit_article_page_header = page.locator("h1")
        self.edit_by_another_user_warning_banner = page.locator("div#locked-warning")
        self.edit_by_another_user_warning_message = page.locator("div#locked-warning p")
        self.edit_by_another_user_edit_anyway_option = page.locator("a#unlock-button")

        # KB Article edit page field locators.
        self.edit_article_keywords_field = page.locator("input#id_keywords")
        self.edit_article_search_result_summary_field = page.locator("textarea#id_summary")
        self.edit_article_content_textarea_field = page.locator("textarea#id_content")
        self.edit_article_toggle_syntax_highlight = page.locator(
            "//a[text()='Toggle syntax highlighting']")
        self.edit_article_expiry_date_field = page.locator("input#id_expires")
        self.edit_article_submit_for_review_button = page.locator(
            "article#edit-document").get_by_role(
            "button", name="Submit for Review", exact=True)

        # Submit your changes locators.
        self.edit_article_submit_changes_panel_comment_field = page.locator("input#id_comment")
        self.edit_article_submit_changes_panel_submit_button = page.locator(
            "button#submit-document-form")

    # Edit kb article page actions.
    def get_edit_article_page_header(self) -> str:
        return self._get_text_of_element(self.edit_article_page_header)

    def get_warning_banner_locator(self) -> Locator:
        return self.edit_by_another_user_warning_banner

    def get_edit_article_warning_message(self) -> str:
        paragraphs = self._get_text_of_elements(self.edit_by_another_user_warning_message)
        return ' '.join(paragraphs)

    def click_on_edit_anyway_option(self):
        self._click(self.edit_by_another_user_edit_anyway_option)

    def is_edit_anyway_option_visible(self) -> bool:
        return self._is_element_visible(self.edit_by_another_user_edit_anyway_option)

    # Edit kb article page field actions.
    def get_edit_article_keywords_field_value(self) -> str:
        return self._get_element_input_value(self.edit_article_keywords_field)

    def fill_edit_article_keywords_field(self, text: str):
        self._clear_field(self.edit_article_keywords_field)
        self._fill(self.edit_article_keywords_field, text)

    def get_edit_keywords_field_locator(self) -> Locator:
        return self.edit_article_keywords_field

    def get_edit_article_search_result_summary_text(self) -> str:
        return self._get_text_of_element(self.edit_article_search_result_summary_field)

    def fill_edit_article_search_result_summary_field(self, text: str):
        self._clear_field(self.edit_article_search_result_summary_field)
        self._fill(self.edit_article_search_result_summary_field, text)

    def get_edit_article_content_field_text(self) -> str:
        return self._get_text_of_element(self.edit_article_content_textarea_field)

    def fill_edit_article_content_field(self, text: str):
        # We need to toggle the content field from syntax highlighting to make interaction easier.
        self._click(self.edit_article_toggle_syntax_highlight)
        self._clear_field(self.edit_article_content_textarea_field)
        self._fill(self.edit_article_content_textarea_field, text)

    def get_edit_article_expiry_date_value(self) -> str:
        return self._get_element_attribute_value(self.edit_article_expiry_date_field,"value")

    def fill_edit_article_expiry_date(self, text: str):
        self._type(self.edit_article_expiry_date_field, text, 0)

    # Edit kb button actions.
    def click_submit_for_review_button(self):
        self._click_on_first_item(self.edit_article_submit_for_review_button)

    # Submit you changes panel actions.
    def fill_edit_article_changes_panel_comment(self, text: str):
        self._fill(self.edit_article_submit_changes_panel_comment_field, text)

    def click_edit_article_changes_panel_submit_button(self):
        self._click(self.edit_article_submit_changes_panel_submit_button)
