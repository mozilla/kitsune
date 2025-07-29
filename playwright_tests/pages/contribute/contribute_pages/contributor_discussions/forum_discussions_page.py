import re

from playwright.sync_api import Page

from playwright_tests.core.basepage import BasePage

"""
    This class contains the locators and actions for the {x} discussions page.
"""


class ForumDiscussionsPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        # Locators related to the forum discussions page.
        self.forum_page_title = page.locator("article#threads h1")
        self.forum_side_nav_selected_option = page.locator(
            "nav#for-contributors-sidebar a.selected")
        self.post_a_new_thread_button = page.locator("a#new-thread")

        # Locators related to the search section.
        self.search_this_forum_search_field = page.locator("form#find-thread input#search-q")
        self.search_this_forum_search_button = page.locator("form#find-thread input.search-button")

        # Locators related to the threads table.
        self.thread_title = lambda thread_name : page.locator(
            "tbody.threads td.title").get_by_role("link", name=thread_name, exact=True)
        self.thread_type = lambda thread_name, type_image: page.locator(
            f"//tbody[@class='threads']//td[@class='title']/a[text()='{thread_name}']/../../"
            f"td[@class='type']/img[@title='{type_image}']")
        self.thread_author = lambda thread_name: page.locator(
            f"//tbody[@class='threads']//td[@class='title']/a[text()='{thread_name}']/../../"
            f"td[@class='author']/a")
        self.reply_count = lambda thread_name: page.locator(
            f"//tbody[@class='threads']//td[@class='title']/a[text()='{thread_name}']/../../"
            f"td[@class='replies']")
        self.last_post_date = lambda thread_name: page.locator(
            f"//tbody[@class='threads']//td[@class='title']/a[text()='{thread_name}']/../../"
            f"td[@class='last-post']/a/time")
        self.last_post_by = lambda thread_name: page.locator(
            f"//tbody[@class='threads']//td[@class='title']/a[text()='{thread_name}']/../../"
            f"td[@class='last-post']/a[@class='username']")

    def is_thread_type_image_displayed(self, thread: str, image_type: str) -> bool:
        """
            Check if the thread locked image is displayed.
            returns:
                bool: True if the thread locked image is displayed, False otherwise.
        """
        return self._is_element_visible(self.thread_type(thread, image_type))

    def is_thread_displayed(self, thread_name: str) -> bool:
        """
            Check if the thread is displayed in the threads table.
            Args:
                thread_name (str): The name of the thread.
            returns:
                bool: True if the thread is displayed, False otherwise.
        """
        return self._is_element_visible(self.thread_title(thread_name))

    def click_on_new_thread_button(self):
        """
            Click on the 'Post a new thread' button.
        """
        self._click(self.post_a_new_thread_button)

    def get_forum_discussions_page_title(self) -> str:
        """
            Get the forum discussions page title.
            returns:
                str: The forum discussions page title.
        """
        return super()._get_text_of_element(self.forum_page_title)

    def get_forum_discussions_side_nav_selected_option(self) -> str:
        """
            Get the selected option from the forum discussions side navigation.
        """
        option = super()._get_text_of_element(
            self.forum_side_nav_selected_option)
        return re.sub(r'\s+', ' ', option).strip()
