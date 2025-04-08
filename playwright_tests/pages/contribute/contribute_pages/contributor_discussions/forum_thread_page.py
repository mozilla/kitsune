from datetime import datetime
from playwright_tests.core.basepage import BasePage
from playwright_tests.core.utilities import Utilities

"""
    This class contains the locators and actions for the {x} discussions thread page.
"""


class ForumThreadPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.utilities = Utilities(page)

        # Locators related to the thread-actions section.
        self.edit_thread_title_option = page.get_by_role("link", name="Edit Thread Title")
        self.delete_this_thread_option = page.get_by_role("link", name="Delete this thread")
        self.lock_this_thread_option = page.locator("//a[text()='Lock this thread']")
        self.thread_locked_text = page.locator("p#thread-locked")
        self.unlock_this_thread_option = page.locator("//a[text()='Unlock this thread']")
        self.sticky_this_thread_option = page.locator("//a[text()='Sticky this thread']")
        self.unsticky_this_thread_option = page.locator("//a[text()='Unsticky this thread']")

        # Delete thread page.
        self.delete_button = page.locator("input[value='Delete']")

        # Locators related to the move thread section.
        self.move_thread_dropdown = page.locator("select[name='forum']")
        self.move_thread_button = page.locator("input[value='Move Thread']")

        # Thread locators
        self.forum_title = page.locator("p#forum-title")
        self.thread_title = page.locator("h1.sumo-page-heading")
        self.thread_posted_thread_title = page.locator("h1#sumo-page-heading")
        self.thread_meta = page.locator("ul#thread-meta li")
        self.watch_this_thread_button = page.locator("button#watch-thread-toggle")
        self.post_author = lambda post_id: page.locator(
            f"//li[@id='post-{post_id}']//span[@class='display-name']")
        self.post_time = lambda post_id: page.locator(
            f"//li[@id='post-{post_id}']//span[@class='asked-on']/time")
        self.post_content = lambda post_id: page.locator(
            f"//li[@id='post-{post_id}']//div[@class='content']/p")
        self.thread_post = lambda post_id: page.locator(f"li#post-{post_id}")

        # Thread post more options locators
        self.post_3_dotted_menu = lambda post_id: page.locator(f"li#post-{post_id}").get_by_role(
            "button", name="more options")
        self.post_edit_this_post = lambda post_id: page.locator(
            f"li#post-{post_id} ul#expand-expand-datahasdropdown-0 li").get_by_role(
            "link", name="Edit this post")
        self.delete_this_post = lambda post_id: page.locator(
            f"li#post-{post_id} ul#expand-expand-datahasdropdown-0 li").get_by_role(
            "link", name="Delete this post")
        self.quote_this_post = lambda post_id: page.locator(
            f"li#post-{post_id} ul#expand-expand-datahasdropdown-0 li").get_by_role(
            "link", name="Quote")
        self.report_this_post = lambda post_id: page.locator(
            f"li#post-{post_id} ul#expand-expand-datahasdropdown-0 li").get_by_role(
            "link", name="Report Abuse")
        self.link_this_post = lambda post_id: page.locator(
            f"li#post-{post_id} ul#expand-expand-datahasdropdown-0 li").get_by_role(
            "link", name="Link to this post")

        # Post a reply locators
        self.post_reply_textarea = page.locator("textarea#id_content")
        self.preview_reply_button = page.locator("button#preview")
        self.post_reply_button = page.get_by_role("button", name="Post Reply")

    def get_thread_meta_information(self) -> list[str]:
        return self._get_text_of_elements(self.thread_meta)

    def is_thread_post_visible(self, post_id: str) -> bool:
        """
            Check if a specific thread post is visible.
            Args:
                post_id (str): The ID of the post.
            Returns:
                bool: True if the post is visible, False otherwise.
        """
        return self._is_element_visible(self.thread_post(post_id))

    def is_edit_thread_title_option_visible(self) -> bool:
        """
            Check if the edit thread title option is visible.
            Returns:
                bool: True if the option is visible, False otherwise.
        """
        return self._is_element_visible(self.edit_thread_title_option)

    def click_on_edit_thread_title_option(self):
        """
            Click on the edit thread title option.
        """
        self._click(self.edit_thread_title_option)

    def is_lock_this_thread_option_visible(self) -> bool:
        """
            Check if the lock this thread option is visible.
            Returns:
                bool: True if the option is visible, False otherwise.
        """
        return self._is_element_visible(self.lock_this_thread_option)

    def click_lock_this_thread_option(self):
        """
            Click on the lock this thread option.
        """
        self._click(self.lock_this_thread_option)

    def is_sticky_this_thread_option_visible(self) -> bool:
        """
            Check if the sticky this thread option is visible.
            Returns:
                bool: True if the option is visible, False otherwise.
        """
        return self._is_element_visible(self.sticky_this_thread_option)

    def click_sticky_this_thread_option(self):
        """
            Click on the sticky this thread option.
        """
        self._click(self.sticky_this_thread_option)

    def is_unsticky_this_thread_option_visible(self) -> bool:
        """
            Check if the unsticky this thread option is visible.
            Returns:
                bool: True if the option is visible, False otherwise.
        """
        return self._is_element_visible(self.unsticky_this_thread_option)

    def click_unsticky_this_thread_option(self):
        """
            Click on the unsticky this thread option.
        """
        self._click(self.unsticky_this_thread_option)

    def is_thread_locked_message_displayed(self) -> bool:
        """
            Check if the thread locked message is displayed.
            Returns:
                bool: True if the message is displayed, False otherwise.
        """
        return self._is_element_visible(self.thread_locked_text)

    def get_thread_locked_message(self) -> str:
        """
            Get the thread locked message.
            Returns:
                str: The thread locked message.
        """
        return self._get_text_of_element(self.thread_locked_text)

    def is_unlock_this_thread_option_visible(self) -> bool:
        """
            Check if the unlock this thread option is visible.
            Returns:
                bool: True if the option is visible, False otherwise.
        """
        return self._is_element_visible(self.unlock_this_thread_option)

    def click_unlock_this_thread_option(self):
        """
            Click on the unlock this thread option.
        """
        self._click(self.unlock_this_thread_option)

    def get_forum_thread_title(self) -> str:
        """
            Get the title of the forum thread.
        """
        return self._get_text_of_element(self.thread_title)

    def is_delete_thread_option_visible(self) -> bool:
        """
            Check if the delete thread option is visible.
            Returns:
                bool: True if the option is visible, False otherwise.
        """
        return self._is_element_visible(self.delete_this_thread_option)

    def click_on_delete_thread_option(self):
        """
            Click on the delete thread option.
        """
        self._click(self.delete_this_thread_option)

    def click_on_delete_button_from_confirmation_page(self):
        """
            Click on the delete button from the confirmation page.
        """
        self._click(self.delete_button)

    def get_post_time(self, post_id: str, timezone: str) -> datetime:
        """
            Get the post time of a specific thread post.
            Args:
                post_id (str): The ID of the post.
                timezone (str): The timezone to parse the date into.
        """
        return self.utilities.parse_date(self._get_text_of_element(self.post_time(post_id)),
                                         tzinfo=timezone)

    def select_new_forum_from_dropdown(self, forum: str):
        """
            Select a new forum from the dropdown.
            Args:
                forum (str): The name of the forum to select.
        """
        self._select_option_by_label(self.move_thread_dropdown, forum)

    def click_on_move_thread_button(self):
        """
            Click on the move thread button.
        """
        self._click(self.move_thread_button)

    def fill_thread_reply_textarea(self, reply_body: str):
        """
            Fill the thread reply textarea.
            Args:
                reply_body (str): The body of the reply.
        """
        self._fill(self.post_reply_textarea, reply_body)

    def click_on_post_reply_button(self):
        """
            Click on the post reply button.
        """
        self._click(self.post_reply_button)

    def is_reply_textarea_visible(self) -> bool:
        """
            Check if the reply textarea is visible.
            Returns:
                bool: True if the textarea is visible, False otherwise.
        """
        return self._is_element_visible(self.post_reply_textarea)
