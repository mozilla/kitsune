import re
from playwright.sync_api import Page
from playwright_tests.core.utilities import Utilities
from playwright_tests.pages.contribute.contribute_pages.contributor_discussions.\
    delete_thread_post_page import DeleteThreadPostPage
from playwright_tests.pages.contribute.contribute_pages.contributor_discussions.\
    edit_thread_post_page import EditThreadPostPage
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
        self.edit_post_page = EditThreadPostPage(page)
        self.delete_thread_post_page = DeleteThreadPostPage(page)

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

        action = self.new_thread_page.click_on_cancel_button if cancel else (
            self.new_thread_page.click_on_post_thread_button)
        action()

        if not cancel:
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

    def quote_thread_post(self, post_id: str) -> str:
        """
            Quote a thread post.
            Args:
                post_id (str): The ID of the post to be quoted.
        """
        self.forum_thread_page.click_on_quote_option(post_id)
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

    def edit_thread_post(self, post_id: str, new_thread_post: str):
        """
            Edit the thread post.
            Args:
                post_id (str): The ID of the post to be edited.
                new_thread_post (str): The new post for the thread.
        """
        self.forum_thread_page.click_on_edit_this_post_option(post_id)
        self.edit_post_page.add_text_inside_the_edit_post_textarea(new_thread_post)
        self.edit_post_page.click_on_update_post_button()

    def delete_thread_post(self, post_id: str):
        """
            Delete a thread post.
            Args:
                post_id (str): The ID of the post to be deleted.
        """
        self.forum_thread_page.click_on_delete_this_post_option(post_id)
        self.delete_thread_post_page.click_on_delete_button()

    def report_thread_post(self, post_id: str):
        """
            Report a thread post.
            Args:
                post_id (str): The ID of the post to be reported.
        """
        self.forum_thread_page.click_on_report_abuse_option(post_id)

    def delete_thread(self):
        """
            Delete a thread.
        """
        self.forum_thread_page.click_on_delete_thread_option()
        self.forum_thread_page.click_on_delete_button_from_confirmation_page()
