from playwright.sync_api import Page

from playwright_tests.core.basepage import BasePage


class SupportForumsPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        # Locators belonging to the page heading section.
        self.page_main_heading = page.locator("h1[class='sumo-page-heading']")
        self.page_intro = page.locator("p[class='sumo-page-intro']")

        # Locators belonging to the product community forums cards.
        self.product_card_titles = page.locator("h3[class='card--title']")
        self.product_card = lambda card_name: page.locator(
            f"//a[normalize-space(.)='{card_name}']")
        self.card_description = lambda card_title: page.locator(
            f"//strong[text()='{card_title}']/../../following-sibling::p")
        self.all_products_support_forum_button = page.get_by_role("link").filter(
            has_text="All Products Community Forums")

    # Page heading actions.
    def get_page_heading_text(self) -> str:
        """Get the text of the page title."""
        return self._get_text_of_element(self.page_main_heading)

    def get_page_intro_text(self) -> str:
        """Get the text of the page subtitle."""
        return self._get_text_of_element(self.page_intro)

    # Product cards actions.
    def click_on_a_particular_product_card(self, card_name: str):
        """
        Click on a particular product community forum card.
        Args:
            card_name (str): The product community forum card on which the click event to be fired.
        """
        self._click(self.product_card(card_name))

    def get_product_card_titles_list(self) -> list[str]:
        """Get all product community forum card titles."""
        return self._get_text_of_elements(self.product_card_titles)

    def get_card_description_text(self, card_title: str) -> str:
        """
        Get the product community forum card description from a certain card.
        Args:
            card_title (str): The product community forum card title.
        """
        return self._get_text_of_element(self.card_description(card_title))

    def click_on_all_products_support_forum_button(self):
        """Click on the 'All Products Community Forums' button."""
        self._click(self.all_products_support_forum_button)
