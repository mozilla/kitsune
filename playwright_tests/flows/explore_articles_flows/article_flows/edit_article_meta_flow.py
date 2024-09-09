from playwright_tests.core.utilities import Utilities
from playwright.sync_api import Page

from playwright_tests.messages.explore_help_articles.kb_article_revision_page_messages import \
    KBArticleRevision
from playwright_tests.pages.explore_help_articles.articles.kb_article_page import KBArticlePage
from playwright_tests.pages.explore_help_articles.articles.kb_edit_article_meta import (
    KBArticleEditMetadata)
from playwright_tests.pages.explore_help_articles.articles.submit_kb_article_page import \
    SubmitKBArticlePage


class EditArticleMetaFlow(Utilities, KBArticleEditMetadata, SubmitKBArticlePage,
                          KBArticlePage):

    def __init__(self, page: Page):
        super().__init__(page)

    def edit_article_metadata(self, title=None,
                              slug=None,
                              category=None,
                              product=None,
                              topics=None,
                              obsolete=False,
                              discussions=True,
                              needs_change=False,
                              needs_change_comment=False,
                              restricted_to_groups: list[str] = None,
                              single_group=""):

        if KBArticleRevision.KB_EDIT_METADATA not in self._get_current_page_url():
            self._click_on_edit_article_metadata()

        if restricted_to_groups:
            for group in restricted_to_groups:
                self._add_and_select_restrict_visibility_group_metadata(group)
        if single_group != "":
            self._add_and_select_restrict_visibility_group_metadata(single_group)

        if title:
            self._add_text_to_title_field(title)

        if slug:
            self._add_text_to_slug_field(slug)

        if category:
            self._select_category(category)

        if product:
            self._check_product_checkbox(product)

        if topics:
            if isinstance(topics, list):
                self._click_on_a_particular_child_topic_checkbox(
                    topics[0],
                    topics[1],
                )
            else:
                self._click_on_a_particular_parent_topic_checkbox(
                    topics
                )

        if obsolete:
            self._click_on_obsolete_checkbox()

        if discussions:
            if not self._is_allow_discussion_checkbox_checked():
                self._click_on_allow_discussion_on_article_checkbox()
        else:
            if self._is_allow_discussion_checkbox_checked():
                self._click_on_allow_discussion_on_article_checkbox()

        # If it needs change we are going to ensure that the needs change checkbox is checked.
        if needs_change:
            if not self._is_needs_change_checkbox():
                self._click_needs_change_checkbox()
                # If it needs change with comment we are also adding the comment.
            if needs_change_comment:
                self._fill_needs_change_textarea(
                    self.kb_revision_test_data['needs_change_message']
                )
            # If it doesn't need comment we are ensuring that the textarea field is empty.
            else:
                self._fill_needs_change_textarea('')

        # If it doesn't need change we are ensuring that the checkbox is not checked.
        else:
            if self._is_needs_change_checkbox():
                self._click_needs_change_checkbox()

        self._click_on_save_changes_button()

    def _remove_a_restricted_visibility_group(self, group_name=''):
        if KBArticleRevision.KB_EDIT_METADATA not in self._get_current_page_url():
            self._click_on_edit_article_metadata()

        self._delete_a_restricted_visibility_group_metadata(group_name)
        self._click_on_save_changes_button()
