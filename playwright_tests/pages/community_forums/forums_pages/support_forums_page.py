from playwright.sync_api import Page

from playwright_tests.core.basepage import BasePage


class SupportForumsPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        # Support forum page locators.
        self.page_main_heading = page.locator("h1[class='sumo-page-heading']")
        self.page_intro = page.locator("p[class='sumo-page-intro']")
        self.product_card_titles = page.locator("h3[class='card--title']")
        self.all_products_support_forum_button = page.get_by_role("link").filter(
            has_text="All Products Community Forums")
        self.product_card = lambda card_name: page.get_by_role(
            "strong", name=card_name, exact=True)
        self.card_description = lambda card_title: page.locator(
            f"//strong[text()='{card_title}']/../../following-sibling::p")

    # Page content actions.
    def _get_page_heading_text(self) -> str:
        return super()._get_text_of_element(self.page_main_heading)

    def _get_page_intro_text(self) -> str:
        return super()._get_text_of_element(self.page_intro)

    def _click_on_all_products_support_forum_button(self):
        super()._click(self.all_products_support_forum_button)

    # Product cards actions.
    def _click_on_a_particular_product_card(self, card_name: str):
        super()._click(self.product_card(card_name))

    def _get_product_card_titles_list(self) -> list[str]:
        return super()._get_text_of_elements(self.product_card_titles)

    def _get_card_description_text(self, card_title: str) -> str:
        return super()._get_text_of_element(self.card_description(card_title))
