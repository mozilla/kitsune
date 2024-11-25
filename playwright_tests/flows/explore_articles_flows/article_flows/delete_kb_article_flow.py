from playwright.sync_api import Page

from playwright_tests.core.utilities import Utilities
from playwright_tests.pages.explore_help_articles.articles.kb_article_page import KBArticlePage
from playwright_tests.pages.explore_help_articles.articles.kb_article_show_history_page import \
    KBArticleShowHistoryPage


class DeleteKbArticleFlow:

    def __init__(self, page: Page):
        self.kb_article_show_history_page = KBArticleShowHistoryPage(page)
        self.kb_article_page = KBArticlePage(page)
        self.utilities = Utilities(page)

    def delete_kb_article(self):
        return self.utilities.re_call_function_on_error(
            lambda: self._delete_kb_article()
        )

    def _delete_kb_article(self):
        # If the delete button is not displayed we presume that we are not on the show history page
        # Clicking on the 'Show History' page.
        if not self.kb_article_show_history_page.is_delete_button_displayed():
            self.kb_article_page.click_on_show_history_option()
        self.kb_article_show_history_page.click_on_delete_this_document_button()
        self.kb_article_show_history_page.click_on_confirmation_delete_button()
