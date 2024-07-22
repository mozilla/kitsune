import re

from playwright.sync_api import Page

from playwright_tests.core.basepage import BasePage


class ExploreByTopicPage(BasePage):
    __explore_by_topic_page_header = "//div[@class='documents-product-title']/h1"
    __filter_by_product_dropdown_selected_option = ("//select[@id='products-topics-dropdown"
                                                    "']/option[@selected]")
    __all_topics_side_navbar_options = "//ul[@class='sidebar-nav--list']/li/a"
    __all_topics_selected_option = ("//ul[@class='sidebar-nav--list']/li/a[contains(@class, "
                                    "'selected')]")
    __AAQ_widget_continue_button = ("//div[@class='aaq-widget card is-inverse elevation-01 "
                                    "text-center radius-md']/a")
    __AAQ_widget_text = ("//div[@class='aaq-widget card is-inverse elevation-01 text-center "
                         "radius-md']/p")
    __volunteer_learn_more_option = "//section[@id='get-involved-button']//a"

    def __init__(self, page: Page):
        super().__init__(page)

    def _get_explore_by_topic_page_header(self) -> str:
        return super()._get_text_of_element(self.__explore_by_topic_page_header)

    def _get_selected_topic_side_navbar_option(self) -> str:
        return super()._get_text_of_element(self.__all_topics_selected_option)

    def _get_current_topic_filter_dropdown_option(self) -> str:
        option = super()._get_text_of_element(self.__filter_by_product_dropdown_selected_option)
        return re.sub(r'\s+', ' ', option).strip()
