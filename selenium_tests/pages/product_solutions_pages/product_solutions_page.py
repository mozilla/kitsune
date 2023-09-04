from selenium.webdriver.common.by import By
from selenium_tests.core.base_page import BasePage
from selenium.webdriver.remote.webdriver import WebDriver


class ProductSolutionsPage(BasePage):
    __complete_progress_item = (By.XPATH, "//li[@class='progress--item is-complete']/a")
    __complete_progress_item_label = (
        By.XPATH,
        "//li[@class='progress--item is-complete']//span[" "@class='progress--label']",
    )
    __current_progress_item = (By.XPATH, "//li[@class='progress--item is-current']/a")
    __current_progress_item_label = (
        By.XPATH,
        "//li[@class='progress--item is-current']//span[@class='progress--label']",
    )
    __product_title_heading = (By.XPATH, "//span[@class='product-title-text']")
    __product_solutions_find_help_searchbar = (
        By.XPATH,
        "//form[@id='question-search-masthead']/input",
    )
    __product_solutions_find_help_search_button = (
        By.XPATH,
        "//form[@id='question-search-masthead']/button",
    )
    __page_heading_intro_text = (By.XPATH, "//p[@class='page-heading--intro-text']")
    __still_need_help_ask_now_button = (By.XPATH, "//a[@data-event-action='aaq']")
    __featured_articles_cards = (By.XPATH, "//h2[contains(text(),'Featured Articles')]/../..//a")
    __popular_topics_cards = (By.XPATH, "//h2[contains(text(),'Popular Topics')]/../..//a")

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    def click_ask_now_button(self):
        super()._click(self.__still_need_help_ask_now_button)

    def is_product_solutions_page_header_displayed(self):
        super()._is_element_displayed(self.__product_title_heading)
