from playwright.sync_api import Page

from playwright_tests.core.testutilities import TestUtilities
from playwright_tests.messages.kb_article.kb_article_page_messages import KBArticlePageMessages
from playwright_tests.pages.articles.submit_kb_article_page import SubmitKBArticlePage


class AddKbArticleFlow(TestUtilities, SubmitKBArticlePage):

    def __init__(self, page: Page):
        super().__init__(page)

    # Submitting a KB article flow.
    def submit_simple_kb_article(self) -> str:
        self._page.goto(KBArticlePageMessages.CREATE_NEW_KB_ARTICLE_STAGE_URL)

        kb_article_test_data = super().kb_article_test_data

        super().add_text_to_article_form_title_field(kb_article_test_data["kb_article_title"])
        super().select_category_option_by_text(kb_article_test_data["category_options"])
        super()._click_on_a_relevant_to_option_checkbox(kb_article_test_data["relevant_to_option"])
        super()._click_on_a_particular_parent_topic(kb_article_test_data["selected_parent_topic"])
        super()._click_on_a_particular_child_topic_checkbox(
            kb_article_test_data["selected_parent_topic"],
            kb_article_test_data["selected_child_topic"],
        )
        super().add_text_to_related_documents_field(kb_article_test_data["related_documents"])
        super().add_text_to_keywords_field(kb_article_test_data["keywords"])
        super().add_text_to_search_result_summary_field(
            kb_article_test_data["search_result_summary"]
        )

        if not super().is_content_textarea_displayed():
            super().click_on_toggle_syntax_highlight_option()

        super().add_text_to_content_textarea(kb_article_test_data["article_content"])
        self._page.keyboard.press("Enter")
        super().add_text_to_content_textarea(kb_article_test_data["article_heading_one"])
        self._page.keyboard.press("Enter")
        super().add_text_to_content_textarea(kb_article_test_data["article_heading_two"])
        self._page.keyboard.press("Enter")
        super().add_text_to_content_textarea(kb_article_test_data["article_heading_three"])
        super().click_on_insert_media_button()
        super()._click_on_first_image_from_media_panel()
        super()._click_on_insert_media_modal_button()
        super().add_text_to_expiry_date_field(kb_article_test_data["expiry_date"])
        super().click_on_submit_for_review_button()
        super().add_text_to_changes_description_field(kb_article_test_data["changes_description"])
        super().click_on_changes_submit_button()

        posted_article_title = kb_article_test_data["kb_article_title"]

        return posted_article_title
