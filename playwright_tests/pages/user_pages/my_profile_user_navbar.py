from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class UserNavbar(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """Locators belonging to the profile navbar section."""
        self.my_profile_option = page.locator("ul#user-nav").get_by_role(
            "link", name="My profile", exact=True)
        self.edit_my_profile_option = page.locator("ul#user-nav").get_by_role(
            "link", name="Edit my profile", exact=True)
        self.edit_my_profile_settings_option = page.locator("ul#user-nav").get_by_role(
            "link", name="Edit settings", exact=True)
        self.edit_my_profile_contribution_areas_option = page.locator("ul#user-nav").get_by_role(
            "link", name="Edit contribution areas", exact=True)
        self.edit_my_profile_manage_watch_list_option = page.locator("ul#user-nav").get_by_role(
            "link", name="Manage watch list", exact=True)
        self.edit_my_profile_my_questions_option = page.locator("ul#user-nav").get_by_role(
            "link", name="My questions", exact=True)

    """Actions against the My Profile navbar section."""
    def click_on_my_profile_option(self):
        """Click on my profile option in the navbar."""
        self._click(self.my_profile_option)

    def click_on_edit_my_profile_option(self):
        """Click on the edit my profile option in the navbar."""
        self._click(self.edit_my_profile_option)

    def click_on_edit_contribution_areas_option(self):
        """Click on the edit contribution areas option in the navbar."""
        self._click(self.edit_my_profile_contribution_areas_option)

    def click_on_my_questions_option(self):
        """Click on the my questions option in the navbar."""
        self._click(self.edit_my_profile_my_questions_option)
