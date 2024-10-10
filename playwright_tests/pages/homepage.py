from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class Homepage(BasePage):

    # Product list section
    __product_list = "div.card--product"
    __product_card_titles = "//div[contains(@class, 'card--product')]//h3[@class='card--title']/a"

    # Featured articles section
    __featured_articles_list = "div.card--article"
    __featured_articles_card_items = "div.card--article"
    __featured_articles_card_titles = "div.card--article a"

    # Join our Community section
    __join_our_community_card_title = "div.card--callout-wrap-narrow h3"

    __join_our_community_card_description = "//div[@class='card--callout-wrap-narrow']//p[1]"
    __learn_more_option = "//a[contains(text(), 'Learn More')]"

    def __init__(self, page: Page):
        super().__init__(page)

    # Product Cards
    def get_text_of_product_card_titles(self) -> list[str]:
        return self._get_text_of_elements(self.__product_card_titles)

    def click_on_product_card(self, element_number):
        self._click_on_an_element_by_index(self.__product_list, element_number)

    def click_on_product_card_by_title(self, card_title: str):
        self._click(f"//h3[@class='card--title']/a[normalize-space(text())='{card_title}']")

    # Featured articles
    def get_number_of_featured_articles(self) -> int:
        return self._get_elements_count(self.__featured_articles_list)

    def get_featured_articles_titles(self) -> list[str]:
        return self._get_text_of_elements(self.__featured_articles_card_titles)

    def click_on_a_featured_card(self, element_number: int):
        self._click_on_an_element_by_index(self.__featured_articles_card_items, element_number)

    # Learn More
    def click_learn_more_option(self):
        self._click(self.__learn_more_option)

    def get_community_card_title(self) -> str:
        return self._get_text_of_element(self.__join_our_community_card_title)

    def get_community_card_description(self) -> str:
        return self._get_text_of_element(self.__join_our_community_card_description)
