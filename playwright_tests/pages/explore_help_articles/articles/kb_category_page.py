from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class KBCategoryPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """Locators belonging to the KB Category page."""
        self.all_articles_from_list = page.locator("ul[class='documents'] li a")
        self.article_from_list = lambda article_name: page.locator(
            "ul[class='documents'] li").get_by_role("link", name=article_name, exact=True)

        """Locators belonging to the KB Category page pagination."""
        self.pagination_section = page.locator("ol.pagination")
        self.selected_pagination_page = page.locator("ol.pagination li.selected a")
        self.next_pagination_button = page.locator("ol.pagination a.btn-page-next")
        self.previous_pagination_button = page.locator("ol.pagination a.btn-page-prev")
        self.pagination_page = lambda page_number: page.locator(
            "ol.pagination li").get_by_role("link", name=str(page_number), exact=True)

    """Actions against the KB Category page."""
    def get_all_listed_articles(self) -> list[str]:
        """Returns the titles of all the articles listed on the category page."""
        return self._get_text_of_elements(self.all_articles_from_list)

    def click_on_article_from_list(self, article_name: str):
        """Clicks on a particular article listed on the category page."""
        self._click(self.article_from_list(article_name))

    """Actions against the KB Category page pagination."""
    def click_on_next_pagination_page(self):
        """Clicks on the 'Next' pagination button."""
        self._click(self.next_pagination_button)

    def click_on_previous_pagination_page(self):
        """Clicks on the 'Previous' pagination button."""
        self._click(self.previous_pagination_button)

    def click_on_pagination_page(self, page_number: int):
        """Clicks on a particular pagination page number."""
        self._click(self.pagination_page(page_number))
