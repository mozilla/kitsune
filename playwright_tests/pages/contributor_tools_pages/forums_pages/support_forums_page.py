from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class SupportForumsPage(BasePage):
    # Support forum page locators.
    __page_main_heading = "//h1[@class='sumo-page-heading']"
    __page_intro = "//p[@class='sumo-page-intro']"
    __product_card_titles = "//h3[@class='card--title']"
    __all_products_support_forum_button = "//a[contains(text(), 'All Products Support Forum')]"

    def __init__(self, page: Page):
        super().__init__(page)

    # Page content actions.
    def _get_page_heading_text(self) -> str:
        return super()._get_text_of_element(self.__page_main_heading)

    def _get_page_intro_text(self) -> str:
        return super()._get_text_of_element(self.__page_intro)

    def _click_on_all_products_support_forum_button(self):
        super()._click(self.__all_products_support_forum_button)

    # Product cards actions.
    def _click_on_a_particular_product_card(self, card_name: str):
        xpath = f"//strong[text()='{card_name}']"
        super()._click(xpath)

    def _get_product_card_titles_list(self) -> list[str]:
        return super()._get_text_of_elements(self.__product_card_titles)

    def _get_card_description_text(self, card_title: str) -> str:
        xpath = f"//strong[text()='{card_title}']/../../following-sibling::p"
        return super()._get_text_of_element(xpath)
