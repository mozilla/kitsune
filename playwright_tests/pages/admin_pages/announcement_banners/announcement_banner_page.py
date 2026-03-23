from playwright.sync_api import Page

from playwright_tests.core.basepage import BasePage


class AnnouncementBannerAdminPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """Locators Belonging to the announcements admin page."""
        self.add_announcement_button = page.locator(
            "//a[normalize-space(text())='Add announcement']")

        """Locators belonging to the add announcements admin page form."""
        self.start_displaying_date = page.locator("//input[@id='id_show_after_0']")
        self.start_displaying_time = page.locator("//input[@id='id_show_after_1']")
        self.stop_displaying_date = page.locator("//input[@id='id_show_until_0']")
        self.stop_displaying_time = page.locator("//input[@id='id_show_until_1']")
        self.banner_content_textarea = page.locator("//textarea[@id='id_content']")
        self.banner_groups = page.locator("//select[@id='id_groups']")
        self.banner_locale = page.locator("//select[@id='id_locale']")
        self.banner_platforms = page.locator("//select[@id='id_platforms']")
        self.banner_product = page.locator("//select[@id='id_product']")
        self.banner_save_button = page.locator("//input[@name='_continue']")
        self.delete_banner_button = page.locator("//a[@class='deletelink']")
        self.delete_banner_confirm_button = page.locator("//input[@type='submit']")

    """Actions against the announcement banners admin page."""
    def click_on_add_announcement_button(self):
        self._click(self.add_announcement_button)

    """Actions against the announcement banners admin page form."""
    def set_start_displaying_date(self, start_date: str):
        self._fill(self.start_displaying_date, start_date)

    def set_start_displaying_time(self, start_time: str):
        self._fill(self.start_displaying_time, start_time)

    def set_stop_displaying_date(self, stop_date: str):
        self._fill(self.stop_displaying_date, stop_date)

    def set_stop_displaying_time(self, stop_time: str):
        self._fill(self.stop_displaying_time, stop_time)

    def set_banner_content(self, content: str):
        self._fill(self.banner_content_textarea, content)

    def set_banner_target_groups(self, groups: [str]):
        for group in groups:
            self._select_option_by_label(self.banner_groups, group)

    def set_banner_target_locale(self, locale: str):
        self._select_option_by_label(self.banner_locale, locale)

    def set_banner_target_platforms(self, platforms: [str]):
        for platform in platforms:
            self._select_option_by_label(self.banner_platforms, platform)

    def set_banner_target_product(self, product: str):
        self._select_option_by_label(self.banner_product, product)

    def click_on_save_new_banner_button(self):
        self._click(self.banner_save_button)

    def click_on_delete_new_banner_button(self):
        self._click(self.delete_banner_button)

    def click_on_delete_confirm_button(self):
        self._click(self.delete_banner_confirm_button)
