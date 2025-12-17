from playwright.sync_api import Locator, Page

from playwright_tests.core.basepage import BasePage


class TranslateArticlePage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.translating_an_unready_article_banner = page.locator("ul[class='user-messages'] li")
        self.article_translation_page_title = page.locator("h1[class='sumo-page-heading']")
        self.translation_title_field = page.locator("input#id_title")
        self.translation_slug_field = page.locator("input#id_slug")
        self.allow_article_comments_label = page.locator("label[for='id_allow_discussion']")
        self.translation_keyword_field = page.locator("input#id_keywords")
        self.translation_summary_field = page.locator("textarea#id_summary")
        self.translation_english_readonly_field = page.locator("div#content-or-diff textarea")
        self.translation_text = page.locator("textarea#id_content")
        self.change_body_view = page.locator("div#editor_wrapper + a")
        self.send_translation_for_approval_button = page.locator(
            "button[class*='btn-submit']").first
        self.save_translation_as_draft_button = page.locator("button[class*='btn-draft']").first
        self.draft_saved_successfully_message = page.locator("div#draft-message")
        self.translation_changes_description_input_field = page.locator("input#id_comment")
        self.translation_changes_description_submit_button = page.locator(
            "button#submit-document-form")
        self.locale_from_list = lambda locale: page.locator("article#select-locale").get_by_role(
            "link", name=f"({locale})")

    def click_on_locale_from_list(self, locale: str):
        self._click(self.locale_from_list(locale))

    def get_text_of_article_unready_for_translation_banner(self) -> str:
        return self._get_text_of_element(self.translating_an_unready_article_banner)

    def get_unready_for_translation_banner(self) -> Locator:
        return self.translating_an_unready_article_banner

    def get_translate_page_title(self) -> str:
        return self._get_text_of_element(self.article_translation_page_title)

    def fill_translation_title_field(self, text: str):
        self._fill(self.translation_title_field, text)

    def fill_translation_slug_field(self, text: str):
        self._fill(self.translation_slug_field, text)

    def click_on_allow_translated_article_comments_checkbox(self):
        self._click(self.allow_article_comments_label)

    def fill_translated_article_keyword(self, text: str):
        self._fill(self.translation_keyword_field, text)

    def fill_translated_article_summary(self, text: str):
        self._fill(self.translation_summary_field, text)

    def get_text_of_english_version(self) -> str:
        return self._get_text_of_element(self.translation_english_readonly_field)

    def fill_body_translation_field(self, text: str):
        self._click(self.change_body_view)
        self._clear_field(self.translation_text)
        self._fill(self.translation_text, text)

    def click_on_submit_translation_for_approval_button(self):
        self.send_translation_for_approval_button.first.click()

    def fill_translation_changes_description_field(self, text: str):
        self._fill(self.translation_changes_description_input_field, text)

    def click_on_description_submit_button(self):
        self._click(self.translation_changes_description_submit_button)

    def click_on_save_translation_as_draft_button(self):
        self.save_translation_as_draft_button.first.click()

    def get_draft_success_message_locator(self) -> Locator:
        return self.draft_saved_successfully_message
