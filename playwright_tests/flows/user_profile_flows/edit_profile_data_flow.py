from playwright.sync_api import Page
from playwright_tests.core.testutilities import TestUtilities
from playwright_tests.pages.user_pages.my_profile_edit import MyProfileEdit


class EditProfileDataFlow(MyProfileEdit, TestUtilities):
    def __init__(self, page: Page):
        super().__init__(page)

    # Editing a profile with data flow.
    def edit_profile_with_test_data(self):
        edit_test_data = super().profile_edit_test_data

        self._clear_input_fields()
        super()._send_text_to_username_field(edit_test_data["valid_user_edit"]["username"])
        super()._send_text_to_display_name_field(edit_test_data["valid_user_edit"]["display_name"])
        super()._send_text_to_biography_field(edit_test_data["valid_user_edit"]["biography"])
        super()._send_text_to_website_field(edit_test_data["valid_user_edit"]["website"])
        super()._send_text_to_twitter_username_field(
            edit_test_data["valid_user_edit"]["twitter_username"]
        )
        super()._send_text_to_community_portal_field(
            edit_test_data["valid_user_edit"]["community_portal_username"]
        )
        super()._send_text_to_people_directory_username(
            edit_test_data["valid_user_edit"]["people_directory_username"]
        )
        super()._send_text_to_matrix_nickname(
            edit_test_data["valid_user_edit"]["matrix_nickname"]
        )
        super()._select_country_dropdown_option_by_value(
            edit_test_data["valid_user_edit"]["country_code"]
        )
        super()._sent_text_to_city_field(edit_test_data["valid_user_edit"]["city"])
        super()._select_timezone_dropdown_option_by_value(
            edit_test_data["valid_user_edit"]["timezone"]
        )
        super()._select_preferred_language_dropdown_option_by_value(
            edit_test_data["valid_user_edit"]["preferred_language"]
        )
        super()._select_involved_from_month_option_by_value(
            edit_test_data["valid_user_edit"]["involved_from_month_number"]
        )
        super()._select_involved_from_year_option_by_value(
            edit_test_data["valid_user_edit"]["involved_from_year"]
        )

    # Clear all profile edit input fields flow.
    def _clear_input_fields(self):
        super()._clear_all_input_fields()
        super()._clear_username_field()
        super()._clear_biography_textarea_field()
