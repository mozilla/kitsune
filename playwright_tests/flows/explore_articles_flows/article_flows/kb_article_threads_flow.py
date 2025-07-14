from typing import Any

from playwright.sync_api import Page

from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.explore_help_articles.kb_article_page_messages import (
    KBArticlePageMessages,
)
from playwright_tests.pages.explore_help_articles.articles.kb_article_discussion_page import (
    KBArticleDiscussionPage,
)
from playwright_tests.pages.explore_help_articles.articles.kb_article_page import KBArticlePage


class KbThreads:
    def __init__(self, page: Page):
        self.page = page
        self.utilities = Utilities(page)
        self.kb_article_discussion_page = KBArticleDiscussionPage(page)
        self.kb_article_page = KBArticlePage(page)

    def delete_article_thread(self, thread_id: str, confirm_deletion=True):
        self.kb_article_discussion_page.click_on_a_particular_thread(thread_id)
        self.kb_article_discussion_page.click_on_delete_this_thread_option()

        if confirm_deletion:
            self.kb_article_discussion_page.click_on_delete_this_thread_reply_confirmation_button(
            )

    def add_new_kb_discussion_thread(self, title='') -> [dict[str, Any]]:
        self.kb_article_page.click_on_editing_tools_discussion_option()
        article_discussion_url = self.utilities.get_page_url()
        self.kb_article_discussion_page.click_on_post_a_new_thread_option()

        thread_title = (title or self.utilities.kb_new_thread_test_data[
            'new_thread_title']) + self.utilities.generate_random_number(0, 5000)
        thread_body = self.utilities.kb_new_thread_test_data['new_thread_body']

        # Adding text to the title field.
        self.kb_article_discussion_page.add_text_to_new_thread_title_field(thread_title)

        # Adding text to the body field.
        self.kb_article_discussion_page.add_text_to_new_thread_body_input_field(thread_body)

        # Clicking on the post a new thread option.
        self.kb_article_discussion_page.click_on_submit_new_thread_button()

        # Fetching the article url & the thread id from the url.
        thread_url = self.page.url
        thread_id = str(self.utilities.number_extraction_from_string_endpoint(
            KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT, thread_url)
        )

        return {
            "thread_title": thread_title,
            "thread_body": thread_body,
            "thread_url": thread_url,
            "thread_id": thread_id,
            "article_discussion_url": article_discussion_url
        }

    def _edit_article_thread(self, thread_title="", submit_edit=True):
        self.kb_article_discussion_page.click_on_edit_this_thread_option()
        self.kb_article_discussion_page.add_text_to_edit_article_thread_title_field(thread_title)

        action = (self.kb_article_discussion_page.
                  click_on_edit_article_thread_update_button) if submit_edit else (
            self.kb_article_discussion_page.click_on_edit_article_thread_cancel_button)
        action()

    def post_reply_to_thread(self, text: str, post_reply=True) -> dict[str, Any]:
        self.kb_article_discussion_page.fill_the_thread_post_a_reply_textarea(text)

        if post_reply:
            self.kb_article_discussion_page.click_on_thread_post_reply_button()

        return {
            "reply_id": self.kb_article_discussion_page.get_thread_reply_id
            (self.utilities.get_page_url())
        }

    def delete_reply_to_thread(self, reply_id: str, submit_deletion=True):
        self.kb_article_discussion_page.click_on_dotted_menu_for_a_certain_reply(reply_id)
        self.kb_article_discussion_page.click_on_delete_this_thread_reply(reply_id)

        if submit_deletion:
            self.kb_article_discussion_page.click_on_delete_this_thread_reply_confirmation_button(
            )
