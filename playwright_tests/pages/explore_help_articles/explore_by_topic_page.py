import re

from playwright.sync_api import Page

from playwright_tests.core.basepage import BasePage

"""
    This class contains the locators and actions for the /topics/ page.
"""


class ExploreByTopicPage(BasePage):
    """
        Locators belonging to the header section.
    """
    __explore_by_topic_page_header = "//div[@class='documents-product-title']/h1"

    """
        Locators belonging to the listed KB articles.
    """
    __article_metadata_info = "//div[@id='document_metadata']//span[@class='tooltip']"

    """
        Locators belonging to the side-navbar section.
    """
    __filter_by_product_dropdown = "//select[@id='products-topics-dropdown']"
    __filter_by_product_dropdown_selected_option = ("//select[@id='products-topics-dropdown"
                                                    "']/option[@selected]")
    __filter_by_product_dropdown_options = "//select[@id='products-topics-dropdown']/option"
    __all_topics_side_navbar_options = "//ul[@class='sidebar-nav--list']/li/a"
    __all_topics_selected_option = ("//ul[@class='sidebar-nav--list']/li/a[contains(@class, "
                                    "'selected')]")
    __AAQ_widget_continue_button = ("//div[@class='aaq-widget card is-inverse elevation-01 "
                                    "text-center radius-md']/a")
    __AAQ_widget_text = ("//div[@class='aaq-widget card is-inverse elevation-01 text-center "
                         "radius-md']/p")

    """
        Locators belonging to the Volunteer card section.
    """
    __volunteer_learn_more_option = "//section[@id='get-involved-button']//a"

    def __init__(self, page: Page):
        super().__init__(page)

    """
        Actions against the page header section.
    """
    def _get_explore_by_topic_page_header(self) -> str:
        return super()._get_text_of_element(self.__explore_by_topic_page_header)

    """
       Actions against the listed KB articles.
    """
    def _get_metadata_of_all_listed_articles(self) -> list[list[str]]:
        elements = []
        for metadata in super()._get_elements_locators(self.__article_metadata_info):
            metadata_elements = super()._get_text_content_of_all_locators(metadata)
            for item in metadata_elements:
                split_items = [i.strip() for i in item.strip().split(',')]
                elements.append(split_items)
        return elements

    """
        Actions against the page side-navbar section.
    """
    def _get_selected_topic_side_navbar_option(self) -> str:
        return super()._get_text_of_element(self.__all_topics_selected_option)

    def _get_all_topics_side_navbar_options(self) -> list[str]:
        return super()._get_text_of_elements(self.__all_topics_side_navbar_options)

    def _click_on_a_topic_filter(self, option: str):
        super()._click(f"//ul[@class='sidebar-nav--list']/li/"
                       f"a[normalize-space(text())='{option}']")

    def _get_current_product_filter_dropdown_option(self) -> str:
        option = super()._get_text_of_element(self.__filter_by_product_dropdown_selected_option)
        return re.sub(r'\s+', ' ', option).strip()

    def _get_all_filter_by_product_options(self) -> list[str]:
        return super()._get_text_of_elements(self.__filter_by_product_dropdown_options)

    def _select_a_filter_by_product_option(self, option: str):
        super()._select_option_by_label(self.__filter_by_product_dropdown, option)

    def _get_text_of_aaq_widget(self) -> str:
        return super()._get_text_of_element(self.__AAQ_widget_text)

    def _click_on_aaq_continue_button(self):
        super()._click(self.__AAQ_widget_continue_button)

    def _is_aaq_text_visible(self) -> bool:
        return super()._is_element_visible(self.__AAQ_widget_text)
