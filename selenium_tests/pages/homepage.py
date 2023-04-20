from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium_tests.core.base_page import BasePage


class Homepage(BasePage):
    __search_bar = (By.XPATH, "//form[@id='support-search-masthead']/input[@id='search-q']")
    __search_bar_button = (
        By.XPATH,
        "//form[@id='support-search-masthead']/button[@class='search-button']",
    )
    __popular_searches = (By.XPATH, "//p[@class='popular-searches']/a")
    __product_list = (By.XPATH, "//div[contains(@class, 'card--product')]")
    __featured_articles_list = (By.XPATH, "//div[contains(@class, 'card--article')]")
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

    def click_learn_more_option(self):
        super()._click(self.__learn_more_option)

    def get_community_card_title(self) -> str:
        return super()._get_text_of_element(self.__join_our_community_card_title)

    def get_community_card_description(self) -> str:
        return super()._get_text_of_element(self.__join_our_community_card_description)
