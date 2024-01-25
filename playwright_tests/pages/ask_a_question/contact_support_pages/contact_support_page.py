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
    def _get_text_of_current_milestone(self) -> str:
        return super()._get_text_of_element(self.__current_milestone)

    # Page actions.
    def _get_contact_support_main_heading(self) -> str:
        return super()._get_text_of_element(self.__page_main_heading)

    def _get_contact_support_subheading_text(self) -> str:
        return super()._get_text_of_element(self.__page_subheading)

    def _click_on_browse_all_product_forums_button(self):
        super()._click(self.__browse_all_product_forums_button)

    # Product card actions.
    def _get_all_product_card_titles(self) -> list[str]:
        return super()._get_text_of_elements(self.__product_cards_titles)

    def _get_product_card_subtitle(self, card_name: str) -> str:
        xpath = (f"//a[@data-event-label='{card_name}']/..//following-sibling::p["
                 f"@class='card--desc']")
        return super()._get_text_of_element(xpath)

    def _click_on_a_particular_card(self, card_name: str):
        xpath = f"//h3[@class='card--title']/a[@data-event-label='{card_name}']"
        super()._click(xpath)
