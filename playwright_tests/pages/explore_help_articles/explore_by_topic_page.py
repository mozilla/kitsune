import re

from playwright.sync_api import Page

from playwright_tests.core.basepage import BasePage

"""
    This class contains the locators and actions for the /topics/ page.
"""


class ExploreByTopicPage(BasePage):
    # Locators belonging to the header section.
    HEADER_SECTION_LOCATORS = {
        "explore_by_topic_page_header": "//div[@class='documents-product-title']/h1"
    }

    # Locators belonging to the listed KB articles.
    LISTED_ARTICLES_LOCATORS = {
        "article_metadata_info": "//div[@id='document_metadata']//span[@class='tooltip']"
    }

    # Locators belonging to the page side-navbar section.
    SIDE_NAVBAR_LOCATORS = {
        "filter_by_product_dropdown": "//select[@id='products-topics-dropdown']",
        "filter_by_product_dropdown_selected_option": "//select[@id='products-topics-dropdown']/"
                                                      "option[@selected]",
        "filter_by_product_dropdown_options": "//select[@id='products-topics-dropdown']/option",
        "all_topics_side_navbar_options": "//ul[@class='sidebar-nav--list']/li/a",
        "all_topics_selected_option": "//ul[@class='sidebar-nav--list']/li/a[contains(@class, "
                                      "'selected')]",
        "AAQ_widget_continue_button": "//div[@class='aaq-widget card is-inverse elevation-01 text"
                                      "-center radius-md']/a",
        "AAQ_widget_text": "//div[@class='aaq-widget card is-inverse elevation-01 text-center "
                           "radius-md']/p"
    }

    # Locators belonging to the Volunteer card section.
    VOLUNTEER_CARD_LOCATORS = {
        "volunteer_learn_more_option": "//section[@id='get-involved-button']//a"
    }

    def __init__(self, page: Page):
        super().__init__(page)

    """
        Actions against the page header section.
    """
    def get_explore_by_topic_page_header(self) -> str:
        """Get the text of the page header."""
        return self._get_text_of_element(self.HEADER_SECTION_LOCATORS
                                         ["explore_by_topic_page_header"])

    """
       Actions against the listed KB articles.
    """
    def get_metadata_of_all_listed_articles(self) -> list[list[str]]:
        """Get the metadata of all listed articles."""
        elements = [
            [i.strip() for i in item.strip().split(',')]
            for metadata in self._get_elements_locators(self.LISTED_ARTICLES_LOCATORS
                                                        ["article_metadata_info"])
            for item in self._get_text_content_of_all_locators(metadata)
        ]
        return elements

    """
        Actions against the page side-navbar section.
    """
    def get_selected_topic_side_navbar_option(self) -> str:
        """Get the text of the selected topic in the side-navbar."""
        return self._get_text_of_element(self.SIDE_NAVBAR_LOCATORS["all_topics_selected_option"])

    def get_all_topics_side_navbar_options(self) -> list[str]:
        """Get the text of all topics in the side-navbar."""
        return self._get_text_of_elements(self.SIDE_NAVBAR_LOCATORS
                                          ["all_topics_side_navbar_options"])

    def click_on_a_topic_filter(self, option: str):
        """Click on a topic filter in the side-navbar.

        Args:
            option (str): The topic filter to click on.
        """
        self._click(f"//ul[@class='sidebar-nav--list']/li/a[normalize-space(text())='{option}']")

    def get_current_product_filter_dropdown_option(self) -> str:
        """Get the text of the selected option in the product filter dropdown."""
        option = self._get_text_of_element(self.SIDE_NAVBAR_LOCATORS
                                           ["filter_by_product_dropdown_selected_option"])
        return re.sub(r'\s+', ' ', option).strip()

    def get_all_filter_by_product_options(self) -> list[str]:
        """Get the text of all options in the product filter dropdown."""
        return self._get_text_of_elements(self.SIDE_NAVBAR_LOCATORS
                                          ["filter_by_product_dropdown_options"])

    def select_a_filter_by_product_option(self, option: str):
        """Select a filter by product option in the dropdown.

        Args:
            option (str): The option to select in the dropdown
        """
        self._select_option_by_label(self.SIDE_NAVBAR_LOCATORS
                                     ["filter_by_product_dropdown"], option)

    def get_text_of_aaq_widget(self) -> str:
        """Get the text of the AAQ widget."""
        return self._get_text_of_element(self.SIDE_NAVBAR_LOCATORS["AAQ_widget_text"])

    def click_on_aaq_continue_button(self):
        """Click on the continue button of the AAQ widget."""
        self._click(self.SIDE_NAVBAR_LOCATORS["AAQ_widget_continue_button"])

    def is_aaq_text_visible(self) -> bool:
        """Check if the AAQ widget text is visible."""
        return self._is_element_visible(self.SIDE_NAVBAR_LOCATORS["AAQ_widget_text"])
