from playwright.sync_api import Locator, Page
from playwright_tests.core.basepage import BasePage


class KBDashboard(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """Locators related to the top-level filter section."""
        self.products_filter_button = page.locator(
            "article#localize div[class='mzp-c-menu-list featured-dropdown is-details'] button")
        self.products_filter_complete_overview = page.locator("div#product-selector select")
        self.products_filter_complete_overview_options = page.locator(
            "div#product-selector select option")
        self.filter_by_type = page.locator("div[class='table-filters'] select")
        self.filter_by_type_complete_overview = page.locator("select[name='category']")
        self.filter_by_type_complete_overview_options = page.locator(
            "select[name='category'] option")
        self.subscribe_button = page.locator("div#doc-watch button")
        self.complete_overview_link = page.locator("div[class='table-footer'] a")
        self.article_title = lambda article_name: page.locator("td").get_by_role(
            "link", name=article_name, exact=True)
        self.article_status = lambda article_name: page.locator(
            f"//td/a[text()='{article_name}']/../following-sibling::td[contains(@class,'status ')]"
        )
        self.needs_update_status = lambda article_name: page.locator(
            f"//td/a[text()='{article_name}']/../following-sibling::td[contains(@class, "
            f"'needs-update')]")
        self.ready_for_l10n_status = lambda article_name: page.locator(
            f"//td/a[text()='{article_name}']/../following-sibling::td[contains(@class,"
            f"'ready-for-l10n')]")
        self.stale_status = lambda article_name: page.locator(
            f"//td/a[text()='{article_name}']/../following-sibling::td[contains(@class,'stale ')]")
        self.expiry_date = lambda article_name: page.locator(
            f"//td/a[text()='{article_name}']/../following-sibling::td/time")
        self.show_translations_option = lambda article_name: page.locator(
            f"//td/a[text()='{article_name}']/../following-sibling::td/a[contains(text(),"
            f"'Show translations')]")

        """Locator matching every article title link listed in the overview table."""
        self.listed_article_titles = page.locator("table#kb-overview-table td:first-child > a")

    """Actions against the kb dashboard locators."""
    def get_product_filter_options(self) -> list[dict]:
        """Returns the value/label pairs of the product filter dropdown options, excluding the
        empty 'All Products' option."""
        options = []
        for option in self.products_filter_complete_overview_options.all():
            value = option.get_attribute("value")
            if value:
                options.append({"value": value, "label": option.text_content().strip()})
        return options

    def filter_by_product(self, product_value: str):
        """Selects a product in the overview filter dropdown, triggering a page reload."""
        self._select_option_by_value(self.products_filter_complete_overview, product_value)

    def get_type_filter_options(self) -> list[dict]:
        """Returns the value/label pairs of the 'Filter by type' dropdown options, excluding the
        empty 'All' option."""
        options = []
        for option in self.filter_by_type_complete_overview_options.all():
            value = option.get_attribute("value")
            if value:
                options.append({"value": value, "label": option.text_content().strip()})
        return options

    def select_type_filter(self, type_value: str):
        """Selects a type in the 'Filter by type' dropdown, triggering a page reload."""
        self._select_option_by_value(self.filter_by_type_complete_overview, type_value)

    def get_number_of_listed_articles(self) -> int:
        return self.listed_article_titles.count()

    def get_listed_article_title(self, index: int) -> str:
        return self.listed_article_titles.nth(index).text_content().strip()

    def get_listed_article_url(self, index: int) -> str:
        return self.listed_article_titles.nth(index).get_attribute("href")

    def click_on_listed_article(self, index: int):
        self._click(self.listed_article_titles.nth(index))

    def click_on_article_title(self, article_name: str):
        self._click(self.article_title(article_name))

    def click_on_show_translations_option(self, article_name: str):
        self._click(self.show_translations_option(article_name))

    def click_on_the_complete_overview_link(self):
        super()._click(self.complete_overview_link)
