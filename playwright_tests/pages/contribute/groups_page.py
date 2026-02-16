from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class GroupsPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """General locators belonging to the groups page."""
        self.add_group_profile_button = page.get_by_role(
            "link", name="Add group profile", exact=True)
        self.edit_in_admin_button = page.locator(
            "//div[@class='group-header--actions']/a[normalize-space(text())='Edit in admin']")
        self.edit_group_profile_button = page.locator(
            "//div[@class='group-header--actions']/a[normalize-space(text())='Edit Profile']")
        self.group_profile_information = page.locator("//div[@class='group-info-content']/p")
        self.private_message_group_members_button = page.locator("section#main-area > p.pm a")
        self.user_notification = page.locator("ul.user-messages p")
        self.group_leader_list = page.locator("div#group-leaders div.info a")
        self.group_members_list = page.locator("div#group-members div.info a")
        self.group_by_name = lambda group_name: page.get_by_role(
            "link", name=group_name, exact=True)
        self.pm_a_group_user = lambda username: page.locator("div.info").get_by_role(
            "link", name=username, exact=True).locator("+ p a")
        self.search_username = lambda username: page.locator(
            f"//div[@class='name_search']/b[text()='{username}']")
        self.listed_group_member = lambda username: page.locator(
            f"//div[@id='group-members']//a[text()='{username}']")
        self.listed_group_leader = lambda username: page.locator(
            f"//div[@id='group-leaders']//a[text()='{username}']")
        self.group_avatar = page.locator("//img[@class='group-avatar']")

        """Locators belonging to the 'Edit Profile' page."""
        self.edit_group_profile_page_header = page.locator("//article[@id='group-profile']/h1")
        self.edit_group_profile_textarea = page.locator("//textarea[@id='id_information']")
        self.save_group_profile_edit_button = page.locator("//input[@type='submit']")

        """Locators belonging to the Avatar section."""
        self.change_avatar_button = page.locator("//a[normalize-space(text())='Change Avatar']")
        self.delete_uploaded_group_image_option = page.locator(
            "//a[normalize-space(text())='Delete Avatar']")

        """Locators belonging to the 'Manage group' section."""
        self.manage_group_section = page.locator(
            "//h3[@class='card--title' and text()='Manage Group']/..")
        self.add_users_button = page.locator(
            "//h3[@class='card--title']/..//label[@class='action-button']")
        self.username_field = page.locator("//input[@id='token-input-id_users']")
        self.add_to_members_button = page.locator("//button[@value='member']")
        self.add_to_leaders_button = page.locator("//button[@value='leader']")

        """Locators belonging to the change avatar page."""
        self.upload_avatar_page_header = page.locator("article#change-avatar h1")
        self.upload_avatar_image_preview = page.locator("//img[@id='avatar-preview']")
        self.upload_avatar_browse_button = page.locator("//label[@for='id_avatar']")
        self.upload_avatar_button = page.locator(
            "//div[@class='avatar-edit-content']//button[@type='submit']")
        self.upload_avatar_cancel_option = page.get_by_role("link", name="Cancel", exact=True)
        self.preview_overlay = page.locator("//div[@id='avatar-overlay']")

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
            f"//div[@class='info']/a[text()='{username}']/../../..//"
            f"a[@title='Remove user from leaders']")
        self.remove_user = lambda username: page.locator(
            f"//div[@class='info']/a[text()='{username}']/../../..//a["
            f"@title='Remove user from group']")

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

    def is_edit_group_profile_button_visible(self) -> bool:
        """Check if the edit group profile button is visible"""
        return self._is_element_visible(self.edit_group_profile_button)

    def click_on_edit_group_profile_button(self):
        """Click on the edit group profile button"""
        self._click(self.edit_group_profile_button)

    def get_profile_information(self) -> str:
        """Get the profile information"""
        return self._get_text_of_element(self.group_profile_information)

    def is_manage_group_section_visible(self) -> bool:
        """Check if the manage group section is visible"""
        return self._is_element_visible(self.manage_group_section)

    def click_on_add_users_button(self):
        """Click on the 'Add Users' button from the 'Manage Group' section."""
        self._click(self.add_users_button)

    def type_into_add_user_to_group_field(self, text: str):
        """Type into the add users input field.
        Args:
            text (str): The text to type into the add users input field.
        """
        self._type(self.username_field, text, delay=0)

    def click_on_add_group_leader_button(self):
        self._click(self.add_to_leaders_button)

    def click_on_pm_group_members_button(self):
        """Click on the PM group members button"""
        self._click(self.private_message_group_members_button)

    def click_on_pm_for_a_particular_user(self, username: str):
        """Click on the PM button for a particular user

        Args:
            username (str): The username of the user to click on the PM button for
        """
        self._click(self.pm_a_group_user(username))

    """Actions against the 'Edit group profile page'"""
    def get_edit_group_profile_page_header(self) -> str:
        """Get the text of the edit group profile page header"""
        return self._get_text_of_element(self.edit_group_profile_page_header)

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

    def click_on_edit_group_profile_save_button(self):
        """Click on the save group profile edit button"""
        self._click(self.save_group_profile_edit_button)

    """Actions against the add group member locators."""
    def get_group_update_notification(self) -> str:
        """Get the text of the user added successfully message"""
        return self._get_text_of_element(self.user_notification)

    def click_on_change_uploaded_avatar_button(self):
        """Click on the change uploaded avatar button"""
        self._click(self.change_avatar_button, expected_locator=self.upload_avatar_page_header)

    def click_on_delete_uploaded_avatar_button(self):
        """Click on the delete uploaded avatar button"""
        self._click(self.delete_uploaded_group_image_option)

    def click_on_change_avatar_button(self):
        """Click on the change avatar button"""
        self._click(self.change_avatar_button, expected_locator=self.upload_avatar_page_header)

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
            self._hover_over_element(self.listed_group_leader(username))
            self._click(self.remove_leader(username))
        else:
            self._hover_over_element(self.listed_group_member(username))
            self._click(self.remove_user(username))

    def group_click_on_a_searched_username(self, username: str):
        """Click on a searched username

        Args:
            username (str): The username to click on
        """
        self._click(self.search_username(username))

    def click_on_add_member_button(self):
        """Click on the add member button"""
        self._click(self.add_to_members_button)

    def click_on_a_listed_group_member(self, username: str):
        """Click on a listed group member.

        Args:
            username (str): The username of the user to click on
        """
        self._click(self.listed_group_member(username))

    def click_on_a_listed_group_leader(self, username: str):
        """Click on a listed group leader.

        Args:
            username (str): The username of the leader to click on
        """
        self._click(self.listed_group_leader(username))

    """Actions against the 'Remove group members/leaders' page."""
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
