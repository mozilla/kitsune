from typing import Any

from playwright.sync_api import Page

from playwright_tests.core.utilities import Utilities
from playwright_tests.pages.explore_help_articles.articles.kb_article_review_revision_page import \
    KBArticleReviewRevisionPage
from playwright_tests.pages.explore_help_articles.articles.kb_article_show_history_page import \
    KBArticleShowHistoryPage
from playwright_tests.pages.explore_help_articles.articles.kb_translate_article_page import \
    TranslateArticlePage
from playwright_tests.pages.explore_help_articles.articles.submit_kb_article_page import \
    SubmitKBArticlePage


class KbArticleTranslationFlow(TranslateArticlePage, Utilities, SubmitKBArticlePage,
                               KBArticleShowHistoryPage, KBArticleReviewRevisionPage):
    def __init__(self, page: Page):
        super().__init__(page)

    def _add_article_translation(self, approve_translation_revision: bool, title='', slug='',
                                 allow_discussions=True, keyword='', summary='', body='',
                                 save_as_draft=False, submit=True) -> dict[str, Any]:

        if title != '':
            translation_title = title
            super()._fill_translation_title_field(translation_title)

        else:
            translation_title = super().kb_article_test_data['translated_title'] + super(
            ).generate_random_number(1, 1000)
            super()._fill_translation_title_field(translation_title)

        if slug != '':
            translation_slug = slug
            super()._fill_translation_slug_field(translation_slug)
        else:
            translation_slug = super().kb_article_test_data['translated_slug'] + super(
            ).generate_random_number(1, 1000)
            super()._fill_translation_slug_field(translation_slug)

        if not allow_discussions:
            super()._click_on_allow_translated_article_comments_checkbox()

        if keyword != '':
            translation_keyword = keyword
            super()._fill_translated_article_keyword(translation_keyword)
        else:
            translation_keyword = super().kb_article_test_data['translated_keyword']
            super()._fill_translated_article_keyword(translation_keyword)

        if summary != '':
            translation_summary = summary
            super()._fill_translated_article_summary(translation_summary)
        else:
            translation_summary = super().kb_article_test_data['translated_search_summary']
            super()._fill_translated_article_summary(translation_summary)

        if body != '':
            translation_body = body
            super()._fill_body_translation_field(translation_body)
        else:
            translation_body = super().kb_article_test_data['translated_body']
            super()._fill_body_translation_field(translation_body)

        if save_as_draft:
            super()._click_on_save_translation_as_draft_button()

        if submit:
            super()._click_on_submit_translation_for_approval_button()
            super()._fill_translation_changes_description_field(
                super().kb_article_test_data['translated_review_description']
            )
            super()._click_on_description_submit_button()

        first_revision_id = super().get_last_revision_id()
        if approve_translation_revision:
            self.approve_kb_translation(first_revision_id)

        return {
            "translation_title": translation_title,
            "translation_slug": translation_slug,
            "translation_keyword": translation_keyword,
            "translation_summary": translation_summary,
            "translation_body": translation_body,
            "revision_id": first_revision_id
        }

    def approve_kb_translation(self, revision_id: str):
        super().click_on_review_revision(
            revision_id
        )
        super().click_on_approve_revision_button()
        super().click_accept_revision_accept_button()
