from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class UserNavbar(BasePage):

    # My profile navbar locators.
    __my_profile_option = "//ul[@id='user-nav']//a[contains(text(), 'My profile')]"
    __edit_my_profile_option = "//ul[@id='user-nav']//a[contains(text(),'Edit my profile')]"
    __edit_my_profile_settings_option = "//ul[@id='user-nav']//a[contains(text(),'Edit settings')]"
    __edit_my_profile_contribution_areas_option = ("//ul[@id='user-nav']//a[contains(text(),'Edit "
                                                   "contribution areas')]")
    __edit_my_profile_manage_watch_list_option = ("//ul[@id='user-nav']//a[contains(text(),"
                                                  "'Manage watch list')]")
    __edit_my_profile_my_questions_option = ("//ul[@id='user-nav']//a[contains(text(),"
                                             "'My questions')]")

    def __init__(self, page: Page):
        super().__init__(page)

    # My profile navbar actions.
    def _click_on_my_profile_option(self):
        super()._click(self.__my_profile_option)

    def _click_on_edit_my_profile_option(self):
        super()._click(self.__edit_my_profile_option)

    def _click_on_edit_contribution_areas_option(self):
        super()._click(self.__edit_my_profile_contribution_areas_option)

    def _click_on_my_questions_option(self):
        super()._click(self.__edit_my_profile_my_questions_option)
