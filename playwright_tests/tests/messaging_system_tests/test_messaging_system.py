import allure
import pytest
from pytest_check import check
from playwright.sync_api import expect, Page

from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.mess_system_pages_messages.inbox_page_messages import (
    InboxPageMessages)
from playwright_tests.messages.mess_system_pages_messages.new_message_page_messages import (
    NewMessagePageMessages)
from playwright_tests.messages.mess_system_pages_messages.sent_messages_page_messages import (
    SentMessagesPageMessages)
from playwright_tests.messages.my_profile_pages_messages.my_profile_page_messages import (
    MyProfileMessages)
from playwright_tests.pages.sumo_pages import SumoPages


# C891415
@pytest.mark.messagingSystem
def test_there_are_no_messages_here_text_is_displayed_when_no_messages_are_available(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with a non-admin user account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts['TEST_ACCOUNT_12']
        ))

    with allure.step("Navigating to the inbox page"):
        sumo_pages.top_navbar.click_on_inbox_option()

    if sumo_pages.inbox_page.are_inbox_messages_displayed():
        with allure.step("Clearing the inbox since there are some existing messages"):
            sumo_pages.inbox_page.delete_all_inbox_messages(
                expected_url=InboxPageMessages.INBOX_PAGE_STAGE_URL
            )

    with check, allure.step("Verifying that the correct message is displayed"):
        assert sumo_pages.inbox_page.get_text_of_inbox_no_message_header(
        ) == InboxPageMessages.NO_MESSAGES_IN_INBOX_TEXT

    with allure.step("Navigating to the 'Sent Messages' page"):
        sumo_pages.mess_system_user_navbar.click_on_messaging_system_nav_sent_messages()

    if sumo_pages.sent_message_page.are_sent_messages_displayed():
        with allure.step("Clearing sent messages list since there are some existing messages"):
            sumo_pages.sent_message_page.delete_all_displayed_sent_messages(
                expected_url=SentMessagesPageMessages.SENT_MESSAGES_PAGE_URL
            )

    with check, allure.step("Verifying that the correct page message is displayed"):
        assert sumo_pages.sent_message_page.get_sent_messages_no_message_text(
        ) == SentMessagesPageMessages.NO_MESSAGES_IN_SENT_MESSAGES_TEXT


# T5697913, C2706735
# This test needs to be updated to fetch the username from a different place
@pytest.mark.messagingSystem
def test_private_messages_can_be_sent_via_user_profiles(page: Page, is_firefox):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    message_body = "Test " + utilities.generate_random_number(1, 1000)
    user_two = utilities.username_extraction_from_email(
        utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_2"]
    )

    with allure.step("Signing in with a non-admin user account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_1"]
        ))

    sumo_pages.top_navbar.get_text_of_logged_in_username()

    with allure.step("Navigating to the profile page for user two"):
        utilities.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(username=user_two))

    with allure.step("Clicking on the 'Private Message button'"):
        sumo_pages.my_profile_page.click_on_private_message_button(
            expected_url=NewMessagePageMessages.NEW_MESSAGE_PAGE_STAGE_URL + f"?to={user_two}"
        )

    with allure.step("Verifying that the receiver is automatically added inside the 'To' "
                     "field"):
        # Firefox GH runner fails here. We are running this assertion only in Chrome for now
        if not is_firefox:
            assert sumo_pages.new_message_page.get_user_to_text() == user_two, (
                f"Incorrect 'To' receiver. Expected: {user_two}. "
                f"Received: {sumo_pages.new_message_page.get_user_to_text()}"
            )

    with allure.step("Sending a message to the user"):
        sumo_pages.messaging_system_flow.complete_send_message_form_with_data(
            message_body=message_body,
            expected_url=SentMessagesPageMessages.SENT_MESSAGES_PAGE_URL
        )

    with check, allure.step("Verifying that the correct message sent banner is displayed"):
        assert sumo_pages.inbox_page.get_text_inbox_page_message_banner_text(
        ) == InboxPageMessages.MESSAGE_SENT_BANNER_TEXT

    with allure.step("Clicking on the 'Sent Messages option"):
        sumo_pages.mess_system_user_navbar.click_on_messaging_system_nav_sent_messages()

    with allure.step("Verifying that the sent message is displayed"):
        expect(
            sumo_pages.sent_message_page.sent_messages_by_excerpt_locator(message_body)
        ).to_be_visible()

    with allure.step("Deleting the message from the sent messages page"):
        sumo_pages.messaging_system_flow.delete_message_flow(
            excerpt=message_body, from_sent_list=True,
            expected_url=SentMessagesPageMessages.SENT_MESSAGES_PAGE_URL
        )

    with check, allure.step("Verifying that the correct banner is displayed"):
        assert sumo_pages.sent_message_page.get_sent_messages_page_deleted_banner_text(
        ) == SentMessagesPageMessages.DELETE_MESSAGE_BANNER_TEXT

    with allure.step("Verifying that messages from user two are not displayed"):
        expect(sumo_pages.sent_message_page.sent_messages_by_excerpt_locator(message_body)
               ).to_be_hidden()

    with allure.step("Signing in with the user which received the message"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_2"]
        ))

    with allure.step("Accessing the Inbox section"):
        sumo_pages.top_navbar.click_on_inbox_option()

    with allure.step("Verifying that the inbox contains the previously sent messages"):
        expect(sumo_pages.inbox_page._inbox_message_based_on_excerpt(message_body)).to_be_visible()

    with allure.step("Fetching the unread messages count and verifying that the counter displays "
                     "the correct data"):
        unread_messages = len(sumo_pages.inbox_page.get_all_unread_messages())
        sumo_pages.top_navbar.mouse_over_profile_avatar()
        assert (unread_messages == sumo_pages.top_navbar.
                get_unread_message_notification_counter_value())

    with allure.step("Deleting the messages from the inbox section"):
        sumo_pages.messaging_system_flow.delete_message_flow(
            excerpt=message_body, from_inbox_list=True,
            expected_url=InboxPageMessages.INBOX_PAGE_STAGE_URL
        )

    with allure.step("Verifying that the messages are no longer displayed inside the inbox"):
        expect(sumo_pages.inbox_page._inbox_message_based_on_excerpt(excerpt=message_body)
               ).to_be_hidden()

    with check, allure.step("Verifying that the correct banner is displayed"):
        assert sumo_pages.sent_message_page.get_sent_messages_page_deleted_banner_text(
        ) == SentMessagesPageMessages.DELETE_MESSAGE_BANNER_TEXT


# C891419
@pytest.mark.messagingSystem
def test_private_message_can_be_sent_via_new_message_page(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    message_body = "Test " + utilities.generate_random_number(1, 1000)
    test_user = utilities.username_extraction_from_email(
        utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_4"]
    )

    with allure.step("Signing in with a non-admin account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_3"]
        ))

    sumo_pages.top_navbar.get_text_of_logged_in_username()

    with allure.step("Accessing the New Message page and sending a message to another user"):
        sumo_pages.top_navbar.click_on_inbox_option()
        sumo_pages.mess_system_user_navbar.click_on_messaging_system_nav_new_message()
        sumo_pages.messaging_system_flow.complete_send_message_form_with_data(
            recipient_username=test_user,
            message_body=message_body,
            expected_url=SentMessagesPageMessages.SENT_MESSAGES_PAGE_URL
        )

    with check, allure.step("Verifying that the correct banner is displayed"):
        assert sumo_pages.inbox_page.get_text_inbox_page_message_banner_text(
        ) == InboxPageMessages.MESSAGE_SENT_BANNER_TEXT

    with allure.step("Verifying that the sent message is displayed inside the sent messages "
                     "page"):
        sumo_pages.mess_system_user_navbar.click_on_messaging_system_nav_sent_messages()
        expect(sumo_pages.sent_message_page.sent_messages_by_excerpt_locator(message_body)
               ).to_be_visible()

    with allure.step("Clearing the sent messages list"):
        sumo_pages.messaging_system_flow.delete_message_flow(
            excerpt=message_body, from_sent_list=True,
            expected_url=SentMessagesPageMessages.SENT_MESSAGES_PAGE_URL
        )

    with allure.step("Signing in with the receiver account and verifying that the message is "
                     "displayed inside the inbox section"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_4"]
        ))
        sumo_pages.top_navbar.click_on_inbox_option()
        expect(sumo_pages.inbox_page._inbox_message_based_on_excerpt(message_body)
               ).to_be_visible()

    with allure.step("Clearing the inbox"):
        sumo_pages.messaging_system_flow.delete_message_flow(
            excerpt=message_body, from_inbox_list=True,
            expected_url=InboxPageMessages.INBOX_PAGE_STAGE_URL
        )


# C891412, C891413
@pytest.mark.messagingSystem
def test_navbar_options_redirect_to_the_correct_page_and_options_are_correctly_highlighted(
    page: Page
):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with a non-admin user account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

    with allure.step("Accessing the inbox section via the top-navbar"):
        sumo_pages.top_navbar.click_on_inbox_option()

    with allure.step("Verifying that we are on the correct page and the 'Inbox' navbar "
                     "option is highlighted"):
        expect(page).to_have_url(InboxPageMessages.INBOX_PAGE_STAGE_URL)
        expect(
            sumo_pages.mess_system_user_navbar.get_inbox_navbar_element()
        ).to_have_css("background-color", InboxPageMessages.NAVBAR_INBOX_SELECTED_BG_COLOR)

    with allure.step("Clicking on the sent messages navbar option"):
        sumo_pages.mess_system_user_navbar.click_on_messaging_system_nav_sent_messages()

    with allure.step("Verifying that we are on the correct page and the 'Sent Messages' "
                     "navbar option is highlighted"):
        expect(
            page
        ).to_have_url(SentMessagesPageMessages.SENT_MESSAGES_PAGE_URL)
        expect(
            sumo_pages.mess_system_user_navbar.get_sent_messages_navbar_element()
        ).to_have_css("background-color",
                      SentMessagesPageMessages.NAVBAR_SENT_MESSAGES_SELECTED_BG_COLOR)

    with allure.step("Clicking on the 'New message' navbar option"):
        sumo_pages.mess_system_user_navbar.click_on_messaging_system_nav_new_message()

    with allure.step("Verifying that we are on the correct page and the 'New Message' navbar "
                     "option is successfully highlighted"):
        expect(page).to_have_url(NewMessagePageMessages.NEW_MESSAGE_PAGE_STAGE_URL)
        expect(
            sumo_pages.mess_system_user_navbar.get_new_message_navbar_element()
        ).to_have_css("background-color",
                      NewMessagePageMessages.NAVBAR_NEW_MESSAGE_SELECTED_BG_COLOR)

    with allure.step("Clicking on the navbar inbox messaging system navbar option"):
        sumo_pages.mess_system_user_navbar.click_on_messaging_system_navbar_inbox()

    with allure.step("Verifying that we are on the correct page and the 'Inbox' navbar "
                     "option is highlighted"):
        expect(page).to_have_url(InboxPageMessages.INBOX_PAGE_STAGE_URL)
        expect(
            sumo_pages.mess_system_user_navbar.get_inbox_navbar_element()
        ).to_have_css("background-color", InboxPageMessages.NAVBAR_INBOX_SELECTED_BG_COLOR)


# C891416
@pytest.mark.messagingSystem
def test_new_message_field_validation(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    user_two = utilities.username_extraction_from_email(
        utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_1"]
    )

    with allure.step("Signing in with a non-admin user account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

    with allure.step("Accessing the New Message page"):
        sumo_pages.top_navbar.click_on_inbox_option()
        sumo_pages.mess_system_user_navbar.click_on_messaging_system_nav_new_message()

    with allure.step("Trying to submit the form without any data and verifying that we are "
                     "still on the 'New Message' page"):
        sumo_pages.messaging_system_flow.complete_send_message_form_with_data()
        expect(page).to_have_url(NewMessagePageMessages.NEW_MESSAGE_PAGE_STAGE_URL)

    with allure.step("Adding a recipient inside the 'To' field and trying to submit the form "
                     "without any message body"):
        sumo_pages.messaging_system_flow.complete_send_message_form_with_data(
            recipient_username=user_two)
        expect(page).to_have_url(NewMessagePageMessages.NEW_MESSAGE_PAGE_STAGE_URL)

    with check, allure.step("Verifying that the default remaining characters is the correct "
                            "one"):
        assert (sumo_pages.new_message_page.get_characters_remaining_text(
        ) in NewMessagePageMessages.NEW_MESSAGE_DEFAULT_REMAINING_CHARACTERS)

    with allure.step("Verifying that the characters remaining color is the expected one"):
        expect(
            sumo_pages.new_message_page.get_characters_remaining_text_element()
        ).to_have_css("color", NewMessagePageMessages.ENOUGH_CHARACTERS_REMAINING_COLOR)

    with allure.step("Adding 9990 characters inside the input field"):
        sumo_pages.new_message_page.fill_into_new_message_body_textarea(
            text=utilities.user_message_test_data["valid_user_message"][
                "9990_characters_long_message"
            ])

    with check, allure.step("Verifying that the correct remaining characters left message is "
                            "displayed"):
        assert sumo_pages.new_message_page.get_characters_remaining_text(
        ) in NewMessagePageMessages.TEN_CHARACTERS_REMAINING_MESSAGE

    with allure.step("Verifying that the characters remaining color is the expected one"):
        expect(sumo_pages.new_message_page.get_characters_remaining_text_element()
               ).to_have_css("color", NewMessagePageMessages.ENOUGH_CHARACTERS_REMAINING_COLOR)

    # elif self.browser == "firefox":
    #     check.equal(
    #         self.pages.new_message_page.get_characters_remaining_text_color(),
    #         NewMessagePageMessages.ENOUGH_CHARACTERS_REMAINING_COLOR_FIREFOX,
    #         f"Incorrect color displayed. "
    #         f"Expected: {NewMessagePageMessages.ENOUGH_CHARACTERS_REMAINING_COLOR_FIREFOX} "
    #         f"Received: {self.pages.new_message_page.get_characters_remaining_text_color()}",
    #     )

    with allure.step("Adding one character inside the textarea field"):
        sumo_pages.new_message_page.type_into_new_message_body_textarea(
            text=utilities.user_message_test_data["valid_user_message"]
            ["one_character_message"]
        )

    with check, allure.step("Verifying that the char remaining string is updated accordingly"):
        assert sumo_pages.new_message_page.get_characters_remaining_text(
        ) in NewMessagePageMessages.NINE_CHARACTERS_REMAINING_MESSAGE

    with allure.step("Verifying that the characters remaining color is the expected one"):
        expect(sumo_pages.new_message_page.get_characters_remaining_text_element()
               ).to_have_css("color", NewMessagePageMessages.NO_CHARACTERS_REMAINING_COLOR)

    # elif self.browser == "firefox":
    #     check.equal(
    #         self.pages.new_message_page.get_characters_remaining_text_color(),
    #         NewMessagePageMessages.NO_CHARACTERS_REMAINING_COLOR_FIREFOX,
    #         f"Incorrect color displayed. "
    #         f"Expected: {NewMessagePageMessages.NO_CHARACTERS_REMAINING_COLOR_FIREFOX} "
    #         f"Received: {self.pages.new_message_page.get_characters_remaining_text_color()}",
    #     )

    with allure.step("Adding 9 characters inside the textarea field"):
        sumo_pages.new_message_page.type_into_new_message_body_textarea(
            text=utilities.user_message_test_data["valid_user_message"]
            ["9_characters_message"]
        )

    with allure.step("Verifying that the char remaining string is updated accordingly"):
        expect(
            sumo_pages.new_message_page.get_characters_remaining_text_element()
        ).to_have_css("color", NewMessagePageMessages.NO_CHARACTERS_REMAINING_COLOR)

    # elif self.browser == "firefox":
    #     check.equal(
    #         self.pages.new_message_page.get_characters_remaining_text_color(),
    #         NewMessagePageMessages.NO_CHARACTERS_REMAINING_COLOR_FIREFOX,
    #         f"Incorrect color displayed. "
    #         f"Expected: {NewMessagePageMessages.NO_CHARACTERS_REMAINING_COLOR_FIREFOX} "
    #         f"Received: {self.pages.new_message_page.get_characters_remaining_text_color()}",
    #     )

    with allure.step("Verifying that the characters remaining color is the expected one"):
        expect(
            sumo_pages.new_message_page.get_characters_remaining_text_element()
        ).to_have_css("color", NewMessagePageMessages.NO_CHARACTERS_REMAINING_COLOR)

    # elif self.browser == "firefox":
    #     check.equal(
    #         self.pages.new_message_page.get_characters_remaining_text_color(),
    #         NewMessagePageMessages.NO_CHARACTERS_REMAINING_COLOR_FIREFOX,
    #         f"Incorrect color displayed. "
    #         f"Expected: {NewMessagePageMessages.NO_CHARACTERS_REMAINING_COLOR_FIREFOX} "
    #         f"Received: {self.pages.new_message_page.get_characters_remaining_text_color()}",
    #     )


# C891417
@pytest.mark.messagingSystem
def test_new_message_cancel_button(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    message_body = "Test " + utilities.generate_random_number(1, 1000)
    user_two = utilities.username_extraction_from_email(
        utilities.user_secrets_accounts["TEST_ACCOUNT_13"]
    )

    with allure.step("Signing in with a non-admin user account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

    sumo_pages.top_navbar.get_text_of_logged_in_username()

    with allure.step("Accessing the 'New Message' section"):
        sumo_pages.top_navbar.click_on_inbox_option()
        sumo_pages.mess_system_user_navbar.click_on_messaging_system_nav_new_message()

    with allure.step("Filling the new message form with data"):
        sumo_pages.messaging_system_flow.complete_send_message_form_with_data(
            recipient_username=user_two,
            message_body=message_body,
            submit_message=False
        )

    with allure.step("Clicking on the 'Cancel' button and verifying that the user is "
                     "redirected back to the inbox page"):
        sumo_pages.new_message_page.click_on_new_message_cancel_button()
        expect(
            sumo_pages.mess_system_user_navbar.get_inbox_navbar_element()
        ).to_have_css("background-color", InboxPageMessages.NAVBAR_INBOX_SELECTED_BG_COLOR)
        expect(page).to_have_url(InboxPageMessages.INBOX_PAGE_STAGE_URL)

    with allure.step("Navigating to the 'Sent Messages' page and verifying that the message "
                     "was not sent"):
        sumo_pages.mess_system_user_navbar.click_on_messaging_system_nav_sent_messages()
        expect(sumo_pages.sent_message_page.sent_messages_by_excerpt_locator(message_body)
               ).to_be_hidden()

    with allure.step("Signing out and signing in with the receiver account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_13"]
        ))

    with allure.step("Navigating to the receiver inbox and verifying that no message was "
                     "received"):
        sumo_pages.top_navbar.click_on_inbox_option()
        expect(sumo_pages.inbox_page._inbox_message_based_on_excerpt(message_body)).to_be_hidden()


# C2706741, C2706736, C2706740, C2706739, C2706735
@pytest.mark.messagingSystem
def test_messaging_system_unread_notification_after_message_deletion(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    content_first_message = "Test Test " + utilities.generate_random_number(1,100)
    content_second_message = "Test Test " + utilities.generate_random_number(1, 100)

    test_user = utilities.username_extraction_from_email(
        utilities.user_secrets_accounts["TEST_ACCOUNT_13"]
    )

    with allure.step("Signing in with an admin account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

    with allure.step("Accessing the inbox section and navigating to the new message page"):
        sumo_pages.top_navbar.click_on_inbox_option()
        sumo_pages.mess_system_user_navbar.click_on_messaging_system_nav_new_message()

    with allure.step("Sending the first message"):
        sumo_pages.messaging_system_flow.complete_send_message_form_with_data(
            recipient_username=test_user,
            message_body=content_first_message,
            expected_url=SentMessagesPageMessages.SENT_MESSAGES_PAGE_URL
        )

    sumo_pages.mess_system_user_navbar.click_on_messaging_system_nav_new_message()
    with allure.step("Sending the second message"):
        sumo_pages.messaging_system_flow.complete_send_message_form_with_data(
            recipient_username=test_user,
            message_body=content_second_message,
            expected_url=SentMessagesPageMessages.SENT_MESSAGES_PAGE_URL
        )

    with allure.step("Deleting sent messages"):
        sumo_pages.sent_message_page.delete_all_sent_messages_via_delete_selected_button(
            expected_url=SentMessagesPageMessages.SENT_MESSAGES_PAGE_URL
        )

    with allure.step("Signing in with the recipient"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_13"]
        ))

    with allure.step("Navigating to the inbox section"):
        sumo_pages.top_navbar.click_on_inbox_option()

    with allure.step("Verifying that the avatar notification and the new message counter is "
                     "correct"):
        inbox_messages_count = len(sumo_pages.inbox_page.get_all_unread_messages())
        sumo_pages.top_navbar.mouse_over_profile_avatar()
        assert (sumo_pages.top_navbar
                .get_unread_message_notification_counter_value() == inbox_messages_count)
        assert sumo_pages.top_navbar.is_unread_message_notification_displayed()

    with allure.step("Marking the first received message as read"):
        sumo_pages.inbox_page.check_a_particular_message(content_first_message)
        sumo_pages.inbox_page.click_on_inbox_mark_selected_as_read_button()

    with allure.step("Verifying that the message is successfully marked as read"):
        assert content_first_message in sumo_pages.inbox_page.get_all_read_messages_excerpt()

    with allure.step("Verifying that the new message notification counter resembles the unread "
                     "inbox message count"):
        inbox_messages_count = len(sumo_pages.inbox_page.get_all_unread_messages())
        sumo_pages.top_navbar.mouse_over_profile_avatar()
        assert (sumo_pages.top_navbar
                .get_unread_message_notification_counter_value() == inbox_messages_count)
        assert sumo_pages.top_navbar.is_unread_message_notification_displayed()

    with allure.step("Deleting the first message"):
        sumo_pages.messaging_system_flow.delete_message_flow(
            excerpt=content_first_message, from_inbox_list=True,
            expected_url=InboxPageMessages.INBOX_PAGE_STAGE_URL
        )

    with allure.step("Verifying that the new message notification counter resembles the unread "
                     "inbox message count"):
        inbox_messages_count = len(sumo_pages.inbox_page.get_all_unread_messages())
        sumo_pages.top_navbar.mouse_over_profile_avatar()
        assert (sumo_pages.top_navbar
                .get_unread_message_notification_counter_value() == inbox_messages_count)
        assert sumo_pages.top_navbar.is_unread_message_notification_displayed()

    with allure.step("Marking the second received message as read"):
        sumo_pages.inbox_page.check_a_particular_message(content_second_message)
        sumo_pages.inbox_page.click_on_inbox_mark_selected_as_read_button()

    with allure.step("Verifying that the new message notification counter resembles the unread "
                     "inbox message count"):
        inbox_messages_count = len(sumo_pages.inbox_page.get_all_unread_messages())
        sumo_pages.top_navbar.mouse_over_profile_avatar()
        if inbox_messages_count == 0:
            assert not sumo_pages.top_navbar.is_unread_message_notification_counter_visible()
            assert not sumo_pages.top_navbar.is_unread_message_notification_displayed()
        else:
            assert (sumo_pages.top_navbar
                    .get_unread_message_notification_counter_value() == inbox_messages_count)
            assert sumo_pages.top_navbar.is_unread_message_notification_displayed()

    with allure.step("Deleting the second received message"):
        sumo_pages.messaging_system_flow.delete_message_flow(
            excerpt=content_second_message, from_inbox_list=True,
            expected_url=InboxPageMessages.INBOX_PAGE_STAGE_URL
        )

    with allure.step("Verifying that the new message notification counter resembles the unread "
                     "inbox message count"):
        inbox_messages_count = len(sumo_pages.inbox_page.get_all_unread_messages())
        sumo_pages.top_navbar.mouse_over_profile_avatar()
        if inbox_messages_count == 0:
            assert not sumo_pages.top_navbar.is_unread_message_notification_counter_visible()
        else:
            assert (sumo_pages.top_navbar
                    .get_unread_message_notification_counter_value() == inbox_messages_count)


# C891418
@pytest.mark.messagingSystem
def test_new_message_preview(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = utilities.username_extraction_from_email(
        utilities.user_secrets_accounts["TEST_ACCOUNT_13"]
    )

    with allure.step("Signing in with a non-admin user account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_4"]
        ))

    username = sumo_pages.top_navbar.get_text_of_logged_in_username()

    with allure.step("Accessing the inbox section and navigating to the new message page"):
        sumo_pages.top_navbar.click_on_inbox_option()
        sumo_pages.mess_system_user_navbar.click_on_messaging_system_nav_new_message()

    with allure.step("Adding text inside the message content section"):
        sumo_pages.messaging_system_flow.complete_send_message_form_with_data(
            recipient_username=test_user,
            message_body=utilities.user_message_test_data["valid_user_message"]["message"],
            submit_message=False
        )

    with allure.step("Clicking on the 'Preview' button and verifying that the preview "
                     "section is successfully displayed"):
        sumo_pages.new_message_page.click_on_new_message_preview_button()
        expect(sumo_pages.new_message_page.message_preview_section_element()).to_be_visible()

    with check, allure.step("Verifying that all the preview items are displayed"):
        assert sumo_pages.new_message_page.get_text_of_test_data_first_paragraph_text(
        ) in NewMessagePageMessages.PREVIEW_MESSAGE_CONTENT_FIRST_PARAGRAPH_TEXT

        assert sumo_pages.new_message_page.get_text_of_test_data_first_p_strong_text(
        ) in NewMessagePageMessages.PREVIEW_MESSAGE_CONTENT_FIRST_PARAGRAPH_STRONG_TEXT

        assert sumo_pages.new_message_page.get_text_of_test_data_first_p_italic_text(
        ) in NewMessagePageMessages.PREVIEW_MESSAGE_CONTENT_FIRST_PARAGRAPH_ITALIC_TEXT

        numbered_list_items = [
            NewMessagePageMessages.PREVIEW_MESSAGE_OL_LI_NUMBER_ONE,
            NewMessagePageMessages.PREVIEW_MESSAGE_OL_LI_NUMBER_TWO,
            NewMessagePageMessages.PREVIEW_MESSAGE_OL_LI_NUMBER_THREE,
        ]

        bulleted_list_items = [
            NewMessagePageMessages.PREVIEW_MESSAGE_UL_LI_NUMBER_ONE,
            NewMessagePageMessages.PREVIEW_MESSAGE_UL_LI_NUMBER_TWO,
            NewMessagePageMessages.PREVIEW_MESSAGE_UL_LI_NUMBER_THREE,
        ]

        assert sumo_pages.new_message_page.get_text_of_numbered_list_items(
        ) == numbered_list_items

        assert sumo_pages.new_message_page.get_text_of_bulleted_list_items(
        ) == bulleted_list_items

        expect(sumo_pages.new_message_page.new_message_preview_external_link_test_data_element()
               ).to_be_visible()

        expect(sumo_pages.new_message_page.new_message_preview_internal_link_test_data_element()
               ).to_be_visible()

    with allure.step("Clicking on the internal link and verifying that the user is "
                     "redirected to the correct article"):
        sumo_pages.new_message_page.click_on_preview_internal_link()
        assert (
            sumo_pages.kb_article_page.get_text_of_article_title()
            == NewMessagePageMessages.PREVIEW_MESSAGE_INTERNAL_LINK_TITLE
        ), (
            f"Incorrect article title displayed! "
            f"Expected: {NewMessagePageMessages.PREVIEW_MESSAGE_INTERNAL_LINK_TITLE} "
            f"Received: {sumo_pages.kb_article_page.get_text_of_article_title()}"
        )

    with allure.step("Verifying that the message was no sent by checking the "
                     "'Sent Messages page'"):
        sumo_pages.top_navbar.click_on_inbox_option()
        sumo_pages.mess_system_user_navbar.click_on_messaging_system_nav_sent_messages()
        expect(sumo_pages.sent_message_page.sent_messages(username=test_user)).to_be_hidden()

    with allure.step("Signing in with the potential message receiver and verifying that no "
                     "message were received"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_13"]
        ))
        sumo_pages.top_navbar.click_on_inbox_option()
        expect(sumo_pages.inbox_page.inbox_message(username=username)
               ).to_be_hidden()


# C891421, C891424
@pytest.mark.messagingSystem
def test_messages_can_be_selected_and_deleted(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    message_body = "Test " + utilities.generate_random_number(1, 1000)
    test_user = utilities.username_extraction_from_email(
        utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_6"]
    )

    with allure.step("Signing in with a non-admin account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_5"]
        ))

    username_one = sumo_pages.top_navbar.get_text_of_logged_in_username()

    with allure.step("Accessing the 'New Message' page and sending a message to a different "
                     "user"):
        sumo_pages.top_navbar.click_on_inbox_option()
        sumo_pages.mess_system_user_navbar.click_on_messaging_system_nav_new_message()
        sumo_pages.messaging_system_flow.complete_send_message_form_with_data(
            recipient_username=test_user,
            message_body=message_body,
            expected_url=SentMessagesPageMessages.SENT_MESSAGES_PAGE_URL
        )

    with allure.step("Navigating to the sent messages page"):
        sumo_pages.mess_system_user_navbar.click_on_messaging_system_nav_sent_messages()

    with allure.step("Clicking on the 'Delete Selected' button"):
        sumo_pages.sent_message_page.click_on_delete_selected_button(
            expected_locator=(
                sumo_pages.sent_message_page.SENT_MESSAGE_PAGE_LOCATORS
                ["sent_messages_page_message_banner_text"])
        )

    with check, allure.step("Verifying that the correct message is displayed"):
        assert sumo_pages.sent_message_page.get_sent_messages_page_deleted_banner_text(
        ) in SentMessagesPageMessages.NO_MESSAGES_SELECTED_BANNER_TEXT

    with allure.step("Verifying that the message is still listed inside the sent messages "
                     "section"):
        expect(
            sumo_pages.sent_message_page.sent_messages_by_excerpt_locator(message_body)
        ).to_be_visible()

    with allure.step("Sending another message to self twice"):
        for i in range(2):
            sumo_pages.mess_system_user_navbar.click_on_messaging_system_nav_new_message()
            sumo_pages.messaging_system_flow.complete_send_message_form_with_data(
                recipient_username=username_one,
                message_body=message_body,
                expected_url=SentMessagesPageMessages.SENT_MESSAGES_PAGE_URL
            )

    with check, allure.step("Clicking on the 'delete selected' button while no messages is "
                            "selected and verifying that the correct banner is displayed"):
        sumo_pages.mess_system_user_navbar.click_on_messaging_system_navbar_inbox()
        sumo_pages.inbox_page.click_on_inbox_delete_selected_button(
            expected_locator=sumo_pages.inbox_page.INBOX_PAGE_LOCATORS
            ['inbox_page_message_action_banner']
        )
        assert sumo_pages.inbox_page.get_text_inbox_page_message_banner_text(
        ) in InboxPageMessages.NO_MESSAGES_SELECTED_BANNER_TEXT
        expect(sumo_pages.inbox_page._inbox_message_based_on_excerpt(message_body).first
               ).to_be_visible()

    with allure.step("Selecting the messages and deleting it via the delete selected button"):
        sumo_pages.inbox_page.delete_all_inbox_messages_via_delete_selected_button(
            message_body, expected_url=InboxPageMessages.INBOX_PAGE_STAGE_URL)

    with check, allure.step("Verifying that the messages are no longer displayed"):
        expect(sumo_pages.inbox_page._inbox_message_based_on_excerpt(message_body)).to_be_hidden()
        assert sumo_pages.inbox_page.get_text_inbox_page_message_banner_text(
        ) in InboxPageMessages.MULTIPLE_MESSAGES_DELETION_BANNER_TEXT

    with allure.step("Navigating to the sent messages section and clearing all messages via "
                     "the 'delete selected button'"):
        sumo_pages.mess_system_user_navbar.click_on_messaging_system_nav_sent_messages()
        sumo_pages.sent_message_page.delete_all_sent_messages_via_delete_selected_button(
            message_body, expected_url=SentMessagesPageMessages.SENT_MESSAGES_PAGE_URL)

    with allure.step("Verifying that the messages are no longer displayed"):
        expect(sumo_pages.sent_message_page.sent_messages_by_excerpt_locator(message_body)
               ).to_be_hidden()

    with check, allure.step("Verifying that the correct banner is displayed"):
        assert sumo_pages.sent_message_page.get_sent_messages_page_deleted_banner_text(
        ) in SentMessagesPageMessages.MULTIPLE_MESSAGES_DELETION_BANNER_TEXT

    with allure.step("Signing in with the receiver account and navigating to the inbox"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_6"]
        ))
        sumo_pages.top_navbar.click_on_inbox_option()

    with allure.step("Verifying that the messages are displayed inside the inbox section"):
        expect(sumo_pages.inbox_page._inbox_message_based_on_excerpt(message_body)).to_be_visible()

    with allure.step("Deleting all messages from the inbox page via the delete selected "
                     "button'"):
        sumo_pages.inbox_page.delete_all_inbox_messages_via_delete_selected_button(
            message_body, expected_url=InboxPageMessages.INBOX_PAGE_STAGE_URL)

    with check, allure.step("Verifying that the messages are no longer displayed inside the "
                            "inbox section and the correct banner is displayed"):
        expect(sumo_pages.inbox_page._inbox_message_based_on_excerpt(message_body)).to_be_hidden()
        assert sumo_pages.inbox_page.get_text_inbox_page_message_banner_text(
        ) in InboxPageMessages.MESSAGE_DELETED_BANNER_TEXT


# C2566115, C2602253, C2602252
@pytest.mark.messagingSystem
def test_group_messages_cannot_be_sent_by_non_staff_users(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with a non-staff account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts['TEST_ACCOUNT_12']
        ))

    with allure.step("Navigating to the new message page"):
        sumo_pages.top_navbar.click_on_inbox_option()
        sumo_pages.mess_system_user_navbar.click_on_messaging_system_nav_new_message()

    with allure.step("Typing in a group name inside the To field"):
        sumo_pages.new_message_page.type_into_new_message_to_input_field(
            utilities.user_message_test_data['test_groups'][0]
        )

    with allure.step("Verifying that no users are returned"):
        expect(sumo_pages.new_message_page.get_no_user_to_locator()).to_be_visible(timeout=10000)

    with allure.step("Navigating to the groups page"):
        utilities.navigate_to_link(utilities.general_test_data['groups'])
        sumo_pages.user_groups.click_on_a_particular_group(
            utilities.user_message_test_data['test_groups'][0])

    with allure.step("Verifying that the pm group members button is not displayed"):
        expect(sumo_pages.user_groups.get_pm_group_members_button()).to_be_hidden()

    with allure.step("Deleting the user session and verifying that the pm group members "
                     "button is not displayed"):
        utilities.delete_cookies()
        expect(sumo_pages.user_groups.get_pm_group_members_button()).to_be_hidden()

    # The PM group members button was removed for staff members as well.
    with allure.step("Signing in with a staff account and verifying that the pm group "
                     "members button is not displayed"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts['TEST_ACCOUNT_MODERATOR']
        ))
        expect(sumo_pages.user_groups.get_pm_group_members_button()).to_be_hidden()


# C2566115, C2566116, C2566119
@pytest.mark.messagingSystem
def test_staff_users_can_send_group_messages(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    message_body = "Test " + utilities.generate_random_number(1, 1000)
    with allure.step("Signing in with an admin account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts['TEST_ACCOUNT_MODERATOR']
        ))
    targeted_test_group = utilities.user_message_test_data['test_groups'][0]

    with allure.step("Navigating to the new messages page"):
        sumo_pages.top_navbar.click_on_inbox_option()
        sumo_pages.mess_system_user_navbar.click_on_messaging_system_nav_new_message()

    with allure.step("Sending out a message to a test group"):
        sumo_pages.messaging_system_flow.complete_send_message_form_with_data(
            recipient_username=targeted_test_group,
            message_body=message_body,
            expected_url=SentMessagesPageMessages.SENT_MESSAGES_PAGE_URL
        )

    with allure.step("Navigating to the 'Sent Messages page' and verifying that the message "
                     "was sent"):
        sumo_pages.mess_system_user_navbar.click_on_messaging_system_nav_sent_messages()
        expect(
            sumo_pages.sent_message_page.sent_messages_to_group(targeted_test_group, message_body)
        ).to_be_visible()

    with allure.step("Deleting the outbox"):
        sumo_pages.sent_message_page.delete_all_sent_messages_via_delete_selected_button(
            message_body, expected_url=SentMessagesPageMessages.SENT_MESSAGES_PAGE_URL)

    with allure.step("Signing in with all targeted group members, verifying that the message "
                     "was received and clearing the inbox"):
        for user in utilities.general_test_data['testGroup1users']:
            utilities.start_existing_session(utilities.username_extraction_from_email(
                utilities.user_secrets_accounts[user]
            ))

            sumo_pages.top_navbar.click_on_inbox_option()
            expect(sumo_pages.inbox_page._inbox_message_based_on_excerpt(message_body)
                   ).to_be_visible()
            sumo_pages.inbox_page.delete_all_inbox_messages_via_delete_selected_button(
                message_body, expected_url=InboxPageMessages.INBOX_PAGE_STAGE_URL)

    with allure.step("Signing in with users from second test group and verifying that the "
                     "message was not received"):
        for user in utilities.general_test_data["testGroup2users"]:
            utilities.start_existing_session(utilities.username_extraction_from_email(
                utilities.user_secrets_accounts[user]
            ))

            sumo_pages.top_navbar.click_on_inbox_option()
            expect(sumo_pages.inbox_page._inbox_message_based_on_excerpt(message_body)
                   ).to_be_hidden()


# C2566117, C2566119
@pytest.mark.messagingSystem
def test_staff_users_can_send_messages_to_multiple_groups(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    message_body = "Test " + utilities.generate_random_number(1, 1000)
    with allure.step("Signing in with an admin account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts['TEST_ACCOUNT_MODERATOR']
        ))
    targeted_test_group = utilities.user_message_test_data['test_groups']

    with allure.step("Navigating to the new messages page"):
        sumo_pages.top_navbar.click_on_inbox_option()
        sumo_pages.mess_system_user_navbar.click_on_messaging_system_nav_new_message()

    with allure.step("Sending out a message to a test group"):
        sumo_pages.messaging_system_flow.complete_send_message_form_with_data(
            recipient_username=targeted_test_group,
            message_body=message_body,
            expected_url=SentMessagesPageMessages.SENT_MESSAGES_PAGE_URL
        )

    with check, allure.step("Navigating to the 'Sent Messages page' and verifying that the "
                            "message was sent"):
        sumo_pages.mess_system_user_navbar.click_on_messaging_system_nav_sent_messages()
        sumo_pages.sent_message_page.click_on_sent_message_subject(message_body)
        check.equal(sumo_pages.sent_message_page.get_text_of_all_sent_groups(),
                    targeted_test_group)

    with allure.step("Deleting the outbox"):
        utilities.navigate_back()
        sumo_pages.sent_message_page.delete_all_sent_messages_via_delete_selected_button(
            message_body, expected_url=SentMessagesPageMessages.SENT_MESSAGES_PAGE_URL)

    with allure.step("Signing in with all targeted group members, verifying that the message "
                     "was received and clearing the inbox"):
        for user in utilities.general_test_data['testGroup1users'] + (
                utilities.general_test_data['testGroup2users'][1:]):
            utilities.start_existing_session(utilities.username_extraction_from_email(
                utilities.user_secrets_accounts[user]
            ))

            sumo_pages.top_navbar.click_on_inbox_option()
            expect(sumo_pages.inbox_page._inbox_message_based_on_excerpt(message_body)
                   ).to_be_visible()
            sumo_pages.inbox_page.delete_all_inbox_messages_via_delete_selected_button(
                message_body, expected_url=InboxPageMessages.INBOX_PAGE_STAGE_URL)


# C2566118, C2566119, C2566120
@pytest.mark.messagingSystem
def test_staff_users_can_send_messages_to_both_groups_and_user(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with an admin account"):
        message_body = "Test " + utilities.generate_random_number(1, 1000)
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts['TEST_ACCOUNT_MODERATOR']
        ))
    targeted_test_group = utilities.user_message_test_data['test_groups'][0]
    targeted_user = [utilities.username_extraction_from_email(
        utilities.user_secrets_accounts['TEST_ACCOUNT_MESSAGE_4']),
        utilities.username_extraction_from_email(
            utilities.user_secrets_accounts['TEST_ACCOUNT_MESSAGE_5'])]

    with allure.step("Navigating to the new messages page"):
        sumo_pages.top_navbar.click_on_inbox_option()
        sumo_pages.mess_system_user_navbar.click_on_messaging_system_nav_new_message()

    with allure.step("Sending out a message to a test group + user"):
        sumo_pages.messaging_system_flow.complete_send_message_form_with_data(
            recipient_username=targeted_user + [targeted_test_group],
            message_body=message_body,
            expected_url=SentMessagesPageMessages.SENT_MESSAGES_PAGE_URL
        )

    with check, allure.step("Navigating to the 'Sent Messages page' and verifying that the "
                            "message was sent"):
        sumo_pages.mess_system_user_navbar.click_on_messaging_system_nav_sent_messages()
        sumo_pages.sent_message_page.click_on_sent_message_subject(message_body)
        check.is_in(targeted_test_group,
                    sumo_pages.sent_message_page.get_text_of_all_sent_groups())
        check.equal(set(targeted_user),
                    set(sumo_pages.sent_message_page.get_text_of_all_recipients()))

    with allure.step("Deleting the outbox"):
        utilities.navigate_back()
        sumo_pages.sent_message_page.delete_all_sent_messages_via_delete_selected_button(
            message_body, expected_url=SentMessagesPageMessages.SENT_MESSAGES_PAGE_URL)

    with allure.step("Signing in with all targeted group members, verifying that the message "
                     "was received and clearing the inbox"):
        for user in utilities.general_test_data['testGroup1users'] + ['TEST_ACCOUNT_MESSAGE_5']:
            utilities.start_existing_session(utilities.username_extraction_from_email(
                utilities.user_secrets_accounts[user]
            ))

            sumo_pages.top_navbar.click_on_inbox_option()
            expect(sumo_pages.inbox_page._inbox_message_based_on_excerpt(message_body)
                   ).to_be_visible()
            sumo_pages.inbox_page.delete_all_inbox_messages_via_delete_selected_button(
                message_body, expected_url=InboxPageMessages.INBOX_PAGE_STAGE_URL)


# C2566116
@pytest.mark.messagingSystem
def test_removed_group_users_do_not_receive_group_messages(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    message_body = "Test " + utilities.generate_random_number(1, 1000)
    with allure.step("Signing in with a staff account and removing a user from the targeted "
                     "group"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts['TEST_ACCOUNT_MODERATOR']
        ))
        targeted_test_group = utilities.user_message_test_data['test_groups'][0]
        targeted_user = utilities.remove_character_from_string(
            utilities.username_extraction_from_email(
                utilities.user_special_chars
            ),
            '*'
        )

        utilities.navigate_to_link(utilities.general_test_data['groups'])
        sumo_pages.user_groups.click_on_a_particular_group(targeted_test_group)
        sumo_pages.user_group_flow.remove_a_user_from_group(targeted_user)

    with allure.step("Navigating to the new message page and sending a message to the group"):
        sumo_pages.top_navbar.click_on_inbox_option()
        sumo_pages.mess_system_user_navbar.click_on_messaging_system_nav_new_message()
        sumo_pages.messaging_system_flow.complete_send_message_form_with_data(
            recipient_username=targeted_test_group,
            message_body=message_body,
            expected_url=SentMessagesPageMessages.SENT_MESSAGES_PAGE_URL
        )

    with allure.step("Deleting the outbox"):
        sumo_pages.sent_message_page.delete_all_sent_messages_via_delete_selected_button(
            message_body, expected_url=SentMessagesPageMessages.SENT_MESSAGES_PAGE_URL)

    with allure.step("Signing in with all targeted group members, verifying that the message "
                     "was received and clearing the inbox"):
        for user in utilities.general_test_data['testGroup1users']:
            logged_user = utilities.start_existing_session(
                utilities.username_extraction_from_email(
                    utilities.user_secrets_accounts[user]
                ))
            sumo_pages.top_navbar.click_on_inbox_option()

            if logged_user == targeted_user:
                with allure.step("Verifying that the removed user has not received the group "
                                 "message"):
                    expect(sumo_pages.inbox_page._inbox_message_based_on_excerpt(message_body)
                           ).to_be_hidden()
            else:
                expect(sumo_pages.inbox_page._inbox_message_based_on_excerpt(message_body)
                       ).to_be_visible()
                sumo_pages.inbox_page.delete_all_inbox_messages_via_delete_selected_button(
                    message_body, expected_url=InboxPageMessages.INBOX_PAGE_STAGE_URL)

    with allure.step("Signing in with an staff account and adding the user back to the group"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts['TEST_ACCOUNT_MODERATOR']
        ))
        utilities.navigate_to_link(utilities.general_test_data['groups'])
        sumo_pages.user_groups.click_on_a_particular_group(targeted_test_group)
        sumo_pages.user_group_flow.add_a_user_to_group(targeted_user)


# C2584835
@pytest.mark.messagingSystem
def test_unable_to_send_group_messages_to_profiless_groups(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with an admin account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts['TEST_ACCOUNT_MODERATOR']
        ))

    with allure.step("Navigating to the new message page"):
        sumo_pages.top_navbar.click_on_inbox_option()
        sumo_pages.mess_system_user_navbar.click_on_messaging_system_nav_new_message()

    with allure.step("Typing in a profiless group name inside the To field"):
        sumo_pages.new_message_page.type_into_new_message_to_input_field("kb-contributors")

    with allure.step("Verifying that no users are returned"):
        expect(sumo_pages.new_message_page.get_no_user_to_locator()).to_be_visible(timeout=10000)


@pytest.mark.messagingSystemCleanup
def test_clear_inbox_and_outbox(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)

    for user in utilities.user_secrets_accounts:
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts[user]
        ))
        utilities.navigate_to_link(InboxPageMessages.INBOX_PAGE_STAGE_URL)
        inbox_and_outbox_deletion(page)

    utilities.delete_cookies()
    sumo_pages.auth_flow_page.sign_in_flow(
        username=utilities.user_special_chars,
        account_password=utilities.user_secrets_pass,
    )
    inbox_and_outbox_deletion(page)


def inbox_and_outbox_deletion(page: Page):
    sumo_pages = SumoPages(page)
    if sumo_pages.inbox_page.are_inbox_messages_displayed():
        sumo_pages.inbox_page.delete_all_inbox_messages_via_delete_selected_button(
            expected_url=InboxPageMessages.INBOX_PAGE_STAGE_URL
        )

    sumo_pages.mess_system_user_navbar.click_on_messaging_system_nav_sent_messages()
    if sumo_pages.sent_message_page.are_sent_messages_displayed():
        sumo_pages.sent_message_page.delete_all_sent_messages_via_delete_selected_button(
            expected_url=SentMessagesPageMessages.SENT_MESSAGES_PAGE_URL
        )
