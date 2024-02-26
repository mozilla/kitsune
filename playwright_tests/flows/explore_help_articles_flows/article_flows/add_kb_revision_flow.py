from playwright_tests.core.testutilities import TestUtilities
from playwright.sync_api import Page
from playwright_tests.pages.explore_help_articles.articles.kb_article_page import KBArticlePage
from playwright_tests.pages.explore_help_articles.articles.kb_article_show_history_page import \
    KBArticleShowHistoryPage
from playwright_tests.pages.explore_help_articles.articles.kb_edit_article_page import (
    EditKBArticlePage)


class AddKBArticleRevision(TestUtilities,
                           KBArticlePage,
                           EditKBArticlePage,
                           KBArticleShowHistoryPage):
    def __init__(self, page: Page):
        super().__init__(page)

    def submit_new_kb_revision(self,
                               keywords=None,
                               search_result_summary=None,
                               content=None,
                               expiry_date=None,
                               changes_description=None,
                               is_admin=False
                               ) -> str:

        super()._click_on_edit_article_option()

        # Only admin accounts can update article keywords.
        if is_admin:
            # Keywords step.
            if keywords is None:
                super()._fill_edit_article_keywords_field(
                    self.kb_article_test_data['updated_keywords']
                )
            else:
                super()._fill_edit_article_keywords_field(keywords)

        # Search Result Summary step.
        if search_result_summary is None:
            super()._fill_edit_article_search_result_summary_field(
                self.kb_article_test_data['updated_search_result_summary']
            )
        else:
            super()._fill_edit_article_search_result_summary_field(search_result_summary)

        # Content step.
        if content is None:
            super()._fill_edit_article_content_field(
                self.kb_article_test_data['updated_article_content']
            )
        else:
            super()._fill_edit_article_content_field(content)

        # Expiry date step.
        if expiry_date is None:
            super()._fill_edit_article_expiry_date(
                self.kb_article_test_data['updated_expiry_date']
            )
        else:
            super()._fill_edit_article_expiry_date(expiry_date)

        # Submitting for preview steps
        super()._click_submit_for_review_button()

        if changes_description is None:
            super()._fill_edit_article_changes_panel_comment(
                self.kb_article_test_data['changes_description']
            )
        else:
            super()._fill_edit_article_changes_panel_comment(changes_description)

        super()._click_edit_article_changes_panel_submit_button()

        return super()._get_last_revision_id()
