from playwright_tests.core.basepage import BasePage
from playwright.sync_api import Page, Locator


class GroupsPage(BasePage):
    GENERAL_GROUPS_PAGE_LOCATORS = {
        "add_group_profile_button": "//a[normalize-space(text())= 'Add group profile']"
    }

    GROUP_PAGE_LOCATORS = {
        "group_avatar_image": "//section[@id='avatar-area']/img",
        "change_uploaded_group_image_option": "//section[@id='avatar-area']/p/a[normalize-space("
                                              "text())='Change']",
        "delete_uploaded_group_image_option": "//section[@id='avatar-area']/p/a["
                                              "@title='Delete avatar']",
        "change_avatar_button": "//section[@id='avatar-area']//p/a[@title='Change avatar']",
        "edit_in_admin_button": "//section[@id='main-area']/a[text()='Edit in admin']",
        "group_profile_information": "//div[@id='doc-content']/p",
        "edit_group_profile_page_header": "//article[@id='group-profile']/h1",
        "edit_group_profile_button": "//section[@id='main-area']/a[text()='Edit group profile']",
        "edit_group_profile_textarea": "//textarea[@id='id_information']",
        "save_group_profile_edit_button": "//article[@id='group-profile']//input[@value='Save']",
        "edit_group_leaders_button": "//div[@id='group-leaders']/a[text()='Edit group leaders']",
        "private_message_group_members_button": "//section[@id='main-area']/p[@class='pm']/a",
        "user_notification": "//ul[@class='user-messages']//p",
        "edit_group_members_option": "//div[@id='group-members']/a",
        "add_group_member_field": "//div[@id='group-members']//input[@id='token-input-id_users']",
        "add_member_button": "//div[@id='group-members']//input[@value='Add Member']",
        "remove_user_from_group_confirmation_button": "//input[@value='Remove member']",
        "group_members_list": "//div[@id='group-members']//div[@class='info']/a"
    }

    CHANGE_AVATAR_PAGE_LOCATORS = {
        "upload_avatar_page_header": "//article[@id='change-avatar']/h1",
        "upload_avatar_image_preview": "//input[@id='id_avatar']/preceding-sibling::img",
        "upload_avatar_browse_button": "//input[@id='id_avatar']",
        "upload_avatar_button": "//input[@type='submit']",
        "upload_avatar_cancel_option": "//a[normalize-space(text())='Cancel']"
    }

    DELETE_AVATAR_PAGE_LOCATORS = {
        "delete_uploaded_avatar_page_header": "//article[@id='avatar-delete']/h1",
        "delete_uploaded_avatar_image_preview": "//div[@id='avatar-preview']/img",
        "delete_uploaded_avatar_page_info": "//form/p",
        "delete_uploaded_avatar_button": "//input[@value='Delete avatar']",
        "delete_uploaded_avatar_cancel_button": "//a[normalize-space(text())='Cancel']"
    }

    REMOVE_USER_PAGE_LOCATORS = {
        "remove_user_page_header": "//article[@id='remove-member']/h1",
        "remove_member_button": "//input[@value='Remove member']",
        "remove_member_cancel_button": "//div[@class='form-actions']/a[text()='Cancel']"
    }

    def __init__(self, page: Page):
        super().__init__(page)

    # Actions against the all groups page.
    def is_add_group_profile_button_visible(self) -> bool:
        """Check if the add group profile button is visible"""
        return self._is_element_visible(
            self.GENERAL_GROUPS_PAGE_LOCATORS["add_group_profile_button"])

    def click_on_a_particular_group(self, group_name):
        """Click on a particular group

        Args:
            group_name (str): The name of the group to click on
        """
        self._click(f"//a[text()='{group_name}']")

    # Actions against the group page.
    def get_all_members_name(self) -> list[str]:
        """Get the names of all the members in the group"""
        return self._get_text_of_elements(self.GROUP_PAGE_LOCATORS["group_members_list"])

    def get_group_avatar_locator(self) -> Locator:
        """Get the locator of the group avatar image"""
        return self._get_element_locator(self.GROUP_PAGE_LOCATORS["group_avatar_image"])

    def is_change_avatar_button_visible(self) -> bool:
        """Check if the change avatar button is visible"""
        return self._is_element_visible(self.GROUP_PAGE_LOCATORS["change_avatar_button"])

    def is_edit_in_admin_button_visible(self) -> bool:
        """Check if the edit in admin button is visible"""
        return self._is_element_visible(self.GROUP_PAGE_LOCATORS["edit_in_admin_button"])

    def get_edit_group_profile_page_header(self) -> str:
        """Get the text of the edit group profile page header"""
        return self._get_text_of_element(self.GROUP_PAGE_LOCATORS
                                         ["edit_group_profile_page_header"])

    def is_edit_group_profile_button_visible(self) -> bool:
        """Check if the edit group profile button is visible"""
        return self._is_element_visible(self.GROUP_PAGE_LOCATORS["edit_group_profile_button"])

    def click_on_edit_group_profile_button(self):
        """Click on the edit group profile button"""
        self._click(self.GROUP_PAGE_LOCATORS["edit_group_profile_button"])

    def get_edit_group_profile_textarea_content(self) -> str:
        """Get the content of the edit group profile textarea"""
        return self._get_element_input_value(self.GROUP_PAGE_LOCATORS
                                             ["edit_group_profile_textarea"])

    def type_into_edit_group_profile_textarea(self, text: str):
        """Type into the edit group profile textarea

        Args:
            text (str): The text to type into the edit group profile textarea
        """
        self._clear_field(self.GROUP_PAGE_LOCATORS["edit_group_profile_textarea"])
        self._fill(self.GROUP_PAGE_LOCATORS["edit_group_profile_textarea"], text)

    def get_profile_information(self) -> str:
        """Get the profile information"""
        return self._get_text_of_element(self.GROUP_PAGE_LOCATORS["group_profile_information"])

    def click_on_edit_group_profile_save_button(self):
        """Click on the save group profile edit button"""
        self._click(self.GROUP_PAGE_LOCATORS["save_group_profile_edit_button"])

    def is_edit_group_leaders_button_visible(self) -> bool:
        """Check if the edit group leaders button is visible"""
        return self._is_element_visible(self.GROUP_PAGE_LOCATORS["edit_group_leaders_button"])

    def is_edit_group_members_option_visible(self) -> bool:
        """Check if the edit group members option is visible"""
        return self._is_element_visible(self.GROUP_PAGE_LOCATORS["edit_group_members_option"])

    def click_on_pm_group_members_button(self):
        """Click on the PM group members button"""
        self._click(self.GROUP_PAGE_LOCATORS["private_message_group_members_button"])

    def click_on_pm_for_a_particular_user(self, username: str):
        """Click on the PM button for a particular user

        Args:
            username (str): The username of the user to click on the PM button for
        """
        self._click(
            f"//div[@class='info']/a[normalize-space(text())='{username}']/following-sibling::p/a")

    # Add Group member
    def get_group_update_notification(self) -> str:
        """Get the text of the user added successfully message"""
        return self._get_text_of_element(self.GROUP_PAGE_LOCATORS["user_notification"])

    def get_pm_group_members_button(self) -> Locator:
        """Get the locator of the PM group members button"""
        return self._get_element_locator(self.GROUP_PAGE_LOCATORS
                                         ["private_message_group_members_button"])

    def click_on_change_uploaded_avatar_button(self):
        """Click on the change uploaded avatar button"""
        self._click(self.GROUP_PAGE_LOCATORS["change_uploaded_group_image_option"],
                    expected_locator=self.CHANGE_AVATAR_PAGE_LOCATORS["upload_avatar_page_header"])

    def click_on_delete_uploaded_avatar_button(self):
        """Click on the delete uploaded avatar button"""
        self._click(self.GROUP_PAGE_LOCATORS["delete_uploaded_group_image_option"])

    def click_on_change_avatar_button(self):
        """Click on the change avatar button"""
        self._click(self.GROUP_PAGE_LOCATORS["change_avatar_button"],
                    expected_locator=self.CHANGE_AVATAR_PAGE_LOCATORS["upload_avatar_page_header"])

    def click_on_edit_group_members(self):
        """Click on the edit group members option"""
        self._click(self.GROUP_PAGE_LOCATORS["edit_group_members_option"])

    # Actions against the change avatar page.
    def get_change_avatar_image_preview_locator(self) -> Locator:
        """Get the locator of the change avatar image preview"""
        return self._get_element_locator(self.CHANGE_AVATAR_PAGE_LOCATORS
                                         ["upload_avatar_image_preview"])

    def get_upload_avatar_page_header(self) -> str:
        """Get the text of the upload avatar page header"""
        return self._get_text_of_element(self.CHANGE_AVATAR_PAGE_LOCATORS
                                         ["upload_avatar_page_header"])

    def click_on_upload_avatar_button(self, expected_url=None):
        """Click on the upload avatar button"""
        self._click(self.CHANGE_AVATAR_PAGE_LOCATORS["upload_avatar_button"],
                    expected_url=expected_url)

    def click_on_upload_avatar_cancel_button(self):
        """Click on the upload avatar cancel button"""
        self._click(self.CHANGE_AVATAR_PAGE_LOCATORS["upload_avatar_cancel_option"])

    # Actions against the delete avatar page.
    def get_delete_avatar_image_preview_locator(self) -> Locator:
        """Get the locator of the delete avatar image preview"""
        return self._get_element_locator(self.DELETE_AVATAR_PAGE_LOCATORS
                                         ["delete_uploaded_avatar_image_preview"])

    def click_on_cancel_delete_avatar_button(self):
        """Click on the cancel delete avatar button"""
        self._click(self.DELETE_AVATAR_PAGE_LOCATORS["delete_uploaded_avatar_cancel_button"])

    def get_delete_avatar_page_header(self) -> str:
        """Get the text of the delete avatar page header"""
        return self._get_text_of_element(self.DELETE_AVATAR_PAGE_LOCATORS
                                         ["delete_uploaded_avatar_page_header"])

    def is_image_preview_visible(self) -> bool:
        """Check if the image preview is visible"""
        return self._is_element_visible(self.DELETE_AVATAR_PAGE_LOCATORS
                                        ["delete_uploaded_avatar_image_preview"])

    def get_delete_avatar_page_info(self) -> str:
        """Get the text of the delete avatar page info"""
        return self._get_text_of_element(self.DELETE_AVATAR_PAGE_LOCATORS
                                         ["delete_uploaded_avatar_page_info"])

    def click_on_delete_avatar_button(self):
        """Click on the delete avatar button"""
        self._click(self.DELETE_AVATAR_PAGE_LOCATORS["delete_uploaded_avatar_button"])

    # Actions against the removal or user addition
    def click_on_remove_a_user_from_group_button(self, username: str):
        """Click on the remove a user from group button

        Args:
            username (str): The username of the user to remove from the group
        """
        self._click(f"//div[@class='info']/a[text()='{username}']/../..//a[@title="
                    f"'Remove user from group']")

    def click_on_remove_member_confirmation_button(self):
        """Click on the remove member confirmation button"""
        self._click(self.GROUP_PAGE_LOCATORS["remove_user_from_group_confirmation_button"])

    def type_into_add_member_field(self, text: str):
        """Type into the add member field

        Args:
            text (str): The text to type into the add member field
        """
        self._type(self.GROUP_PAGE_LOCATORS["add_group_member_field"], text, delay=0)

    def group_click_on_a_searched_username(self, username: str):
        """Click on a searched username

        Args:
            username (str): The username to click on
        """
        self._click(f"//div[@class='name_search']/b[text()='{username}']")

    def click_on_add_member_button(self):
        """Click on the add member button"""
        self._click(self.GROUP_PAGE_LOCATORS["add_member_button"])

    def click_on_a_listed_group_user(self, username: str):
        """Click on a listed group user.

        Args:
            username (str): The username of the user to click on
        """
        self._click(f"//div[@class='info']/a[text()='{username}']")

    def get_remove_user_page_header(self) -> str:
        """Get the text of the remove user page header"""
        return self._get_text_of_element(self.REMOVE_USER_PAGE_LOCATORS["remove_user_page_header"])

    def click_on_remove_member_button(self):
        """Click on the remove member button"""
        self._click(self.REMOVE_USER_PAGE_LOCATORS["remove_member_button"])

    def click_on_remove_member_cancel_button(self):
        """Click on the remove member cancel button"""
        self._click(self.REMOVE_USER_PAGE_LOCATORS["remove_member_cancel_button"])
