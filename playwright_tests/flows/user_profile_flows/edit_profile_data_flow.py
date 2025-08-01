from playwright.sync_api import Page, TimeoutError
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.my_profile_pages_messages.edit_my_profile_page_messages import \
    EditMyProfilePageMessages
from playwright_tests.pages.top_navbar import TopNavbar
from playwright_tests.pages.user_pages.my_profile_edit import MyProfileEdit
from playwright_tests.pages.user_pages.my_profile_edit_contribution_areas_page import (
    MyProfileEditContributionAreasPage,
)
from playwright_tests.pages.user_pages.my_profile_edit_settings_page import (
    MyProfileEditSettingsPage,
)
from playwright_tests.pages.user_pages.my_profile_user_navbar import UserNavbar

class EditProfileDataFlow:
    def __init__(self, page: Page):
        self.utilities = Utilities(page)
        self.edit_profile_page = MyProfileEdit(page)
        self.top_navbar = TopNavbar(page)
        self.edit_settings_page = MyProfileEditSettingsPage(page)
        self.profile_navbar = UserNavbar(page)
        self.profile_contribution_areas = MyProfileEditContributionAreasPage(page)

    # Editing a profile with data flow.
    def edit_profile_with_test_data(self, info_only=False, submit_change=False,
                                    expected_url=None) -> dict[str, str]:
        edit_test_data = self.utilities.profile_edit_test_data
        valid_user_edit = edit_test_data["valid_user_edit"]

        self.clear_input_fields(info_only)

        if not info_only:
            self._update_fields([
                ("send_text_to_username_field", valid_user_edit["username"]),
                ("send_text_to_display_name_field", valid_user_edit["display_name"]),
                ("select_timezone_dropdown_option_by_value", valid_user_edit["timezone"]),
                ("select_preferred_language_dropdown_option_by_value",
                 valid_user_edit["preferred_language"])
            ])

        self._update_fields([
            ("send_text_to_biography_field", valid_user_edit["biography"]),
            ("send_text_to_website_field", valid_user_edit["website"]),
            ("send_text_to_twitter_username_field", valid_user_edit["twitter_username"]),
            ("send_text_to_community_portal_field", valid_user_edit["community_portal_username"]),
            ("send_text_to_people_directory_username",
             valid_user_edit["people_directory_username"]),
            ("send_text_to_matrix_nickname", valid_user_edit["matrix_nickname"]),
            ("select_country_dropdown_option_by_value", valid_user_edit["country_code"]),
            ("sent_text_to_city_field", valid_user_edit["city"]),
            ("select_involved_from_month_option_by_value",
             valid_user_edit["involved_from_month_number"]),
            ("select_involved_from_year_option_by_value", valid_user_edit["involved_from_year"])
        ])

        if submit_change:
            self.edit_profile_page.click_update_my_profile_button(expected_url=expected_url)

        return {
            "username": valid_user_edit["username"],
            "display_name": valid_user_edit["display_name"],
            "biography": valid_user_edit["biography"],
            "website": valid_user_edit["website"],
            "twitter": valid_user_edit["twitter_username"],
            "community_portal": valid_user_edit["community_portal_username"],
            "people_directory": valid_user_edit["people_directory_username"],
            "matrix_nickname": valid_user_edit["matrix_nickname"],
            "country": valid_user_edit["country_value"],
            "city": valid_user_edit["city"],
            "timezone": valid_user_edit["timezone"],
            "preferred_language": valid_user_edit["preferred_language"],
            "involved_from_month": valid_user_edit["involved_from_month_value"],
            "involved_from_year": valid_user_edit["involved_from_year"]
        }

    def _update_fields(self, fields: list[tuple[str, str]]):
        """
        Updates the fields on the edit profile page.

        Args:
            fields (list[tuple[str, str]]): A list of tuples where each tuple contains the method
            name and the value to be set.
        """
        for method_name, value in fields:
            getattr(self.edit_profile_page, method_name)(value)

    # Clear all profile edit input fields flow.
    def clear_input_fields(self, only_profile_info=False, submit_change=False):
        """
        Clears all profile edit input fields.

        Args:
            only_profile_info (bool): If True, all profile info fields are cleared except username
            and display name.
            submit_change (bool): If True, submits the changes after clearing the fields.
        """
        self.edit_profile_page.clear_all_input_fields(only_profile_info)
        self.edit_profile_page.clear_biography_textarea_field()
        if submit_change:
            self.edit_profile_page.click_update_my_profile_button()

    def check_all_user_settings(self):
        """
        Navigates to the settings profile option, checks all settings checkboxes,
        and updates the settings.
        """
        self.top_navbar.click_on_settings_profile_option()
        self.edit_settings_page.click_on_all_settings_checkboxes()
        self.edit_settings_page.click_on_update_button()

    def check_all_profile_contribution_areas(self, checked: bool):
        """
        Navigates to the contribution areas section and checks or unchecks all contribution areas.

        Args:
            checked (bool): If True, checks all contribution areas. If False, unchecks all
            contribution areas.
        """
        self.top_navbar.click_on_settings_profile_option()
        self.profile_navbar.click_on_edit_contribution_areas_option()

        if not checked:
            self.profile_contribution_areas.click_on_unchecked_cont_areas_checkboxes()
        else:
            self.profile_contribution_areas.click_on_all_checked_cont_areas_checkboxes()

        self.profile_contribution_areas.click_on_update_contribution_areas_button()

    def close_account(self):
        """
        Navigates to the settings profile option and closes the account.
        """
        if self.utilities.get_page_url() != EditMyProfilePageMessages.STAGE_EDIT_MY_PROFILE_URL:
            self.utilities.navigate_to_link(EditMyProfilePageMessages.STAGE_EDIT_MY_PROFILE_URL)
        self.edit_profile_page.click_close_account_option()
        self.edit_profile_page.add_confirmation_code_to_close_account_modal()
        try:
            self.edit_profile_page.click_close_account_button()
        except TimeoutError:
            print("Load not complete")
