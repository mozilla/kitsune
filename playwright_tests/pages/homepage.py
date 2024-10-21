from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class Homepage(BasePage):
    # Product list section
    PRODUCT_LIST_SECTION_LOCATORS = {
        "product_list": "div.card--product",
        "product_card_titles": "//div[contains(@class, 'card--product')]//h3[@class='card--title']"
                               "/a"
    }
    # Featured articles section
    FEATURED_ARTICLES_SECTION_LOCATORS = {
        "featured_articles_list": "div.card--article",
        "featured_articles_card_items": "div.card--article",
        "featured_articles_card_titles": "div.card--article a"
    }
    # Join our Community section
    JOIN_OUR_COMMUNITY_SECTION_LOCATORS = {
        "join_our_community_card_title": "div.card--callout-wrap-narrow h3",
        "join_our_community_card_description": "//div[@class='card--callout-wrap-narrow']//p[1]",
        "learn_more_option": "//a[contains(text(), 'Learn More')]"
    }

    def __init__(self, page: Page):
        super().__init__(page)

    # Product Cards
    def get_text_of_product_card_titles(self) -> list[str]:
        """Get text of all product card titles"""
        return self._get_text_of_elements(
            self.PRODUCT_LIST_SECTION_LOCATORS["product_card_titles"])

    def click_on_product_card(self, element_number):
        """Click on a product card by its index"""
        self._click_on_an_element_by_index(self.PRODUCT_LIST_SECTION_LOCATORS["product_list"],
                                           element_number)

    def click_on_product_card_by_title(self, card_title: str):
        """Click on a product card by its title"""
        self._click(f"//h3[@class='card--title']/a[normalize-space(text())='{card_title}']")

    # Featured articles
    def get_number_of_featured_articles(self) -> int:
        """Get the number of featured articles"""
        return self._get_elements_count(
            self.FEATURED_ARTICLES_SECTION_LOCATORS["featured_articles_list"])

    def get_featured_articles_titles(self) -> list[str]:
        """Get the titles of featured articles"""
        return self._get_text_of_elements(
            self.FEATURED_ARTICLES_SECTION_LOCATORS["featured_articles_card_titles"])

    def click_on_a_featured_card(self, element_number: int):
        """Click on a featured card by its index"""
        self._click_on_an_element_by_index(
            self.FEATURED_ARTICLES_SECTION_LOCATORS["featured_articles_card_items"],
            element_number)

    # Learn More
    def click_learn_more_option(self):
        """Click on Learn More option"""
        self._click(self.JOIN_OUR_COMMUNITY_SECTION_LOCATORS["learn_more_option"])

    def get_community_card_title(self) -> str:
        """Get the title of the community card"""
        return self._get_text_of_element(
            self.JOIN_OUR_COMMUNITY_SECTION_LOCATORS["join_our_community_card_title"])

    def get_community_card_description(self) -> str:
        """Get the description of the community card"""
        return self._get_text_of_element(
            self.JOIN_OUR_COMMUNITY_SECTION_LOCATORS["join_our_community_card_description"])
