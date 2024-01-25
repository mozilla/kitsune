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
    def _get_text_of_product_card_titles(self) -> list[str]:
        return super()._get_text_of_elements(self.__product_card_titles)

    def _click_on_product_card(self, element_number):
        super()._click_on_an_element_by_index(self.__product_list, element_number)

    # Featured articles
    def _get_number_of_featured_articles(self) -> int:
        return super()._get_elements_count(self.__featured_articles_list)

    def _get_featured_articles_titles(self) -> list[str]:
        return super()._get_text_of_elements(self.__featured_articles_card_titles)

    def _click_on_a_featured_card(self, element_number: int):
        super()._click_on_an_element_by_index(self.__featured_articles_card_items, element_number)

    # Learn More
    def _click_learn_more_option(self):
        super()._click(self.__learn_more_option)

    def _get_community_card_title(self) -> str:
        return super()._get_text_of_element(self.__join_our_community_card_title)

    def _get_community_card_description(self) -> str:
        return super()._get_text_of_element(self.__join_our_community_card_description)
