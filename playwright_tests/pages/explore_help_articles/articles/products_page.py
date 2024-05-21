from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class ProductsPage(BasePage):
    # Page breadcrumb locators.
    __first_breadcrumb = "//ol[@id='breadcrumbs']/li/a"

    # Page content locators.
    __page_header = "//h1[@class='sumo-page-heading-xl']"

    # Product cards locators.
    __all_product_card_titles = "//h3[@class='card--title']"

    def __init__(self, page: Page):
        super().__init__(page)

    # Page breadcrumbs actions.
    def _click_on_first_breadcrumb(self):
        super()._click(self.__first_breadcrumb)

    # Page content actions.
    def _get_page_header(self) -> str:
        return super()._get_text_of_element(self.__page_header)

    # Product card actions.
    def _get_subheading_of_card(self, card_title: str) -> str:
        return super()._get_text_of_element(f"//a[normalize-space(text())='{card_title}']/../"
                                            f"following-sibling::p[@class='card--desc']")

    def _click_on_a_particular_product_support_card(self, card_title):
        super()._click(f"//div[@class='card--details']//a[normalize-space(text())='{card_title}']")

    def _get_all_product_support_titles(self) -> list[str]:
        return super()._get_text_of_elements(self.__all_product_card_titles)
