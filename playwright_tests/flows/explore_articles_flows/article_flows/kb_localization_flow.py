from typing import Any

from playwright.sync_api import Page

from playwright_tests.core.utilities import Utilities
from playwright_tests.pages.explore_help_articles.articles.kb_article_page import KBArticlePage
from playwright_tests.pages.explore_help_articles.articles.kb_article_review_revision_page import \
    KBArticleReviewRevisionPage
from playwright_tests.pages.explore_help_articles.articles.kb_article_show_history_page import \
    KBArticleShowHistoryPage
from playwright_tests.pages.explore_help_articles.articles.kb_translate_article_page import \
    TranslateArticlePage


class KbArticleTranslationFlow:
    def __init__(self, page: Page):
        self.utilities = Utilities(page)
        self.kb_article_page = KBArticlePage(page)
        self.translate_article_page = TranslateArticlePage(page)
        self.kb_article_show_history_page = KBArticleShowHistoryPage(page)
        self.kb_article_review_revision_page = KBArticleReviewRevisionPage(page)

    def _add_article_translation(self, approve_translation_revision: bool, title='', slug='',
                                 allow_discussions=True, keyword='', summary='', body='',
                                 save_as_draft=False, submit=True, locale=None) -> dict[str, Any]:

        if locale:
            self.kb_article_page.click_on_translate_article_option()
            self.translate_article_page.click_on_locale_from_list(locale)

        if title != '':
            translation_title = title
            self.translate_article_page.fill_translation_title_field(translation_title)

        else:
            translation_title = (self.utilities.kb_article_test_data['translated_title'] + self.
                                 utilities.generate_random_number(1, 1000))
            self.translate_article_page.fill_translation_title_field(translation_title)

        if slug != '':
            translation_slug = slug
            self.translate_article_page.fill_translation_slug_field(translation_slug)
        else:
            translation_slug = (self.utilities.kb_article_test_data['translated_slug'] + self.
                                utilities.generate_random_number(1, 1000))
            self.translate_article_page.fill_translation_slug_field(translation_slug)

        if not allow_discussions:
            self.translate_article_page.click_on_allow_translated_article_comments_checkbox()

        if keyword != '':
            translation_keyword = keyword
            self.translate_article_page.fill_translated_article_keyword(translation_keyword)
        else:
            translation_keyword = self.utilities.kb_article_test_data['translated_keyword']
            self.translate_article_page.fill_translated_article_keyword(translation_keyword)

        if summary != '':
            translation_summary = summary
            self.translate_article_page.fill_translated_article_summary(translation_summary)
        else:
            translation_summary = self.utilities.kb_article_test_data['translated_search_summary']
            self.translate_article_page.fill_translated_article_summary(translation_summary)

        if body != '':
            translation_body = body
            self.translate_article_page.fill_body_translation_field(translation_body)
        else:
            translation_body = self.utilities.kb_article_test_data['translated_body']
            self.translate_article_page.fill_body_translation_field(translation_body)

        if save_as_draft:
            self.translate_article_page.click_on_save_translation_as_draft_button()

        if submit:
            self.translate_article_page.click_on_submit_translation_for_approval_button()
            self.translate_article_page.fill_translation_changes_description_field(
                self.utilities.kb_article_test_data['translated_review_description']
            )
            self.translate_article_page.click_on_description_submit_button()

        first_revision_id = self.kb_article_show_history_page.get_last_revision_id()
        if approve_translation_revision:
            self.approve_kb_translation(revision_id=first_revision_id)

        return {
            "translation_title": translation_title,
            "translation_slug": translation_slug,
            "translation_keyword": translation_keyword,
            "translation_summary": translation_summary,
            "translation_body": translation_body,
            "revision_id": first_revision_id
        }

    def approve_kb_translation(self, revision_id: str):
        self.kb_article_show_history_page.click_on_review_revision(
            revision_id
        )
        self.kb_article_review_revision_page.click_on_approve_revision_button()
        self.kb_article_review_revision_page.click_accept_revision_accept_button()
