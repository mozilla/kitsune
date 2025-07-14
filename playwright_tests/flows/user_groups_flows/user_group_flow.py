from playwright.sync_api import Page

from playwright_tests.core.utilities import Utilities
from playwright_tests.pages.contribute.groups_page import GroupsPage


class UserGroupFlow:
    def __init__(self, page: Page):
        self.utilities = Utilities(page)
        self.groups_page = GroupsPage(page)

    def remove_a_user_from_group(self, user: str, is_leader=False):
        """
        Remove a user from a group.

        Args:
            user (str): The username to be removed from the group.
            is_leader (bool, optional): If True, the user is a leader. Defaults
        """
        self.groups_page.click_on_edit_group_leaders_option(
        ) if is_leader else self.groups_page.click_on_edit_group_members()

        self.groups_page.click_on_remove_a_user_from_group_button(
            user,True) if is_leader else (self.groups_page.
                                          click_on_remove_a_user_from_group_button(user))

        self.groups_page.click_on_remove_leader_button(
        ) if is_leader else self.groups_page.click_on_remove_member_button()

    def add_a_user_to_group(self, user: str, is_leader=False):
        """
        Add a user to a group.

        Args:
            user (str): The username of the user to add to the group.
            is_leader (bool, optional): If True, the user will be added as a leader. Defaults to
            False.
        """

        self.groups_page.click_on_edit_group_leaders_option(
        ) if is_leader else self.groups_page.click_on_edit_group_members()
        self.groups_page.type_into_add_leader_field(
            user) if is_leader else self.groups_page.type_into_add_member_field(user)
        self.groups_page.group_click_on_a_searched_username(user)
        self.groups_page.click_on_add_group_leader_button(
        ) if is_leader else self.groups_page.click_on_add_member_button()
