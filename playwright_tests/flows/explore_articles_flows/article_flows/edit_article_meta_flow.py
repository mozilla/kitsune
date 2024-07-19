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
                              relevancy=None,
                              topics=None,
                              obsolete=False,
                              discussions=True,
                              needs_change=False,
                              needs_change_comment=False,
                              restricted_to_groups: list[str] = None,
                              single_group=""):

        if KBArticleRevision.KB_EDIT_METADATA not in super()._get_current_page_url():
            super()._click_on_edit_article_metadata()

        if restricted_to_groups is not None:
            for group in restricted_to_groups:
                super()._add_and_select_restrict_visibility_group_metadata(group)
        if single_group != "":
            super()._add_and_select_restrict_visibility_group_metadata(single_group)

        if title is not None:
            super()._add_text_to_title_field(title)

        if slug is not None:
            super()._add_text_to_slug_field(slug)

        if category is not None:
            super()._select_category(category)

        if relevancy is not None:
            super()._check_a_particular_relevancy_option(relevancy)

        if topics is not None:
            super()._click_on_a_particular_parent_topic(
                topics[0]
            )
            super()._click_on_a_particular_child_topic_checkbox(
                topics[0],
                topics[1],
            )

        if obsolete:
            super()._click_on_obsolete_checkbox()

        if discussions:
            if not super()._is_allow_discussion_checkbox_checked():
                super()._click_on_allow_discussion_on_article_checkbox()
        else:
            if super()._is_allow_discussion_checkbox_checked():
                super()._click_on_allow_discussion_on_article_checkbox()

        # If it needs change we are going to ensure that the needs change checkbox is checked.
        if needs_change:
            if not super()._is_needs_change_checkbox():
                super()._click_needs_change_checkbox()
                # If it needs change with comment we are also adding the comment.
            if needs_change_comment:
                super()._fill_needs_change_textarea(
                    super().kb_revision_test_data['needs_change_message']
                )
            # If it doesn't need comment we are ensuring that the textarea field is empty.
            else:
                super()._fill_needs_change_textarea('')

        # If it doesn't need change we are ensuring that the checkbox is not checked.
        else:
            if super()._is_needs_change_checkbox():
                super()._click_needs_change_checkbox()

        super()._click_on_save_changes_button()

    def _remove_a_restricted_visibility_group(self, group_name=''):
        if KBArticleRevision.KB_EDIT_METADATA not in super()._get_current_page_url():
            super()._click_on_edit_article_metadata()

        super()._delete_a_restricted_visibility_group_metadata(group_name)
        super()._click_on_save_changes_button()
