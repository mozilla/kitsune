from playwright.sync_api import Page

from playwright_tests.core.basepage import BasePage


class ContactSupportPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        # Breadcrumb locators.
        self.current_milestone = page.locator(
            "li[class='progress--item is-current'] span[class='progress--label']")

        # Page content locators.
        self.page_main_heading = page.locator("h1[class='sumo-page-heading']")
        self.page_subheading = page.locator("h2[class='sumo-page-subheading']")
        self.browse_all_product_forums_button = page.get_by_role("link").filter(
            has_text="Browse All Product Forums")

        # Product Card Titles locators.
        self.product_cards_titles = page.locator("div#product-picker h3[class='card--title']")
        self.product_card_subtitle = lambda card_name: page.locator(
            f"//a[normalize-space(text()) = '{card_name}']/..//following-sibling::p"
            f"[@class='card--desc']")
        self.product_card_by_name = lambda card_name: page.locator(
            "h3[class='card--title']").get_by_role("link", name=card_name, exact=True)

    # Breadcrumb related actions.
    def get_text_of_current_milestone(self) -> str:
        return self._get_text_of_element(self.current_milestone)

    # Page actions.
    def get_contact_support_main_heading(self) -> str:
        return self._get_text_of_element(self.page_main_heading)

    def get_contact_support_subheading_text(self) -> str:
        return self._get_text_of_element(self.page_subheading)

    def click_on_browse_all_product_forums_button(self):
        self._click(self.browse_all_product_forums_button)

    # Product card actions.
    def get_all_product_card_titles(self) -> list[str]:
        return self._get_text_of_elements(self.product_cards_titles)

    def get_product_card_subtitle(self, card_name: str) -> str:
        return self._get_text_of_element(self.product_card_subtitle(card_name))

    def click_on_a_particular_card(self, card_name: str):
        self._click(self.product_card_by_name(card_name))
