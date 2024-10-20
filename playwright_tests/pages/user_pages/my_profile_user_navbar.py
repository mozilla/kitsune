from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class UserNavbar(BasePage):
    # My profile navbar locators.
    MY_PROFILE_NAVBAR_LOCATORS = {
        "my_profile_option": "//ul[@id='user-nav']//a[contains(text(), 'My profile')]",
        "edit_my_profile_option": "//ul[@id='user-nav']//a[contains(text(),'Edit my profile')]",
        "edit_my_profile_settings_option": "//ul[@id='user-nav']//a[contains(text(),'Edit "
                                           "settings')]",
        "edit_my_profile_contribution_areas_option": "//ul[@id='user-nav']//a[contains(text(),'"
                                                     "Edit contribution areas')]",
        "edit_my_profile_manage_watch_list_option": "//ul[@id='user-nav']//a[contains(text(),"
                                                    "'Manage watch list')]",
        "edit_my_profile_my_questions_option": "//ul[@id='user-nav']//a[contains(text(),'My "
                                               "questions')]"
    }

    def __init__(self, page: Page):
        super().__init__(page)

    # My profile navbar actions.
    def click_on_my_profile_option(self):
        """Click on my profile option in the navbar."""
        self._click(self.MY_PROFILE_NAVBAR_LOCATORS["my_profile_option"])

    def click_on_edit_my_profile_option(self):
        """Click on the edit my profile option in the navbar."""
        self._click(self.MY_PROFILE_NAVBAR_LOCATORS["edit_my_profile_option"])

    def click_on_edit_contribution_areas_option(self):
        """Click on the edit contribution areas option in the navbar."""
        self._click(self.MY_PROFILE_NAVBAR_LOCATORS["edit_my_profile_contribution_areas_option"])

    def click_on_my_questions_option(self):
        """Click on the my questions option in the navbar."""
        self._click(self.MY_PROFILE_NAVBAR_LOCATORS["edit_my_profile_my_questions_option"])
