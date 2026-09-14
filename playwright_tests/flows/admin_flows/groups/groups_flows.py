from playwright.sync_api import Page

from playwright_tests.core.utilities import Utilities
from playwright_tests.pages.admin_pages.groups.admin_groups_page import AdminGroupsPage


class AdminGroupsFlows:
    def __init__(self, page: Page):
        self.utilities = Utilities(page)
        self.groups_page = AdminGroupsPage(page)

    def create_group(self, group_name: str) -> str:
        """Flow for creating a new user group via the groups admin page.

        Args:
            group_name (str): The name of the group to create.
        """
        self.utilities.navigate_to_link(
            self.utilities.different_endpoints["admin_groups_page"] + "add/")
        self.groups_page.add_text_to_name_field(group_name)
        self.groups_page.click_on_save_button()
        return group_name

    def delete_group(self, group_name: str, ignore_missing: bool = False):
        """Flow for deleting an existing user group via the groups admin page.

        Args:
            group_name (str): The name of the group to delete.
            ignore_missing (bool): If True, a group which is no longer listed is skipped
                instead of failing. Used by test teardown, which cannot know whether the
                test itself already deleted the group.
        """
        self.utilities.navigate_to_link(self.utilities.different_endpoints["admin_groups_page"])
        self.groups_page.search_for_group(group_name)

        if ignore_missing and not self.groups_page.is_group_listed(group_name):
            return

        self.groups_page.click_on_a_group(group_name)
        self.groups_page.click_on_delete_button()
        self.groups_page.click_on_confirm_deletion_button()

    def is_group_listed(self, group_name: str) -> bool:
        """Search the groups admin page for a group and report whether it still exists.

        Args:
            group_name (str): The name of the group to search for.
        """
        self.utilities.navigate_to_link(self.utilities.different_endpoints["admin_groups_page"])
        self.groups_page.search_for_group(group_name)
        return self.groups_page.is_group_listed(group_name)
