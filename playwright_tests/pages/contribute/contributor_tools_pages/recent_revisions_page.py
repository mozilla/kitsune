import time

from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright_tests.core.basepage import BasePage

# How long without a new revision list request before a filter change counts as applied. wiki.js
# sends the request 200 ms after the last change.
FILTER_QUIET_PERIOD = 0.5


class RecentRevisions(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """Locators related to the right-side menu."""
        self.kb_dashboard_option = page.get_by_role("link", name="KB Dashboard", exact=True)
        self.locale_metrics_option = page.get_by_role("link", name="Locale Metrics", exact=True)
        self.kb_team_option = page.get_by_role("link").filter(has_text="KB Team")
        self.selected_right_side_option = page.locator(
            "li#editing-tools-sidebar li[class='selected'] a")
        self.aggregated_metrics = page.get_by_role("link", name="Aggregated Metrics", exact=True)

        """Locators related to the Recent Revisions table."""
        self.revisions_table = page.locator("//div[@id='revisions-fragment']")
        self.locale_select_field = page.locator("select#id_locale")
        self.locale_tag = page.locator("span[class='locale']")
        self.all_editors = page.locator("div[class='creator'] a")
        self.users_input_field = page.locator("input#id_users")
        self.start_date_input_field = page.locator("input#id_start")
        self.end_date_input_field = page.locator("input#id_end")
        self.all_dates = page.locator("div[class='date'] a time")
        self.recent_revision_based_on_article = lambda article_title: page.locator(
            "div#revisions-fragment div[class='title']").get_by_role(
            "link", name=article_title, exact=True)
        self.recent_revisions_based_on_article_and_user = lambda article_title, user: page.locator(
            f"//div[@id='revisions-fragment']//div[@class='title']//a[text()='{article_title}']/"
            f"../../div[@class='creator']/a[contains(text(),'{user}')]")
        self.article_title = lambda creator, article_title: page.locator(
            f"//div[@id='revisions-fragment']//div[@class='creator']/a[contains(text(),"
            f"'{creator}')]/../../div[@class='title']/a[text()='{article_title}']")
        self.article_creator = lambda article_title, creator: page.locator(
            f"//div[@id='revisions-fragment']//div[@class='title']/a[text()='{article_title}']/../"
            f"..//div[@class='creator']/a[contains(text(),'{creator}')]")
        self.show_diff = lambda article_title, creator: page.locator(
            f"//div[@id='revisions-fragment']//div[@class='title']/a[text()='{article_title}']/../"
            f"../div[@class='creator']/a[contains(text(),'{creator}')]/../../"
            f"div[@class='showdiff']/a[@class='show-diff']")
        self.close_diff = lambda article_title, creator: page.locator(
            f"//div[@id='revisions-fragment']//div[@class='title']/a[text()='{article_title}']/../"
            f"../div[@class='creator']/a[contains(text(),'{creator}')]/../../"
            f"div[@class='showdiff']/a[@class='close-diff']")
        self.revision_date = lambda article_title, username: page.locator(
            f"//div[@class='creator']/a[contains(text(),'{username}')]/../../div[@class='title']/"
            f"a[text()='{article_title}']/../../div[@class='date']/a")
        self.revision_comment = lambda article_title, username: page.locator(
            f"//div[@id='revisions-fragment']//div[@class='title']/a[text()='{article_title}']/../"
            f"../div[@class='creator']/a[contains(text(),'{username}')]/../../"
            f"div[@class='comment wider']")

        """Locators related to the revision diff section."""
        self.revision_diff_section = page.locator("div[class='revision-diff']")

    """Actions against the right-side menu locators."""
    def click_on_kb_dashboard_option(self):
        self._click(self.kb_dashboard_option)

    def click_on_locale_metrics_option(self):
        self._click(self.locale_metrics_option)

    def click_on_kb_team_option(self):
        self._click(self.kb_team_option)

    def click_on_aggregated_metrics_option(self):
        self._click(self.aggregated_metrics)

    """Actions against the recent revisions table locators."""
    def get_all_revision_dates(self) -> list[str]:
        return self._get_text_of_elements(self.all_dates)

    def get_list_of_all_locale_tags(self) -> list[str]:
        return self._get_text_of_elements(self.locale_tag)

    def get_list_of_all_editors(self) -> list[str]:
        return self._get_text_of_elements(self.all_editors)

    def _apply_filter(self, action):
        """Runs a filter change and waits until the revision list shows its result.

        wiki.js sends one request per change, does not cancel the earlier ones and hides the
        loading icon as soon as any of them returns, so the icon cannot tell when the list
        reflects the last change. Every revision list request the change starts is waited for
        instead, until none is left and no new one follows.
        """
        pending, seen = [], []

        def on_request(request):
            if "fragment=1" in request.url:
                pending.append(request)
                seen.append(request)

        def on_done(request):
            if request in pending:
                pending.remove(request)

        self.page.on("request", on_request)
        self.page.on("requestfinished", on_done)
        self.page.on("requestfailed", on_done)
        try:
            action()
            deadline = time.monotonic() + 15
            settled_since = time.monotonic()
            while time.monotonic() < deadline:
                if pending:
                    settled_since = time.monotonic()
                elif seen and time.monotonic() - settled_since >= FILTER_QUIET_PERIOD:
                    return
                self.page.wait_for_timeout(100)
            raise PlaywrightTimeoutError(
                "The revision list did not update after the filter change")
        finally:
            self.page.remove_listener("request", on_request)
            self.page.remove_listener("requestfinished", on_done)
            self.page.remove_listener("requestfailed", on_done)

    def select_locale_option(self, locale_value: str):
        self._apply_filter(
            lambda: self._select_option_by_value(self.locale_select_field, locale_value))

    def fill_in_users_field(self, username: str):
        def fill():
            self._fill(self.users_input_field, username)
            self._press_a_key(self.users_input_field, "Enter")
        self._apply_filter(fill)

    def clearing_the_user_field(self):
        self._apply_filter(lambda: self._clear_field(self.users_input_field))

    def add_start_date(self, start_date: str):
        self._apply_filter(lambda: self._type(self.start_date_input_field, start_date, 0))

    def add_end_date(self, end_date: str):
        self._apply_filter(lambda: self._type(self.end_date_input_field, end_date, 0))

    def click_on_article_title(self, article_title: str, creator: str):
        self._click(self.article_title(creator, article_title))

    def click_article_creator_link(self, article_title: str, creator: str):
        self._click(self.article_creator(article_title, creator))

    def click_on_show_diff_for_article(self, article_title: str, creator: str):
        self._click(self.show_diff(article_title, creator))

    def click_on_hide_diff_for_article(self, article_title: str, creator: str):
        self._click(self.close_diff(article_title, creator))

    def click_on_revision_date_for_article(self, article_title: str, username: str):
        self._click(self.revision_date(article_title, username))
