import re
from datetime import datetime
from playwright_tests.core.basepage import BasePage
from playwright_tests.core.utilities import Utilities

"""This class contains the locators and actions for the {x} discussions thread page."""

class ForumThreadPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.utilities = Utilities(page)

        """Locators belonging to the page breadcrumbs."""
        self.breadcrumb_options = page.locator("ol#breadcrumbs li")
        self.breadcrumb_links = page.locator("ol#breadcrumbs li a")
        self.breadcrumb_link = lambda breadcrumb_name: page.locator(
            "ol#breadcrumbs li").get_by_role("link", name=breadcrumb_name)

        """Locators belonging to the Contributor Discussions side-navbar section."""
        self.contributor_discussions_side_navbar_header = page.locator(
            "#for-contributors-sidebar ul li.sidebar-subheading")
        self.contributor_discussions_side_navbar_items = page.locator(
            "#for-contributors-sidebar ul li:not(.sidebar-subheading)")
        self.contributor_discussions_side_navbar_item = lambda item_name: page.locator(
            "#for-contributors-sidebar ul li:not(.sidebar-subheading)").get_by_role(
            "link", name=item_name, exact=True)

        """Locators belonging to the thread-actions section."""
        self.edit_thread_title_option = page.get_by_role("link", name="Edit Thread Title")
        self.delete_this_thread_option = page.get_by_role("link", name="Delete this thread")
        self.lock_this_thread_option = page.locator("//a[text()='Lock this thread']")
        self.thread_locked_text = page.locator("p#thread-locked")
        self.unlock_this_thread_option = page.locator("//a[text()='Unlock this thread']")
        self.sticky_this_thread_option = page.locator("//a[text()='Sticky this thread']")
        self.unsticky_this_thread_option = page.locator("//a[text()='Unsticky this thread']")

        """Locators belonging to the delete thread page."""
        self.delete_button = page.locator("input[value='Delete']")

        """Locators belonging to the move thread section."""
        self.move_thread_dropdown = page.locator("select[name='forum']")
        self.move_thread_button = page.locator("input[value='Move thread']")

        """General thread page locators."""
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
        self.thread_post_by_content = lambda post_content: page.locator(
            f"//div[@class='content']/p[normalize-space(text())='{post_content}']")
        self.modified_by = lambda post_id: page.locator(f"li#post-{post_id} p.text-body-sm")
        self.quoted_thread_post_mention = lambda post_id: page.locator(
            f"li#post-{post_id} div.content em")
        self.quoted_thread_post_mention_link = lambda post_id: page.locator(
            f"li#post-{post_id} div.content em a")
        self.quoted_thread_post_quote = lambda post_id: page.locator(
            f"li#post-{post_id} div.content blockquote")

        """Locators belonging to the more options section from the thread post."""
        self.post_3_dotted_menu = lambda post_id: page.locator(f"li#post-{post_id}").get_by_role(
            "button", name="more options")
        self.post_3_dotted_menu_expanded = lambda post_id: page.locator(
            f"//li[@id='post-{post_id}']//ul[contains(@id,'expand-datahasdropdown')]")
        self.private_message = lambda post_id: page.locator(
            f"li#post-{post_id} li.mzp-c-menu-list-item").get_by_role(
            "link", name="Private message")
        self.post_edit_this_post = lambda post_id: page.locator(
            f"li#post-{post_id} li.mzp-c-menu-list-item").get_by_role(
            "link", name="Edit this post")
        self.delete_this_post = lambda post_id: page.locator(
            f"li#post-{post_id} li.mzp-c-menu-list-item").get_by_role(
            "link", name="Delete this post")
        self.quote_this_post = lambda post_id: page.locator(
            f"li#post-{post_id} li.mzp-c-menu-list-item").get_by_role(
            "link", name="Quote")
        self.report_this_post = lambda post_id: page.locator(
            f"li#post-{post_id} li.mzp-c-menu-list-item").get_by_role(
            "link", name="Report Abuse")
        self.link_this_post = lambda post_id: page.locator(
            f"li#post-{post_id} li.mzp-c-menu-list-item").get_by_role(
            "link", name="Link to this post")

        """Locators belonging to the post a reply section."""
        self.post_reply_textarea = page.locator("textarea#id_content")
        self.preview_reply_button = page.locator("button#preview")
        self.post_reply_button = page.get_by_role("button", name="Post Reply")


    """Actions against the page breadcrumbs locators."""
    def click_on_a_breadcrumb_link(self, breadcrumb_name: str):
        """
            Click on a specific breadcrumb link.
            Args:
                breadcrumb_name (str): The name of the breadcrumb link.
        """
        self._click(self.breadcrumb_link(breadcrumb_name))

    def get_all_breadcrumb_link_names(self) -> list[str]:
        """
            Get all breadcrumb link names.
            Returns:
                list[str]: A list of breadcrumb link names.
        """
        return self._get_text_of_elements(self.breadcrumb_links)

    """Actions against the general thread page locators."""
    def click_on_edit_thread_title_option(self):
        """
            Click on the edit thread title option.
        """
        self._click(self.edit_thread_title_option)

    def click_lock_this_thread_option(self):
        """
            Click on the lock this thread option.
        """
        self._click(self.lock_this_thread_option)

    def click_sticky_this_thread_option(self):
        """
            Click on the sticky this thread option.
        """
        self._click(self.sticky_this_thread_option)

    def click_unsticky_this_thread_option(self):
        """
            Click on the unsticky this thread option.
        """
        self._click(self.unsticky_this_thread_option)

    def click_unlock_this_thread_option(self):
        """
            Click on the unlock this thread option.
        """
        self._click(self.unlock_this_thread_option)

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

    def get_contributor_discussions_side_navbar_items(self) -> list[str]:
        """
        Get the text of all items in the Contributor Discussions side navbar.
        Returns:
            list[str]: A list of side navbar item texts.
        """
        return self._get_text_of_elements(self.contributor_discussions_side_navbar_items)

    def click_on_contributor_discussions_side_navbar_item(self, item_name: str):
        """
        Click on a specific item in the Contributor Discussions side navbar.
        Args:
            item_name (str): The name of the item to click on.
        """
        self._click(self.contributor_discussions_side_navbar_item(item_name))

    def click_on_3_dotted_menu(self, post_id: str):
        """
        Click on the 3-dotted menu for a specific post.
        Args:
            post_id (str): The ID of the post.
        """
        self._click(self.post_3_dotted_menu(post_id),
                    expected_locator=self.post_3_dotted_menu_expanded(post_id))

    def click_on_edit_this_post_option(self, post_id: str):
        """
        1. Click on the "Edit this post" option for a specific post.
        2. Click on the "Edit this post" option in the 3-dotted menu of the post.
        Args:
            post_id (str): The ID of the post.
        """
        self.click_on_3_dotted_menu(post_id)
        self._click(self.post_edit_this_post(post_id))

    def click_on_quote_option(self, post_id: str):
        """
        Click on the "Quote" option for a specific post.
        Args:
            post_id (str): The ID of the post.
        """
        self.click_on_3_dotted_menu(post_id)
        self._click(self.quote_this_post(post_id))

    def click_on_delete_this_post_option(self, post_id: str):
        """
        Click on the "Delete this post" option for a specific post.
        Args:
            post_id (str): The ID of the post.
        """
        self.click_on_3_dotted_menu(post_id)
        self._click(self.delete_this_post(post_id))

    def click_on_private_message_option(self, post_id: str):
        """
        Click on the "Private message" option for a specific post.
        Args:
            post_id (str): The ID of the post.
        """
        self.click_on_3_dotted_menu(post_id)
        self._click(self.private_message(post_id))

    def click_on_report_abuse_option(self, post_id: str):
        """
        Click on the "Report Abuse" option for a specific post.
        Args:
            post_id (str): The ID of the post.
        """
        self.click_on_3_dotted_menu(post_id)
        self._click(self.report_this_post(post_id))

    def click_on_link_to_this_post_option(self, post_id: str) -> str:
        """
        Click on the "Link to this post" option for a specific post.
        Args:
            post_id (str): The ID of the post.
        Returns:
            str: The ID of the post.
        """
        self.click_on_3_dotted_menu(post_id)
        self._click(self.link_this_post(post_id))

        return re.search(r'post-(\d+)', self.utilities.get_page_url()).group(1)

    def click_on_post_mention_link(self, post_id: str):
        """
            Click on the post mention link.
        """
        self._click(self.quoted_thread_post_mention_link(post_id))
