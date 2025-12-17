import re

from playwright.sync_api import Page

from playwright_tests.core.basepage import BasePage

"""
    This class contains the locators and actions for the /topics/ page.
"""


class ExploreByTopicPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        # Locators belonging to the header section.
        self.explore_by_topic_page_header = page.locator("div.documents-product-title h1")

        # Locators belonging to the listed KB articles.
        self.article_metadata_info = page.locator("div#document_metadata span.tooltip")

        # Locators belonging to the page side-navbar section.
        self.filter_by_product_dropdown = page.locator("select#products-topics-dropdown")
        self.filter_by_product_dropdown_selected_option = page.locator(
            "select#products-topics-dropdown option[selected]")
        self.filter_by_product_dropdown_options = page.locator(
            "select#products-topics-dropdown option")
        self.all_topics_side_navbar_options = page.locator("ul.sidebar-nav--list li a")
        self.all_topics_selected_option = page.locator("ul.sidebar-nav--list li a.selected")
        self.topic_filter = lambda option: page.locator(
            "ul.sidebar-nav--list li").get_by_role("link", name=option, exact=True)

    """
        Actions against the page header section.
    """
    def get_explore_by_topic_page_header(self) -> str:
        """Get the text of the page header."""
        return self._get_text_of_element(self.explore_by_topic_page_header)

    """
       Actions against the listed KB articles.
    """
    def get_metadata_of_all_listed_articles(self) -> list[list[str]]:
        """Get the metadata of all listed articles."""
        elements = [
            [i.strip() for i in item.strip().split(',')]
            for metadata in self.article_metadata_info.all()
            for item in self._get_text_content_of_all_locators(metadata)
        ]
        return elements

    """
        Actions against the page side-navbar section.
    """
    def get_selected_topic_side_navbar_option(self) -> str:
        """Get the text of the selected topic in the side-navbar."""
        return self._get_text_of_element(self.all_topics_selected_option)

    def get_all_topics_side_navbar_options(self) -> list[str]:
        """Get the text of all topics in the side-navbar."""
        return self._get_text_of_elements(self.all_topics_side_navbar_options)

    def click_on_a_topic_filter(self, option: str):
        """Click on a topic filter in the side-navbar.

        Args:
            option (str): The topic filter to click on.
        """
        self._click(self.topic_filter(option))

    def get_current_product_filter_dropdown_option(self) -> str:
        """Get the text of the selected option in the product filter dropdown."""
        option = self._get_text_of_element(self.filter_by_product_dropdown_selected_option)
        return re.sub(r'\s+', ' ', option).strip()

    def get_all_filter_by_product_options(self) -> list[str]:
        """Get the text of all options in the product filter dropdown."""
        return self._get_text_of_elements(self.filter_by_product_dropdown_options)

    def select_a_filter_by_product_option(self, option: str):
        """Select a filter by product option in the dropdown.

        Args:
            option (str): The option to select in the dropdown
        """
        self._select_option_by_label(self.filter_by_product_dropdown, option)
