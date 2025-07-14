from playwright.sync_api import Page

from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.explore_help_articles.kb_article_revision_page_messages import (
    KBArticleRevision,
)
from playwright_tests.pages.explore_help_articles.articles.kb_article_page import KBArticlePage
from playwright_tests.pages.explore_help_articles.articles.kb_edit_article_meta import (
    KBArticleEditMetadata,
)
from playwright_tests.pages.explore_help_articles.articles.kb_edit_article_page import (
    EditKBArticlePage,
)
from playwright_tests.pages.explore_help_articles.articles.submit_kb_article_page import (
    SubmitKBArticlePage,
)


class EditArticleMetaFlow:

    def __init__(self, page: Page):
        self.utilities = Utilities(page)
        self.kb_article_edit_metadata_page = KBArticleEditMetadata(page)
        self.submit_kb_article_page = SubmitKBArticlePage(page)
        self.kb_article_page = KBArticlePage(page)
        self.edit_kb_article_page = EditKBArticlePage(page)

    def edit_article_metadata(self, **kwargs):
        return self.utilities.re_call_function_on_error(
            lambda: self._edit_article_metadata(**kwargs)
        )

    def _edit_article_metadata(self, title=None, slug=None, category=None, product=None,
                               topics=None, obsolete=False, discussions=True, needs_change=False,
                               needs_change_comment=False, restricted_to_groups: list[str] = None,
                               related_documents: list[str] = None, single_group=""):

        if KBArticleRevision.KB_EDIT_METADATA not in self.utilities.get_page_url():
            self.kb_article_page.click_on_edit_article_metadata()

        if self.edit_kb_article_page.is_edit_anyway_option_visible():
            self.edit_kb_article_page.click_on_edit_anyway_option()

        if restricted_to_groups or single_group:
            for group in (restricted_to_groups or []) + ([single_group] if single_group else []):
                (self.kb_article_edit_metadata_page.
                 add_and_select_restrict_visibility_group_metadata(group))

        if title:
            self.kb_article_edit_metadata_page.add_text_to_title_field(title)

        if slug:
            self.kb_article_edit_metadata_page.add_text_to_slug_field(slug)

        if category:
            self.kb_article_edit_metadata_page.select_category(category)

        if product:
            self.kb_article_edit_metadata_page.check_product_checkbox(product)

        if topics:
            if isinstance(topics, list):
                self.submit_kb_article_page.click_on_a_particular_child_topic_checkbox(
                    topics[0],
                    topics[1],
                )
            else:
                self.submit_kb_article_page.click_on_a_particular_parent_topic_checkbox(
                    topics
                )

        if self.kb_article_edit_metadata_page.is_obsolete_checkbox_displayed():
            if self.kb_article_edit_metadata_page.is_obsolete_checkbox_checked() != obsolete:
                self.kb_article_edit_metadata_page.click_on_obsolete_checkbox()

        if self.kb_article_edit_metadata_page.is_allow_discussion_checkbox_checked() != \
           discussions:
            self.kb_article_edit_metadata_page.click_on_allow_discussion_on_article_checkbox()

        # Ensure the needs change checkbox and textarea are updated accordingly.
        if self.kb_article_edit_metadata_page.is_needs_change_checkbox_displayed():
            if needs_change:
                if not self.kb_article_edit_metadata_page.is_needs_change_checkbox():
                    self.kb_article_edit_metadata_page.click_needs_change_checkbox()
                # If it needs change with comment we are also adding the comment.
                # If it doesn't need comment we are ensuring that the textarea field is empty.
                self.kb_article_edit_metadata_page.fill_needs_change_textarea(
                    self.utilities.kb_revision_test_data[
                        'needs_change_message'] if needs_change_comment else ''
                )
            elif self.kb_article_edit_metadata_page.is_needs_change_checkbox():
                self.kb_article_edit_metadata_page.click_needs_change_checkbox()

        if related_documents:
            for document in related_documents:
                self.kb_article_edit_metadata_page.add_related_documents(document)

        self.kb_article_edit_metadata_page.click_on_save_changes_button()

    def remove_a_restricted_visibility_group(self, **kwargs):
        return self.utilities.re_call_function_on_error(
            lambda: self._remove_a_restricted_visibility_group(**kwargs)
        )

    def _remove_a_restricted_visibility_group(self, group_name=""):
        if KBArticleRevision.KB_EDIT_METADATA not in self.utilities.get_page_url():
            self.kb_article_page.click_on_edit_article_metadata()

        if self.edit_kb_article_page.is_edit_anyway_option_visible():
            self.edit_kb_article_page.click_on_edit_anyway_option()
        self.kb_article_edit_metadata_page.delete_a_restricted_visibility_group_metadata(
            group_name)
        self.kb_article_edit_metadata_page.click_on_save_changes_button()
