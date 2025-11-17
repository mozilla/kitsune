from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class ProductsPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """Locators belonging to the page breadcrumbs."""
        self.first_breadcrumb = page.locator("ol#breadcrumbs li a")

        """General page locators."""
        self.page_header = page.locator("h1.sumo-page-heading-xl")

        """Locators belonging to the product cards."""
        self.all_product_card_titles = page.locator("h3.card--title")
        self.card_subheading = lambda card_title: page.locator(
            f"//a[normalize-space(text())='{card_title}']/../following-sibling::p[@class='card--"
            f"desc']")
        self.card = lambda card_title: page.locator(
            "div.card--details").get_by_role("link", name=card_title, exact=True)

    """Actions against the page breadcrumb locators."""
    def click_on_first_breadcrumb(self):
        self._click(self.first_breadcrumb)

    """Actions against the general page content locators."""
    def get_page_header(self) -> str:
        return self._get_text_of_element(self.page_header)

    """Actions against the product cards locators."""
    def get_subheading_of_card(self, card_title: str) -> str:
        return self._get_text_of_element(self.card_subheading(card_title))

    def click_on_a_particular_product_support_card(self, card_title):
        self._click(self.card(card_title))

    def get_all_product_support_titles(self) -> list[str]:
        return self._get_text_of_elements(self.all_product_card_titles)
