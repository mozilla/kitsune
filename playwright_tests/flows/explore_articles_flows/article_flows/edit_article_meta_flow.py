from playwright_tests.core.testutilities import TestUtilities
from playwright.sync_api import Page

from playwright_tests.pages.explore_help_articles.articles.kb_edit_article_meta import (
    KBArticleEditMetadata)


class EditArticleMetaFlow(TestUtilities, KBArticleEditMetadata):

    def __init__(self, page: Page):
        super().__init__(page)

    def edit_article_metadata(self, title=None, needs_change=False, needs_change_comment=False):
        if title is not None:
            super()._add_text_to_title_field(title)

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
