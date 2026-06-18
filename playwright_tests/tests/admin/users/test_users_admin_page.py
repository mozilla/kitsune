import allure
import pytest
from playwright.sync_api import Page, expect
from pytest_check import check

from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.homepage_messages import HomepageMessages
from playwright_tests.messages.my_profile_pages_messages.my_profile_page_messages import \
    MyProfileMessages
from playwright_tests.pages.sumo_pages import SumoPages
from playwright_tests.tests.user_page_tests.test_my_questions import _submit_firefox_question


# C916054
@pytest.mark.userAdminPages
def test_users_can_be_deactivated(page:Page, restmail_test_account_creation,
                                  navigate_to_users_admin_page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    email, _, _ = restmail_test_account_creation()
    username = utilities.username_extraction_from_email(email)
    staff_user = utilities.username_extraction_from_email(utilities.staff_user)
    admin_page = navigate_to_users_admin_page(username)
    admin_pages = SumoPages(admin_page)
    admin_utilities = Utilities(admin_page)
    moderator_page = utilities.create_new_context_page()
    moderator_utilities = Utilities(moderator_page)
    moderator_pages = SumoPages(moderator_page)

    with allure.step("Signing in with an admin user account"):
        moderator_utilities.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL_EN_US)
        moderator_utilities.start_existing_session(session_file_name=staff_user)

    with allure.step("Submitting a question against the AAQ forum with the simple user"):
        question_info = _submit_firefox_question(utilities, sumo_pages)

    with allure.step("Navigating to the test user profile page"):
        moderator_utilities.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(username))

    with check, allure.step("Deactivating the user profile and verifying that the correct "
                            "deactivation status is displayed."):
        moderator_pages.my_profile_page.click_on_deactivate_this_user_button()
        expect(moderator_pages.my_profile_page.this_user_was_deactivated_message).to_have_text(
            MyProfileMessages.USER_DEACTIVATED_MESSAGE)

    with check, allure.step("Verifying that the question was not deleted"):
        moderator_utilities.navigate_to_link(question_info["question_page_url"])
        expect(moderator_pages.question_page.question_author).to_have_text(username)

    with check, allure.step("Verifying that the after a page refresh the deactivated user was "
                            "logged out"):
        utilities.refresh_page()
        expect(sumo_pages.top_navbar.signin_signup_button).to_be_visible()

    with check, allure.step("Trying to manually sign in and verifying that the user is unable "
                            "to and that the correct error message is displayed"):
        sumo_pages.top_navbar.click_on_sumo_nav_logo()
        sumo_pages.top_navbar.click_on_signin_signup_button()
        sumo_pages.auth_flow_page.login_with_existing_session()
        expect(sumo_pages.top_navbar.signin_signup_button).to_be_visible()
        expect(sumo_pages.homepage.user_notification).to_have_text(
            HomepageMessages.USER_DEACTIVATED_MESSAGE)

    with check, allure.step("Verifying that the is active checkbox is unchecked in admin"):
        admin_utilities.refresh_page()
        expect(admin_pages.admin_users_page.active_checkbox).not_to_be_checked()

    with allure.step("Checking the is active checkbox and saving the changes"):
        admin_pages.admin_users_page.active_checkbox.check()
        admin_pages.admin_users_page.click_on_save_changes_button()
        admin_page.close()

    with check, allure.step("Signing in with the test user and verify that the user successfully "
                            "logs in"):
        sumo_pages.top_navbar.click_on_sumo_nav_logo()
        sumo_pages.top_navbar.click_on_signin_signup_button()
        sumo_pages.auth_flow_page.login_with_existing_session()
        expect(sumo_pages.top_navbar.signed_in_username).to_have_text(username)
        expect(sumo_pages.homepage.user_notification).to_be_hidden()

    with allure.step("Navigating to the test user profile page and verifying that the "
                     "deactivation message is not displayed"):
        utilities.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(username))
        expect(sumo_pages.my_profile_page.this_user_was_deactivated_message).to_be_hidden()


# C916055
@pytest.mark.userAdminPages
def test_deactivation_via_deactivate_and_mark_content_as_spam(page: Page,
                                                              navigate_to_users_admin_page,
                                                              restmail_test_account_creation):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    email, _, _ = restmail_test_account_creation()
    username = utilities.username_extraction_from_email(email)
    staff_user = utilities.username_extraction_from_email(utilities.staff_user)
    admin_page = navigate_to_users_admin_page(username)
    admin_pages = SumoPages(admin_page)
    admin_utilities = Utilities(admin_page)
    moderator_page = utilities.create_new_context_page()
    moderator_utilities = Utilities(moderator_page)
    moderator_pages = SumoPages(moderator_page)

    with allure.step("Submitting a question against the AAQ forum with the simple user"):
        question_info = _submit_firefox_question(utilities, sumo_pages)

    with allure.step("Signing in with an admin user account"):
        moderator_utilities.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL_EN_US)
        moderator_utilities.start_existing_session(session_file_name=staff_user)

    with allure.step("Navigating to the test user profile page"):
        moderator_utilities.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(username))

    with check, allure.step("Deactivating the user profile via deactivate this user and mark "
                            "all content as spam button and verifying that the correct "
                            "deactivation status is displayed."):
        moderator_pages.my_profile_page.click_deactivate_this_user_and_mark_all_content_as_spam()
        expect(moderator_pages.my_profile_page.this_user_was_deactivated_message).to_have_text(
            MyProfileMessages.USER_DEACTIVATED_MESSAGE)

    with allure.step("Verifying that the question was marked as spam"):
        moderator_utilities.navigate_to_link(question_info["question_page_url"])
        expect(moderator_pages.question_page.marked_as_spam_banner).to_be_visible()

    with check, allure.step("Verifying that the after a page refresh the deactivated user was "
                            "logged out"):
        utilities.refresh_page()
        expect(sumo_pages.top_navbar.signin_signup_button).to_be_visible()

    with check, allure.step("Trying to manually sign in and verifying that the user is unable "
                            "to and that the correct error message is displayed"):
        sumo_pages.top_navbar.click_on_sumo_nav_logo()
        sumo_pages.top_navbar.click_on_signin_signup_button()
        sumo_pages.auth_flow_page.login_with_existing_session()
        expect(sumo_pages.top_navbar.signin_signup_button).to_be_visible()
        expect(sumo_pages.homepage.user_notification).to_have_text(
            HomepageMessages.USER_DEACTIVATED_MESSAGE)

    with check, allure.step("Verifying that the is active checkbox is unchecked in admin"):
        admin_utilities.refresh_page()
        expect(admin_pages.admin_users_page.active_checkbox).not_to_be_checked()

    with allure.step("Checking the is active checkbox and saving the changes"):
        admin_pages.admin_users_page.active_checkbox.check()
        admin_pages.admin_users_page.click_on_save_changes_button()
        admin_page.close()

    with check, allure.step("Signing in with the test user and verify that the user successfully "
                            "logs in"):
        sumo_pages.top_navbar.click_on_sumo_nav_logo()
        sumo_pages.top_navbar.click_on_signin_signup_button()
        sumo_pages.auth_flow_page.login_with_existing_session()
        expect(sumo_pages.top_navbar.signed_in_username).to_have_text(username)
        expect(sumo_pages.homepage.user_notification).to_be_hidden()

    with allure.step("Navigating to the test user profile page and verifying that the "
                     "deactivation message is not displayed"):
        utilities.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(username))
        expect(sumo_pages.my_profile_page.this_user_was_deactivated_message).to_be_hidden()

    with allure.step("Verifying that the question is still marked as spam"):
        moderator_utilities.refresh_page()
        expect(moderator_pages.question_page.marked_as_spam_banner).to_be_visible()


# C3293157
@pytest.mark.userAdminPages
def test_superusers_cannot_be_deactivated_via_ui(page: Page, navigate_to_users_admin_page,
                                                 create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    staff_user = utilities.username_extraction_from_email(utilities.staff_user)
    admin_page = navigate_to_users_admin_page(test_user["username"])
    admin_pages = SumoPages(admin_page)

    with allure.step("Making the newly created user a superuser"):
        admin_pages.admin_users_page.superuser_checkbox.check()
        admin_pages.admin_users_page.click_on_save_and_continue_editing_button()

    with allure.step("Signing in with the staff user"):
        utilities.start_existing_session(session_file_name=staff_user)

    with allure.step("Navigating to the superuser profile page and verifying that the user cannot "
                     "be deactivated via UI"):
        utilities.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(
            test_user["username"]))
        expect(sumo_pages.my_profile_page.deactivate_this_user_button).to_be_hidden()
        expect(sumo_pages.my_profile_page.deactivate_this_user_and_mark_all_content_as_spam
               ).to_be_hidden()

    with allure.step("Stripping the user from having superuser permissions"):
        admin_pages.admin_users_page.superuser_checkbox.uncheck()
        admin_pages.admin_users_page.click_on_save_and_continue_editing_button()
        admin_page.close()

    with allure.step("Verifying that the user can be deactivated"):
        utilities.refresh_page()
        expect(sumo_pages.my_profile_page.deactivate_this_user_button).to_be_visible()
        expect(sumo_pages.my_profile_page.deactivate_this_user_and_mark_all_content_as_spam
               ).to_be_visible()
        sumo_pages.my_profile_page.click_on_deactivate_this_user_button()
        expect(sumo_pages.my_profile_page.this_user_was_deactivated_message).to_have_text(
            MyProfileMessages.USER_DEACTIVATED_MESSAGE)
