import allure
import pytest
from pytest_check import check
from playwright.sync_api import expect

from playwright_tests.core.testutilities import TestUtilities
from playwright_tests.messages.auth_pages_messages.fxa_page_messages import FxAPageMessages
from playwright_tests.messages.my_profile_pages_messages.edit_my_profile_page_messages import (
    EditMyProfilePageMessages)
from playwright_tests.messages.my_profile_pages_messages.my_profile_page_messages import (
    MyProfileMessages)


class TestEditMyProfile(TestUtilities):
    # C891529
    @pytest.mark.editUserProfileTests
    def test_username_field_is_automatically_populated(self):
        with allure.step("Signing in with a non-admin user and navigating to the 'Edit Profile' "
                         "page"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_12']
            ))
            self.sumo_pages.top_navbar._click_on_edit_profile_option()

        with allure.step("Verifying that username field is automatically populated with the "
                         "correct data"):
            top_navbar_displayed_username = (
                self.sumo_pages.top_navbar._get_text_of_logged_in_username())
            assert (
                self.sumo_pages.edit_my_profile_page._get_username_input_field_value()
                == top_navbar_displayed_username
            )

    # C1491017
    # This test is currently covering the: my profile section, top navbar, and posted questions.
    # Might want to extend the coverage
    @pytest.mark.editUserProfileTests
    def test_edit_profile_field_validation_with_symbols(self):
        with allure.step("Signing in with a non-admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_12']
            ))

        with allure.step("Navigating to the profile edit page"):
            self.sumo_pages.top_navbar._click_on_edit_profile_option()

        original_username = self.sumo_pages.edit_my_profile_page._get_username_input_field_value()

        with allure.step("Clearing the username, display name fields and inserting the new one"):
            self.sumo_pages.edit_my_profile_page._clear_username_field()
            self.sumo_pages.edit_my_profile_page._clear_display_name_field()
            profile_edit_data = super().profile_edit_test_data

            if self.requested_browser == "chrome":
                new_username = profile_edit_data["valid_user_edit_with_symbols"][
                    "username_with_valid_symbols_chrome"
                ]
            elif self.requested_browser == "firefox":
                new_username = profile_edit_data["valid_user_edit_with_symbols"][
                    "username_with_valid_symbols_firefox"
                ]
            self.sumo_pages.edit_my_profile_page._send_text_to_username_field(new_username)

        with allure.step("Clicking on the 'Update My Profile' button"):
            self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()

        with check, allure.step("Verify that the newly set username is successfully applied to "
                                "the my profile section"):
            assert self.sumo_pages.my_profile_page._get_my_profile_display_name_header_text(
            ) == new_username

        with check, allure.step("Verify that the newly set username is displayed inside the "
                                "top navbar"):
            assert self.sumo_pages.top_navbar._get_text_of_logged_in_username() == new_username

        with check, allure.step("Access a previously posted question and verify that the display"
                                " name has changed"):
            self.sumo_pages.my_profile_page._click_on_my_profile_questions_link()
            self.sumo_pages.my_questions_page._click_on_a_question_by_index(1)

            assert self.sumo_pages.question_page._get_question_author_name() == new_username

        with allure.step("Going back to the my profile page and reverting the username back to "
                         "the original one"):
            self.sumo_pages.top_navbar._click_on_edit_profile_option()
            self.sumo_pages.edit_my_profile_page._clear_username_field()
            self.sumo_pages.edit_my_profile_page._send_text_to_username_field(original_username)
            self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()

        with check, allure.step("Verifying that the username was updated back to the original "
                                "one"):
            assert self.sumo_pages.my_profile_page._get_my_profile_display_name_header_text(
            ) == original_username

        with check, allure.step("Verify that the newly set username is displayed inside the top "
                                "navbar"):
            assert self.sumo_pages.top_navbar._get_text_of_logged_in_username(
            ) == original_username

        with check, allure.step("Access a previously posted question and verify that the display "
                                "name has changed"):
            self.sumo_pages.my_profile_page._click_on_my_profile_questions_link()
            self.sumo_pages.my_questions_page._click_on_a_question_by_index(1)
            assert self.sumo_pages.question_page._get_question_author_name() == original_username

    # C1491017
    @pytest.mark.editUserProfileTests
    def test_username_with_invalid_symbols(self):
        with allure.step("Signing in with a non-admin user account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_12']
            ))

        with allure.step("Accessing the edit profile page"):
            self.sumo_pages.top_navbar._click_on_edit_profile_option()

        original_username = self.sumo_pages.edit_my_profile_page._get_username_input_field_value()

        with allure.step("Clearing the username input field and adding an invalid user"):
            self.sumo_pages.edit_my_profile_page._clear_username_field()
            profile_edit_data = super().profile_edit_test_data
            new_username = profile_edit_data["invalid_username_with_symbols"][
                "username_with_invalid_symbols"
            ]
            self.sumo_pages.edit_my_profile_page._send_text_to_username_field(new_username)

        with check, allure.step("Clicking on the 'Update My Profile' button and verifying that "
                                "the correct error message is displayed"):
            self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()
            assert self.sumo_pages.edit_my_profile_page._get_username_error_message_text(
            ) == EditMyProfilePageMessages.USERNAME_INPUT_ERROR_MESSAGE

        with allure.step("Accessing the Edit Profile page and verifying that the username was "
                         "not changed"):
            self.sumo_pages.top_navbar._click_on_view_profile_option()
            assert (self.sumo_pages.my_profile_page
                    ._get_my_profile_display_name_header_text() == original_username)

    #  C891530,  C2107866
    @pytest.mark.editUserProfileTests
    def test_cancel_profile_edit(self):
        with allure.step("Signing in with a normal user account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_12']
            ))

        with allure.step("Accessing the Edit My Profile page"):
            self.sumo_pages.top_navbar._click_on_edit_profile_option()

        original_values = self.sumo_pages.edit_my_profile_page._get_value_of_all_fields()

        with allure.step("Populating edit profile fields with data"):
            self.sumo_pages.edit_profile_flow.edit_profile_with_test_data()

        with allure.step("Clicking on the 'Cancel' button and verifying that we are on the same "
                         "page and all input field values were reverted back to original"):
            self.sumo_pages.edit_my_profile_page._click_cancel_button()
            assert self.sumo_pages.edit_my_profile_page._get_value_of_all_fields(
            ) == original_values

    #  C946232
    @pytest.mark.editUserProfileTests
    def test_manage_firefox_account_redirects_to_firefox_account_settings_page(self):
        with allure.step("Signing in with a non-admin user"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_12']
            ))

        with allure.step("Accessing the 'Edit my profile' page and clicking on the 'Manage "
                         "account' button"):
            self.sumo_pages.top_navbar._click_on_edit_profile_option()
            self.sumo_pages.edit_my_profile_page._click_manage_firefox_account_button()

        with allure.step("Verifying that the user was redirected to the Mozilla account settings "
                         "page in a new tab"):
            with self.page.context.expect_page() as tab:
                fxa_page = tab.value
            assert FxAPageMessages.ACCOUNT_SETTINGS_URL in fxa_page.url

    #  C1491461
    @pytest.mark.editUserProfileTests
    def test_duplicate_usernames_are_not_allowed(self):
        with allure.step("Signing in with a non-admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_12']
            ))

        original_username = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        with allure.step("Clicking on the 'edit profile' option"):
            self.sumo_pages.top_navbar._click_on_edit_profile_option()

        with allure.step("Clearing the username input field and adding an existing username "
                         "to it"):
            self.sumo_pages.edit_my_profile_page._clear_username_field()
            self.sumo_pages.edit_my_profile_page._send_text_to_username_field(
                super().username_extraction_from_email(
                    super().user_secrets_accounts["TEST_ACCOUNT_MESSAGE_6"]
                )
            )
            self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()

        with check, allure.step("Verify that the error message is displayed under the username "
                                "input field and is the correct one"):
            assert self.sumo_pages.edit_my_profile_page._get_username_error_message_text(
            ) == EditMyProfilePageMessages.DUPLICATE_USERNAME_ERROR_MESSAGE

        with check, allure.step("Verifying that the username displayed inside the top navbar is "
                                "the correct one"):
            assert self.sumo_pages.top_navbar._get_text_of_logged_in_username(
            ) == original_username

        with allure.step("Accessing the my profile page and verifying that the username "
                         "displayed inside the page is the correct one"):
            self.sumo_pages.top_navbar._click_on_view_profile_option()
            assert self.sumo_pages.my_profile_page._get_my_profile_display_name_header_text(
            ) == original_username

    #  C1491462
    @pytest.mark.editUserProfileTests
    def test_profile_username_field_cannot_be_left_empty(self):
        with allure.step("Signing in with a non-admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_12']
            ))

        original_username = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        with allure.step("Accessing the Edit My Profile page and clearing the username input "
                         "field"):
            self.sumo_pages.top_navbar._click_on_edit_profile_option()
            self.sumo_pages.edit_my_profile_page._clear_username_field()
            self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()

        with check, allure.step("Verifying that we are still on the edit profile page"):
            assert self.get_page_url() == EditMyProfilePageMessages.STAGE_EDIT_MY_PROFILE_URL

        with allure.step("Verifying that the displayed username inside the top navbar is the "
                         "original one"):
            assert self.sumo_pages.top_navbar._get_text_of_logged_in_username(
            ) == original_username

        with allure.step("Accessing the my profile page and verifying that the username is the "
                         "original one"):
            self.sumo_pages.user_navbar._click_on_my_profile_option()
            assert self.sumo_pages.my_profile_page._get_my_profile_display_name_header_text(
            ) == original_username

    # C1491018, C891531,C1491021
    @pytest.mark.editUserProfileTests
    def test_username_can_contain_uppercase_and_lowercase_letters(self):
        with allure.step("Signing in with a non-admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_MESSAGE_4']
            ))

        original_username = self.sumo_pages.top_navbar._get_text_of_logged_in_username()
        new_username = super().profile_edit_test_data["uppercase_lowercase_valid_username"][
            "uppercase_lowercase_username"
        ]

        with allure.step("Accessing the edit my profile page and updating the username field to "
                         "contain uppercase and lowercase characters"):
            self.sumo_pages.top_navbar._click_on_edit_profile_option()
            self.sumo_pages.edit_my_profile_page._clear_username_field()
            self.sumo_pages.edit_my_profile_page._send_text_to_username_field(new_username)
            self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()

        with allure.step("Verifying that the username displayed inside the top-navbar updates "
                         "successfully"):
            assert self.sumo_pages.top_navbar._get_text_of_logged_in_username() == new_username

        with allure.step("Verifying that the username displayed inside the my profile section is "
                         "the correct one"):
            assert self.sumo_pages.my_profile_page._get_my_profile_display_name_header_text(
            ) == new_username

        with allure.step("Reverting the username back to the original one"):
            self.sumo_pages.top_navbar._click_on_edit_profile_option()
            self.sumo_pages.edit_my_profile_page._clear_username_field()
            self.sumo_pages.edit_my_profile_page._send_text_to_username_field(original_username)
            self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()

    #  C1491463, C1491464
    @pytest.mark.editUserProfileTests
    def test_display_name_replaces_the_username_text(self):
        with allure.step("Signing in with a non-admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_MESSAGE_1']
            ))

        original_username = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        if self.requested_browser == "chrome":
            new_display_name = super().profile_edit_test_data["valid_user_edit"][
                "display_name_chrome"
            ]
        elif self.requested_browser == "firefox":
            new_display_name = super().profile_edit_test_data["valid_user_edit"][
                "display_name_firefox"
            ]

        with allure.step("Accessing the edit profile page and adding a new display name"):
            self.sumo_pages.top_navbar._click_on_edit_profile_option()
            self.sumo_pages.edit_my_profile_page._clear_display_name_field()
            self.sumo_pages.edit_my_profile_page._send_text_to_display_name_field(new_display_name)
            self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()

        with allure.step("Verifying that the top navbar username updates with the display name"):
            assert self.sumo_pages.top_navbar._get_text_of_logged_in_username() == new_display_name

        with allure.step(f"Verifying that the 'My profile' display name contains "
                         f"{new_display_name}"):
            assert self.sumo_pages.my_profile_page._get_my_profile_display_name_header_text(
            ) == f"{new_display_name} ({original_username})"

        with allure.step("Reverting back and deleting the display name"):
            self.sumo_pages.top_navbar._click_on_edit_profile_option()
            self.sumo_pages.edit_my_profile_page._clear_display_name_field()
            self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()

        with allure.step(f"Verifying that the displayed name inside the top navbar is reverted "
                         f"back to {original_username}"):
            assert self.sumo_pages.top_navbar._get_text_of_logged_in_username(
            ) == original_username

        with allure.step("Verifying that the displayed name inside the main profile page is "
                         "reverted back to the username"):
            assert self.sumo_pages.my_profile_page._get_my_profile_display_name_header_text(
            ) == original_username

    # This needs update. No longer fails due to:
    # https://github.com/mozilla/sumo/issues/1345
    @pytest.mark.skip
    def test_biography_field_accepts_html_tags(self):
        with allure.step("Signing in with a non-admin user account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))

        with allure.step("Accessing the edit profile page via top-navbar and adding data inside "
                         "the biography field"):
            self.sumo_pages.top_navbar._click_on_edit_profile_option()
            self.sumo_pages.edit_my_profile_page._clear_biography_textarea_field()
            html_test_data = super().profile_edit_test_data
            self.sumo_pages.edit_my_profile_page._send_text_to_biography_field(
                html_test_data["biography_field_with_html_data"]["biography_html_data"]
            )
            self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()

    #  C2107899, C2107899
    @pytest.mark.editUserProfileTests
    def test_make_my_email_address_visible_checkbox_checked(self):
        logged_in_email = super().user_secrets_accounts["TEST_ACCOUNT_12"]

        with allure.step("Signing in with a non-admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))

        username_one = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        with allure.step("Accessing the 'Edit My Profile' page and checking the 'make email "
                         "visible checkbox'"):
            self.sumo_pages.top_navbar._click_on_edit_profile_option()
            if not self.sumo_pages.edit_my_profile_page._is_make_email_visible_checkbox_selected():
                self.sumo_pages.edit_my_profile_page._click_make_email_visible_checkbox()
                self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()

        with check, allure.step("Returning to My Profile page and verifying that the email is "
                                "displayed"):
            self.sumo_pages.top_navbar._click_on_view_profile_option()
            assert self.sumo_pages.my_profile_page._get_text_of_publicly_displayed_username(
            ) == logged_in_email

        with allure.step("Signing in with a different user"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_13"]
            ))

        with check, allure.step("Accessing the previous user profile and verifying that the email"
                                " address is displayed"):
            self.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(username_one))
            assert self.sumo_pages.my_profile_page._get_text_of_publicly_displayed_username(
            ) == logged_in_email

        with allure.step("Signing out"):
            self.delete_cookies()

        with allure.step("Accessing the previous user profile and verifying that the email "
                         "address is not displayed to signed out users"):
            # This also needs an update
            self.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(username_one))
            expect(
                self.sumo_pages.my_profile_page._publicly_displayed_email_element()
            ).to_be_hidden()

    #  C2107899
    @pytest.mark.editUserProfileTests
    def test_make_my_email_address_visible_checkbox_unchecked(self):
        with allure.step("Signing in with a non-admin user account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))

        username_one = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        with allure.step("Accessing the 'Edit My Profile' page and unchecking the make email "
                         "visible checkbox"):
            self.sumo_pages.top_navbar._click_on_edit_profile_option()
            if self.sumo_pages.edit_my_profile_page._is_make_email_visible_checkbox_selected():
                self.sumo_pages.edit_my_profile_page._click_make_email_visible_checkbox()
                self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()

        with allure.step("Returning to My Profile page and verifying that the email is not "
                         "displayed"):
            self.sumo_pages.user_navbar._click_on_my_profile_option()
            expect(
                self.sumo_pages.my_profile_page._publicly_displayed_email_element()
            ).to_be_hidden()

        with allure.step("Signing in with a different non-admin user"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_13"]
            ))

        with allure.step("Accessing the previous user profile and verifying that the email "
                         "address is not displayed"):
            # This also needs an update
            self.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(username_one))
            expect(
                self.sumo_pages.my_profile_page._publicly_displayed_email_element()
            ).to_be_hidden()

    # C2107900, C2107900
    @pytest.mark.editUserProfileTests
    def test_website_information_is_displayed(self):
        with allure.step("Signing in with a non-admin user"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))

        username_one = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        with allure.step("Accessing the 'Edit My Profile' page and updating the website field"):
            self.sumo_pages.top_navbar._click_on_edit_profile_option()
            website_field_test_data = super().profile_edit_test_data["valid_user_edit"]["website"]
            self.sumo_pages.edit_my_profile_page._clear_website_field()
            self.sumo_pages.edit_my_profile_page._send_text_to_website_field(
                website_field_test_data)
            self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()

        with check, allure.step("Verify that the correct website is displayed"):
            assert self.sumo_pages.my_profile_page._get_my_profile_website_text(
            ) == website_field_test_data

        with allure.step("Signing in with a different non-admin user"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_13"]
            ))
        with check, allure.step("Verifying that the correct website information is displayed for "
                                "the first user"):
            self.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(username_one))
            assert self.sumo_pages.my_profile_page._get_my_profile_website_text(
            ) == website_field_test_data

        with check, allure.step("Clicking on the website and verifying that the user is "
                                "redirected to the correct page"):
            self.sumo_pages.my_profile_page._click_on_my_website_link()
            assert website_field_test_data in self.get_page_url()

        with check, allure.step("Navigating back to the SUMO page, signing out and verifying "
                                "that the correct website is displayed for the first user"):
            self.navigate_back()
            self.delete_cookies()
            self.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(username_one))
            assert self.sumo_pages.my_profile_page._get_my_profile_website_text(
            ) == website_field_test_data

        with check, allure.step("Clicking on the website and verifying that the user is "
                                "redirected to the correct page"):
            self.sumo_pages.my_profile_page._click_on_my_website_link()
            assert website_field_test_data in self.get_page_url()

        with allure.step("Navigating back to the SUMO page and clearing the website field"):
            self.navigate_back()
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))
            self.sumo_pages.top_navbar._click_on_edit_profile_option()
            self.sumo_pages.edit_my_profile_page._clear_website_field()
            self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()

    # C2107901, C2107901
    @pytest.mark.editUserProfileTests
    def test_twitter_information_is_displayed(self):
        with allure.step("Signing in with a non-admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))

        username_one = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        with allure.step("Accessing the Edit My Profile' page, clearing and adding data inside "
                         "the twitter input field"):
            self.sumo_pages.top_navbar._click_on_edit_profile_option()
            twitter_field_test_data = super().profile_edit_test_data["valid_user_edit"][
                "twitter_username"
            ]
            self.sumo_pages.edit_my_profile_page._clear_twitter_field()
            self.sumo_pages.edit_my_profile_page._send_text_to_twitter_username_field(
                twitter_field_test_data
            )
            self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()

        with check, allure.step("Navigating back to the My Profile page and verify that the "
                                "correct twitter is displayed"):
            self.sumo_pages.top_navbar._click_on_view_profile_option()
            assert self.sumo_pages.my_profile_page._get_my_profile_twitter_text(
            ) == twitter_field_test_data

        with check, allure.step("Signing in with a different user and verifying that the correct "
                                "website information is displayed for the first user"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_13"]
            ))
            self.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(username_one))
            assert self.sumo_pages.my_profile_page._get_my_profile_twitter_text(
            ) == twitter_field_test_data

        with allure.step("Clicking on the twitter link and verifying that the user is redirected "
                         "correctly"):
            self.sumo_pages.my_profile_page._click_on_twitter_link()
            assert (MyProfileMessages.TWITTER_REDIRECT_LINK + twitter_field_test_data in self.
                    get_page_url())

        with check, allure.step("Navigating back to the SUMO page, signing out, accessing the "
                                "profile and verifying that the twitter information is displayed"):
            self.navigate_back()
            self.delete_cookies()
            self.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(username_one))
            assert self.sumo_pages.my_profile_page._get_my_profile_twitter_text(
            ) == twitter_field_test_data

        with check, allure.step("Clicking on the twitter link and verifying that the user is "
                                "redirected correctly"):
            self.sumo_pages.my_profile_page._click_on_twitter_link()
            assert (MyProfileMessages.TWITTER_REDIRECT_LINK + twitter_field_test_data in self.
                    get_page_url())

        with allure.step("Navigating back to the SUMO page and clearing the twitter input field "
                         "changes"):
            self.navigate_back()
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))
            self.sumo_pages.top_navbar._click_on_edit_profile_option()
            self.sumo_pages.edit_my_profile_page._clear_twitter_field()
            self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()

    # C2107903, C2107903
    @pytest.mark.editUserProfileTests
    def test_community_portal_username_is_displayed(self):
        with allure.step("Signing in with a non-admin user account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))

        username_one = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        with allure.step("Accessing the 'Edit My Profile' page, clearing and adding data inside "
                         "the 'Community Portal' input field"):
            self.sumo_pages.top_navbar._click_on_edit_profile_option()
            community_portal_field_test_data = super().profile_edit_test_data["valid_user_edit"][
                "community_portal_username"
            ]
            self.sumo_pages.edit_my_profile_page._clear_community_portal_field()
            self.sumo_pages.edit_my_profile_page._send_text_to_community_portal_field(
                community_portal_field_test_data
            )
            self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()

        with check, allure.step("Navigating back to the My Profile page and verify that the "
                                "correct Community portal information is displayed"):
            self.sumo_pages.top_navbar._click_on_view_profile_option()
            assert self.sumo_pages.my_profile_page._get_my_profile_community_portal_text(
            ) == community_portal_field_test_data

        with check, allure.step("Signing in with a different user and verifying that the correct "
                                "community portal information is displayed for the first user"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_13"]
            ))
            self.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(username_one))
            assert self.sumo_pages.my_profile_page._get_my_profile_community_portal_text(
            ) == community_portal_field_test_data

        with check, allure.step("Clicking on the community portal link and verifying that the "
                                "user is redirected correctly"):
            self.sumo_pages.my_profile_page._click_on_community_portal_link()
            assert MyProfileMessages.COMMUNITY_PORTAL_LINK in self.get_page_url()

        with check, allure.step("Navigating back to the SUMO page, signing out, accessing the "
                                "profile and verifying that the community portal information is "
                                "displayed"):
            self.navigate_back()
            self.delete_cookies()
            self.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(username_one))
            assert self.sumo_pages.my_profile_page._get_my_profile_community_portal_text(
            ) == community_portal_field_test_data

        with check, allure.step("Clicking on the community portal link and verifying that the "
                                "user is redirected correctly"):
            self.sumo_pages.my_profile_page._click_on_community_portal_link()
            assert MyProfileMessages.COMMUNITY_PORTAL_LINK in self.get_page_url()

        with allure.step("Navigating back to the SUMO page, and clearing the community portal "
                         "field changes"):
            self.navigate_back()
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))
            self.sumo_pages.top_navbar._click_on_edit_profile_option()
            self.sumo_pages.edit_my_profile_page._clear_community_portal_field()
            self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()

    # C2107902,C2107902
    @pytest.mark.editUserProfileTests
    def test_people_directory_information_is_displayed(self):
        with allure.step("Signing in with a non-admin user"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))

        username_one = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        with allure.step("Accessing the 'Edit My Profile' page, clearing and adding data inside "
                         "the 'People Directory' input field"):
            self.sumo_pages.top_navbar._click_on_edit_profile_option()
            people_directory_field_test_data = super().profile_edit_test_data["valid_user_edit"][
                "people_directory_username"
            ]
            self.sumo_pages.edit_my_profile_page._clear_people_directory_field()
            self.sumo_pages.edit_my_profile_page._send_text_to_people_directory_username(
                people_directory_field_test_data
            )
            self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()

        with check, allure.step("Navigating back to the My Profile page and verify that the "
                                "correct People Directory information is displayed"):
            self.sumo_pages.top_navbar._click_on_view_profile_option()
            assert self.sumo_pages.my_profile_page._get_my_profile_people_directory_text(
            ) == people_directory_field_test_data

        with check, allure.step("Signing in with a different user and verifying that the correct "
                                "people directory information is displayed for the first user"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_13"]
            ))
            self.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(username_one))
            assert self.sumo_pages.my_profile_page._get_my_profile_people_directory_text(
            ) == people_directory_field_test_data

        with check, allure.step("Signing out, accessing the profile and verifying that the "
                                "people directory information is displayed"):
            self.delete_cookies()
            self.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(username_one))
            assert self.sumo_pages.my_profile_page._get_my_profile_people_directory_text(
            ) == people_directory_field_test_data

        with allure.step("Clearing the people directory field changes"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))
            self.sumo_pages.top_navbar._click_on_edit_profile_option()
            self.sumo_pages.edit_my_profile_page._clear_people_directory_field()
            self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()

    # C2107933, C2107933
    @pytest.mark.editUserProfileTests
    def test_matrix_information_is_displayed(self):
        with allure.step("Signing in with a non-admin user account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))

        username_one = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        with allure.step("Accessing the 'Edit My Profile' page, clearing and adding data inside "
                         "the Matrix input field"):
            self.sumo_pages.top_navbar._click_on_edit_profile_option()
            matrix_field_test_data = super().profile_edit_test_data["valid_user_edit"][
                "matrix_nickname"
            ]
            self.sumo_pages.edit_my_profile_page._clear_matrix_field()
            self.sumo_pages.edit_my_profile_page._send_text_to_matrix_nickname(
                matrix_field_test_data)
            self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()

        with check, allure.step("Navigating back to the My Profile page and verify that the "
                                "correct Matrix information is displayed"):
            self.sumo_pages.top_navbar._click_on_view_profile_option()
            assert (matrix_field_test_data in self.sumo_pages.
                    my_profile_page._get_my_profile_matrix_text())

        with check, allure.step("Signing in with a different user and verifying that the correct "
                                "Matrix information is displayed for the first user"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_13"]
            ))
            self.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(username_one))
            assert (matrix_field_test_data in self.sumo_pages.
                    my_profile_page._get_my_profile_matrix_text())

        with check, allure.step("Signing out, accessing the profile and verifying that the "
                                "Matrix information is displayed"):
            self.delete_cookies()
            self.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(username_one))
            assert (matrix_field_test_data in self.sumo_pages.
                    my_profile_page._get_my_profile_matrix_text())

        with allure.step("Clearing the Matrix field changes"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))

            self.sumo_pages.top_navbar._click_on_edit_profile_option()
            self.sumo_pages.edit_my_profile_page._clear_matrix_field()
            self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()

    # C2107934, C2107934
    @pytest.mark.editUserProfileTests
    def test_country_location_information_is_displayed(self):
        with allure.step("Signing in with a non-admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))

        username_one = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        with allure.step("Accessing the 'Edit My Profile' page, clearing and adding data inside "
                         "the country input field"):
            self.sumo_pages.top_navbar._click_on_edit_profile_option()
            country_field_test_data_code = super().profile_edit_test_data["valid_user_edit"][
                "country_code"
            ]
            country_field_test_data_value = super().profile_edit_test_data["valid_user_edit"][
                "country_value"
            ]
            self.sumo_pages.edit_my_profile_page._clear_country_dropdown_field()
            self.sumo_pages.edit_my_profile_page._select_country_dropdown_option_by_value(
                country_field_test_data_code
            )
            self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()

        with check, allure.step("Verify that the correct Country information is displayed"):
            assert (country_field_test_data_value in self.sumo_pages.
                    my_profile_page._get_text_of_profile_subheading_location())

        with check, allure.step("Signing in with a different user and verifying that the correct "
                                "Country information is displayed for the first user"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_13"]
            ))
            self.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(username_one))
            assert (country_field_test_data_value in self.sumo_pages.
                    my_profile_page._get_text_of_profile_subheading_location())

        with check, allure.step("Signing out, accessing the profile and verifying that the "
                                "Country information is displayed"):
            self.delete_cookies()
            self.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(username_one))
            assert (country_field_test_data_value in self.sumo_pages.
                    my_profile_page._get_text_of_profile_subheading_location())

        with allure.step("Clearing the Country field changes"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))

            self.sumo_pages.top_navbar._click_on_edit_profile_option()
            self.sumo_pages.edit_my_profile_page._clear_country_dropdown_field()
            self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()

    # C2107935, C2107935
    @pytest.mark.editUserProfileTests
    def test_city_location_information_is_displayed(self):
        with allure.step("Signing in with a non-admin user account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))

        username_one = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        with allure.step("Accessing the 'Edit' My profile page, clearing and adding data inside "
                         "the City input field"):
            self.sumo_pages.top_navbar._click_on_edit_profile_option()
            city_field_test_data_value = super().profile_edit_test_data["valid_user_edit"]["city"]
            self.sumo_pages.edit_my_profile_page._clear_city_field()
            self.sumo_pages.edit_my_profile_page._sent_text_to_city_field(
                city_field_test_data_value)
            self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()

        with check, allure.step("Verify that the correct City information is displayed"):
            assert (city_field_test_data_value in self.sumo_pages.
                    my_profile_page._get_text_of_profile_subheading_location())

        with check, allure.step("Signing in with a different user and verifying that the correct "
                                "City information is displayed for the first user"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_13"]
            ))
            self.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(username_one))
            assert (city_field_test_data_value in self.sumo_pages.
                    my_profile_page._get_text_of_profile_subheading_location())

        with check, allure.step("Signing out, accessing the profile and verifying that the City "
                                "information is displayed"):
            self.delete_cookies()
            self.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(username_one))
            assert (city_field_test_data_value in self.sumo_pages.my_profile_page.
                    _get_text_of_profile_subheading_location())

        with allure.step("Clearing the City field changes"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))
            self.sumo_pages.top_navbar._click_on_edit_profile_option()
            self.sumo_pages.edit_my_profile_page._clear_city_field()
            self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()

    # C2107938, C2107938
    @pytest.mark.editUserProfileTests
    def test_involved_since_information_is_displayed(self):
        with allure.step("Signing in with a non-admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))

        username_one = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        with allure.step("Accessing the 'Edit My Profile' page, clearing and adding data inside "
                         "the involved since input fields"):
            self.sumo_pages.top_navbar._click_on_edit_profile_option()
            involved_since_month_number_test_data = (super(
            ).profile_edit_test_data["valid_user_edit"]["involved_from_month_number"])
            involved_since_month_test_data_value = (
                super().profile_edit_test_data["valid_user_edit"]["involved_from_month_value"])
            involved_since_year_test_data_value = (super(
            ).profile_edit_test_data["valid_user_edit"]["involved_from_year"])
            self.sumo_pages.edit_my_profile_page._clear_involved_from_month_select_field()
            self.sumo_pages.edit_my_profile_page._clear_involved_from_year_select_field()
            self.sumo_pages.edit_my_profile_page._select_involved_from_month_option_by_value(
                involved_since_month_number_test_data
            )
            self.sumo_pages.edit_my_profile_page._select_involved_from_year_option_by_value(
                involved_since_year_test_data_value
            )
            self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()

        with check, allure.step("Verify that the correct involved from information is displayed"):
            assert (involved_since_month_test_data_value and involved_since_year_test_data_value in
                    self.sumo_pages.my_profile_page._get_my_contributed_from_text())

        with check, allure.step("Signing in with a different user and verifying that the correct "
                                "involved from information is displayed for the first user"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_13"]
            ))
            self.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(username_one))
            assert (involved_since_month_test_data_value and involved_since_year_test_data_value in
                    self.sumo_pages.my_profile_page._get_my_contributed_from_text())

        with check, allure.step("Signing out, accessing the profile and verifying that the "
                                "involved from information is displayed"):
            self.delete_cookies()
            self.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(username_one))
            assert (involved_since_month_test_data_value and involved_since_year_test_data_value in
                    self.sumo_pages.my_profile_page._get_my_contributed_from_text())

        with allure.step("Clearing the involved from field changes"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))
            self.sumo_pages.top_navbar._click_on_edit_profile_option()
            self.sumo_pages.edit_my_profile_page._clear_involved_from_month_select_field()
            self.sumo_pages.edit_my_profile_page._clear_involved_from_year_select_field()
            self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()

    # C2087552, C2108840
    @pytest.mark.editUserProfileTests
    def test_edit_user_profile_button_is_not_displayed_for_non_admin_users(self):
        target_username = self.remove_character_from_string(
            super().username_extraction_from_email(
                super().user_special_chars
            ),
            "*",
        )

        with allure.step("Accessing a user profile while not being signed in to SUMO"):
            self.navigate_to_link(
                MyProfileMessages.get_my_profile_stage_url(target_username)
            )

        with allure.step("Verifying that the 'Edit user profile' option is not displayed"):
            expect(
                self.sumo_pages.my_profile_page._edit_user_profile_option_element()
            ).to_be_hidden()

        with allure.step("Navigating to the profile edit link directly and verifying that the "
                         "user is redirected to the auth page"):
            self.navigate_to_link(
                EditMyProfilePageMessages.get_url_of_other_profile_edit_page(target_username)
            )
            assert (
                self.sumo_pages.auth_page._is_continue_with_firefox_button_displayed()
            ), "The auth page is not displayed! It should be!"
            expect(
                self.sumo_pages.edit_my_profile_page._is_my_profile_edit_form_displayed()
            ).to_be_hidden()

        with allure.step("Signing in with another non-admin account and accessing another user "
                         "account"):
            self.sumo_pages.top_navbar._click_on_sumo_nav_logo()
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))
            self.navigate_to_link(
                MyProfileMessages.get_my_profile_stage_url(target_username)
            )

        with allure.step("Verifying that the 'Edit user profile' option is not displayed"):
            expect(
                self.sumo_pages.my_profile_page._edit_user_profile_option_element()
            ).to_be_hidden()

        with check, allure.step("Navigating to the profile edit link directly, verifying that "
                                "the correct message is displayed and that the edit form is not "
                                "displayed"):
            self.navigate_to_link(
                EditMyProfilePageMessages.get_url_of_other_profile_edit_page(target_username)
            )
            assert self.sumo_pages.edit_my_profile_page._get_access_denied_header_text(
            ) == EditMyProfilePageMessages.PROFILE_ACCESS_DENIED_HEADING
            assert self.sumo_pages.edit_my_profile_page._get_access_denied_subheading_text(
            ) == EditMyProfilePageMessages.PROFILE_ACCESS_DENIED_SUBHEADING
            expect(
                self.sumo_pages.edit_my_profile_page._is_my_profile_edit_form_displayed()
            ).to_be_hidden()

    # C2108839
    @pytest.mark.editUserProfileTests
    def test_report_user_is_displayed_and_accessible_for_signed_in_users_only(self):
        with allure.step("Signing in with a non-admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))

        target_username = self.remove_character_from_string(
            super().username_extraction_from_email(
                super().user_special_chars
            ),
            "*",
        )
        with allure.step("Accessing another user profile and verifying that the 'Report Abuse' "
                         "option is displayed"):
            self.navigate_to_link(
                MyProfileMessages.get_my_profile_stage_url(target_username)
            )
            expect(
                self.sumo_pages.my_profile_page._is_report_user_option_displayed()
            ).to_be_visible()

        with allure.step("Clicking on the 'Report Abuse' option and verifying that the report "
                         "abuse panel is displayed"):
            self.sumo_pages.my_profile_page._click_on_report_abuse_option()
            expect(
                self.sumo_pages.my_profile_page._is_report_abuse_panel_displayed()
            ).to_be_visible()

        with allure.step("Closing the report abuse panel and verifying that the report user "
                         "panel is no longer displayed"):
            self.sumo_pages.my_profile_page._click_on_report_abuse_close_button()
            expect(
                self.sumo_pages.my_profile_page._is_report_abuse_panel_displayed()
            ).to_be_hidden()

        with allure.step("Signing out and verifying that the 'Report Abuse' option is not "
                         "displayed on user profiles"):
            self.delete_cookies()
            self.navigate_to_link(
                MyProfileMessages.get_my_profile_stage_url(target_username)
            )
            expect(
                self.sumo_pages.my_profile_page._is_report_user_option_displayed()
            ).to_be_hidden()

    # C2108841
    @pytest.mark.editUserProfileTests
    def test_private_message_button_redirects_non_signed_in_users_to_the_fxa_login_flow(self):
        target_username = self.remove_character_from_string(
            super().username_extraction_from_email(
                super().user_special_chars
            ),
            "*",
        )

        with allure.step("Accessing a user profile"):
            self.navigate_to_link(
                MyProfileMessages.get_my_profile_stage_url(target_username)
            )

        with allure.step("Clicking on the 'Private Message' button and verifying that the "
                         "non-signed in user is redirected to the fxa page"):
            self.sumo_pages.my_profile_page._click_on_private_message_button()
            assert (
                self.sumo_pages.auth_page._is_continue_with_firefox_button_displayed()
            ), "The auth page is not displayed! It should be!"

    # C916055, C916054
    @pytest.mark.editUserProfileTests
    def test_deactivate_this_user_buttons_are_displayed_only_for_admin_users(self):
        target_username = self.remove_character_from_string(
            super().username_extraction_from_email(
                super().user_special_chars
            ),
            "*",
        )
        with allure.step("Navigating ot a user profile while not signed in with a user"):
            self.navigate_to_link(
                MyProfileMessages.get_my_profile_stage_url(target_username)
            )

        with allure.step("Verifying that the deactivate user buttons are not displayed"):
            expect(
                self.sumo_pages.my_profile_page._is_deactivate_this_user_button_displayed()
            ).to_be_hidden()

            expect(
                self.sumo_pages.my_profile_page._deactivate_user_and_mark_content_as_spam_button()
            ).to_be_hidden()

        with allure.step("Signing in with a non-admin account"):
            self.sumo_pages.top_navbar._click_on_sumo_nav_logo()
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))

        with allure.step("Accessing another user profile and verifying that the deactivate "
                         "buttons are not displayed"):
            self.navigate_to_link(
                MyProfileMessages.get_my_profile_stage_url(target_username)
            )
            expect(
                self.sumo_pages.my_profile_page._is_deactivate_this_user_button_displayed()
            ).to_be_hidden()
            expect(
                self.sumo_pages.my_profile_page._deactivate_user_and_mark_content_as_spam_button()
            ).to_be_hidden()

        with allure.step("Signing in with an admin account"):
            self.sumo_pages.top_navbar._click_on_sumo_nav_logo()
            self.delete_cookies()
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Accessing another user profile and verifying that the deactivate user "
                         "buttons are displayed"):
            self.navigate_to_link(
                MyProfileMessages.get_my_profile_stage_url(target_username)
            )
            expect(
                self.sumo_pages.my_profile_page._is_deactivate_this_user_button_displayed()
            ).to_be_visible()
            expect(
                self.sumo_pages.my_profile_page._deactivate_user_and_mark_content_as_spam_button()
            ).to_be_visible()
