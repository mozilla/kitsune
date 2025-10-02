import allure
import pytest
from playwright.sync_api import Page, expect
from pytest_check import check
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.mess_system_pages_messages.read_message_page_messages import \
    ReadMessagePageMessages
from playwright_tests.pages.sumo_pages import SumoPages


# C2939485
@pytest.mark.smokeTest
@pytest.mark.userDeletion
def test_deleted_user_is_displayed_in_both_inbox_and_outbox(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    test_user_two = create_user_factory()
    deleted_user_username = "deleted user"
    first_message_body = "Test " + utilities.generate_random_number(1, 1000)
    second_message_body = "Test " + utilities.generate_random_number(1, 1000)

    with allure.step("Signing in with the first test user and sending a message to the second "
                     "user"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.top_navbar.click_on_inbox_option()
        sumo_pages.inbox_page.click_on_new_message_button()
        sumo_pages.messaging_system_flow.complete_send_message_form_with_data(
            recipient_username=test_user_two["username"], message_body=first_message_body)

    with allure.step("Signing in with the second user and sending a message to the first user"):
        utilities.start_existing_session(cookies=test_user_two)
        sumo_pages.top_navbar.click_on_inbox_option()
        sumo_pages.mess_system_user_navbar.click_on_messaging_system_nav_new_message()
        sumo_pages.messaging_system_flow.complete_send_message_form_with_data(
            recipient_username=test_user["username"], message_body=second_message_body)

    with allure.step("Deleting the second user account"):
        sumo_pages.edit_profile_flow.close_account()

    with allure.step("Signing in with the first user and navigating to the inbox page"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.top_navbar.click_on_inbox_option()

    with check, allure.step("Verifying that sender of the message is the 'delete user'"):
        assert (sumo_pages.inbox_page.
                get_sender_by_excerpt(second_message_body) == deleted_user_username)

    with check, allure.step("Clicking on the message excerpt and verifying that the 'delete user "
                            "is successfully displayed as the message sender'"):
        sumo_pages.inbox_page.click_on_message_by_excerpt(second_message_body)
        assert (deleted_user_username in sumo_pages.inbox_page.
                get_the_deleted_user_message_sender_text())

    with check, allure.step("Verifying that the deleted user information text is successfully "
                            "displayed"):
        assert (sumo_pages.inbox_page.
                get_the_deleted_user_information_text() == ReadMessagePageMessages.
                DELETED_USER_INFO)

    with check, allure.step("Navigating to the outbox and verifying that the 'delete user' is the "
                            "recipient of the sent message"):
        utilities.wait_for_dom_to_load()
        sumo_pages.mess_system_user_navbar.click_on_messaging_system_nav_sent_messages()
        assert (sumo_pages.sent_message_page.
                get_deleted_user_recipient_based_on_excerpt(first_message_body
                                                            ) == deleted_user_username)

    with check, allure.step("Clicking on the message subject and verifying that the 'delete user'"
                            " is successfully displayed inside the TO field"):
        sumo_pages.sent_message_page.click_on_sent_message_subject(first_message_body)
        assert deleted_user_username in sumo_pages.sent_message_page.get_deleted_user()


# C2939485
@pytest.mark.userDeletion
def test_messages_cannot_be_sent_to_system_user(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    user = create_user_factory()

    with allure.step("Signing in with the test account and navigating to the new message page"):
        utilities.start_existing_session(cookies=user)
        sumo_pages.top_navbar.click_on_inbox_option()
        sumo_pages.mess_system_user_navbar.click_on_messaging_system_nav_new_message()

    with allure.step("Adding the system user inside the TO: field and verifying that the system "
                     "user is not returned"):
        sumo_pages.new_message_page.type_into_to_input_field(
            utilities.general_test_data["system_account_name"])
        expect(sumo_pages.new_message_page.get_no_user_message_locator()).to_be_visible(
            timeout=15000)
