from playwright_tests.core.utilities import Utilities
from playwright_tests.pages.contribute.groups_page import GroupsPage
from playwright.sync_api import Page


class UserGroupFlow:
    def __init__(self, page: Page):
        self.utilities = Utilities(page)
        self.groups_page = GroupsPage(page)

    def remove_a_user_from_group(self, user: str):
        self.groups_page.click_on_edit_group_members()
        self.groups_page.click_on_remove_a_user_from_group_button(user)
        self.groups_page.click_on_remove_member_confirmation_button()

    def add_a_user_to_group(self, user: str):
        self.groups_page.click_on_edit_group_members()
        self.groups_page.type_into_add_member_field(user)
        self.groups_page.group_click_on_a_searched_username(user)
        self.groups_page.click_on_add_member_button()
