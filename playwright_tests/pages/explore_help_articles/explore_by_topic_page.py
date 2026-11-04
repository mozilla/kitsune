import re
from urllib.parse import urlparse
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from playwright_tests.core.basepage import BasePage

"""
    This class contains the locators and actions for the /topics/ page.
"""


class ExploreByTopicPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """Locators belonging to the page breadcrumb section."""
        self.product_breadcrumb = lambda product: page.locator(
            f"//ol[@id='breadcrumbs']/li/a[text()='{product}']")

        """Locators belonging to the page header section."""
        self.explore_by_topic_page_header = page.locator("header.topic-header h1.topic-title")

        """Locators belonging to the listed KB articles."""
        self.listed_articles = page.locator("section[data-topic-list] article.topic-doc-list--item")

        """Locators belonging to the page side-navbar section."""
        self.filter_by_product_dropdown = page.locator("select#products-topics-dropdown")
        self.filter_by_product_dropdown_selected_option = page.locator(
            "select#products-topics-dropdown option[selected]")
        self.filter_by_product_dropdown_options = page.locator(
            "select#products-topics-dropdown option")
        self.filter_by_product_dropdown_option = lambda option: page.locator(
            f"//select[@id='products-topics-dropdown']/option[normalize-space(text())="
            f"'{option}']")
        self.all_topics_side_navbar_options = page.locator("ul.sidebar-nav--list li a")
        self.all_topics_selected_option = page.locator("ul.sidebar-nav--list li a.selected")
        self.topic_filter = lambda option: page.locator(
            "ul.sidebar-nav--list li").get_by_role("link", name=option, exact=True)

    """Actions against the listed KB articles."""
    def get_urls_of_all_listed_articles(self, timeout=5000) -> list[str]:
        """Get the URL of every listed article."""
        try:
            self.listed_articles.first.wait_for(state="attached", timeout=timeout)
        except PlaywrightTimeoutError:
            return []
        return self.listed_articles.evaluate_all(
            "articles => articles.map(a => a.querySelector('h3 a').getAttribute('href'))")

    def get_products_of_all_listed_articles(self, timeout=5000) -> dict[str, list[str]]:
        """Map every listed article's URL to the products in its metadata.

        Only the "All Products" listing names the products; with a product selected, the
        metadata names the article's other products instead.
        """
        try:
            self.listed_articles.first.wait_for(state="attached", timeout=timeout)
        except PlaywrightTimeoutError:
            return {}
        return self.listed_articles.evaluate_all("""articles => Object.fromEntries(
            articles.map(a => {
                const spans = a.querySelectorAll('.topic-doc-list--meta span');
                const products = spans.length > 2 ? spans[spans.length - 1].textContent : '';
                return [a.querySelector('h3 a').getAttribute('href'),
                        products.split(',').map(p => p.trim()).filter(Boolean)];
            }))""")

    """Actions against the page side-navbar section."""
    def get_all_topics_side_navbar_options(self) -> list[str]:
        """Get the text of all topics in the side-navbar."""
        return self._get_text_of_elements(self.all_topics_side_navbar_options)

    def click_on_a_topic_filter(self, option: str):
        """Click on a topic filter in the side-navbar.

        Args:
            option (str): The topic filter to click on.
        """
        self._click(self.topic_filter(option), expected_locator=self.explore_by_topic_page_header)

    def get_all_filter_by_product_options(self) -> list[str]:
        """Get the text of all options in the product filter dropdown."""
        return self._get_text_of_elements(self.filter_by_product_dropdown_options)

    def select_a_filter_by_product_option(self, option: str, retries=3, delay=500):
        """Select a filter by product option in the dropdown and wait for the navigation it
        triggers to land on the selected option's target URL.

        Args:
            option (str): The option to select in the dropdown
            retries (int): How many times to re-issue the selection before giving up
            delay (int): Milliseconds to wait between attempts
        """
        target_path = urlparse(
            self.filter_by_product_dropdown_option(option).get_attribute("value")).path
        for attempt in range(retries):
            try:
                with self.page.expect_navigation(
                        url=lambda url: urlparse(url).path == target_path, timeout=10000):
                    self._select_option_by_label(self.filter_by_product_dropdown, option)
                return
            except PlaywrightTimeoutError:
                if attempt == retries - 1:
                    raise
                self._wait_for_given_timeout(delay)
