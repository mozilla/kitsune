from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class Homepage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """Locators belonging to the product list section."""
        self.product_list = page.locator("div.card--product")
        self.product_card_titles = page.locator("div.card--product h3.card--title"
                                                ).get_by_role("link")
        self.product_card = lambda card_title: page.get_by_role(
            "link", name=f'{card_title}', exact=True)

        """Locators belonging to the featured articles section."""
        self.featured_articles_list = page.locator("div.card--article")
        self.featured_articles_card_titles = page.locator("div.card--article").get_by_role("link")


    """Actions against the product cards."""
    def get_text_of_product_card_titles(self) -> list[str]:
        """Get text of all product card titles"""
        return self._get_text_of_elements(self.product_card_titles)

    def click_on_product_card(self, element_number):
        """Click on a product card by its index"""
        self._click_on_an_element_by_index(self.product_list, element_number)

    def click_on_product_card_by_title(self, card_title: str):
        """Click on a product card by its title"""
        self._click(self.product_card(card_title))

    """Actions against the featured articles cards."""
    def get_number_of_featured_articles(self) -> int:
        """Get the number of featured articles"""
        return self._get_elements_count(self.featured_articles_list)

    def get_featured_articles_titles(self) -> list[str]:
        """Get the titles of featured articles"""
        return self._get_text_of_elements(self.featured_articles_card_titles)

    def click_on_a_featured_card(self, element_number: int):
        """Click on a featured card by its index"""
        self._click_on_an_element_by_index(self.featured_articles_list, element_number)
