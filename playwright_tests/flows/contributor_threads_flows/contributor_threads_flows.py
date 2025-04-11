import re
from playwright.sync_api import Page
from playwright_tests.core.utilities import Utilities
from playwright_tests.pages.contribute.contribute_pages.contributor_discussions.\
    edit_thread_title_page import EditThreadTitle
from playwright_tests.pages.contribute.contribute_pages.contributor_discussions\
    .forum_discussions_page import ForumDiscussionsPage
from playwright_tests.pages.contribute.contribute_pages.contributor_discussions.forum_thread_page \
    import ForumThreadPage
from playwright_tests.pages.contribute.contribute_pages.contributor_discussions.new_thread_page \
    import NewThreadPage


class ContributorThreadFlow:
    def __init__(self, page: Page):
        self.utilities = Utilities(page)
        self.new_thread_page = NewThreadPage(page)
        self.forum_discussions_page = ForumDiscussionsPage(page)
        self.forum_thread_page = ForumThreadPage(page)
        self.edit_thread_title_page = EditThreadTitle(page)

    def post_a_new_thread(self, thread_title: str, thread_body: str, cancel=False) -> str:
        """
            Post a new thread inside a contributor's forum.
            Args:
                thread_title (str): The title of the new thread.
                thread_body (str): The body of the new thread.
                cancel (bool): If True, click on the cancel button instead of posting the thread.
            returns:
                str: The thread ID of the newly created thread which is fetched from the url.
        """
        if "/new" not in self.utilities.get_page_url():
            self.forum_discussions_page.click_on_new_thread_button()
        self.new_thread_page.fill_title_input_field(thread_title)
        self.new_thread_page.fill_content_textarea_field(thread_body)
        if cancel:
            self.new_thread_page.click_on_cancel_button()
        else:
            self.new_thread_page.click_on_post_thread_button()
            return re.search(r'last=(\d+)', self.utilities.get_page_url()).group(1)

    def move_thread_to_a_different_forum(self, target_forum: str):
        """
            Move a thread to a different forum.
            Args:
                target_forum (str): The name of the target forum.
        """
        self.forum_thread_page.select_new_forum_from_dropdown(target_forum)
        self.forum_thread_page.click_on_move_thread_button()

    def post_thread_reply(self, reply_body: str) -> str:
        """
            Post a reply to a thread.
            Args:
                reply_body (str): The body of the reply.
        """
        self.forum_thread_page.fill_thread_reply_textarea(reply_body)
        self.forum_thread_page.click_on_post_reply_button()

        return re.search(r'post-(\d+)', self.utilities.get_page_url()).group(1)

    def edit_thread_title(self, new_title: str):
        """
            Edit the title of a thread.
            Args:
                new_title (str): The new title for the thread.
        """
        self.forum_thread_page.click_on_edit_thread_title_option()
        self.edit_thread_title_page.fill_into_thread_title_input_field(new_title)
        self.edit_thread_title_page.click_on_update_thread_button()

    def delete_thread(self):
        """
            Delete a thread.
        """
        self.forum_thread_page.click_on_delete_thread_option()
        self.forum_thread_page.click_on_delete_button_from_confirmation_page()
