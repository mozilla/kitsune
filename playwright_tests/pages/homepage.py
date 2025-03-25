from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class Homepage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        # Product list section locators.
        self.product_list = page.locator("div.card--product")
        self.product_card_titles = page.locator("div.card--product h3.card--title"
                                                ).get_by_role("link")
        self.product_card = lambda card_title: page.get_by_role(
            "link", name=f'{card_title}', exact=True)

        # Featured articles section locators.
        self.featured_articles_list = page.locator("div.card--article")
        self.featured_articles_card_titles = page.locator("div.card--article").get_by_role("link")

        # Join our Community section locators.
        self.join_our_community_card_title = page.locator("div.card--callout-wrap-narrow h3")
        self.join_our_community_card_description = page.locator("div.card--callout-wrap-narrow "
                                                                "p:nth-of-type(1)")
        self.learn_more_option = page.get_by_role("link").filter(has_text="Learn More")

    # Product Cards
    def get_text_of_product_card_titles(self) -> list[str]:
        """Get text of all product card titles"""
        return self._get_text_of_elements(self.product_card_titles)

    def click_on_product_card(self, element_number):
        """Click on a product card by its index"""
        self._click_on_an_element_by_index(self.product_list, element_number)

    def click_on_product_card_by_title(self, card_title: str):
        """Click on a product card by its title"""
        self._click(self.product_card(card_title))

    # Featured articles
    def get_number_of_featured_articles(self) -> int:
        """Get the number of featured articles"""
        return self._get_elements_count(self.featured_articles_list)

    def get_featured_articles_titles(self) -> list[str]:
        """Get the titles of featured articles"""
        return self._get_text_of_elements(self.featured_articles_card_titles)

    def click_on_a_featured_card(self, element_number: int):
        """Click on a featured card by its index"""
        self._click_on_an_element_by_index(self.featured_articles_list, element_number)

    # Learn More
    def click_learn_more_option(self):
        """Click on Learn More option"""
        self._click(self.learn_more_option)

    def get_community_card_title(self) -> str:
        """Get the title of the community card"""
        return self._get_text_of_element(self.join_our_community_card_title)

    def get_community_card_description(self) -> str:
        """Get the description of the community card"""
        return self._get_text_of_element(self.join_our_community_card_description)
