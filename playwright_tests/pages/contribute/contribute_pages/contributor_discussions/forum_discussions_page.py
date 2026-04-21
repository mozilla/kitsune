import re
from playwright.sync_api import Page, ElementHandle
from playwright_tests.core.basepage import BasePage

"""This class contains the locators and actions for the {x} discussions page."""


class ForumDiscussionsPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """Locators belonging to the forum discussions page."""
        self.forum_page_title = page.locator("article#threads h1")
        self.forum_side_nav_selected_option = page.locator(
            "nav#for-contributors-sidebar a.selected")
        self.post_a_new_thread_button = page.locator("a#new-thread")

        """Locators belonging to the search section."""
        self.search_this_forum_search_field = page.locator("form#find-thread input#search-q")
        self.search_this_forum_search_button = page.locator("form#find-thread input.search-button")
        self.search_results_headers = page.locator(
            "//div[@id='search-results']//h3[@class='sumo-card-heading']/a")
        self.search_results_body = page.locator(
            "//div[@id='search-results']//div[@class='topic-article--text']/p")

        """Locators belonging to the threads table section."""
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

    def click_on_new_thread_button(self):
        """
            Click on the 'Post a new thread' button.
        """
        self._click(self.post_a_new_thread_button)

    def search_in_community_discussion(self, search_string: str):
        self._fill(self.search_this_forum_search_field, search_string)
        self._click(self.search_this_forum_search_button)
        self.wait_for_dom_to_load()

    def get_all_thread_titles_from_search_results(self) -> list[str]:
        return self._get_text_of_elements(self.search_results_headers)

    def get_all_thread_titles_from_search_results_handles(self) -> list[ElementHandle]:
        return self._get_element_handles(self.search_results_headers)

    def get_all_thread_content_from_search_results(self) -> list[str]:
        return self._get_text_of_elements(self.search_results_body)

