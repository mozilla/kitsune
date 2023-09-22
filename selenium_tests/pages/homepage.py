from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from selenium_tests.core.base_page import BasePage


class Homepage(BasePage):
    # Searchbar section
    __search_bar = (By.XPATH, "//form[@id='support-search-masthead']/input[@id='search-q']")
    __search_bar_button = (
        By.XPATH,
        "//form[@id='support-search-masthead']/button[@class='search-button']",
    )
    __popular_searches = (By.XPATH, "//p[@class='popular-searches']/a")

    # Product list section
    __product_list = (By.XPATH, "//div[contains(@class, 'card--product')]")
    __product_card_titles = (
        By.XPATH,
        "//div[contains(@class, 'card--product')]/div[@class='card--details']/h3["
        "@class='card--title']/a",
    )

    # Featured articles section
    __featured_articles_list = (By.XPATH, "//div[contains(@class, 'card--article')]")
    __featured_articles_first_item_card = (By.XPATH, "//div[contains(@class, 'card--article')][1]")
    __featured_articles_card_titles = (
        By.XPATH,
        "//div[contains(@class, 'card--article')]/div/h3/a",
    )

    # Join our Community section
    __join_our_community_card_title = (
        By.XPATH,
        "//div[@class='card--callout-wrap-narrow']//h3[@class='card--title']",
    )
    __join_our_community_card_description = (
        By.XPATH,
        "//div[@class='card--callout-wrap-narrow']//p[1]",
    )
    __learn_more_option = (By.LINK_TEXT, "Learn More")

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    def click_on_product_card(self, product_card):
        super()._click_on_web_element(product_card)

    def get_list_of_product_cards(self) -> list[WebElement]:
        return super()._find_elements(self.__product_list)

    def get_text_of_product_card_titles(self) -> list[str]:
        return super()._get_text_of_elements(self.__product_card_titles)

    def get_number_of_featured_articles(self) -> int:
        return super()._get_number_of_elements(self.__featured_articles_list)

    def get_featured_articles_titles(self) -> list[str]:
        return super()._get_text_of_elements(self.__featured_articles_card_titles)

    def click_on_featured_article(self):
        super()._click(self.__featured_articles_first_item_card)

    def click_learn_more_option(self):
        super()._click(self.__learn_more_option)

    def get_community_card_title(self) -> str:
        return super()._get_text_of_element(self.__join_our_community_card_title)

    def get_community_card_description(self) -> str:
        return super()._get_text_of_element(self.__join_our_community_card_description)

    def click_on_search_button(self):
        super()._click(self.__search_bar_button)

    def get_popular_searches_options(self) -> list[WebElement]:
        return super()._find_elements(self.__popular_searches)

    def click_on_popular_search_option(self, popular_search_option):
        super()._click(popular_search_option)

    def wait_for_searchbar_to_be_displayed_and_clickable(self):
        super()._wait_for_element_to_be_clickable(self.__search_bar)
