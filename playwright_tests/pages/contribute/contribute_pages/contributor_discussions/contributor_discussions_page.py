from playwright.sync_api import Page

from playwright_tests.core.basepage import BasePage

"""
    This class contains the locators and actions for the general "Contributor Discussions" page.
"""


class ContributorDiscussionPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        # Contributor Discussions breadcrumb locators.
        self.contributor_discussions_page_breadcrumbs = page.locator('ol#breadcrumbs li')

        # Contributor Discussions side navbar locators.
        self.contributor_discussions_side_navbar_header = page.locator(
            "#for-contributors-sidebar ul li.sidebar-subheading")
        self.contributor_discussions_side_navbar_items = page.locator(
            "#for-contributors-sidebar ul li:not(.sidebar-subheading)")
        self.contributor_discussions_side_navbar_item = lambda item_name: page.locator(
            "#for-contributors-sidebar ul li:not(.sidebar-subheading)").get_by_role(
            "link", name=item_name, exact=True)

        # Contributor Discussions forums list locators.
        self.contributor_discussions_page_title = page.locator("div#forums h1")
        self.contributor_discussions_forum_names = page.locator("h5[class='sumo-card-heading']")
        self.contributor_discussions_forum_name = lambda forum: page.locator(
            "tbody[class='forums'] td h5").get_by_text(forum, exact=True)
        self.contributor_discussions_forum_thread_count = lambda forum: page.locator(
            f"//h5[@class='sumo-card-heading']/a[text()='{forum}']/../../"
            f"following-sibling::td[@class='threads']")
        self.contributor_discussions_forum_last_post_date = lambda forum: page.locator(
            f"//h5[@class='sumo-card-heading']/a[text()='{forum}']/../../"
            f"following-sibling::td[@class='last-post']/a").first
        self.contributor_discussions_forum_last_post_by = lambda forum: page.locator(
            f"//h5[@class='sumo-card-heading']/a[text()='{forum}']/../../"
            f"following-sibling::td[@class='last-post']/a").nth(1)

    # Actions against the Contributor Discussions breadcrumb locators.
    def get_contributor_discussions_breadcrumbs(self) -> list[str]:
        """
        Get the text of all the breadcrumbs on the Contributor Discussions page.
        Returns:
            list[str]: A list of breadcrumb texts.
        """
        return self._get_text_of_elements(self.contributor_discussions_page_breadcrumbs)

    def click_on_first_breadcrumb(self):
        """
        Click on the first breadcrumb of the Contributor Discussions page.
        """
        self._click(self.contributor_discussions_page_breadcrumbs.first)

    # Actions against the Contributor Discussions forums list locators.
    def get_contributor_discussions_page_title(self) -> str:
        """
        Get the title of the Contributor Discussions page.
        """
        return self._get_text_of_element(self.contributor_discussions_page_title)

    def get_contributor_discussions_forums_titles(self) -> list[str]:
        """
        Get the titles of all forums on the Contributor Discussions page.
        Returns:
            list[str]: A list of forum titles.
        """
        return self._get_text_of_elements(self.contributor_discussions_forum_names)

    def click_on_an_available_contributor_forum(self, forum: str):
        """
        Click on a specific forum in the Contributor Discussions page.
        Args:
            forum (str): The name of the forum to click on.
        """
        self._click(self.contributor_discussions_forum_name(forum))

    def get_forum_description(self, forum: str) -> str:
        """
        Get the description of a specific forum in the Contributor Discussions page.
        Args:
            forum (str): The name of the forum.
        """
        return self.eval_on_selector_for_last_child_text(
            f"//h5[@class='sumo-card-heading']/a[text()='{forum}']/../.."
        )

    def get_forum_thread_count(self, forum: str) -> int:
        """
        Get the number of threads in a specific forum in the Contributor Discussions page.
        Args:
            forum (str): The name of the forum.
        Returns:
            int: The number of threads in the forum.
        """
        return int(self._get_text_of_element(self.contributor_discussions_forum_thread_count(
            forum)))

    def get_forum_last_post_date(self, forum: str) -> str:
        """
        Get the date of the last post in a specific forum in the Contributor Discussions page.
        Args:
            forum (str): The name of the forum.
        Returns:
            str: The date of the last post in the forum.

        """
        return self._get_text_of_element(
            self.contributor_discussions_forum_last_post_date(forum)).replace("\u202f", " ")

    def click_on_last_post_date(self, forum: str):
        """
        Click on the date of the last post in a specific forum in the Contributor Discussions page.
        Args:
            forum (str): The name of the forum.
        """
        self._click(self.contributor_discussions_forum_last_post_date(forum))

    def get_forum_last_post_by(self, forum: str) -> str:
        """
        Get the author of the last post in a specific forum in the Contributor Discussions page.
        Args:
            forum (str): The name of the forum.
        Returns:
            str: The author of the last post in the forum.

        """
        return self._get_text_of_element(self.contributor_discussions_forum_last_post_by(forum))

    def click_on_last_post_by(self, forum: str):
        """
        Click on the author of the last post in a specific forum in the Contributor Discussions
        page.
        Args:
            forum (str): The name of the forum.
        """
        self._click(self.contributor_discussions_forum_last_post_by(forum))

    # Actions against the Contributor Discussions side navbar locators.
    def get_contributor_discussions_side_navbar_header(self) -> str:
        """
        Get the header text of the Contributor Discussions side navbar.
        Returns:
            str: The header text of the side navbar.
        """
        return self._get_text_of_element(self.contributor_discussions_side_navbar_header)

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
