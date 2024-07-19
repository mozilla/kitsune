from playwright_tests.core.utilities import Utilities
from playwright.sync_api import Page

from playwright_tests.pages.explore_help_articles.articles.kb_article_page import KBArticlePage
from playwright_tests.pages.explore_help_articles.articles.kb_article_show_history_page import \
    KBArticleShowHistoryPage
from playwright_tests.pages.top_navbar import TopNavbar


class DeleteKbArticleFlow(Utilities, KBArticleShowHistoryPage, KBArticlePage, TopNavbar):

    def __init__(self, page: Page):
        super().__init__(page)

    def delete_kb_article(self):
        # If the delete button is not displayed we presume that we are not on the show history page
        # Clicking on the 'Show History' page.
        if not super()._is_delete_button_displayed():
            super()._click_on_show_history_option()
        super()._click_on_delete_this_document_button()
        super()._click_on_confirmation_delete_button()
