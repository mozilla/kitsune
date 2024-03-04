from playwright_tests.core.basepage import BasePage
from playwright.sync_api import Page, Locator


class KBDashboard(BasePage):
    # Top-level filter locators
    __products_filter_button = ("//article[@id='localize']/div[@class='mzp-c-menu-list "
                                "featured-dropdown is-details']//button")
    __products_filter_complete_overview = "//div[@id='product-selector']/select"
    __filter_by_type = "//div[@class='table-filters']//select"
    __filter_by_type_complete_overview = "//select[@name='category']"
    __subscribe_button = "//div[@id='doc-watch']/button"
    __complete_overview_link = "//div[@class='table-footer']/a"

    def __init__(self, page: Page):
        super().__init__(page)

    # KB Dashboard actions
    def _get_a_particular_article_title_locator(self, article_name: str) -> Locator:
        xpath = f"//td/a[text()='{article_name}']"
        return super()._get_element_locator(xpath)

    def _click_on_article_title(self, article_name: str):
        xpath = f"//td/a[text()='{article_name}']"
        super()._click(xpath)

    def _get_a_particular_article_status(self, article_name: str) -> str:
        xpath = (f"//td/a[text()='{article_name}']/../following-sibling::td[contains(@class,"
                 f"'status ')]")
        return super()._get_text_of_element(xpath)

    def _get_needs_update_status(self, article_name: str) -> str:
        xpath = (f"//td/a[text()='{article_name}']/../following-sibling::td[contains(@class,"
                 f"'needs-update')]")
        return super()._get_text_of_element(xpath)

    def _is_needs_change_empty(self, article_name: str) -> bool:
        xpath = (f"//td/a[text()='{article_name}']/../following-sibling::td[contains(@class,"
                 f"'needs-update')]")
        return super()._is_element_empty(xpath)

    def _get_ready_for_l10n_status(self, article_name: str) -> str:
        xpath = (f"//td/a[text()='{article_name}']/../following-sibling::td[contains(@class,"
                 f"'ready-for-l10n')]")
        return super()._get_text_of_element(xpath)

    def _get_stale_status(self, article_name: str) -> str:
        xpath = (f"//td/a[text()='{article_name}']/../following-sibling::td[contains(@class,"
                 f"'stale ')]")
        return super()._get_text_of_element(xpath)

    def _is_stale_status_empty(self, article_name: str) -> bool:
        xpath = (f"//td/a[text()='{article_name}']/../following-sibling::td[contains(@class,"
                 f"'stale ')]")
        return super()._is_element_empty(xpath)

    def _get_existing_expiry_date(self, article_name: str) -> str:
        xpath = f"//td/a[text()='{article_name}']/../following-sibling::td/time"
        return super()._get_text_of_element(xpath)

    def _get_expiry_date_locator(self, article_name: str) -> Locator:
        xpath = f"//td/a[text()='{article_name}']/../following-sibling::td/time"
        return super()._get_element_locator(xpath)

    def _click_on_show_translations_option(self, article_name: str):
        xpath = (f"//td/a[text()='{article_name}']/../following-sibling::td/a[contains(text(),"
                 f"'Show translations')]")
        super()._click(xpath)

    def _click_on_the_complete_overview_link(self):
        super()._click(self.__complete_overview_link)
