from playwright.sync_api import Page
from playwright_tests.core.utilities import Utilities
from playwright_tests.pages.admin_pages.users.admin_users_page import AdminUserPage


class AdminUsersFlows:
    def __init__(self, page: Page):
        self.utilities = Utilities(page)
        self.users_page = AdminUserPage(page)

    def navigate_to_a_particular_user_profile_in_admin(self, username: str):
        """Flow for navigating and accessing a user profile in admin."""
        self.utilities.navigate_to_link(self.utilities.different_endpoints["admin_users_page"])
        self.users_page.search_for_username(username)
        self.users_page.click_on_a_user(username)
