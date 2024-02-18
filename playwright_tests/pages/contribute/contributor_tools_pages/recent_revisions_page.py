from playwright_tests.core.basepage import BasePage
from playwright.sync_api import Page, Locator


class RecentRevisions(BasePage):

    # Right-side menu locators
    __kb_dashboard_option = "//a[text()='KB Dashboard']"
    __locale_metrics_option = "//a[text()='Locale Metrics']"
    __kb_team_option = "//a[contains(text(),'KB Team')]"
    __selected_right_side_option = "//li[@id='editing-tools-sidebar']//li[@class='selected']/a"
    __aggregated_metrics = "//a[text()='Aggregated Metrics']"

    # Recent Revisions table locators.
    __locale_select_field = "//select[@id='id_locale']"
    __locale_tag = "//span[@class='locale']"
    __all_editors = "//div[@class='creator']/a"
    __users_input_field = "//input[@id='id_users']"
    __start_date_input_field = "//input[@id='id_start']"
    __end_date_input_field = "//input[@id='id_end']"
    __all_dates = "//div[@class='date']/a/time"

    # Revision diff locators.
    __revision_diff_section = "//div[@class='revision-diff']"

    def __init__(self, page: Page):
        super().__init__(page)

    # Right-side menu actions.
    def _click_on_kb_dashboard_option(self):
        super()._click(self.__kb_dashboard_option)

    def _click_on_locale_metrics_option(self):
        super()._click(self.__locale_metrics_option)

    def _click_on_kb_team_option(self):
        super()._click(self.__kb_team_option)

    def _get_text_of_selected_menu_option(self) -> str:
        return super()._get_text_of_element(self.__selected_right_side_option)

    def _click_on_aggregated_metrics_option(self):
        super()._click(self.__aggregated_metrics)

    # Recent Revisions table actions.

    def _get_all_revision_dates(self) -> list[str]:
        return super()._get_text_of_elements(self.__all_dates)

    def _get_list_of_all_locale_tage(self) -> list[str]:
        return super()._get_text_of_elements(self.__locale_tag)

    def _get_list_of_all_editors(self) -> list[str]:
        return super()._get_text_of_elements(self.__all_editors)

    def _select_locale_option(self, locale_value: str):
        super()._select_option_by_value(self.__locale_select_field, locale_value)

    def _fill_in_users_field(self, username: str):
        super()._fill(self.__users_input_field, username)
        super()._press_a_key(self.__users_input_field, "Enter")

    def _clearing_the_user_field(self):
        super()._clear_field(self.__users_input_field)

    def _add_start_date(self, start_date: str):
        super()._type(self.__start_date_input_field, start_date, 0)

    def _add_end_date(self, end_date: str):
        super()._type(self.__end_date_input_field, end_date, 0)

    def _get_recent_revision_based_on_article_locator(self, title: str) -> Locator:
        xpath = f"//div[@id='revisions-fragment']//div[@class='title']//a[text()='{title}']"
        return super()._get_element_locator(xpath)

    def _get_recent_revision_based_on_article_title_and_user(self, title: str,
                                                             username: str) -> Locator:
        xpath = (f"//div[@id='revisions-fragment']//div[@class='title']//a[text()='{title}'"
                 f"]/../../div[@class='creator']/a[contains(text(),'{username}')]")
        return super()._get_element_locator(xpath)

    def _click_on_article_title(self, article_title: str, creator: str):
        xpath = (f"//div[@id='revisions-fragment']//div[@class='creator']"
                 f"/a[contains(text(),'{creator}')]/../../div[@class='title']/"
                 f"a[text()='{article_title}']")
        super()._click(xpath)

    def _click_article_creator_link(self, article_title: str, creator: str):
        xpath = (f"//div[@id='revisions-fragment']//div[@class='title']/a[text()='{article_title}'"
                 f"]/../..//div[@class='creator']/a[contains(text(),'{creator}')]")
        super()._click(xpath)

    def _click_on_show_diff_for_article(self, article_title: str, creator: str):
        xpath = (f"//div[@id='revisions-fragment']//div[@class='title']/a[text()='{article_title}'"
                 f"]/../../div[@class='creator']/a[contains(text(),'{creator}')]/../../"
                 f"div[@class='showdiff']/a[@class='show-diff']")
        super()._click(xpath)

    def _get_show_diff_article_locator(self, article_title: str, creator: str) -> Locator:
        xpath = (f"//div[@id='revisions-fragment']//div[@class='title']/a[text()='{article_title}'"
                 f"]/../../div[@class='creator']/a[contains(text(),'{creator}')]/../../"
                 f"div[@class='showdiff']/a[@class='show-diff']")
        return super()._get_element_locator(xpath)

    def _click_on_hide_diff_for_article(self, article_title: str, creator: str):
        xpath = (f"//div[@id='revisions-fragment']//div[@class='title']/a[text()='{article_title}'"
                 f"]/../../div[@class='creator']/a[contains(text(),'{creator}')]/../../"
                 f"div[@class='showdiff']/a[@class='close-diff']")
        super()._click(xpath)

    def _click_on_revision_date_for_article(self, article_title: str, username: str):
        xpath = (f"//div[@class='creator']/a[contains(text(),'{username}')]/../../div["
                 f"@class='title']/a[text()='{article_title}']/../../div[@class='date']/a")
        super()._click(xpath)

    def _get_revision_comment(self, article_title: str, username: str) -> str:
        xpath = (f"//div[@id='revisions-fragment']//div[@class='title']/a[text()='{article_title}'"
                 f"]/../../div[@class='creator']/a[contains(text(),'{username}')]/../../"
                 f"div[@class='comment wider']")
        return super()._get_element_inner_text_from_page(xpath)

    def _get_revision_and_username_locator(self, article_title: str, username: str) -> Locator:
        xpath = (f"//div[@id='revisions-fragment']//div[@class='title']/a[text()='{article_title}'"
                 f"]/../../div[@class='creator']/a[contains(text(),'{username}')]")
        return super()._get_element_locator(xpath)

    # Diff section actions
    def _get_diff_section_locator(self) -> Locator:
        return super()._get_element_locator(self.__revision_diff_section)
