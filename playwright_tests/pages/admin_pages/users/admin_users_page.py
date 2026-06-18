from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class AdminUserPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """Locators belonging to the users listing page"""
        self.users_page = page.locator("//th[@id='auth-user']/a")
        self.searchbar = page.locator("//input[@id='searchbar']")
        self.search_submit_button = page.locator("//input[@type='submit']")
        self.user = lambda username: page.locator(
            f"//th[@class='field-username']/a[text()='{username}']")
        self.active_checkbox = page.locator("//input[@id='id_is_active']")
        self.superuser_checkbox = page.locator("//input[@id='id_is_superuser']")
        self.save_button = page.locator("//input[@value='Save']")
        self.save_and_continue_editing_button = page.locator(
            "//input[@value='Save and continue editing']")

    def click_on_users_page_option(self):
        self._click(self.users_page)

    def search_for_username(self, username: str):
        """Search for a particular username inside the user admin page.
        Args:
            username (str): The username.
        """
        self._fill(self.searchbar, username)
        self._click(self.search_submit_button)

    def click_on_a_user(self, username: str):
        """Click on a username from the User admin page table.
        Args:
            username (str): The username
        """
        self._click(self.user(username))

    def click_on_save_changes_button(self):
        self._click(self.save_button)

    def click_on_save_and_continue_editing_button(self):
        self._click(self.save_and_continue_editing_button)
