from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class EditKBArticlePage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """Locators belonging to the kb article edit page."""
        self.edit_article_page_header = page.locator("h1")
        self.edit_by_another_user_warning_banner = page.locator("div#locked-warning")
        self.edit_by_another_user_edit_anyway_option = page.locator("a#unlock-button")
        self.draft_revision_banner = page.locator("ul.user-messages li").filter(
            has=page.locator("input[name='restore']"))
        self.draft_revision_banner_restore_button = page.locator("input[name='restore']")
        self.draft_revision_banner_discard_button = page.locator("input[name='discard']")

        """Locators belonging to the kb article edit page field section."""
        self.edit_article_keywords_field = page.locator("input#id_keywords")
        self.edit_article_search_result_summary_field = page.locator("textarea#id_summary")
        self.edit_article_content_textarea_field = page.locator("textarea#id_content")
        self.edit_article_toggle_syntax_highlight = page.locator(
            "//a[text()='Toggle syntax highlighting']")
        self.edit_article_expiry_date_field = page.locator("input#id_expires")
        self.edit_article_submit_for_review_button = page.locator(
            "article#edit-document").get_by_role(
            "button", name="Submit for Review", exact=True)
        self.edit_article_save_as_draft_button = page.locator(
            "article#edit-document button.btn-draft").first
        self.edit_article_draft_message = page.locator("div#draft-message")

        """Locators belonging to the submit your changes section."""
        self.edit_article_submit_changes_panel_comment_field = page.locator("input#id_comment")
        self.edit_article_submit_changes_panel_submit_button = page.locator(
            "button#submit-document-form")

    """Actions against the edit kb article page locators."""
    # Edit kb article page actions.
    def click_on_edit_anyway_option(self):
        with self.page.expect_response(lambda response: "steal-lock" in response.url):
            self._click(self.edit_by_another_user_edit_anyway_option)

    def is_edit_anyway_option_visible(self) -> bool:
        return self._is_element_visible(self.edit_by_another_user_edit_anyway_option)

    def click_on_restore_draft_button(self):
        self._click(self.draft_revision_banner_restore_button, wait_for_navigation=True)

    def click_on_discard_draft_button(self):
        self._click(self.draft_revision_banner_discard_button, wait_for_navigation=True)

    """Actions against the kb article page field locators."""
    def fill_edit_article_keywords_field(self, text: str):
        self._clear_field(self.edit_article_keywords_field)
        self._fill(self.edit_article_keywords_field, text)

    def fill_edit_article_search_result_summary_field(self, text: str):
        self._clear_field(self.edit_article_search_result_summary_field)
        self._fill(self.edit_article_search_result_summary_field, text)

    def fill_edit_article_content_field(self, text: str):
        # The plain textarea is easier to drive than the syntax highlighting editor. The toggle
        # is flipped only while the textarea is hidden, and the click is retried until the
        # textarea shows, since a click landing while the editor is still being set up is lost.
        if not self._is_element_visible(self.edit_article_content_textarea_field):
            self._click(self.edit_article_toggle_syntax_highlight,
                        expected_locator=self.edit_article_content_textarea_field)
        self._clear_field(self.edit_article_content_textarea_field)
        self._fill(self.edit_article_content_textarea_field, text)

    def fill_edit_article_expiry_date(self, text: str):
        self._type(self.edit_article_expiry_date_field, text, 0)

    """Actions against the submit your changes section locators."""
    def click_submit_for_review_button(self):
        self._click_on_first_item(self.edit_article_submit_for_review_button)

    def click_on_save_as_draft_button(self):
        with self.page.expect_response(lambda response: "save-draft" in response.url):
            self._click(self.edit_article_save_as_draft_button)

    def fill_edit_article_changes_panel_comment(self, text: str):
        self._fill(self.edit_article_submit_changes_panel_comment_field, text)

    def click_edit_article_changes_panel_submit_button(self):
        self._click(self.edit_article_submit_changes_panel_submit_button)
