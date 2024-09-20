from playwright.sync_api import Page
from playwright_tests.core.utilities import Utilities
from playwright_tests.pages.top_navbar import TopNavbar
from playwright_tests.pages.user_pages.my_profile_edit import MyProfileEdit
from playwright_tests.pages.user_pages.my_profile_edit_contribution_areas_page import \
    MyProfileEditContributionAreasPage
from playwright_tests.pages.user_pages.my_profile_edit_settings_page import \
    MyProfileEditSettingsPage
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
    def edit_profile_with_test_data(self):
        edit_test_data = self.utilities.profile_edit_test_data

        self._clear_input_fields()
        self.edit_profile_page.send_text_to_username_field(
            edit_test_data["valid_user_edit"]["username"]
        )
        self.edit_profile_page.send_text_to_display_name_field(
            edit_test_data["valid_user_edit"]["display_name"]
        )
        self.edit_profile_page.send_text_to_biography_field(
            edit_test_data["valid_user_edit"]["biography"]
        )
        self.edit_profile_page.send_text_to_website_field(
            edit_test_data["valid_user_edit"]["website"]
        )
        self.edit_profile_page.send_text_to_twitter_username_field(
            edit_test_data["valid_user_edit"]["twitter_username"]
        )
        self.edit_profile_page.send_text_to_community_portal_field(
            edit_test_data["valid_user_edit"]["community_portal_username"]
        )
        self.edit_profile_page.send_text_to_people_directory_username(
            edit_test_data["valid_user_edit"]["people_directory_username"]
        )
        self.edit_profile_page.send_text_to_matrix_nickname(
            edit_test_data["valid_user_edit"]["matrix_nickname"]
        )
        self.edit_profile_page.select_country_dropdown_option_by_value(
            edit_test_data["valid_user_edit"]["country_code"]
        )
        self.edit_profile_page.sent_text_to_city_field(edit_test_data["valid_user_edit"]["city"])
        self.edit_profile_page.select_timezone_dropdown_option_by_value(
            edit_test_data["valid_user_edit"]["timezone"]
        )
        self.edit_profile_page.select_preferred_language_dropdown_option_by_value(
            edit_test_data["valid_user_edit"]["preferred_language"]
        )
        self.edit_profile_page.select_involved_from_month_option_by_value(
            edit_test_data["valid_user_edit"]["involved_from_month_number"]
        )
        self.edit_profile_page.select_involved_from_year_option_by_value(
            edit_test_data["valid_user_edit"]["involved_from_year"]
        )

    # Clear all profile edit input fields flow.
    def _clear_input_fields(self):
        self.edit_profile_page.clear_all_input_fields()
        self.edit_profile_page.clear_username_field()
        self.edit_profile_page.clear_biography_textarea_field()

    def check_all_user_settings(self):
        self.top_navbar.click_on_settings_profile_option()
        self.edit_settings_page.click_on_all_settings_checkboxes()
        self.edit_settings_page.click_on_update_button()

    def check_all_profile_contribution_areas(self, checked: bool):
        self.top_navbar.click_on_settings_profile_option()
        self.profile_navbar.click_on_edit_contribution_areas_option()

        if not checked:
            self.profile_contribution_areas.click_on_unchecked_cont_areas_checkboxes()
        else:
            self.profile_contribution_areas.click_on_all_checked_cont_areas_checkboxes()

        self.profile_contribution_areas.click_on_update_contribution_areas_button()
