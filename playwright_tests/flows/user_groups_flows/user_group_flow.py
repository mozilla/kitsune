from playwright_tests.core.testutilities import TestUtilities
from playwright_tests.pages.contribute.groups_page import GroupsPage
from playwright.sync_api import Page


class UserGroupFlow(TestUtilities, GroupsPage):
    def __init__(self, page: Page):
        super().__init__(page)

    def remove_a_user_from_group(self, user: str):
        super()._click_on_edit_group_members()
        super()._click_on_remove_a_user_from_group_button(user)
        super()._click_on_remove_member_confirmation_button()

    def add_a_user_to_group(self, user: str):
        super()._click_on_edit_group_members()
        super()._type_into_add_member_field(user)
        super()._group_click_on_a_searched_username(user)
        super()._click_on_add_member_button()
