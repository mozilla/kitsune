from playwright.sync_api import Page, ElementHandle
from playwright_tests.core.basepage import BasePage


class ProductSolutionsPage(BasePage):
    __complete_progress_item = "//li[@class='progress--item is-complete']/a"
    __complete_progress_item_label = ("//li[@class='progress--item is-complete']//span["
                                      "@class='progress--label']")
    __current_progress_item = "//li[@class='progress--item is-current']/a"
    __current_progress_item_label = ("//li[@class='progress--item is-current']//span["
                                     "@class='progress--label']")
    __product_title_heading = "//span[@class='product-title-text']"
    __product_solutions_find_help_searchbar = "//form[@id='question-search-masthead']/input"
    __product_solutions_find_help_search_button = "//form[@id='question-search-masthead']/button"
    __page_heading_intro_text = "//p[@class='page-heading--intro-text']"
    __still_need_help_ask_now_button = "//a[@data-event-action='aaq']"
    __featured_articles_cards = "//h2[contains(text(),'Featured Articles')]/../..//a"
    __popular_topics_cards = "//h2[contains(text(),'Popular Topics')]/../..//a"

    def __init__(self, page: Page):
        super().__init__(page)

    def click_ask_now_button(self):
        super()._click(self.__still_need_help_ask_now_button)

    def is_product_solutions_page_header_displayed(self) -> ElementHandle:
        return super()._get_element_handle(self.__product_title_heading)
