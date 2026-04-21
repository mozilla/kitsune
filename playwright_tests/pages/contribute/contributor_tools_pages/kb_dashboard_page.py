from playwright.sync_api import Locator, Page
from playwright_tests.core.basepage import BasePage


class KBDashboard(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """Locators related to the top-level filter section."""
        self.products_filter_button = page.locator(
            "article#localize div[class='mzp-c-menu-list featured-dropdown is-details'] button")
        self.products_filter_complete_overview = page.locator("div#product-selector select")
        self.filter_by_type = page.locator("div[class='table-filters'] select")
        self.filter_by_type_complete_overview = page.locator("select[name='category']")
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

    """Actions against the kb dashboard locators."""
    def click_on_article_title(self, article_name: str):
        self._click(self.article_title(article_name))

    def click_on_show_translations_option(self, article_name: str):
        self._click(self.show_translations_option(article_name))

    def click_on_the_complete_overview_link(self):
        super()._click(self.complete_overview_link)
