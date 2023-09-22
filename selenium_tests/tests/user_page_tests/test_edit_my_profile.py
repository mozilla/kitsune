import pytest
import pytest_check as check

from selenium_tests.core.test_utilities import TestUtilities
from selenium_tests.messages.auth_pages_messages.fxa_page_messages import (
    FxAPageMessages,
)
from selenium_tests.messages.my_profile_pages_messages.edit_my_profile_page_messages import (
    EditMyProfilePageMessages,
)
from selenium_tests.messages.my_profile_pages_messages.my_profile_page_messages import (
    MyProfileMessages,
)


class TestEditMyProfile(TestUtilities):
    # C891529
    @pytest.mark.userPageTests
    def test_username_field_is_automatically_populated(self):
        self.logger.info(
            "Signing in with a simple user account and navigating to the 'Edit Profile' page"
        )

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.top_navbar.click_on_edit_profile_option()

        self.logger.info(
            "Verifying that username field is automatically populated with the correct data"
        )

        top_navbar_displayed_username = self.pages.top_navbar.get_text_of_logged_in_username()

        assert (
            self.pages.edit_my_profile_page.get_username_input_field_value()
            == top_navbar_displayed_username
        ), (
            f"Incorrect username displayed inside the user field. "
            f"Expected: {top_navbar_displayed_username}, "
            f"received: {self.pages.edit_my_profile_page.get_username_input_field_value()}"
        )

    # C1491017
    # This test is currently covering the: my profile section, top navbar, and posted questions.
    # Might want to extend the coverage
    @pytest.mark.userPageTests
    def test_edit_profile_field_validation_with_symbols(self):
        self.logger.info("Signing in with a normal account")

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.logger.info("Navigating to the profile edit page")

        self.pages.top_navbar.click_on_edit_profile_option()

        self.logger.info("Extracting the username value")

        original_username = self.pages.edit_my_profile_page.get_username_input_field_value()

        self.logger.info(
            "Clearing the username and display name fields and inserting the new username"
        )

        self.pages.edit_my_profile_page.clear_username_field()
        self.pages.edit_my_profile_page.clear_display_name_field()

        profile_edit_data = super().profile_edit_test_data

        if self.browser == "chrome":
            new_username = profile_edit_data["valid_user_edit_with_symbols"][
                "username_with_valid_symbols_chrome"
            ]
        elif self.browser == "firefox":
            new_username = profile_edit_data["valid_user_edit_with_symbols"][
                "username_with_valid_symbols_firefox"
            ]

        self.pages.edit_my_profile_page.send_text_to_username_field(new_username)

        self.logger.info("Clicking on the 'Update My Profile' button")

        self.pages.edit_my_profile_page.click_update_my_profile_button()

        self.logger.info(
            "Verify that the newly set username is successfully applied to the my profile section"
        )

        check.equal(
            self.pages.my_profile_page.get_my_profile_display_name_header_text(),
            new_username,
            f"The username displayed inside the profile section should be {new_username} "
            f"but instead is: "
            f"{self.pages.my_profile_page.get_my_profile_display_name_header_text()}",
        )

        self.logger.info("Verify that the newly set username is displayed inside the top navbar")

        check.equal(
            self.pages.top_navbar.get_text_of_logged_in_username(),
            new_username,
            f"The username displayed inside the top navbar section should be {new_username} "
            f"but instead is {self.pages.top_navbar.get_text_of_logged_in_username()}",
        )

        self.logger.info(
            "Access a previously posted question and verify that the display name has changed"
        )

        self.pages.my_profile_page.click_on_my_profile_questions_link()

        self.pages.my_questions_page.click_on_a_question_by_index(1)

        check.equal(
            self.pages.question_page.get_question_author_name(),
            new_username,
            "The new username should be reflected under the posted questions as well",
        )

        self.logger.info(
            "Going back to the my profile page and reverting the username back to the original one"
        )

        self.pages.top_navbar.click_on_edit_profile_option()

        self.pages.edit_my_profile_page.clear_username_field()

        self.pages.edit_my_profile_page.send_text_to_username_field(original_username)

        self.pages.edit_my_profile_page.click_update_my_profile_button()

        self.logger.info("Verifying that the username was updated back to the original one")

        check.equal(
            self.pages.my_profile_page.get_my_profile_display_name_header_text(),
            original_username,
            f"The username displayed inside the profile section should be {original_username} "
            f"but instead is: "
            f"{self.pages.my_profile_page.get_my_profile_display_name_header_text()}",
        )

        self.logger.info("Verify that the newly set username is displayed inside the top navbar")

        check.equal(
            self.pages.top_navbar.get_text_of_logged_in_username(),
            original_username,
            f"The username displayed inside the top navbar section should be {original_username} "
            f"but instead is {self.pages.top_navbar.get_text_of_logged_in_username()}",
        )

        self.logger.info(
            "Access a previously posted question and verify that the display name has changed"
        )

        self.pages.my_profile_page.click_on_my_profile_questions_link()

        self.pages.my_questions_page.click_on_a_question_by_index(1)

        check.equal(
            self.pages.question_page.get_question_author_name(),
            original_username,
            "The new username should be reflected under the posted questions as well",
        )

    # C1491017
    @pytest.mark.userPageTests
    def test_username_with_invalid_symbols(self):
        self.logger.info("Signing in with a normal user account")

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.logger.info("Accessing the edit profile page")

        self.pages.top_navbar.click_on_edit_profile_option()

        self.logger.info("Extracting the original username")

        original_username = self.pages.edit_my_profile_page.get_username_input_field_value()

        self.logger.info("Clearing the username input field and adding an invalid user")

        self.pages.edit_my_profile_page.clear_username_field()

        profile_edit_data = super().profile_edit_test_data

        new_username = profile_edit_data["invalid_username_with_symbols"][
            "username_with_invalid_symbols"
        ]

        self.pages.edit_my_profile_page.send_text_to_username_field(new_username)

        self.logger.info("Clicking on the 'Update My Profile' button")

        self.pages.edit_my_profile_page.click_update_my_profile_button()

        self.logger.info("Verify that the error message is displayed")

        check.equal(
            self.pages.edit_my_profile_page.get_username_error_message_text(),
            EditMyProfilePageMessages.USERNAME_INPUT_ERROR_MESSAGE,
            f"Incorrect error message displayed. "
            f"Expected: {EditMyProfilePageMessages.USERNAME_INPUT_ERROR_MESSAGE} "
            f"but received: {self.pages.edit_my_profile_page.get_username_error_message_text()}",
        )

        self.logger.info(
            "Accessing the Edit Profile page and verifying that the username was not changed"
        )

        self.pages.top_navbar.click_on_view_profile_option()

        assert (
            self.pages.my_profile_page.get_my_profile_display_name_header_text()
            == original_username
        ), (
            f"The username should be: {original_username} "
            f"but instead is: {self.pages.my_profile_page.get_my_profile_display_name_header_text}"
        )

    #  C891530,  C2107866
    @pytest.mark.userPageTests
    def test_cancel_profile_edit(self):
        self.logger.info("Signing in with a normal user account")

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.logger.info("Accessing the Edit My Profile page")

        self.pages.top_navbar.click_on_edit_profile_option()

        self.logger.info("Extracting all the edit my profile fields values")

        original_values = self.pages.edit_my_profile_page.get_value_of_all_fields()

        self.logger.info("Populating edit profile fields with data")

        self.pages.edit_profile_flow.edit_profile_with_test_data()

        self.logger.info("Clicking on the 'Cancel' button")

        self.pages.edit_my_profile_page.click_cancel_button()

        self.logger.info(
            "Verifying that we are on the same page "
            "and all the input field values were reverted back to original"
        )

        assert self.pages.edit_my_profile_page.get_value_of_all_fields() == original_values, (
            f"Fields values were not restored to original values. "
            f"Original values: {original_values}, current field "
            f"values: {self.pages.edit_my_profile_page.get_value_of_all_fields()}"
        )

    #  C946232
    @pytest.mark.skip
    def test_manage_firefox_account_redirects_to_firefox_account_settings_page(self):
        self.logger.info("Signing in with a normal user account")

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.logger.info("Accessing the 'Edit my profile' page")

        self.pages.top_navbar.click_on_edit_profile_option()

        self.logger.info("Click on the 'Manage Firefox Account' button")

        self.pages.edit_my_profile_page.click_manage_firefox_account_button()

        self.logger.info(
            "Verifying that the user was redirected to "
            "the Firefox Account Settings page in a new tab"
        )

        self.pages.edit_my_profile_page._switch_next_child_tab()

        assert (
            FxAPageMessages.ACCOUNT_SETTINGS_URL in self.pages.edit_my_profile_page.current_url()
        ), (
            f"User was not redirected to the Firefox settings page. "
            f"The current url is {self.pages.edit_my_profile_page.current_url()}"
        )

    #  C1491461
    @pytest.mark.userPageTests
    def test_duplicate_usernames_are_not_allowed(self):
        self.logger.info("Sign in with a normal user account")

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        original_username = self.pages.top_navbar.get_text_of_logged_in_username()

        self.pages.top_navbar.click_on_edit_profile_option()

        self.logger.info("Clearing the username input field and adding an existing username to it")

        self.pages.edit_my_profile_page.clear_username_field()

        self.pages.edit_my_profile_page.send_text_to_username_field(
            super().username_extraction_from_email(
                super().user_secrets_data["TEST_ACCOUNT_MESSAGE_6"]
            )
        )

        self.pages.edit_my_profile_page.click_update_my_profile_button()

        self.logger.info(
            "Verify that the error message is displayed "
            "under the username input field and is the correct one"
        )

        check.equal(
            self.pages.edit_my_profile_page.get_username_error_message_text(),
            EditMyProfilePageMessages.DUPLICATE_USERNAME_ERROR_MESSAGE,
            f"Incorrect error message displayed! The expected error message is: "
            f"{EditMyProfilePageMessages.DUPLICATE_USERNAME_ERROR_MESSAGE}"
            f" The displayed error message is:"
            f" {self.pages.edit_my_profile_page.get_username_error_message_text()}",
        )

        self.logger.info(
            "Verifying that the username displayed inside the top navbar is the correct one"
        )

        check.equal(
            self.pages.top_navbar.get_text_of_logged_in_username(),
            original_username,
            f"Incorrect username displayed inside the top-navbar. "
            f"Expected to be: {original_username} "
            f" but got: {self.pages.top_navbar.get_text_of_logged_in_username()}",
        )

        self.logger.info("Accessing the my profile page")

        self.pages.top_navbar.click_on_view_profile_option()

        self.logger.info(
            "Verifying that the username displayed inside the My Profile page is the correct one"
        )

        assert (
            self.pages.my_profile_page.get_my_profile_display_name_header_text()
            == original_username
        ), (
            f"Incorrect username displayed inside the My Profile page."
            f" Expected to be: {original_username}"
            f" but got: {self.pages.my_profile_page.get_my_profile_display_name_header_text()}"
        )

    #  C1491462
    @pytest.mark.skip
    def test_profile_username_field_cannot_be_left_empty(self):
        self.logger.info("Signing in with a normal account")

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        original_username = self.pages.top_navbar.get_text_of_logged_in_username()

        self.logger.info("Accessing the Edit My Profile page")

        self.pages.top_navbar.click_on_edit_profile_option()

        self.logger.info(
            "Clearing the username input field and clicking on the Update My Profile button"
        )

        self.pages.edit_my_profile_page.clear_username_field()

        self.pages.edit_my_profile_page.click_update_my_profile_button()

        self.logger.info("Verifying that we are still on the edit profile page")

        check.equal(
            self.pages.edit_my_profile_page.current_url(),
            EditMyProfilePageMessages.STAGE_EDIT_MY_PROFILE_URL,
            f"We are not on the expected page. Expected page to be:"
            f" {EditMyProfilePageMessages.STAGE_EDIT_MY_PROFILE_URL}"
            f" but we are on the {self.pages.edit_my_profile_page.current_url()} page instead",
        )

        self.logger.info(
            "Verifying that the displayed username inside the top navbar is the original one"
        )

        assert self.pages.top_navbar.get_text_of_logged_in_username() == original_username, (
            f"Expected username to be: {original_username}. "
            f"The displayed username is {self.pages.top_navbar.get_text_of_logged_in_username()}"
        )

        self.logger.info("Accessing the my profile page")

        self.pages.user_navbar.click_on_my_profile_option()

        self.logger.info(
            "Verifying that the username displayed inside the my profile page is the original one"
        )

        assert (
            self.pages.my_profile_page.get_my_profile_display_name_header_text()
            == original_username
        ), (
            f"Expected username to be: {original_username}. "
            f"The displayed username is "
            f"{self.pages.my_profile_page.get_my_profile_display_name_header_text()}"
        )

    # C1491018, C891531,C1491021
    @pytest.mark.userPageTests
    def test_username_can_contain_uppercase_and_lowercase_letters(self):
        self.logger.info("Signing in with a normal account")

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_MESSAGE_4"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        original_username = self.pages.top_navbar.get_text_of_logged_in_username()

        new_username = super().profile_edit_test_data["uppercase_lowercase_valid_username"][
            "uppercase_lowercase_username"
        ]

        self.logger.info("Accessing the edit my profile page")

        self.pages.top_navbar.click_on_edit_profile_option()

        self.logger.info(
            "Updating the username field to contain uppercase and lowercase characters"
        )

        self.pages.edit_my_profile_page.clear_username_field()
        self.pages.edit_my_profile_page.send_text_to_username_field(new_username)

        self.logger.info("Clicking on the 'Update my Profile button'")

        self.pages.edit_my_profile_page.click_update_my_profile_button()

        self.logger.info(
            "Verifying that the username displayed inside the top-navbar updates successfully"
        )

        assert self.pages.top_navbar.get_text_of_logged_in_username() == new_username, (
            f"The displayed username is incorrect. Expected: {new_username} "
            f"but {self.pages.top_navbar.get_text_of_logged_in_username()} is displayed instead"
        )

        self.logger.info(
            "Verifying that the username displayed inside "
            "the my profile section is the correct one"
        )

        assert (
            self.pages.my_profile_page.get_my_profile_display_name_header_text() == new_username
        ), (
            f"The displayed username is incorrect. Expected: {new_username}"
            f"but {self.pages.my_profile_page.get_my_profile_display_name_header_text()} "
            f"is displayed instead"
        )

        self.logger.info("Reverting the username back to the original one")

        self.pages.top_navbar.click_on_edit_profile_option()
        self.pages.edit_my_profile_page.clear_username_field()
        self.pages.edit_my_profile_page.send_text_to_username_field(original_username)
        self.pages.edit_my_profile_page.click_update_my_profile_button()

    #  C1491463, C1491464
    @pytest.mark.userPageTests
    def test_display_name_replaces_the_username_text(self):
        self.logger.info("Signing in with a normal user account")

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_MESSAGE_1"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        original_username = self.pages.top_navbar.get_text_of_logged_in_username()

        if self.browser == "chrome":
            new_display_name = super().profile_edit_test_data["valid_user_edit"][
                "display_name_chrome"
            ]
        elif self.browser == "firefox":
            new_display_name = super().profile_edit_test_data["valid_user_edit"][
                "display_name_firefox"
            ]

        self.logger.info("Accessing the edit profile page and adding a new display name")

        self.pages.top_navbar.click_on_edit_profile_option()

        self.pages.edit_my_profile_page.clear_display_name_field()

        self.pages.edit_my_profile_page.send_text_to_display_name_field(new_display_name)

        self.logger.info("Clicking on the 'Update My Profile' button")

        self.pages.edit_my_profile_page.click_update_my_profile_button()

        self.logger.info("Verifying that the top navbar username updates with the display name")

        assert self.pages.top_navbar.get_text_of_logged_in_username() == new_display_name, (
            f"Incorrect displayed signed in username in top-navbar. "
            f"Expected: {new_display_name} but "
            f"{self.pages.top_navbar.get_text_of_logged_in_username()} is displayed instead"
        )

        self.logger.info(
            "Verifying that the 'My profile' display name contains display name (username)"
        )

        assert (
            self.pages.my_profile_page.get_my_profile_display_name_header_text()
            == f"{new_display_name} ({original_username})"
        ), (
            f"Incorrect displayed signed in username inside the my profile page. "
            f"Expected: {new_display_name} ({original_username})"
            f"but {self.pages.my_profile_page.get_my_profile_display_name_header_text()} "
            f"is displayed instead"
        )

        self.logger.info("Reverting back and deleting the display name")

        self.pages.top_navbar.click_on_edit_profile_option()
        self.pages.edit_my_profile_page.clear_display_name_field()
        self.pages.edit_my_profile_page.click_update_my_profile_button()

        self.logger.info(
            "Verifying that the displayed name inside the top navbar is reverted back to username"
        )

        assert self.pages.top_navbar.get_text_of_logged_in_username() == original_username, (
            f"Incorrect displayed signed in username after deleting the display name. "
            f"Expected: {original_username}"
            f" but received: {self.pages.top_navbar.get_text_of_logged_in_username()}"
        )

        self.logger.info(
            "Verifying that the displayed name inside the main "
            "profile page is reverted back to the username"
        )
        assert {
            self.pages.my_profile_page.get_my_profile_display_name_header_text()
            == original_username
        }, (
            f"Incorrect displayed name inside the profile page. Expected: {original_username} but"
            f" received {self.pages.my_profile_page.get_my_profile_display_name_header_text()}"
        )

    # This needs update. It currently fails due to:
    # https://github.com/mozilla/sumo/issues/1345
    @pytest.mark.skip
    def test_biography_field_accepts_html_tags(self):
        self.logger.info("Signing in with a normal user account")

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.logger.info("Accessing the edit profile page via top-navbar")

        self.pages.top_navbar.click_on_edit_profile_option()

        self.logger.info("Clearing the biography field and inputting html data to it")

        self.pages.edit_my_profile_page.clear_biography_textarea_field()

        html_test_data = super().profile_edit_test_data

        self.pages.edit_my_profile_page.send_text_to_biography_field(
            html_test_data["biography_field_with_html_data"]["biography_html_data"]
        )

        self.logger.info("Clicking on the 'Update My Profile button'")

        self.pages.edit_my_profile_page.click_update_my_profile_button()

    #  C2107899, C2107899
    @pytest.mark.userPageTests
    def test_make_my_email_address_visible_checkbox_checked(self):
        logged_in_email = super().user_secrets_data["TEST_ACCOUNT_12"]

        self.logger.info("Signing in with a normal user account")

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        username_one = self.pages.top_navbar.get_text_of_logged_in_username()

        self.logger.info("Accessing the 'Edit My Profile' page")

        self.pages.top_navbar.click_on_edit_profile_option()

        if not self.pages.edit_my_profile_page.is_make_email_visible_checkbox_selected():
            self.pages.edit_my_profile_page.click_make_email_visible_checkbox()
            self.pages.edit_my_profile_page.click_update_my_profile_button()

        self.logger.info(
            "Checkbox is checked, returning to My Profile page "
            "and verifying that the email is displayed"
        )

        self.pages.top_navbar.click_on_view_profile_option()

        check.equal(
            self.pages.my_profile_page.get_text_of_publicly_displayed_username(),
            logged_in_email,
            f"Incorrect email is displayed inside the "
            f"'My Profile' page. Expected: {logged_in_email} "
            f"received {self.pages.my_profile_page.get_text_of_publicly_displayed_username()}",
        )

        self.logger.info("Signing in with a different user")

        self.pages.my_profile_page.click_my_profile_page_sign_out_button()

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_13"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.logger.info(
            "Accessing the previous user profile and verifying that the email address is displayed"
        )

        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()
        self.pages.homepage.navigate_to(MyProfileMessages.get_my_profile_stage_url(username_one))

        check.equal(
            self.pages.my_profile_page.get_text_of_publicly_displayed_username(),
            logged_in_email,
            f"Incorrect email is displayed inside the 'My Profile' page. "
            f"Expected: {logged_in_email} "
            f"received {self.pages.my_profile_page.get_text_of_publicly_displayed_username()}",
        )

        self.logger.info("Signing out")

        self.pages.top_navbar.click_on_sign_out_button()
        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.logger.info(
            "Accessing the previous user profile and verifying that "
            "the email address is not displayed to signed out users"
        )

        # This also needs an update
        self.pages.homepage.navigate_to(MyProfileMessages.get_my_profile_stage_url(username_one))

        check.is_false(
            self.pages.my_profile_page.is_publicly_displayed_email_displayed(),
            "The email is displayed and it shouldn't be!",
        )

    #  C2107899
    @pytest.mark.userPageTests
    def test_make_my_email_address_visible_checkbox_unchecked(self):
        self.logger.info("Signing in with a normal user account")

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        username_one = self.pages.top_navbar.get_text_of_logged_in_username()

        self.logger.info("Accessing the 'Edit My Profile' page")

        self.pages.top_navbar.click_on_edit_profile_option()

        if self.pages.edit_my_profile_page.is_make_email_visible_checkbox_selected():
            self.pages.edit_my_profile_page.click_make_email_visible_checkbox()
            self.pages.edit_my_profile_page.click_update_my_profile_button()

        self.logger.info(
            "Checkbox is unchecked, returning to My Profile page "
            "and verifying that the email is not displayed"
        )
        self.pages.user_navbar.click_on_my_profile_option()

        assert not (
            self.pages.my_profile_page.is_publicly_displayed_email_displayed()
        ), "The email address is displayed inside the profile! It shouldn't be!"

        self.logger.info("Signing in with a different user")

        self.pages.my_profile_page.click_my_profile_page_sign_out_button()

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_13"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.logger.info(
            "Accessing the previous user profile and verifying that "
            "the email address is not displayed"
        )

        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        # This also needs an update
        self.pages.homepage.navigate_to(MyProfileMessages.get_my_profile_stage_url(username_one))

        assert not (
            self.pages.my_profile_page.is_publicly_displayed_email_displayed()
        ), "The email address is displayed inside the profile! It shouldn't be!"

    # C2107900, C2107900
    @pytest.mark.userPageTests
    def test_website_information_is_displayed(self):
        self.logger.info("Signing in with a normal user account")

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        username_one = self.pages.top_navbar.get_text_of_logged_in_username()

        self.logger.info("Accessing the 'Edit My Profile' page")

        self.pages.top_navbar.click_on_edit_profile_option()

        website_field_test_data = super().profile_edit_test_data["valid_user_edit"]["website"]
        self.pages.edit_my_profile_page.clear_website_field()
        self.pages.edit_my_profile_page.send_text_to_website_field(website_field_test_data)
        self.pages.edit_my_profile_page.click_update_my_profile_button()

        self.logger.info("Verify that the correct website is displayed")

        check.equal(
            self.pages.my_profile_page.get_my_profile_website_text(),
            website_field_test_data,
            f"Incorrect website displayed. Expected: {website_field_test_data}, "
            f"received: {self.pages.my_profile_page.get_my_profile_website_text()}",
        )

        self.logger.info(
            "Signing in with a different user and verifying that the correct website information "
            "is displayed for the first user"
        )

        self.pages.my_profile_page.click_my_profile_page_sign_out_button()

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_13"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.pages.homepage.navigate_to(MyProfileMessages.get_my_profile_stage_url(username_one))

        check.equal(
            self.pages.my_profile_page.get_my_profile_website_text(),
            website_field_test_data,
            f"Incorrect website displayed. Expected: {website_field_test_data}, "
            f"received: {self.pages.my_profile_page.get_my_profile_website_text()}",
        )

        self.logger.info(
            "Clicking on the website and verifying that the user is redirected correctly"
        )

        self.pages.my_profile_page.click_on_my_website_link()

        check.is_in(
            website_field_test_data,
            self.pages.homepage.current_url(),
            f"Incorrect user redirect. Expected: {website_field_test_data} "
            f"received: {self.pages.homepage.current_url()}",
        )

        self.logger.info("Navigating back to the SUMO page")

        self.pages.homepage.navigate_back()

        self.pages.top_navbar.click_on_sign_out_button()

        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.pages.homepage.navigate_to(MyProfileMessages.get_my_profile_stage_url(username_one))

        check.equal(
            self.pages.my_profile_page.get_my_profile_website_text(),
            website_field_test_data,
            f"Incorrect website displayed. Expected: {website_field_test_data}, "
            f"received: {self.pages.my_profile_page.get_my_profile_website_text()}",
        )

        self.logger.info(
            "Clicking on the website and verifying that the user is redirected correctly"
        )

        self.pages.my_profile_page.click_on_my_website_link()

        check.is_in(
            website_field_test_data,
            self.pages.homepage.current_url(),
            f"Incorrect user redirect. Expected: {website_field_test_data} "
            f"received: {self.pages.homepage.current_url()}",
        )

        self.logger.info("Navigating back to the SUMO page")

        self.pages.homepage.navigate_back()

        self.logger.info("Clearing the website field changes")

        self.pages.top_navbar.click_on_sign_out_button()
        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )
        self.pages.top_navbar.click_on_edit_profile_option()
        self.pages.edit_my_profile_page.clear_website_field()
        self.pages.edit_my_profile_page.click_update_my_profile_button()

    # C2107901, C2107901
    @pytest.mark.userPageTests
    def test_twitter_information_is_displayed(self):
        self.logger.info("Signing in with a normal user account")

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        username_one = self.pages.top_navbar.get_text_of_logged_in_username()

        self.logger.info("Accessing the 'Edit My Profile' page")

        self.pages.top_navbar.click_on_edit_profile_option()

        self.logger.info("Clearing and adding data inside the twitter input field")

        twitter_field_test_data = super().profile_edit_test_data["valid_user_edit"][
            "twitter_username"
        ]
        self.pages.edit_my_profile_page.clear_twitter_field()
        self.pages.edit_my_profile_page.send_text_to_twitter_username_field(
            twitter_field_test_data
        )
        self.pages.edit_my_profile_page.click_update_my_profile_button()

        self.logger.info(
            "Navigating back to the My Profile page and verify "
            "that the correct twitter is displayed"
        )

        self.pages.top_navbar.click_on_view_profile_option()

        check.equal(
            self.pages.my_profile_page.get_my_profile_twitter_text(),
            twitter_field_test_data,
            f"Incorrect twitter displayed. Expected: {twitter_field_test_data}, "
            f"received: {self.pages.my_profile_page.get_my_profile_twitter_text()}",
        )

        self.logger.info(
            "Signing in with a different user and verifying that the correct website information "
            "is displayed for the first user"
        )

        self.pages.my_profile_page.click_my_profile_page_sign_out_button()

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_13"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.pages.homepage.navigate_to(MyProfileMessages.get_my_profile_stage_url(username_one))

        check.equal(
            self.pages.my_profile_page.get_my_profile_twitter_text(),
            twitter_field_test_data,
            f"Incorrect twitter displayed. Expected: {twitter_field_test_data}, "
            f"received: {self.pages.my_profile_page.get_my_profile_twitter_text()}",
        )

        self.logger.info(
            "Clicking on the twitter link and verifying that the user is redirected correctly"
        )

        self.pages.my_profile_page.click_on_twitter_link()

        check.is_in(
            MyProfileMessages.TWITTER_REDIRECT_LINK + twitter_field_test_data,
            self.pages.homepage.current_url(),
            f"Incorrect user redirect. "
            f"Expected: {MyProfileMessages.TWITTER_REDIRECT_LINK + twitter_field_test_data} "
            f"received: {self.pages.homepage.current_url()}",
        )

        self.logger.info("Navigating back to the SUMO page")

        self.pages.homepage.navigate_back()

        self.logger.info(
            "Signing out, accessing the profile and verifying that "
            "the twitter information is displayed"
        )

        self.pages.top_navbar.click_on_sign_out_button()

        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.pages.homepage.navigate_to(MyProfileMessages.get_my_profile_stage_url(username_one))

        check.equal(
            self.pages.my_profile_page.get_my_profile_twitter_text(),
            twitter_field_test_data,
            f"Incorrect twitter displayed. Expected: {twitter_field_test_data}, "
            f"received: {self.pages.my_profile_page.get_my_profile_twitter_text()}",
        )

        self.logger.info(
            "Clicking on the twitter link and verifying that the user is redirected correctly"
        )

        self.pages.my_profile_page.click_on_twitter_link()

        check.is_in(
            MyProfileMessages.TWITTER_REDIRECT_LINK + twitter_field_test_data,
            self.pages.homepage.current_url(),
            f"Incorrect user redirect. "
            f"Expected: {MyProfileMessages.TWITTER_REDIRECT_LINK + twitter_field_test_data} "
            f"received: {self.pages.homepage.current_url()}",
        )

        self.logger.info("Navigating back to the SUMO page")

        self.pages.homepage.navigate_back()

        self.logger.info("Clearing the twitter field changes")

        self.pages.top_navbar.click_on_sign_out_button()
        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.top_navbar.click_on_edit_profile_option()
        self.pages.edit_my_profile_page.clear_twitter_field()
        self.pages.edit_my_profile_page.click_update_my_profile_button()

    # C2107903, C2107903
    @pytest.mark.userPageTests
    def test_community_portal_username_is_displayed(self):
        self.logger.info("Signing in with a normal user account")

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        username_one = self.pages.top_navbar.get_text_of_logged_in_username()

        self.logger.info("Accessing the 'Edit My Profile' page")

        self.pages.top_navbar.click_on_edit_profile_option()

        self.logger.info("Clearing and adding data inside the Community Portal input field")

        community_portal_field_test_data = super().profile_edit_test_data["valid_user_edit"][
            "community_portal_username"
        ]
        self.pages.edit_my_profile_page.clear_community_portal_field()
        self.pages.edit_my_profile_page.send_text_to_community_portal_field(
            community_portal_field_test_data
        )
        self.pages.edit_my_profile_page.click_update_my_profile_button()

        self.logger.info(
            "Navigating back to the My Profile page and verify that "
            "the correct Community portal information is displayed"
        )

        self.pages.top_navbar.click_on_view_profile_option()

        check.equal(
            self.pages.my_profile_page.get_my_profile_community_portal_text(),
            community_portal_field_test_data,
            f"Incorrect community portal information is displayed. "
            f"Expected: {community_portal_field_test_data}, "
            f"received: {self.pages.my_profile_page.get_my_profile_community_portal_text()}",
        )

        self.logger.info(
            "Signing in with a different user and verifying "
            "that the correct community portal information is displayed for the first user"
        )

        self.pages.my_profile_page.click_my_profile_page_sign_out_button()

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_13"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.pages.homepage.navigate_to(MyProfileMessages.get_my_profile_stage_url(username_one))

        check.equal(
            self.pages.my_profile_page.get_my_profile_community_portal_text(),
            community_portal_field_test_data,
            f"Incorrect website displayed. Expected: {community_portal_field_test_data}, "
            f"received: {self.pages.my_profile_page.get_my_profile_community_portal_text()}",
        )

        self.logger.info(
            "Clicking on the community portal link and verifying "
            "that the user is redirected correctly"
        )

        self.pages.my_profile_page.click_on_community_portal_link()

        check.is_in(
            MyProfileMessages.COMMUNITY_PORTAL_LINK,
            self.pages.homepage.current_url(),
            f"Incorrect user redirect. Expected: {MyProfileMessages.TWITTER_REDIRECT_LINK} "
            f"received: {self.pages.homepage.current_url()}",
        )

        self.logger.info("Navigating back to the SUMO page")

        self.pages.homepage.navigate_back()

        self.logger.info(
            "Signing out, accessing the profile and verifying that "
            "the community portal information is displayed"
        )

        self.pages.top_navbar.click_on_sign_out_button()

        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.pages.homepage.navigate_to(MyProfileMessages.get_my_profile_stage_url(username_one))

        check.equal(
            self.pages.my_profile_page.get_my_profile_community_portal_text(),
            community_portal_field_test_data,
            f"Incorrect community portal displayed. Expected: {community_portal_field_test_data}, "
            f"received: {self.pages.my_profile_page.get_my_profile_community_portal_text()}",
        )

        self.logger.info(
            "Clicking on the community portal link and verifying that "
            "the user is redirected correctly"
        )

        self.pages.my_profile_page.click_on_community_portal_link()

        check.is_in(
            MyProfileMessages.COMMUNITY_PORTAL_LINK,
            self.pages.homepage.current_url(),
            f"Incorrect user redirect. Expected: {MyProfileMessages.COMMUNITY_PORTAL_LINK} "
            f"received: {self.pages.homepage.current_url()}",
        )

        self.logger.info("Navigating back to the SUMO page")

        self.pages.homepage.navigate_back()

        self.logger.info("Clearing the community portal field changes")
        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.top_navbar.click_on_edit_profile_option()
        self.pages.edit_my_profile_page.clear_community_portal_field()
        self.pages.edit_my_profile_page.click_update_my_profile_button()

    # C2107902,C2107902
    @pytest.mark.userPageTests
    def test_people_directory_information_is_displayed(self):
        self.logger.info("Signing in with a normal user account")

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        username_one = self.pages.top_navbar.get_text_of_logged_in_username()

        self.logger.info("Accessing the 'Edit My Profile' page")

        self.pages.top_navbar.click_on_edit_profile_option()

        self.logger.info("Clearing and adding data inside the People Directory input field")

        people_directory_field_test_data = super().profile_edit_test_data["valid_user_edit"][
            "people_directory_username"
        ]
        self.pages.edit_my_profile_page.clear_people_directory_field()
        self.pages.edit_my_profile_page.send_text_to_people_directory_username(
            people_directory_field_test_data
        )
        self.pages.edit_my_profile_page.click_update_my_profile_button()

        self.logger.info(
            "Navigating back to the My Profile page and verify that "
            "the correct People Directory information is displayed"
        )

        self.pages.top_navbar.click_on_view_profile_option()

        check.equal(
            self.pages.my_profile_page.get_my_profile_people_directory_text(),
            people_directory_field_test_data,
            f"Incorrect people directory text displayed. "
            f"Expected: {people_directory_field_test_data}, "
            f"received: {self.pages.my_profile_page.get_my_profile_people_directory_text()}",
        )

        self.logger.info(
            "Signing in with a different user and verifying that "
            "the correct people directory information is displayed for the first user"
        )

        self.pages.my_profile_page.click_my_profile_page_sign_out_button()

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_13"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.pages.homepage.navigate_to(MyProfileMessages.get_my_profile_stage_url(username_one))

        check.equal(
            self.pages.my_profile_page.get_my_profile_people_directory_text(),
            people_directory_field_test_data,
            f"Incorrect people directory information displayed. "
            f"Expected: {people_directory_field_test_data}, "
            f"received: {self.pages.my_profile_page.get_my_profile_people_directory_text()}",
        )

        self.logger.info(
            "Signing out, accessing the profile and verifying that "
            "the people directory information is displayed"
        )

        self.pages.top_navbar.click_on_sign_out_button()

        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.pages.homepage.navigate_to(MyProfileMessages.get_my_profile_stage_url(username_one))

        check.equal(
            self.pages.my_profile_page.get_my_profile_people_directory_text(),
            people_directory_field_test_data,
            f"Incorrect people directory displayed. Expected: {people_directory_field_test_data}, "
            f"received: {self.pages.my_profile_page.get_my_profile_people_directory_text()}",
        )

        self.logger.info("Clearing the people directory field changes")
        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.top_navbar.click_on_edit_profile_option()
        self.pages.edit_my_profile_page.clear_people_directory_field()
        self.pages.edit_my_profile_page.click_update_my_profile_button()

    # C2107933, C2107933
    @pytest.mark.userPageTests
    def test_matrix_information_is_displayed(self):
        self.logger.info("Signing in with a normal user account")

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        username_one = self.pages.top_navbar.get_text_of_logged_in_username()

        self.logger.info("Accessing the 'Edit My Profile' page")

        self.pages.top_navbar.click_on_edit_profile_option()

        self.logger.info("Clearing and adding data inside the Matrix input field")

        matrix_field_test_data = super().profile_edit_test_data["valid_user_edit"][
            "matrix_nickname"
        ]
        self.pages.edit_my_profile_page.clear_matrix_field()
        self.pages.edit_my_profile_page.send_text_to_matrix_nickname_field(matrix_field_test_data)
        self.pages.edit_my_profile_page.click_update_my_profile_button()

        self.logger.info(
            "Navigating back to the My Profile page and verify that the "
            "correct Matrix information is displayed"
        )

        self.pages.top_navbar.click_on_view_profile_option()

        check.is_in(
            matrix_field_test_data,
            self.pages.my_profile_page.get_my_profile_matrix_text(),
            f"Incorrect Matrix text displayed. Expected: {matrix_field_test_data}, "
            f"received: {self.pages.my_profile_page.get_my_profile_matrix_text()}",
        )

        self.logger.info(
            "Signing in with a different user and verifying that the correct Matrix information "
            "is displayed for the first user"
        )

        self.pages.my_profile_page.click_my_profile_page_sign_out_button()

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_13"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.pages.homepage.navigate_to(MyProfileMessages.get_my_profile_stage_url(username_one))

        check.is_in(
            matrix_field_test_data,
            self.pages.my_profile_page.get_my_profile_matrix_text(),
            f"Incorrect matrix information displayed. Expected: {matrix_field_test_data}, "
            f"received: {self.pages.my_profile_page.get_my_profile_matrix_text()}",
        )

        self.logger.info(
            "Signing out, accessing the profile and verifying that the "
            "Matrix information is displayed"
        )

        self.pages.top_navbar.click_on_sign_out_button()

        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.pages.homepage.navigate_to(MyProfileMessages.get_my_profile_stage_url(username_one))

        check.is_in(
            matrix_field_test_data,
            self.pages.my_profile_page.get_my_profile_matrix_text(),
            f"Incorrect matrix displayed. Expected: {matrix_field_test_data}, "
            f"received: {self.pages.my_profile_page.get_my_profile_matrix_text()}",
        )

        self.logger.info("Clearing the Matrix field changes")

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.top_navbar.click_on_edit_profile_option()
        self.pages.edit_my_profile_page.clear_matrix_field()
        self.pages.edit_my_profile_page.click_update_my_profile_button()

    # C2107934, C2107934
    @pytest.mark.userPageTests
    def test_country_location_information_is_displayed(self):
        self.logger.info("Signing in with a normal user account")

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        username_one = self.pages.top_navbar.get_text_of_logged_in_username()

        self.logger.info("Accessing the 'Edit My Profile' page")

        self.pages.top_navbar.click_on_edit_profile_option()

        self.logger.info("Clearing and adding data inside the Country input field")

        country_field_test_data_code = super().profile_edit_test_data["valid_user_edit"][
            "country_code"
        ]
        country_field_test_data_value = super().profile_edit_test_data["valid_user_edit"][
            "country_value"
        ]
        self.pages.edit_my_profile_page.clear_country_dropdown_field()
        self.pages.edit_my_profile_page.select_country_dropdown_option_by_value(
            country_field_test_data_code
        )
        self.pages.edit_my_profile_page.click_update_my_profile_button()

        self.logger.info("Verify that the correct Country information is displayed")

        check.is_in(
            country_field_test_data_value,
            self.pages.my_profile_page.get_text_of_profile_subheading_location(),
            f"Incorrect Country text displayed. Expected: {country_field_test_data_value}, "
            f"received: {self.pages.my_profile_page.get_text_of_profile_subheading_location()}",
        )

        self.logger.info(
            "Signing in with a different user and verifying that the correct Country information "
            "is displayed for the first user"
        )

        self.pages.my_profile_page.click_my_profile_page_sign_out_button()

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_13"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.pages.homepage.navigate_to(MyProfileMessages.get_my_profile_stage_url(username_one))

        check.is_in(
            country_field_test_data_value,
            self.pages.my_profile_page.get_text_of_profile_subheading_location(),
            f"Incorrect country information displayed. Expected: {country_field_test_data_value}, "
            f"received: {self.pages.my_profile_page.get_text_of_profile_subheading_location()}",
        )

        self.logger.info(
            "Signing out, accessing the profile and verifying that the "
            "Country information is displayed"
        )

        self.pages.top_navbar.click_on_sign_out_button()

        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.pages.homepage.navigate_to(MyProfileMessages.get_my_profile_stage_url(username_one))

        check.is_in(
            country_field_test_data_value,
            self.pages.my_profile_page.get_text_of_profile_subheading_location(),
            f"Incorrect country displayed. Expected: {country_field_test_data_value}, "
            f"received: {self.pages.my_profile_page.get_text_of_profile_subheading_location()}",
        )

        self.logger.info("Clearing the Country field changes")

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.top_navbar.click_on_edit_profile_option()
        self.pages.edit_my_profile_page.clear_country_dropdown_field()
        self.pages.edit_my_profile_page.click_update_my_profile_button()

    # C2107935, C2107935
    @pytest.mark.userPageTests
    def test_city_location_information_is_displayed(self):
        self.logger.info("Signing in with a normal user account")

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        username_one = self.pages.top_navbar.get_text_of_logged_in_username()

        self.logger.info("Accessing the 'Edit My Profile' page")

        self.pages.top_navbar.click_on_edit_profile_option()

        self.logger.info("Clearing and adding data inside the City input field")

        city_field_test_data_value = super().profile_edit_test_data["valid_user_edit"]["city"]
        self.pages.edit_my_profile_page.clear_city_field()
        self.pages.edit_my_profile_page.sent_text_to_city_field(city_field_test_data_value)
        self.pages.edit_my_profile_page.click_update_my_profile_button()

        self.logger.info("Verify that the correct City information is displayed")

        check.is_in(
            city_field_test_data_value,
            self.pages.my_profile_page.get_text_of_profile_subheading_location(),
            f"Incorrect City text displayed. Expected: {city_field_test_data_value}, "
            f"received: {self.pages.my_profile_page.get_text_of_profile_subheading_location()}",
        )

        self.logger.info(
            "Signing in with a different user and verifying that the correct City information "
            "is displayed for the first user"
        )

        self.pages.my_profile_page.click_my_profile_page_sign_out_button()

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_13"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.pages.homepage.navigate_to(MyProfileMessages.get_my_profile_stage_url(username_one))

        check.is_in(
            city_field_test_data_value,
            self.pages.my_profile_page.get_text_of_profile_subheading_location(),
            f"Incorrect city information displayed. Expected: {city_field_test_data_value}, "
            f"received: {self.pages.my_profile_page.get_text_of_profile_subheading_location()}",
        )

        self.logger.info(
            "Signing out, accessing the profile and verifying that the "
            "City information is displayed"
        )

        self.pages.top_navbar.click_on_sign_out_button()

        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.pages.homepage.navigate_to(MyProfileMessages.get_my_profile_stage_url(username_one))

        check.is_in(
            city_field_test_data_value,
            self.pages.my_profile_page.get_text_of_profile_subheading_location(),
            f"Incorrect city displayed. Expected: {city_field_test_data_value}, "
            f"received: {self.pages.my_profile_page.get_text_of_profile_subheading_location()}",
        )

        self.logger.info("Clearing the City field changes")

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.top_navbar.click_on_edit_profile_option()
        self.pages.edit_my_profile_page.clear_city_field()
        self.pages.edit_my_profile_page.click_update_my_profile_button()

    # C2107938, C2107938
    @pytest.mark.userPageTests
    def test_involved_since_information_is_displayed(self):
        self.logger.info("Signing in with a normal user account")

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        username_one = self.pages.top_navbar.get_text_of_logged_in_username()

        self.logger.info("Accessing the 'Edit My Profile' page")

        self.pages.top_navbar.click_on_edit_profile_option()

        self.logger.info("Clearing and adding data inside the involved since input fields")

        involved_since_month_number_test_data = super().profile_edit_test_data["valid_user_edit"][
            "involved_from_month_number"
        ]
        involved_since_month_test_data_value = super().profile_edit_test_data["valid_user_edit"][
            "involved_from_month_value"
        ]
        involved_since_year_test_data_value = super().profile_edit_test_data["valid_user_edit"][
            "involved_from_year"
        ]
        self.pages.edit_my_profile_page.clear_involved_from_month_select_field()
        self.pages.edit_my_profile_page.clear_involved_from_year_select_field()
        self.pages.edit_my_profile_page.select_involved_with_mozilla_from_month_option_by_value(
            involved_since_month_number_test_data
        )
        self.pages.edit_my_profile_page.select_involved_with_mozilla_from_year_option_by_value(
            involved_since_year_test_data_value
        )
        self.pages.edit_my_profile_page.click_update_my_profile_button()

        self.logger.info("Verify that the correct involved from information is displayed")

        check.is_in(
            involved_since_month_test_data_value and involved_since_year_test_data_value,
            self.pages.my_profile_page.get_my_contributed_from_text(),
            f"Incorrect involved from text displayed. "
            f"Expected to contain: {involved_since_month_test_data_value} "
            f"and {involved_since_year_test_data_value}, "
            f"received: {self.pages.my_profile_page.get_my_contributed_from_text()}",
        )

        self.logger.info(
            "Signing in with a different user and verifying that the "
            "correct involved from information is displayed for the first user"
        )

        self.pages.my_profile_page.click_my_profile_page_sign_out_button()

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_13"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.pages.homepage.navigate_to(MyProfileMessages.get_my_profile_stage_url(username_one))

        check.is_in(
            involved_since_month_test_data_value and involved_since_year_test_data_value,
            self.pages.my_profile_page.get_my_contributed_from_text(),
            f"Incorrect involved from information displayed. "
            f"Expected to contain: {involved_since_month_test_data_value} and"
            f" {involved_since_year_test_data_value}, "
            f"received: {self.pages.my_profile_page.get_my_contributed_from_text()}",
        )

        self.logger.info(
            "Signing out, accessing the profile and verifying that the "
            "involved from information is displayed"
        )

        self.pages.top_navbar.click_on_sign_out_button()

        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.pages.homepage.navigate_to(MyProfileMessages.get_my_profile_stage_url(username_one))

        check.is_in(
            involved_since_month_test_data_value and involved_since_year_test_data_value,
            self.pages.my_profile_page.get_my_contributed_from_text(),
            f"Incorrect involved from text displayed. "
            f"Expected to contain: {involved_since_month_test_data_value} "
            f"and {involved_since_year_test_data_value}, "
            f"received: {self.pages.my_profile_page.get_my_contributed_from_text()}",
        )

        self.logger.info("Clearing the involved from field changes")

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.top_navbar.click_on_edit_profile_option()
        self.pages.edit_my_profile_page.clear_involved_from_month_select_field()
        self.pages.edit_my_profile_page.clear_involved_from_year_select_field()
        self.pages.edit_my_profile_page.click_update_my_profile_button()

    # C2087552, C2108840
    @pytest.mark.userPageTests
    def test_edit_user_profile_button_is_not_displayed_for_non_admin_users(self):
        target_username = self.remove_character_from_string(
            super().username_extraction_from_email(
                super().user_secrets_data["TEST_ACCOUNT_SPECIAL_CHARS"]
            ),
            "*",
        )

        self.logger.info("Accessing a user profile while not being signed in to SUMO")

        self.pages.homepage.navigate_to(
            MyProfileMessages.get_my_profile_stage_url(target_username)
        )

        self.logger.info("Verifying that the 'Edit user profile' option is not displayed")

        assert not (
            self.pages.my_profile_page.is_edit_user_profile_option_displayed()
        ), "The edit user profile button is displayed!. It shouldn't be!"

        self.logger.info(
            "Navigating to the profile edit link directly and verifying that the "
            "user is redirected to the auth page"
        )

        self.pages.my_profile_page.navigate_to(
            EditMyProfilePageMessages.get_url_of_other_profile_edit_page(target_username)
        )

        assert (
            self.pages.auth_page.is_continue_with_firefox_button_displayed()
        ), "The auth page is not displayed! It should be!"

        assert not (
            self.pages.edit_my_profile_page.is_my_profile_edit_form_displayed()
        ), "The my profile edit input form is displayed! It shouldn't be!"

        self.logger.info("Signin in with a simple user account")

        self.pages.top_navbar.click_on_sumo_nav_logo()
        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.logger.info("Accessing another user's account")

        self.pages.homepage.navigate_to(
            MyProfileMessages.get_my_profile_stage_url(target_username)
        )

        self.logger.info("Verifying that the 'Edit user profile' option is not displayed")

        assert not (
            self.pages.my_profile_page.is_edit_user_profile_option_displayed()
        ), "The edit user profile button is displayed!. It shouldn't be!"

        self.logger.info(
            "Navigating to the profile edit link directly and verifying that the "
            "correct message is displayed and the "
            "edit form is not displayed"
        )

        self.pages.my_profile_page.navigate_to(
            EditMyProfilePageMessages.get_url_of_other_profile_edit_page(target_username)
        )

        check.equal(
            self.pages.edit_my_profile_page.get_access_denied_header_text(),
            EditMyProfilePageMessages.PROFILE_ACCESS_DENIED_HEADING,
            f"Incorrect access denied heading displayed. "
            f"Expected: {EditMyProfilePageMessages.PROFILE_ACCESS_DENIED_HEADING} "
            f"received: {self.pages.edit_my_profile_page.get_access_denied_header_text()}",
        )

        check.equal(
            self.pages.edit_my_profile_page.get_access_denied_subheading_text(),
            EditMyProfilePageMessages.PROFILE_ACCESS_DENIED_SUBHEADING,
            f"Incorrect access denied subheading displayed. "
            f"Expected: {EditMyProfilePageMessages.PROFILE_ACCESS_DENIED_SUBHEADING} "
            f" received: {self.pages.edit_my_profile_page.get_access_denied_subheading_text()}",
        )

        assert not (
            self.pages.edit_my_profile_page.is_my_profile_edit_form_displayed()
        ), "The my profile edit input form is displayed! It shouldn't be!"

    # C2108839
    @pytest.mark.userPageTests
    def test_report_user_is_displayed_and_accessible_for_signed_in_users_only(self):
        target_username = self.remove_character_from_string(
            super().username_extraction_from_email(
                super().user_secrets_data["TEST_ACCOUNT_SPECIAL_CHARS"]
            ),
            "*",
        )
        self.logger.info("Signing in with a normal user ")

        self.pages.top_navbar.click_on_signin_signup_button()
        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )
        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.logger.info(
            "Accessing another user profile and verifying that the "
            "'Report Abuse' option is displayed"
        )

        self.pages.homepage.navigate_to(
            MyProfileMessages.get_my_profile_stage_url(target_username)
        )

        check.is_true(
            self.pages.my_profile_page.is_report_user_option_displayed(),
            "The Report Abuse option is not displayed! It should be!",
        )

        self.logger.info("Clicking on the 'Report Abuse' option")

        self.pages.my_profile_page.click_on_report_abuse_option()

        self.logger.info("Verifying that the report abuse panel is displayed")

        check.is_true(
            self.pages.my_profile_page.is_report_abuse_panel_displayed(),
            "The report abuse panel is not displayed. It should be!",
        )

        self.logger.info("Closing the report abuse panel")
        self.pages.my_profile_page.click_on_report_abuse_close_button()

        self.logger.info("Verifying that the report user panel is no longer displayed")

        check.is_false(
            self.pages.my_profile_page.is_report_abuse_panel_displayed(),
            "The report user panel is displayed! It shouldn't be!",
        )

        self.logger.info(
            "Signing out and verifying that the 'Report Abuse' options is not displayed"
        )
        self.pages.top_navbar.click_on_sign_out_button()
        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.logger.info(
            "Accessing another users profile and verifying that the "
            "'report abuse' option is not displayed"
        )

        self.pages.homepage.navigate_to(
            MyProfileMessages.get_my_profile_stage_url(target_username)
        )

        check.is_false(
            self.pages.my_profile_page.is_report_user_option_displayed(),
            "The Report Abuse option is displayed! It shouldn't be while "
            "not signed in with a SUMO account",
        )

    # C2108841
    @pytest.mark.userPageTests
    def test_private_message_button_redirects_non_signed_in_users_to_the_fxa_login_flow(self):
        target_username = self.remove_character_from_string(
            super().username_extraction_from_email(
                super().user_secrets_data["TEST_ACCOUNT_SPECIAL_CHARS"]
            ),
            "*",
        )
        self.logger.info("Accessing another users profile")

        self.pages.homepage.navigate_to(
            MyProfileMessages.get_my_profile_stage_url(target_username)
        )

        self.logger.info("Clicking on the 'Private Message' button")

        self.pages.my_profile_page.click_on_private_message_button()

        self.logger.info("Verifying that the non-signed in user is redirected to the fxa page")

        assert (
            self.pages.auth_page.is_continue_with_firefox_button_displayed()
        ), "The auth page is not displayed! It should be!"

    # C916055, C916054
    @pytest.mark.userPageTests
    def test_deactivate_this_user_buttons_are_displayed_only_for_admin_users(self):
        target_username = self.remove_character_from_string(
            super().username_extraction_from_email(
                super().user_secrets_data["TEST_ACCOUNT_SPECIAL_CHARS"]
            ),
            "*",
        )
        self.logger.info("Navigating to a user profile while not signed in with a user")

        self.pages.homepage.navigate_to(
            MyProfileMessages.get_my_profile_stage_url(target_username)
        )

        self.logger.info("Verifying that the deactivate this user buttons are not displayed")

        assert not (
            self.pages.my_profile_page.is_deactivate_this_user_button_displayed()
        ), "The deactivate this user button is displayed. It shouldn't be!"

        assert not (
            self.pages.my_profile_page.is_deactivate_this_user_and_mark_content_as_spam_displayed()
        ), (
            "The deactivate this user and mark all content as "
            "spam button is displayed. It shouldn't be!"
        )

        self.logger.info("Sign in with a normal user account")

        self.pages.top_navbar.click_on_sumo_nav_logo()
        self.pages.top_navbar.click_on_signin_signup_button()
        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )
        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.logger.info(
            "Accessing another user profile and verify that the "
            "deactivate this user buttons are not displayed"
        )

        self.pages.homepage.navigate_to(
            MyProfileMessages.get_my_profile_stage_url(target_username)
        )

        assert not (
            self.pages.my_profile_page.is_deactivate_this_user_button_displayed()
        ), "The deactivate this user button is displayed. It shouldn't be!"

        assert not (
            self.pages.my_profile_page.is_deactivate_this_user_and_mark_content_as_spam_displayed()
        ), "The deactivate this user and mark all content as spam but"

        self.logger.info("Signing in with a moderator account")

        self.pages.top_navbar.click_on_sumo_nav_logo()
        self.pages.top_navbar.click_on_sign_out_button()

        self.pages.top_navbar.click_on_signin_signup_button()
        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_MODERATOR"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.logger.info(
            "Accessing another user profile and verifying that "
            "the deactivate user buttons are displayed"
        )

        self.pages.homepage.navigate_to(
            MyProfileMessages.get_my_profile_stage_url(target_username)
        )

        assert (
            self.pages.my_profile_page.is_deactivate_this_user_button_displayed()
        ), "The deactivate this user button is not displayed. It should be!"

        assert (
            self.pages.my_profile_page.is_deactivate_this_user_and_mark_content_as_spam_displayed()
        ), "The deactivate this user button is not displayed. It should be!"
