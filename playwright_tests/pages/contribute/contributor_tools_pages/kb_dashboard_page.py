from playwright_tests.core.basepage import BasePage
from playwright.sync_api import Page, Locator


class KBDashboard(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        # Top-level filter locators
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

    # KB Dashboard actions
    def get_a_particular_article_title_locator(self, article_name: str) -> Locator:
        return self.article_title(article_name)

    def click_on_article_title(self, article_name: str):
        self._click(self.article_title(article_name))

    def get_a_particular_article_status(self, article_name: str) -> str:
        return self._get_text_of_element(self.article_status(article_name))

    def get_needs_update_status(self, article_name: str) -> str:
        return self._get_text_of_element(self.needs_update_status(article_name))

    def is_needs_change_empty(self, article_name: str) -> bool:
        return self._is_element_empty(self.needs_update_status(article_name))

    def get_ready_for_l10n_status(self, article_name: str) -> str:
        return self._get_text_of_element(self.ready_for_l10n_status(article_name))

    def get_stale_status(self, article_name: str) -> str:
        return self._get_text_of_element(self.stale_status(article_name))

    def is_stale_status_empty(self, article_name: str) -> bool:
        return self._is_element_empty(self.stale_status(article_name))

    def get_existing_expiry_date(self, article_name: str) -> str:
        return self._get_text_of_element(self.expiry_date(article_name))

    def get_expiry_date_locator(self, article_name: str) -> Locator:
        return self.expiry_date(article_name)

    def click_on_show_translations_option(self, article_name: str):
        self._click(self.show_translations_option(article_name))

    def click_on_the_complete_overview_link(self):
        super()._click(self.complete_overview_link)
