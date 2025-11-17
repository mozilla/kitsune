from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class GroupsPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """General locators belonging to the groups page."""
        self.add_group_profile_button = page.get_by_role(
            "link", name="Add group profile", exact=True)
        self.group_avatar_image = page.locator("section#avatar-area img")
        self.change_uploaded_group_image_option = page.locator(
            "section#avatar-area p").get_by_role("link", name="Change", exact=True)
        self.delete_uploaded_group_image_option = page.locator(
            "section#avatar-area p a[title='Delete avatar']")
        self.change_avatar_button = page.locator("section#avatar-area p a[title='Change avatar']")
        self.edit_in_admin_button = page.locator("section#main-area").get_by_role(
            "link", name="Edit in admin", exact=True)
        self.group_profile_information = page.locator("div#doc-content p")
        self.edit_group_profile_page_header = page.locator("article#group-profile h1")
        self.edit_group_profile_button = page.locator("section#main-area").get_by_role(
            "link", name="Edit group profile", exact=True)
        self.edit_group_profile_textarea = page.locator("textarea#id_information")
        self.save_group_profile_edit_button = page.locator(
            "article#group-profile input[value='Save']")
        self.edit_group_leaders_button = page.locator("div#group-leaders").get_by_role(
            "link", name="Edit group leaders", exact=True)
        self.add_group_leader_field = page.locator("div#group-leaders input#token-input-id_users")
        self.add_group_leader_button = page.locator("input[value='Add Leader']")
        self.private_message_group_members_button = page.locator("section#main-area > p.pm a")
        self.user_notification = page.locator("ul.user-messages p")
        self.edit_group_members_option = page.locator("div#group-members").get_by_role(
            "link", name="Edit group members", exact=True)
        self.add_group_member_field = page.locator("div#group-members input#token-input-id_users")
        self.add_member_button = page.locator("div#group-members input[value='Add Member']")
        self.group_leader_list = page.locator("div#group-leaders div.info a")
        self.group_members_list = page.locator("div#group-members div.info a")
        self.group_by_name = lambda group_name: page.get_by_role(
            "link", name=group_name, exact=True)
        self.pm_a_group_user = lambda username: page.locator("div.info").get_by_role(
            "link", name=username, exact=True).locator("+ p a")
        self.search_username = lambda username: page.locator(
            f"//div[@class='name_search']/b[text()='{username}']")
        self.listed_group_user = lambda username: page.locator("div.info").get_by_role(
            "link", name=username, exact=True)
        self.listed_group_leader = lambda username: page.locator(
            "div#group-leaders").get_by_role("link", name=username, exact=True)

        """Locators belonging to the change avatar page."""
        self.upload_avatar_page_header = page.locator("article#change-avatar h1")
        self.upload_avatar_image_preview = page.locator(
            "//input[@id='id_avatar']/preceding-sibling::img")
        self.upload_avatar_browse_button = page.locator("input#id_avatar")
        self.upload_avatar_button = page.locator("input[type='submit']")
        self.upload_avatar_cancel_option = page.get_by_role("link", name="Cancel", exact=True)

        """Locators belonging to the delete avatar page."""
        self.delete_uploaded_avatar_page_header = page.locator("article#avatar-delete h1")
        self.delete_uploaded_avatar_image_preview = page.locator("div#avatar-preview img")
        self.delete_uploaded_avatar_page_info = page.locator("form p")
        self.delete_uploaded_avatar_button = page.locator("input[value='Delete avatar']")
        self.delete_uploaded_avatar_cancel_button = page.get_by_role(
            "link", name="Cancel", exact=True)

        """Locators belonging to the remove user page."""
        self.remove_leader_page_header = page.locator("article#remove-leader h1")
        self.remove_user_page_header = page.locator("article#remove-member h1")
        self.remove_leader_button = page.locator("input[value='Remove leader']")
        self.remove_member_button = page.locator("input[value='Remove member']")
        self.remove_member_cancel_button = page.locator("div.form-actions").get_by_role(
            "link", name="Cancel", exact=True)
        self.remove_leader = lambda username: page.locator(
            f"//div[@class='info']/a[text()='{username}']/../..//a[@title='Remove user from "
            f"leaders']")
        self.remove_user = lambda username: page.locator(
            f"//div[@class='info']/a[text()='{username}']/../..//a[@title='Remove user from "
            f"group']"
        )

    """Actions against the all groups listing page locators."""
    def is_add_group_profile_button_visible(self) -> bool:
        """Check if the add group profile button is visible"""
        return self._is_element_visible(self.add_group_profile_button)

    def click_on_a_particular_group(self, group_name):
        """Click on a particular group

        Args:
            group_name (str): The name of the group to click on
        """
        self._click(self.group_by_name(group_name))

    """Actions against a specific group page locators."""
    def get_all_leaders_name(self) -> list[str]:
        """Get the names of all the leaders in the group"""
        return self._get_text_of_elements(self.group_leader_list)

    def get_all_members_name(self) -> list[str]:
        """Get the names of all the members in the group"""
        return self._get_text_of_elements(self.group_members_list)

    def is_change_avatar_button_visible(self) -> bool:
        """Check if the change avatar button is visible"""
        return self._is_element_visible(self.change_avatar_button)

    def is_edit_in_admin_button_visible(self) -> bool:
        """Check if the edit in admin button is visible"""
        return self._is_element_visible(self.edit_in_admin_button)

    def get_edit_group_profile_page_header(self) -> str:
        """Get the text of the edit group profile page header"""
        return self._get_text_of_element(self.edit_group_profile_page_header)

    def is_edit_group_profile_button_visible(self) -> bool:
        """Check if the edit group profile button is visible"""
        return self._is_element_visible(self.edit_group_profile_button)

    def click_on_edit_group_profile_button(self):
        """Click on the edit group profile button"""
        self._click(self.edit_group_profile_button)

    def get_edit_group_profile_textarea_content(self) -> str:
        """Get the content of the edit group profile textarea"""
        return self._get_element_input_value(self.edit_group_profile_textarea)

    def type_into_edit_group_profile_textarea(self, text: str):
        """Type into the edit group profile textarea

        Args:
            text (str): The text to type into the edit group profile textarea
        """
        self._clear_field(self.edit_group_profile_textarea)
        self._fill(self.edit_group_profile_textarea, text)

    def get_profile_information(self) -> str:
        """Get the profile information"""
        return self._get_text_of_element(self.group_profile_information)

    def click_on_edit_group_profile_save_button(self):
        """Click on the save group profile edit button"""
        self._click(self.save_group_profile_edit_button)

    def is_edit_group_leaders_button_visible(self) -> bool:
        """Check if the edit group leaders button is visible"""
        return self._is_element_visible(self.edit_group_leaders_button)

    def is_edit_group_members_option_visible(self) -> bool:
        """Check if the edit group members option is visible"""
        return self._is_element_visible(self.edit_group_members_option)

    def click_on_edit_group_leaders_option(self):
        self._click(self.edit_group_leaders_button)

    def type_into_add_leader_field(self, text: str):
        """Type into the add leader field

        Args:
            text (str): The text to type into the add leader field
        """
        self._type(self.add_group_leader_field, text, delay=0)

    def click_on_add_group_leader_button(self):
        self._click(self.add_group_leader_button)

    def click_on_pm_group_members_button(self):
        """Click on the PM group members button"""
        self._click(self.private_message_group_members_button)

    def click_on_pm_for_a_particular_user(self, username: str):
        """Click on the PM button for a particular user

        Args:
            username (str): The username of the user to click on the PM button for
        """
        self._click(self.pm_a_group_user(username))

    """Actions against the add group member locators."""
    def get_group_update_notification(self) -> str:
        """Get the text of the user added successfully message"""
        return self._get_text_of_element(self.user_notification)

    def click_on_change_uploaded_avatar_button(self):
        """Click on the change uploaded avatar button"""
        self._click(self.change_uploaded_group_image_option,
                    expected_locator=self.upload_avatar_page_header)

    def click_on_delete_uploaded_avatar_button(self):
        """Click on the delete uploaded avatar button"""
        self._click(self.delete_uploaded_group_image_option)

    def click_on_change_avatar_button(self):
        """Click on the change avatar button"""
        self._click(self.change_avatar_button, expected_locator=self.upload_avatar_page_header)

    def click_on_edit_group_members(self):
        """Click on the edit group members option"""
        self._click(self.edit_group_members_option)

    """Actions against the change avatar page locators."""
    def get_upload_avatar_page_header(self) -> str:
        """Get the text of the upload avatar page header"""
        return self._get_text_of_element(self.upload_avatar_page_header)

    def click_on_upload_avatar_button(self, expected_url=None):
        """Click on the upload avatar button"""
        self._click(self.upload_avatar_button, expected_url=expected_url)

    def click_on_upload_avatar_cancel_button(self):
        """Click on the upload avatar cancel button"""
        self._click(self.upload_avatar_cancel_option)

    """Actions against the delete avatar page locators."""
    def click_on_cancel_delete_avatar_button(self):
        """Click on the cancel delete avatar button"""
        self._click(self.delete_uploaded_avatar_cancel_button)

    def get_delete_avatar_page_header(self) -> str:
        """Get the text of the delete avatar page header"""
        return self._get_text_of_element(self.delete_uploaded_avatar_page_header)

    def is_image_preview_visible(self) -> bool:
        """Check if the image preview is visible"""
        return self._is_element_visible(self.delete_uploaded_avatar_image_preview)

    def get_delete_avatar_page_info(self) -> str:
        """Get the text of the delete avatar page info"""
        return self._get_text_of_element(self.delete_uploaded_avatar_page_info)

    def click_on_delete_avatar_button(self):
        """Click on the delete avatar button"""
        self._click(self.delete_uploaded_avatar_button)

    """Actions against the removal or user addition related locators."""
    def click_on_remove_a_user_from_group_button(self, username: str, from_leaders=False):
        """Click on the remove a user from group button

        Args:
            username (str): The username of the user to remove from the group
            from_leaders (bool, optional): If True, the user will be removed from the leaders.
        """
        if from_leaders:
            self._click(self.remove_leader(username))
        else:
            self._click(self.remove_user(username))

    def type_into_add_member_field(self, text: str):
        """Type into the add member field

        Args:
            text (str): The text to type into the add member field
        """
        self._type(self.add_group_member_field, text, delay=0)

    def group_click_on_a_searched_username(self, username: str):
        """Click on a searched username

        Args:
            username (str): The username to click on
        """
        self._click(self.search_username(username))

    def click_on_add_member_button(self):
        """Click on the add member button"""
        self._click(self.add_member_button)

    def click_on_a_listed_group_user(self, username: str):
        """Click on a listed group user.

        Args:
            username (str): The username of the user to click on
        """
        self._click(self.listed_group_user(username))

    def click_on_a_listed_group_leader(self, username: str):
        """Click on a listed group leader.

        Args:
            username (str): The username of the leader to click on
        """
        self._click(self.listed_group_leader(username))

    def get_remove_leader_page_header(self) -> str:
        return self._get_text_of_element(self.remove_leader_page_header)

    def get_remove_user_page_header(self) -> str:
        """Get the text of the remove user page header"""
        return self._get_text_of_element(self.remove_user_page_header)

    def click_on_remove_leader_button(self):
        self._click(self.remove_leader_button)

    def click_on_remove_member_button(self):
        """Click on the remove member button"""
        self._click(self.remove_member_button)

    def click_on_remove_member_cancel_button(self):
        """Click on the remove member cancel button"""
        self._click(self.remove_member_cancel_button)
