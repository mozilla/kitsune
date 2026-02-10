import datetime
import allure
import pytest
import pytz
from playwright.sync_api import Page, expect
from pytest_check import check

from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.auth_pages_messages.fxa_page_messages import FxAPageMessages
from playwright_tests.messages.my_profile_pages_messages.edit_my_profile_page_messages import (
    EditMyProfilePageMessages,
)
from playwright_tests.messages.my_profile_pages_messages.my_profile_page_messages import (
    MyProfileMessages,
)
from playwright_tests.pages.sumo_pages import SumoPages


def _submit_firefox_question(utilities: Utilities, sumo_pages: SumoPages) -> dict:
    """Navigate to the Firefox AAQ form and submit a standard question."""
    firefox_data = utilities.aaq_question_test_data["valid_firefox_question"]
    utilities.navigate_to_link(utilities.aaq_question_test_data["products_aaq_url"]["Firefox"])
    return sumo_pages.aaq_flow.submit_an_aaq_question(
        subject=firefox_data["subject"],
        topic_name=firefox_data["topic_value"],
        body=firefox_data["question_body"],
    )


# C891529
@pytest.mark.editUserProfileTests
def test_username_field_is_automatically_populated(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()

    with allure.step(f"Signing in with {test_user['username']} user account and navigating to the "
                     f"'Edit Profile' page"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.top_navbar.click_on_edit_profile_option()

    with allure.step("Verifying that username field is automatically populated with the correct "
                     "data"):
        assert (sumo_pages.edit_my_profile_page.get_username_input_field_value(
        ) == sumo_pages.top_navbar.get_text_of_logged_in_username())


# C1491017, C1491019
@pytest.mark.editUserProfileTests
def test_edit_profile_field_validation_with_symbols(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Posting a freemium question to the Firefox forum"):
        article_details = _submit_firefox_question(utilities, sumo_pages)

    usernames = utilities.profile_edit_test_data["valid_user_edit_with_symbols"]
    with allure.step("Navigating to the profile edit page"):
        sumo_pages.top_navbar.click_on_edit_profile_option()

    for value in usernames.values():
        with allure.step("Clearing the username, display name fields and inserting the new one"):
            sumo_pages.edit_my_profile_page.clear_username_field()
            sumo_pages.edit_my_profile_page.clear_display_name_field()
        sumo_pages.edit_my_profile_page.send_text_to_username_field(value)

        with allure.step("Clicking on the 'Update My Profile' button"):
            sumo_pages.edit_my_profile_page.click_update_my_profile_button(
                expected_locator=sumo_pages.my_profile_page.display_name_by_username(value)
            )

        with check, allure.step("Verify that the newly set username is successfully applied to the"
                                " my profile section"):
            assert sumo_pages.my_profile_page.get_my_profile_display_name_header_text() == value

        with check, allure.step("Verify that the newly set username is displayed inside the top"
                                " navbar"):
            assert sumo_pages.top_navbar.get_text_of_logged_in_username() == value

        with check, allure.step("Access a previously posted question and verify that the display"
                                " name has changed"):
            utilities.navigate_to_link(article_details["question_page_url"])
            assert sumo_pages.question_page.get_question_author_name() == value
            sumo_pages.top_navbar.click_on_edit_profile_option()

    with allure.step("Going back to the my profile page and reverting the username back to the "
                     "original one"):
        sumo_pages.edit_my_profile_page.clear_username_field()
        sumo_pages.edit_my_profile_page.send_text_to_username_field(test_user["username"])
        sumo_pages.edit_my_profile_page.click_update_my_profile_button(
            expected_url=MyProfileMessages.get_my_profile_stage_url(test_user["username"])
        )

    with check, allure.step("Verifying that the username was updated back to the original one"):
        assert (sumo_pages.my_profile_page.
                get_my_profile_display_name_header_text() == test_user["username"])

    with check, allure.step("Verify that the newly set username is displayed inside the top"
                            " navbar"):
        assert sumo_pages.top_navbar.get_text_of_logged_in_username() == test_user["username"]

    with allure.step("Access a previously posted question and verify that the display name has "
                     "changed"):
        utilities.navigate_to_link(article_details["question_page_url"])
        assert sumo_pages.question_page.get_question_author_name() == test_user["username"]


# C1491017, C1491019
@pytest.mark.editUserProfileTests
def test_username_with_invalid_symbols(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Accessing the edit profile page"):
        sumo_pages.top_navbar.click_on_edit_profile_option()

    original_username = sumo_pages.edit_my_profile_page.get_username_input_field_value()
    usernames = utilities.profile_edit_test_data["invalid_username_with_symbols"]

    for value in usernames.values():
        with allure.step("Navigating to the profile edit page"):
            sumo_pages.top_navbar.click_on_edit_profile_option()

        with allure.step("Clearing the username input field and adding an invalid user"):
            sumo_pages.edit_my_profile_page.clear_username_field()
            sumo_pages.edit_my_profile_page.clear_display_name_field()
            sumo_pages.edit_my_profile_page.send_text_to_username_field(value)

        with check, allure.step("Clicking on the 'Update My Profile' button and verifying that"
                                " the correct error message is displayed"):
            sumo_pages.edit_my_profile_page.click_update_my_profile_button()
            assert (sumo_pages.edit_my_profile_page.
                    get_username_error_message_text() == EditMyProfilePageMessages.
                    USERNAME_INPUT_ERROR_MESSAGE)

        with allure.step("Accessing the Edit Profile page and verifying that the username was not "
                         "changed"):
            sumo_pages.top_navbar.click_on_view_profile_option()
            assert (sumo_pages.my_profile_page.
                    get_my_profile_display_name_header_text() == original_username)


#  C891530,  C2107866
@pytest.mark.editUserProfileTests
def test_cancel_profile_edit(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Accessing the Edit My Profile page"):
        sumo_pages.top_navbar.click_on_edit_profile_option()

    original_values = sumo_pages.edit_my_profile_page.get_value_of_all_fields()

    with allure.step("Populating edit profile fields with data"):
        sumo_pages.edit_profile_flow.edit_profile_with_test_data()

    with allure.step("Clicking on the 'Cancel' button and verifying that we are on the same "
                     "page and all input field values were reverted back to original"):
        sumo_pages.edit_my_profile_page.click_cancel_button()
        assert sumo_pages.edit_my_profile_page.get_value_of_all_fields() == original_values


#  C946232
@pytest.mark.editUserProfileTests
def test_manage_firefox_account_redirects_to_firefox_account_settings_page(page: Page,
                                                                           create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Accessing the 'Edit my profile' page and clicking on the 'Manage "
                     "account' button"):
        sumo_pages.top_navbar.click_on_edit_profile_option()
        sumo_pages.edit_my_profile_page.click_manage_firefox_account_button()

    with allure.step("Verifying that the user was redirected to the Mozilla account settings "
                     "page in a new tab"):
        with page.context.expect_page() as tab:
            fxa_page = tab.value
        assert FxAPageMessages.ACCOUNT_SETTINGS_URL in fxa_page.url


#  C1491461
@pytest.mark.smokeTest
@pytest.mark.editUserProfileTests
def test_duplicate_usernames_are_not_allowed(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    test_user_two = create_user_factory()

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Clicking on the 'edit profile' option"):
        sumo_pages.top_navbar.click_on_edit_profile_option()

    with allure.step("Clearing the username input field and adding an existing username to it"):
        sumo_pages.edit_my_profile_page.clear_username_field()
        sumo_pages.edit_my_profile_page.send_text_to_username_field(test_user_two["username"])
        sumo_pages.edit_my_profile_page.click_update_my_profile_button()

    with check, allure.step("Verify that the error message is displayed under the username input"
                            " field and is the correct one"):
        assert (sumo_pages.edit_my_profile_page.
                get_username_error_message_text() == EditMyProfilePageMessages.
                DUPLICATE_USERNAME_ERROR_MESSAGE)

    with check, allure.step("Verifying that the username displayed inside the top navbar is the"
                            " correct one"):
        assert sumo_pages.top_navbar.get_text_of_logged_in_username() == test_user["username"]

    with allure.step("Accessing the my profile page and verifying that the username "
                     "displayed inside the page is the correct one"):
        sumo_pages.top_navbar.click_on_view_profile_option()
        assert sumo_pages.my_profile_page.get_my_profile_display_name_header_text(
        ) == test_user["username"]


#  C1491462
@pytest.mark.smokeTest
@pytest.mark.editUserProfileTests
def test_profile_username_field_cannot_be_left_empty(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Accessing the Edit My Profile page and clearing the username input "
                     "field"):
        sumo_pages.top_navbar.click_on_edit_profile_option()
        sumo_pages.edit_my_profile_page.clear_username_field()
        sumo_pages.edit_my_profile_page.click_update_my_profile_button()

    with check, allure.step("Verifying that we are still on the edit profile page"):
        assert utilities.get_page_url() == EditMyProfilePageMessages.STAGE_EDIT_MY_PROFILE_URL

    with check, allure.step("Verifying that the displayed username inside the top navbar is the"
                            " original one"):
        assert sumo_pages.top_navbar.get_text_of_logged_in_username() == test_user["username"]

    with allure.step("Accessing the my profile page and verifying that the username is the "
                     "original one"):
        sumo_pages.user_navbar.click_on_my_profile_option()
        assert sumo_pages.my_profile_page.get_my_profile_display_name_header_text(
        ) == test_user["username"]


# C1491018, C891531,C1491021
@pytest.mark.editUserProfileTests
def test_username_can_contain_uppercase_and_lowercase_letters(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    new_username = utilities.profile_edit_test_data["uppercase_lowercase_valid_username"][
        "uppercase_lowercase_username"
    ]

    with allure.step("Accessing the edit my profile page and updating the username field to "
                     "contain uppercase and lowercase characters"):
        sumo_pages.top_navbar.click_on_edit_profile_option()
        sumo_pages.edit_my_profile_page.clear_username_field()
        sumo_pages.edit_my_profile_page.send_text_to_username_field(new_username)
        sumo_pages.edit_my_profile_page.click_update_my_profile_button(
            expected_url=MyProfileMessages.get_my_profile_stage_url(new_username)
        )

    with check, allure.step("Verifying that the username displayed inside the top-navbar updates "
                            "successfully"):
        assert sumo_pages.top_navbar.get_text_of_logged_in_username() == new_username

    with check, allure.step("Verifying that the username displayed inside the my profile section"
                            " is the correct one"):
        assert sumo_pages.my_profile_page.get_my_profile_display_name_header_text() == new_username

    with allure.step("Reverting the username back to the original one"):
        sumo_pages.top_navbar.click_on_edit_profile_option()
        sumo_pages.edit_my_profile_page.clear_username_field()
        sumo_pages.edit_my_profile_page.send_text_to_username_field(test_user["username"])
        sumo_pages.edit_my_profile_page.click_update_my_profile_button(
            expected_url=MyProfileMessages.get_my_profile_stage_url(test_user["username"])
        )


#  C1491463, C1491464, C2459032
@pytest.mark.editUserProfileTests
def test_display_name_replaces_the_username_text(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    new_display_name = utilities.profile_edit_test_data["valid_user_edit"]["display_name"] + "1"

    with allure.step("Accessing the edit profile page and adding a new display name"):
        sumo_pages.top_navbar.click_on_edit_profile_option()
        sumo_pages.edit_my_profile_page.clear_display_name_field()
        sumo_pages.edit_my_profile_page.send_text_to_display_name_field(new_display_name)
        sumo_pages.edit_my_profile_page.click_update_my_profile_button(
            expected_url=MyProfileMessages.get_my_profile_stage_url(test_user["username"])
        )

    with check, allure.step("Verifying that the top navbar username updates with the display "
                            "name"):
        assert sumo_pages.top_navbar.get_text_of_logged_in_username() == new_display_name

    with check, allure.step(f"Verifying that the 'My profile' display name contains "
                            f"{new_display_name}"):
        assert (sumo_pages.my_profile_page.
                get_my_profile_display_name_header_text() == f"{new_display_name} ("
                                                             f"{test_user['username']})")

    with allure.step("Reverting back and deleting the display name"):
        sumo_pages.top_navbar.click_on_edit_profile_option()
        sumo_pages.edit_my_profile_page.clear_display_name_field()
        sumo_pages.edit_my_profile_page.click_update_my_profile_button(
            expected_url=MyProfileMessages.get_my_profile_stage_url(test_user["username"])
        )

    with check, allure.step(f"Verifying that the displayed name inside the top navbar is reverted"
                            f" back to {test_user['username']}"):
        assert sumo_pages.top_navbar.get_text_of_logged_in_username() == test_user["username"]

    with allure.step("Verifying that the displayed name inside the main profile page is "
                     "reverted back to the username"):
        assert sumo_pages.my_profile_page.get_my_profile_display_name_header_text(
        ) == test_user["username"]


# C2107866, C2107867, C2107868
@pytest.mark.editUserProfileTests
def test_biography_field_accepts_html_tags(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Accessing the edit profile page via top-navbar and adding data inside "
                     "the biography field"):
        sumo_pages.top_navbar.click_on_edit_profile_option()
        sumo_pages.edit_my_profile_page.clear_biography_textarea_field()
        html_test_data = utilities.profile_edit_test_data
        sumo_pages.edit_my_profile_page.send_text_to_biography_field(
            html_test_data["valid_user_edit"]["biography"]
        )
        sumo_pages.edit_my_profile_page.click_update_my_profile_button(
            expected_url=MyProfileMessages.get_my_profile_stage_url(test_user["username"])
        )

    # Expected content
    expected_content = {
        "//section[@class='bio']//b": "What the",
        "//section[@class='bio']//blockquote": "Another test",
        "//section[@class='bio']//code": "host_ip = socket.gethostbyname(socket.gethostname()",
        "//section[@class='bio']//ul/li[1]": "Test",
        "//section[@class='bio']//ul/li[2]": "We",
        "//section[@class='bio']//ol/li/i": "www",
        "//section[@class='bio']//strong": "Emil",
        "//section[@class='bio']//abbr[@title='World Health Organization']": "WHO"
    }

    # Check the content under the HTML tags
    for selector, text in expected_content.items():
        expect(page.locator(selector)).to_have_text(text)

    # Ensure the link is parsed and displayed as a link
    expect(page.locator("//section[@class='bio']//a[@href='https://www.digi24.ro']")
           ).to_be_visible()

    # Ensure the <a> tag with 'Digi link' is displayed as text
    assert "<a href='https://www.digi24.ro'>Digi link</a>" in (
        sumo_pages.my_profile_page.get_my_profile_bio_text_paragraphs()
    )


#  T5697917, C2107899
@pytest.mark.editUserProfileTests
def test_email_visibility(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    staff_email = utilities.staff_user

    with allure.step("Signing in with the admin account"):
        utilities.start_existing_session(
            session_file_name=utilities.username_extraction_from_email(utilities.staff_user))
        staff_username = sumo_pages.top_navbar.get_text_of_logged_in_username()

    with allure.step("Accessing the 'Edit My Profile' page and checking the 'make email visible "
                     "checkbox'"):
        sumo_pages.top_navbar.click_on_edit_profile_option()
        if not sumo_pages.edit_my_profile_page.is_make_email_visible_checkbox_selected():
            sumo_pages.edit_my_profile_page.click_make_email_visible_checkbox(check=True)
            sumo_pages.edit_my_profile_page.click_update_my_profile_button(
                expected_url=MyProfileMessages.get_my_profile_stage_url(staff_username)
            )
        else:
            sumo_pages.top_navbar.click_on_view_profile_option()

    with check, allure.step("Verifying that the email is displayed"):
        assert sumo_pages.my_profile_page.get_text_of_publicly_displayed_username() == staff_email

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with check, allure.step("Verifying that the email address is displayed"):
        assert sumo_pages.my_profile_page.get_text_of_publicly_displayed_username() == staff_email

    with allure.step("Signing out"):
        utilities.delete_cookies()

    with allure.step("Verifying that the email address is not displayed to signed out users"):
        expect(sumo_pages.my_profile_page.displayed_email_address).to_be_hidden()

    with allure.step("Accessing the 'Edit My Profile' page and unchecking the make email "
                     "visible checkbox"):
        utilities.start_existing_session(
            session_file_name=utilities.username_extraction_from_email(utilities.staff_user))

        sumo_pages.top_navbar.click_on_edit_profile_option()
        if sumo_pages.edit_my_profile_page.is_make_email_visible_checkbox_selected():
            sumo_pages.edit_my_profile_page.click_make_email_visible_checkbox(check=False)
            sumo_pages.edit_my_profile_page.click_update_my_profile_button(
                expected_url=MyProfileMessages.get_my_profile_stage_url(staff_username)
            )

    with check, allure.step("Verifying that the email is not displayed"):
        expect(sumo_pages.my_profile_page.displayed_email_address).to_be_hidden()

    with allure.step("Signing in with a different non-admin user"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Accessing the previous user profile and verifying that the email "
                     "address is not displayed"):
        expect(sumo_pages.my_profile_page.displayed_email_address).to_be_hidden()


# T5697918, T5697919, T5697921, T5697920, T5697922, T5697923, T5697924, T5697925
@pytest.mark.editUserProfileTests
def test_profile_information(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    test_user_two = create_user_factory()

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    sumo_pages.top_navbar.click_on_edit_profile_option()
    profile_info = sumo_pages.edit_profile_flow.edit_profile_with_test_data(
        info_only=True, submit_change=True,
        expected_url=MyProfileMessages.get_my_profile_stage_url(test_user["username"]))

    profile_info_keys = [
        "website", "twitter", "community_portal", "people_directory", "matrix_nickname",
        "country", "city", "involved_from_month", "involved_from_year"
    ]

    profile_info_getters = {
        "website": sumo_pages.my_profile_page.get_my_profile_website_text,
        "twitter": sumo_pages.my_profile_page.get_my_profile_twitter_text,
        "community_portal": sumo_pages.my_profile_page.get_my_profile_community_portal_text,
        "people_directory": sumo_pages.my_profile_page.get_my_profile_people_directory_text,
        "matrix_nickname": sumo_pages.my_profile_page.get_my_profile_matrix_text,
        "country": sumo_pages.my_profile_page.get_my_profile_location_text,
        "city": sumo_pages.my_profile_page.get_my_profile_location_text,
        "involved_from_month": sumo_pages.my_profile_page.get_my_contributed_from_text,
        "involved_from_year": sumo_pages.my_profile_page.get_my_contributed_from_text,
    }

    with check, allure.step("Verifying profile info as logged-in user"):
        utilities.start_existing_session(cookies=test_user_two)
        displayed_values = {
            key: getter()
            for key, getter in profile_info_getters.items()
        }

        for key in profile_info_keys:
            assert profile_info[key] in displayed_values[key], \
                f"Incorrect value for '{key}' when logged in."

    with check, allure.step("Verifying profile info after logout"):
        utilities.delete_cookies()

        displayed_values = {
            key: getter()
            for key, getter in profile_info_getters.items()
        }

        for key in profile_info_keys:
            assert profile_info[key] in displayed_values[key], \
                f"Incorrect value for '{key}' when logged out."


# T5697906, T5697929
@pytest.mark.smokeTest
@pytest.mark.editUserProfileTests
def test_edit_user_profile_button_is_not_displayed_for_non_admin_users(page: Page,
                                                                       create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    test_user_two = create_user_factory()

    with allure.step("Accessing a user profile while not being signed in to SUMO"):
        utilities.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(
            test_user["username"]))

    with check, allure.step("Verifying that the 'Edit user profile' option is not displayed"):
        expect(sumo_pages.my_profile_page.edit_user_profile_option).to_be_hidden()

    with check, allure.step("Navigating to the profile edit link directly and verifying that the"
                            " user is redirected to the auth page"):
        utilities.navigate_to_link(
            EditMyProfilePageMessages.get_url_of_other_profile_edit_page(test_user["username"])
        )
        assert sumo_pages.auth_page.is_continue_with_firefox_button_displayed()
        expect(sumo_pages.edit_my_profile_page.edit_my_profile_edit_input_form).to_be_hidden()

    with allure.step(f"Signing in with {test_user_two['username']} user account and accessing "
                     f"another user account"):
        sumo_pages.top_navbar.click_on_sumo_nav_logo()
        utilities.start_existing_session(cookies=test_user_two)
        utilities.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(
            test_user["username"]))

    with check, allure.step("Verifying that the 'Edit user profile' option is not displayed"):
        expect(sumo_pages.my_profile_page.edit_user_profile_option).to_be_hidden()

    with allure.step("Navigating to the profile edit link directly, verifying that the correct"
                     " message is displayed and that the edit form is not displayed"):
        utilities.navigate_to_link(
            EditMyProfilePageMessages.get_url_of_other_profile_edit_page(test_user["username"])
        )
        assert (sumo_pages.edit_my_profile_page.
                get_access_denied_header_text() == EditMyProfilePageMessages.
                PROFILE_ACCESS_DENIED_HEADING)
        assert (sumo_pages.edit_my_profile_page.
                get_access_denied_subheading_text() == EditMyProfilePageMessages.
                PROFILE_ACCESS_DENIED_SUBHEADING)
        expect(sumo_pages.edit_my_profile_page.edit_my_profile_edit_input_form).to_be_hidden()


# T5697928
@pytest.mark.smokeTest
@pytest.mark.editUserProfileTests
def test_report_user_is_displayed_and_accessible_for_signed_in_users_only(page: Page,
                                                                          create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    test_user_two = create_user_factory()

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with check, allure.step("Accessing another user profile and verifying that the 'Report Abuse' "
                            "option is displayed"):
        utilities.navigate_to_link(
            MyProfileMessages.get_my_profile_stage_url(test_user_two["username"])
        )
        expect(sumo_pages.my_profile_page.report_abuse_profile_option).to_be_visible()

    with check, allure.step("Clicking on the 'Report Abuse' option and verifying that the report "
                            "abuse panel is displayed"):
        sumo_pages.my_profile_page.click_on_report_abuse_option()
        expect(sumo_pages.my_profile_page.report_abuse_panel).to_be_visible()

    with check, allure.step("Closing the report abuse panel and verifying that the report user "
                            "panel is no longer displayed"):
        sumo_pages.my_profile_page.click_on_report_abuse_close_button()
        expect(sumo_pages.my_profile_page.report_abuse_panel).to_be_hidden()

    with allure.step("Signing out and verifying that the 'Report Abuse' option is not "
                     "displayed on user profiles"):
        utilities.delete_cookies()
        expect(sumo_pages.my_profile_page.report_abuse_profile_option).to_be_hidden()


# T5697930
@pytest.mark.editUserProfileTests
def test_private_message_button_redirects_signed_out_users_to_fxa_login_flow(page: Page,
                                                                             create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()

    with allure.step("Accessing a user profile"):
        utilities.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(
            test_user["username"]))

    with allure.step("Clicking on the 'Private Message' button and verifying that the non-signed "
                     "in user is redirected to the fxa page"):
        sumo_pages.my_profile_page.click_on_private_message_button()
        assert sumo_pages.auth_page.is_continue_with_firefox_button_displayed()


# C916055, C916054
@pytest.mark.smokeTest
@pytest.mark.editUserProfileTests
def test_deactivate_this_user_buttons_are_displayed_only_for_admin_users(page: Page,
                                                                         create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    test_user_two = create_user_factory()
    test_user_with_deactivation_perms = create_user_factory(permissions=["deactivate_users"])

    with allure.step("Navigating ot a user profile while not signed in with a user"):
        utilities.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(
            test_user["username"]))

    with check, allure.step("Verifying that the deactivate user buttons are not displayed"):
        expect(sumo_pages.my_profile_page.deactivate_this_user_button).to_be_hidden()
        expect(sumo_pages.my_profile_page.deactivate_this_user_and_mark_all_content_as_spam
               ).to_be_hidden()

    with allure.step(f"Signing in with {test_user_two['username']} user account"):
        utilities.start_existing_session(cookies=test_user_two)

    with check, allure.step("Accessing another user profile and verifying that the deactivate "
                            "buttons are not displayed"):
        expect(sumo_pages.my_profile_page.deactivate_this_user_button).to_be_hidden()
        expect(sumo_pages.my_profile_page.deactivate_this_user_and_mark_all_content_as_spam
               ).to_be_hidden()

    with allure.step("Signing in with a user that has user deactivation permissions "
                     f"({test_user_with_deactivation_perms['username']})"):
        utilities.start_existing_session(cookies=test_user_with_deactivation_perms)

    with allure.step("Accessing another user profile and verifying that the deactivate user "
                     "buttons are displayed"):
        utilities.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(
            test_user["username"]))
        expect(sumo_pages.my_profile_page.deactivate_this_user_button).to_be_visible()
        expect(sumo_pages.my_profile_page.deactivate_this_user_and_mark_all_content_as_spam
               ).to_be_visible()


# C2189013
@pytest.mark.editUserProfileTests
def test_timezone_preference_change(page: Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory()

    def normalize_time(timezone: str) -> str:
        """"
            Normalize the time format:
            - Remove the leading 0 from the hour except for "00"
            - Treat "00:00 PM" as "00:00 AM"

            Args:
                timezone (str): The timezone to normalize the time for
        """
        current_time = datetime.datetime.now(pytz.timezone(timezone)).strftime("%I:%M %p")
        return "00:00 AM" if current_time in ["00:00 PM", "00:00 AM"] else (
            f"Today at {current_time.lstrip('0')}")

    def assert_reply_time_matches_timezone(reply_id: int, timezone: str):
        """Post a reply, then verify its displayed time matches the expected timezone."""
        displayed = sumo_pages.question_page.get_time_from_reply(reply_id)
        displayed_clean = displayed.replace("\u202f", " ").replace("Today at ", "")
        expected_clean = normalize_time(timezone).replace("Today at ", "")
        time_difference = abs(
            (datetime.datetime.strptime(displayed_clean, "%I:%M %p")
             - datetime.datetime.strptime(expected_clean, "%I:%M %p")).total_seconds() / 60
        )
        assert time_difference <= 1, (
            f"Time difference is more than 1 minute: {time_difference} minutes"
        )

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Posting a freemium question to the Firefox forum"):
        article_details = _submit_firefox_question(utilities, sumo_pages)

    with allure.step("Accessing the 'Edit My Profile' page and changing the timezone to "
                     "'Europe/Bucharest'"):
        sumo_pages.top_navbar.click_on_edit_profile_option()
        sumo_pages.edit_my_profile_page.select_timezone_dropdown_option_by_value(
            "Europe/Bucharest")
        sumo_pages.edit_my_profile_page.click_update_my_profile_button(
            expected_url=MyProfileMessages.get_my_profile_stage_url(test_user["username"]))

    with check, allure.step("Posting a new reply to the question and verifying that the correct"
                            " time is displayed respecting the chosen timezone"):
        utilities.navigate_to_link(article_details["question_page_url"])
        reply_id = sumo_pages.aaq_flow.post_question_reply_flow(
            repliant_username=test_user["username"], reply="Test test test")
        assert_reply_time_matches_timezone(reply_id, "Europe/Bucharest")

    with allure.step("Accessing the 'Edit My Profile' page and changing the timezone "
                     "to 'US / Central'"):
        sumo_pages.top_navbar.click_on_edit_profile_option()
        sumo_pages.edit_my_profile_page.select_timezone_dropdown_option_by_value(
            "US/Central")
        sumo_pages.edit_my_profile_page.click_update_my_profile_button(
            expected_url=MyProfileMessages.get_my_profile_stage_url(test_user["username"]))

    with allure.step("Posting a new reply to the question and verifying that the correct time is"
                     " displayed respecting the chosen timezone"):
        utilities.navigate_to_link(article_details["question_page_url"])
        reply_id = sumo_pages.aaq_flow.post_question_reply_flow(
            repliant_username=test_user["username"], reply="Test test test")
        assert_reply_time_matches_timezone(reply_id, "US/Central")

# C891532
@pytest.mark.editUserProfileTests
def test_close_account_and_delete_profile_information(page:Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory()

    with allure.step(f"Signing in with a test account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Navigating to the edit profile page and clicking on the 'Close account "
                     "button'"):
        sumo_pages.top_navbar.click_on_edit_profile_option()
        sumo_pages.edit_my_profile_page.click_close_account_option()

    with allure.step("Verifying that the 'Delete Your Account' button is disabled by default"):
        assert sumo_pages.edit_my_profile_page.is_delete_your_account_button_disabled()

    with allure.step("Adding a different code inside the input and verifying that the "
                     "'Delete Your Account' button is disabled"):
        sumo_pages.edit_my_profile_page.add_confirmation_code_to_close_account_modal(
            invalid_code=True)
        assert sumo_pages.edit_my_profile_page.is_delete_your_account_button_disabled()

    with allure.step("Clearing the confirmation code input field, adding the correct code inside "
                     "the input field and closing the modal"):
        sumo_pages.edit_my_profile_page.clear_confirmation_code_from_close_account_modal()
        sumo_pages.edit_my_profile_page.add_confirmation_code_to_close_account_modal()
        sumo_pages.edit_my_profile_page.click_on_close_modal_button()

    with allure.step("Refreshing the page and verifying that the user was not deleted"):
        utilities.refresh_page()
        assert sumo_pages.top_navbar.get_text_of_logged_in_username() == test_user["username"]

    with allure.step("Deleting the user via the 'Close account and delete all profile information'"
                     "modal"):
        sumo_pages.edit_profile_flow.close_account()
        assert utilities.get_page_url() == utilities.profile_edit_test_data["close_account_page"]
        assert sumo_pages.top_navbar.signin_signup_button.is_visible()
