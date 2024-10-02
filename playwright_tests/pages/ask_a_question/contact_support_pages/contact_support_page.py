from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class ContactSupportPage(BasePage):
    # Breadcrumb locators.
    __current_milestone = ("//li[@class='progress--item is-current']//span["
                           "@class='progress--label']")
    # Page content locators.
    __page_main_heading = "//h1[@class='sumo-page-heading']"
    __page_subheading = "//h2[@class='sumo-page-subheading']"
    __browse_all_product_forums_button = "//a[contains(text(), 'Browse All Product Forums')]"

    # Product Card Titles locators.
    __product_cards_titles = "//div[@id='product-picker']//h3[@class='card--title']"

    def __init__(self, page: Page):
        super().__init__(page)

    # Breadcrumb related actions.
    def get_text_of_current_milestone(self) -> str:
        return self._get_text_of_element(self.__current_milestone)

    # Page actions.
    def get_contact_support_main_heading(self) -> str:
        return self._get_text_of_element(self.__page_main_heading)

    def get_contact_support_subheading_text(self) -> str:
        return self._get_text_of_element(self.__page_subheading)

    def click_on_browse_all_product_forums_button(self):
        self._click(self.__browse_all_product_forums_button)

    # Product card actions.
    def get_all_product_card_titles(self) -> list[str]:
        return self._get_text_of_elements(self.__product_cards_titles)

    def get_product_card_subtitle(self, card_name: str) -> str:
        return self._get_text_of_element(f"//a[normalize-space(text()) = '{card_name}']/..//"
                                         f"following-sibling::p[@class='card--desc']")

    def click_on_a_particular_card(self, card_name: str):
        self._click(f"//h3[@class='card--title']/a[normalize-space(text())='{card_name}']")
