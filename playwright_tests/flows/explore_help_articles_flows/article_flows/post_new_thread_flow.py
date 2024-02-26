from typing import Any
from playwright_tests.core.testutilities import TestUtilities
from playwright_tests.messages.explore_help_articles.kb_article_page_messages import (
    KBArticlePageMessages)
from playwright_tests.pages.explore_help_articles.articles.kb_article_discussion_page import (
    KBArticleDiscussionPage)
from playwright.sync_api import Page


class PostNewDiscussionThreadFlow(TestUtilities, KBArticleDiscussionPage):
    def __init__(self, page: Page):
        super().__init__(page)

    def add_new_kb_discussion_thread(self, title='') -> dict[str, Any]:
        if title == '':
            thread_title = (super().kb_new_thread_test_data['new_thread_title'] + super()
                            .generate_random_number(0, 5000))
        else:
            thread_title = (title + super()
                            .generate_random_number(0, 5000))
        thread_body = super().kb_new_thread_test_data['new_thread_body']

        # Adding text to the title field.
        super()._add_text_to_new_thread_title_field(thread_title)

        # Adding text to the body field.
        super()._add_text_to_new_thread_body_input_field(thread_body)

        # Clicking on the post a new thread option.
        super()._click_on_submit_new_thread_button()

        # Fetching the article url & the thread id from the url.
        thread_url = self._page.url
        thread_id = str(super().number_extraction_from_string_endpoint(
            KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT, thread_url)
        )

        return {
            "thread_title": thread_title,
            "thread_body": thread_body,
            "thread_url": thread_url,
            "thread_id": thread_id
        }
