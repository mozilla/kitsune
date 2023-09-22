import pytest
import pytest_check as check

from selenium_tests.core.test_utilities import TestUtilities
from selenium_tests.messages.messaging_system_pages_messages.inbox_page_messages import (
    InboxPageMessages,
)
from selenium_tests.messages.messaging_system_pages_messages.new_message_page_messages import (
    NewMessagePageMessages,
)
from selenium_tests.messages.messaging_system_pages_messages.sent_messages_page_messages import (
    SentMessagesPageMessages,
)
from selenium_tests.messages.my_profile_pages_messages.my_profile_page_messages import (
    MyProfileMessages,
)


class TestMessagingSystem(TestUtilities):
    # C891415
    @pytest.mark.messagingSystem
    def test_there_are_no_messages_here_text_is_displayed_when_no_messages_are_available(self):
        self.logger.info("Signing in with a normal user account")

        self.pages.top_navbar.click_on_signin_signup_button()
        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.logger.info("Navigating to the inbox page")

        self.pages.top_navbar.click_on_inbox_option()

        self.logger.info(
            "Verifying if there are messages displayed inside the inbox section."
            " If there are, we are clearing them all"
        )

        if self.pages.inbox_page.are_inbox_messages_displayed():
            self.pages.inbox_page.delete_all_displayed_inbox_messages()
            self.logger.info("Messages found. Clearing the list")

        self.logger.info("Verifying that the correct page message is displayed")

        check.equal(
            self.pages.inbox_page.get_text_of_inbox_no_message_header(),
            InboxPageMessages.NO_MESSAGES_IN_INBOX_TEXT,
            f"Incorrect message displayed. "
            f"Expected: "
            f"{InboxPageMessages.NO_MESSAGES_IN_INBOX_TEXT} "
            f"Received: "
            f"{self.pages.inbox_page.get_text_of_inbox_no_message_header()}",
        )

        self.logger.info("Navigating to the 'Sent Messages' page")

        self.pages.mess_system_user_navbar.click_on_messaging_system_navbar_sent_messages()

        self.logger.info(
            "Verifying if there are messages displayed inside the inbox section. "
            "If there are, we are clearing them all"
        )

        if self.pages.sent_message_page.are_sent_messages_displayed():
            self.pages.sent_message_page.delete_all_displayed_sent_messages()
            self.logger.info("Messages found. Clearing the list")

        self.logger.info("Verifying that the correct page message is displayed")

        check.equal(
            self.pages.sent_message_page.get_sent_messages_no_message_text(),
            SentMessagesPageMessages.NO_MESSAGES_IN_SENT_MESSAGES_TEXT,
            f"Incorrect message displayed. "
            f"Expected: "
            f"{SentMessagesPageMessages.NO_MESSAGES_IN_SENT_MESSAGES_TEXT} "
            f"Received: "
            f"{self.pages.sent_message_page.get_sent_messages_no_message_text()}",
        )

    # C2094292
    # This test needs to be updated to fetch the username from a different place
    @pytest.mark.messagingSystem
    def test_private_messages_can_be_sent_via_user_profiles(self):
        user_two = super().username_extraction_from_email(
            super().user_secrets_data["TEST_ACCOUNT_MESSAGE_2"]
        )

        self.logger.info("Signing in with user one")

        self.pages.top_navbar.click_on_signin_signup_button()

        user_one = self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_MESSAGE_1"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.pages.homepage.navigate_to(
            MyProfileMessages.get_my_profile_stage_url(username=user_two)
        )

        self.logger.info("Clicking on the 'Private Message button'")

        self.pages.my_profile_page.click_on_private_message_button()

        self.logger.info(
            "Verifying that the receiver is automatically added inside the 'To' field"
        )

        assert self.pages.new_message_page.get_user_to_text() == user_two, (
            f"Incorrect 'To' receiver. Expected: {user_two}. "
            f"Received: {self.pages.new_message_page.get_user_to_text()}"
        )

        self.logger.info("Adding text into the new message textarea field")

        self.pages.new_message_page.type_into_new_message_body_textarea(
            super().user_message_test_data["valid_user_message"]["message"]
        )

        self.logger.info("Clicking on the 'Send' button")

        self.pages.new_message_page.click_on_new_message_send_button()

        self.logger.info("Verifying that the correct message sent banner is displayed")

        check.equal(
            self.pages.inbox_page.get_text_inbox_page_message_banner_text(),
            InboxPageMessages.MESSAGE_SENT_BANNER_TEXT,
            f"Incorrect banner text displayed. "
            f"Expected: "
            f"{InboxPageMessages.MESSAGE_SENT_BANNER_TEXT}. "
            f"Received: "
            f"{self.pages.inbox_page.get_text_inbox_page_message_banner_text()}",
        )

        self.logger.info(
            "Clicking on the close button of the banner "
            "and verifying that the banner is no longer displayed"
        )

        self.pages.inbox_page.click_on_inbox_message_banner_close_button()

        check.is_false(
            self.pages.inbox_page.is_inbox_page_message_banner_displayed(),
            "The banner is displayed. It shouldn't be!",
        )

        self.logger.info(
            "Clicking on the 'Sent Messages option' "
            "and verifying that the message was successfully sent"
        )

        self.pages.mess_system_user_navbar.click_on_messaging_system_navbar_sent_messages()

        self.logger.info("Verifying that the sent message is displayed")

        assert self.pages.sent_message_page.is_sent_message_displayed(
            username=user_two
        ), "The message is not displayed! it should be!"

        self.logger.info(
            "Deleting the message from the sent messages link "
            "and verifying that the message is no longer displayed"
        )

        self.pages.sent_message_page.click_on_sent_message_delete_button(username=user_two)
        self.pages.sent_message_page.click_on_delete_page_delete_button()

        self.logger.info("Verifying that the correct banner is displayed")

        check.equal(
            self.pages.sent_message_page.get_sent_messages_page_deleted_banner_text(),
            SentMessagesPageMessages.DELETE_MESSAGE_BANNER_TEXT,
            f"Wrong message displayed inside the banner. "
            f"Expected: "
            f"{SentMessagesPageMessages.DELETE_MESSAGE_BANNER_TEXT} "
            f"Received: "
            f"{self.pages.sent_message_page.get_sent_messages_page_deleted_banner_text()}",
        )

        self.logger.info(
            "Closing the banner and verifying that the banner was closed successfully"
        )

        self.pages.sent_message_page.click_on_sent_messages_page_banner_close_button()

        check.is_false(
            self.pages.sent_message_page.is_sent_message_banner_displayed(),
            "Banner is still displayed! It shouldn't be!",
        )

        assert not (
            self.pages.sent_message_page.is_sent_message_displayed(username=user_two)
        ), "The message is displayed! it shouldn't be!"

        self.logger.info("Signing in with the user which received the message")

        self.pages.top_navbar.click_on_sign_out_button()

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_MESSAGE_2"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.logger.info(
            "Accessing the Inbox section " "and verifying that the message was received"
        )

        self.pages.top_navbar.click_on_inbox_option()

        assert self.pages.inbox_page.is_message_displayed_inside_the_inbox_section(
            username=user_one
        ), "The message is not displayed! It should be!"

        self.logger.info(
            "Deleting the message and verifying that it "
            "is no longer displayed inside the inbox section"
        )

        self.pages.inbox_page.click_on_inbox_message_delete_button(username=user_one)

        self.pages.inbox_page.click_on_delete_page_delete_button()

        assert not (
            self.pages.inbox_page.is_message_displayed_inside_the_inbox_section(username=user_one)
        ), "Message is displayed! It shouldn't be!"

        self.logger.info("Verifying that the correct banner is displayed")

        check.equal(
            self.pages.sent_message_page.get_sent_messages_page_deleted_banner_text(),
            SentMessagesPageMessages.DELETE_MESSAGE_BANNER_TEXT,
            f"Wrong message displayed inside the banner. "
            f"Expected: "
            f"{SentMessagesPageMessages.DELETE_MESSAGE_BANNER_TEXT} "
            f"Received: "
            f"{self.pages.sent_message_page.get_sent_messages_page_deleted_banner_text()}",
        )

        self.logger.info(
            "Closing the banner and verifying that the banner was closed successfully"
        )

        self.pages.sent_message_page.click_on_sent_messages_page_banner_close_button()

    # C891419
    @pytest.mark.messagingSystem
    def test_private_message_can_be_sent_via_new_message_page(self):
        test_user = super().username_extraction_from_email(
            super().user_secrets_data["TEST_ACCOUNT_MESSAGE_4"]
        )

        self.logger.info("Signing in with a normal user account")
        self.pages.top_navbar.click_on_signin_signup_button()

        user_one = self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_MESSAGE_3"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()
        self.logger.info(
            "Accessing the 'New Message page " "and sending a message to another user'"
        )

        self.pages.top_navbar.click_on_inbox_option()
        self.pages.mess_system_user_navbar.click_on_messaging_system_navbar_new_message()
        self.pages.messaging_system_flow.complete_send_message_form_with_data(
            recipient_username=test_user,
            message_body=super().user_message_test_data["valid_user_message"]["message"],
        )
        self.pages.new_message_page.click_on_new_message_send_button()

        self.logger.info("Verifying that the correct banner is displayed")

        check.equal(
            self.pages.inbox_page.get_text_inbox_page_message_banner_text(),
            InboxPageMessages.MESSAGE_SENT_BANNER_TEXT,
            f"Incorrect banner text displayed. "
            f"Expected: "
            f"{InboxPageMessages.MESSAGE_SENT_BANNER_TEXT} "
            f"Received: "
            f"{self.pages.inbox_page.get_text_inbox_page_message_banner_text()}",
        )

        self.logger.info("Closing the banner and verifying that it is no longer displayed")

        self.pages.inbox_page.click_on_inbox_message_banner_close_button()

        check.is_false(
            self.pages.inbox_page.is_inbox_page_message_banner_displayed(),
            "Banner is still displayed! It shouldn't be!",
        )

        self.logger.info(
            "Verifying that the sent message is displayed inside the 'sent messages' page"
        )

        self.pages.mess_system_user_navbar.click_on_messaging_system_navbar_sent_messages()

        assert self.pages.sent_message_page.is_sent_message_displayed(test_user), (
            "The sent message is not displayed inside the 'Sent Messages page'. "
            "It should have been!"
        )

        self.logger.info("Clearing the sent messages list")

        self.pages.sent_message_page.delete_all_displayed_sent_messages()

        self.logger.info(
            "Signing in with the receiver account and verifying that the message "
            "is displayed inside the inbox section"
        )

        self.pages.top_navbar.click_on_sign_out_button()
        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_MESSAGE_4"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.pages.top_navbar.click_on_inbox_option()

        assert self.pages.inbox_page.is_message_displayed_inside_the_inbox_section(
            username=user_one
        )

        self.logger.info("Clearing the inbox")

        self.pages.inbox_page.delete_all_displayed_inbox_messages()

    # C891412, C891413
    @pytest.mark.messagingSystem
    def test_navbar_options_redirect_to_the_correct_page_and_options_are_correctly_highlighted(
        self,
    ):
        self.logger.info("Signing in with a normal user account")

        self.pages.top_navbar.click_on_signin_signup_button()
        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.logger.info("Accessing the inbox section via the top-navbar")

        self.pages.top_navbar.click_on_inbox_option()

        self.logger.info(
            "Verifying that we are on the correct page "
            "and the 'Inbox' navbar option is highlighted"
        )

        assert self.pages.inbox_page.current_url() == InboxPageMessages.INBOX_PAGE_STAGE_URL, (
            f"Incorrect page displayed. "
            f"Expected: "
            f"{InboxPageMessages.INBOX_PAGE_STAGE_URL} "
            f"Received: "
            f"{self.pages.inbox_page.current_url()}"
        )

        if self.browser == "chrome":
            assert (
                self.pages.mess_system_user_navbar.get_inbox_option_background_value()
                == InboxPageMessages.NAVBAR_INBOX_SELECTED_BG_COLOR_CHROME
            ), (
                f"Incorrect background color displayed. "
                f"Expected: "
                f"{InboxPageMessages.NAVBAR_INBOX_SELECTED_BG_COLOR_CHROME} "
                f"Received: "
                f"{self.pages.mess_system_user_navbar.get_inbox_option_background_value()}"
            )
        elif self.browser == "firefox":
            assert (
                self.pages.mess_system_user_navbar.get_inbox_option_background_value()
                == InboxPageMessages.NAVBAR_INBOX_SELECTED_BG_COLOR_FIREFOX
            ), (
                f"Incorrect background color displayed. "
                f"Expected: "
                f"{InboxPageMessages.NAVBAR_INBOX_SELECTED_BG_COLOR_FIREFOX} "
                f"Received: "
                f"{self.pages.mess_system_user_navbar.get_inbox_option_background_value()}"
            )

        self.pages.mess_system_user_navbar.click_on_messaging_system_navbar_sent_messages()

        self.logger.info(
            "Verifying that we are on the correct page "
            "and the 'Sent Messages' page is successfully displayed"
        )

        assert (
            self.pages.sent_message_page.current_url()
            == SentMessagesPageMessages.SENT_MESSAGES_PAGE_URL
        ), (
            f"Incorrect page displayed. "
            f"Expected: "
            f"{SentMessagesPageMessages.SENT_MESSAGES_PAGE_URL} "
            f"Received: "
            f"{self.pages.sent_message_page.current_url()}"
        )

        self.logger.info("Verifying that the 'Sent Messages' option is highlighted")

        if self.browser == "chrome":
            assert (
                self.pages.mess_system_user_navbar.get_sent_messages_option_background_value()
                == SentMessagesPageMessages.NAVBAR_SENT_MESSAGES_SELECTED_BG_COLOR_CHROME
            ), (
                f"Incorrect background color displayed. "
                f"Expected: "
                f"{SentMessagesPageMessages.NAVBAR_SENT_MESSAGES_SELECTED_BG_COLOR_CHROME}"
                f"Received: "
                f"{self.pages.mess_system_user_navbar.get_sent_messages_option_background_value()}"
            )
        elif self.browser == "firefox":
            assert (
                self.pages.mess_system_user_navbar.get_sent_messages_option_background_value()
                == SentMessagesPageMessages.NAVBAR_SENT_MESSAGES_SELECTED_BG_COLOR_FIREFOX
            ), (
                f"Incorrect background color displayed. "
                f"Expected: "
                f"{SentMessagesPageMessages.NAVBAR_SENT_MESSAGES_SELECTED_BG_COLOR_FIREFOX} "
                f"Received: "
                f"{self.pages.mess_system_user_navbar.get_sent_messages_option_background_value()}"
            )

        self.logger.info("Clicking on the 'New message' navbar option")

        self.pages.mess_system_user_navbar.click_on_messaging_system_navbar_new_message()

        self.logger.info("Verifying that the 'New Message' page is displayed")

        assert (
            self.pages.new_message_page.current_url()
            == NewMessagePageMessages.NEW_MESSAGE_PAGE_STAGE_URL
        ), (
            f"Incorrect page displayed. "
            f"Expected: {NewMessagePageMessages.NEW_MESSAGE_PAGE_STAGE_URL} "
            f"Received: {self.pages.new_message_page.current_url()}"
        )

        self.logger.info("Verifying that the 'New Message' navbar option is highlighted")

        if self.browser == "chrome":
            assert (
                self.pages.mess_system_user_navbar.get_new_message_option_background_value()
                == NewMessagePageMessages.NAVBAR_NEW_MESSAGE_SELECTED_BG_COLOR_CHROME
            ), (
                f"Incorrect background color displayed. "
                f"Expected: "
                f"{NewMessagePageMessages.NAVBAR_NEW_MESSAGE_SELECTED_BG_COLOR_CHROME} "
                f"Received: "
                f"{self.pages.mess_system_user_navbar.get_new_message_option_background_value()}"
            )
        elif self.browser == "firefox":
            assert (
                self.pages.mess_system_user_navbar.get_new_message_option_background_value()
                == NewMessagePageMessages.NAVBAR_NEW_MESSAGE_SELECTED_BG_COLOR_FIREFOX
            ), (
                f"Incorrect background color displayed. "
                f"Expected: "
                f"{NewMessagePageMessages.NAVBAR_NEW_MESSAGE_SELECTED_BG_COLOR_FIREFOX} "
                f"Received: "
                f"{self.pages.mess_system_user_navbar.get_new_message_option_background_value()}"
            )

        self.logger.info("Clicking on the navbar inbox messaging system navbar option")

        self.pages.mess_system_user_navbar.click_on_messaging_system_navbar_inbox()

        self.logger.info(
            "Verifying that we are on the correct page "
            "and the 'Inbox' navbar option is highlighted"
        )

        assert self.pages.inbox_page.current_url() == InboxPageMessages.INBOX_PAGE_STAGE_URL, (
            f"Incorrect page displayed. Expected: {InboxPageMessages.INBOX_PAGE_STAGE_URL} "
            f"Received: {self.pages.inbox_page.current_url()}"
        )

        if self.browser == "chrome":
            assert (
                self.pages.mess_system_user_navbar.get_inbox_option_background_value()
                == InboxPageMessages.NAVBAR_INBOX_SELECTED_BG_COLOR_CHROME
            ), (
                f"Incorrect background color displayed. "
                f"Expected: "
                f"{InboxPageMessages.NAVBAR_INBOX_SELECTED_BG_COLOR_CHROME} "
                f"Received: "
                f"{self.pages.mess_system_user_navbar.get_inbox_option_background_value()}"
            )
        elif self.browser == "firefox":
            assert (
                self.pages.mess_system_user_navbar.get_inbox_option_background_value()
                == InboxPageMessages.NAVBAR_INBOX_SELECTED_BG_COLOR_FIREFOX
            ), (
                f"Incorrect background color displayed. "
                f"Expected: "
                f"{InboxPageMessages.NAVBAR_INBOX_SELECTED_BG_COLOR_FIREFOX} "
                f"Received: "
                f"{self.pages.mess_system_user_navbar.get_inbox_option_background_value()}"
            )

    # C891416
    @pytest.mark.messagingSystem
    def test_new_message_field_validation(self):
        user_two = super().username_extraction_from_email(
            super().user_secrets_data["TEST_ACCOUNT_MESSAGE_1"]
        )
        self.logger.info("Signing in with normal user account")

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.logger.info("Accessing the New Message page")

        self.pages.top_navbar.click_on_inbox_option()
        self.pages.mess_system_user_navbar.click_on_messaging_system_navbar_new_message()

        self.pages.new_message_page.click_on_new_message_send_button()

        self.logger.info("Verifying that we are still on the 'New Message page'")

        check.equal(
            self.pages.new_message_page.current_url(),
            NewMessagePageMessages.NEW_MESSAGE_PAGE_STAGE_URL,
            f"We are on the incorrect page!. "
            f"Expected to be on: {NewMessagePageMessages.NEW_MESSAGE_PAGE_STAGE_URL} "
            f"We are on the: {self.pages.new_message_page.current_url()} page",
        )

        self.logger.info("Adding a valid user inside the 'To' field")

        self.pages.new_message_page.type_into_new_message_to_input_field(text=user_two)
        self.pages.new_message_page.click_on_a_searched_user(username=user_two)

        self.logger.info(
            "Clicking the 'Send' button and verifying that we are still on the same page"
        )

        self.pages.new_message_page.click_on_new_message_send_button()

        check.equal(
            self.pages.new_message_page.current_url(),
            NewMessagePageMessages.NEW_MESSAGE_PAGE_STAGE_URL,
            f"We are on the incorrect page!. "
            f"Expected to be on: {NewMessagePageMessages.NEW_MESSAGE_PAGE_STAGE_URL} "
            f"We are on the: {self.pages.new_message_page.current_url()} page",
        )

        self.logger.info("Verifying that the default remaining characters is the correct one")

        check.equal(
            self.pages.new_message_page.get_characters_remaining_text(),
            NewMessagePageMessages.NEW_MESSAGE_DEFAULT_REMAINING_CHARACTERS,
            f" The default character remaining string is not the correct one! "
            f"Expected: {NewMessagePageMessages.NEW_MESSAGE_DEFAULT_REMAINING_CHARACTERS}"
            f"Received: {self.pages.new_message_page.get_characters_remaining_text()}",
        )

        self.logger.info("Verifying that the characters remaining color is the expected one")

        if self.browser == "chrome":
            check.equal(
                self.pages.new_message_page.get_characters_remaining_text_color(),
                NewMessagePageMessages.ENOUGH_CHARACTERS_REMAINING_COLOR_CHROME,
                f"Incorrect color displayed. "
                f"Expected: {NewMessagePageMessages.ENOUGH_CHARACTERS_REMAINING_COLOR_CHROME} "
                f"Received: {self.pages.new_message_page.get_characters_remaining_text_color()}",
            )
        elif self.browser == "firefox":
            check.equal(
                self.pages.new_message_page.get_characters_remaining_text_color(),
                NewMessagePageMessages.ENOUGH_CHARACTERS_REMAINING_COLOR_FIREFOX,
                f"Incorrect color displayed. "
                f"Expected: {NewMessagePageMessages.ENOUGH_CHARACTERS_REMAINING_COLOR_FIREFOX} "
                f"Received: {self.pages.new_message_page.get_characters_remaining_text_color()}",
            )

        # Firefox container crashes when performing the below steps. Executing in Chrome for now

        if self.browser == "chrome":
            self.logger.info("Adding 9990 characters inside the input field")

            self.pages.new_message_page.type_into_new_message_body_textarea(
                text=super().user_message_test_data["valid_user_message"][
                    "9990_characters_long_message"
                ]
            )
            check.equal(
                self.pages.new_message_page.get_characters_remaining_text(),
                NewMessagePageMessages.TEN_CHARACTERS_REMAINING_MESSAGE,
                f"Incorrect remaining characters string displayed. "
                f"Expected: {NewMessagePageMessages.TEN_CHARACTERS_REMAINING_MESSAGE}"
                f"Displayed: {self.pages.new_message_page.get_characters_remaining_text()}",
            )
            self.logger.info("Verifying that the characters remaining color is the expected one")

            check.equal(
                self.pages.new_message_page.get_characters_remaining_text_color(),
                NewMessagePageMessages.ENOUGH_CHARACTERS_REMAINING_COLOR_CHROME,
                f"Incorrect color displayed. "
                f"Expected: {NewMessagePageMessages.ENOUGH_CHARACTERS_REMAINING_COLOR_CHROME} "
                f"Received: {self.pages.new_message_page.get_characters_remaining_text_color()}",
            )

        # elif self.browser == "firefox":
        #     check.equal(
        #         self.pages.new_message_page.get_characters_remaining_text_color(),
        #         NewMessagePageMessages.ENOUGH_CHARACTERS_REMAINING_COLOR_FIREFOX,
        #         f"Incorrect color displayed. "
        #         f"Expected: {NewMessagePageMessages.ENOUGH_CHARACTERS_REMAINING_COLOR_FIREFOX} "
        #         f"Received: {self.pages.new_message_page.get_characters_remaining_text_color()}",
        #     )

            self.logger.info("Adding one character inside the textarea field")

            self.pages.new_message_page.type_into_new_message_body_textarea(
                text=super().user_message_test_data["valid_user_message"]["one_character_message"]
            )

            self.logger.info("Verifying that the char remaining string is updated accordingly")

            check.equal(
                self.pages.new_message_page.get_characters_remaining_text(),
                NewMessagePageMessages.NINE_CHARACTERS_REMAINING_MESSAGE,
                f"Incorrect remaining characters string displayed. "
                f"Expected:{NewMessagePageMessages.NINE_CHARACTERS_REMAINING_MESSAGE} "
                f"Displayed: {self.pages.new_message_page.get_characters_remaining_text()}",
            )

            self.logger.info("Verifying that the characters remaining color is the expected one")

            check.equal(
                self.pages.new_message_page.get_characters_remaining_text_color(),
                NewMessagePageMessages.NO_CHARACTERS_REMAINING_COLOR_CHROME,
                f"Incorrect color displayed. "
                f"Expected: {NewMessagePageMessages.NO_CHARACTERS_REMAINING_COLOR_CHROME} "
                f"Received: {self.pages.new_message_page.get_characters_remaining_text_color()}",
            )
        # elif self.browser == "firefox":
        #     check.equal(
        #         self.pages.new_message_page.get_characters_remaining_text_color(),
        #         NewMessagePageMessages.NO_CHARACTERS_REMAINING_COLOR_FIREFOX,
        #         f"Incorrect color displayed. "
        #         f"Expected: {NewMessagePageMessages.NO_CHARACTERS_REMAINING_COLOR_FIREFOX} "
        #         f"Received: {self.pages.new_message_page.get_characters_remaining_text_color()}",
        #     )

            self.logger.info("Adding 9 characters inside the textarea field")

            self.pages.new_message_page.type_into_new_message_body_textarea(
                text=super().user_message_test_data["valid_user_message"]["9_characters_message"]
            )

            self.logger.info("Verifying that the char remaining string is updated accordingly")

            check.equal(
                self.pages.new_message_page.get_characters_remaining_text_color(),
                NewMessagePageMessages.NO_CHARACTERS_REMAINING_COLOR_CHROME,
                f"Incorrect color displayed. "
                f"Expected: {NewMessagePageMessages.NO_CHARACTERS_REMAINING_COLOR_CHROME} "
                f"Received: {self.pages.new_message_page.get_characters_remaining_text_color()}",
            )
        # elif self.browser == "firefox":
        #     check.equal(
        #         self.pages.new_message_page.get_characters_remaining_text_color(),
        #         NewMessagePageMessages.NO_CHARACTERS_REMAINING_COLOR_FIREFOX,
        #         f"Incorrect color displayed. "
        #         f"Expected: {NewMessagePageMessages.NO_CHARACTERS_REMAINING_COLOR_FIREFOX} "
        #         f"Received: {self.pages.new_message_page.get_characters_remaining_text_color()}",
        #     )

            self.logger.info("Verifying that the characters remaining color is the expected one")

            check.equal(
                self.pages.new_message_page.get_characters_remaining_text_color(),
                NewMessagePageMessages.NO_CHARACTERS_REMAINING_COLOR_CHROME,
                f"Incorrect color displayed. "
                f"Expected: {NewMessagePageMessages.NO_CHARACTERS_REMAINING_COLOR_CHROME} "
                f"Received: {self.pages.new_message_page.get_characters_remaining_text_color()}",
            )
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
    def test_new_message_cancel_button(self):
        user_two = super().username_extraction_from_email(
            super().user_secrets_data["TEST_ACCOUNT_13"]
        )
        self.logger.info("Signing in with a normal user account")

        self.pages.top_navbar.click_on_signin_signup_button()
        user_one = self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.logger.info("Accessing the 'New Message' section")

        self.pages.top_navbar.click_on_inbox_option()
        self.pages.mess_system_user_navbar.click_on_messaging_system_navbar_new_message()

        self.logger.info("Filling the new message form with data")

        self.pages.messaging_system_flow.complete_send_message_form_with_data(
            recipient_username=user_two,
            message_body=super().user_message_test_data["valid_user_message"]["message"],
        )

        self.logger.info("Clicking on the 'Cancel' button")

        self.pages.new_message_page.click_on_new_message_cancel_button()

        self.logger.info("Verifying that the user is redirected to the inbox page")

        if self.browser == "chrome":
            check.equal(
                self.pages.mess_system_user_navbar.get_inbox_option_background_value(),
                InboxPageMessages.NAVBAR_INBOX_SELECTED_BG_COLOR_CHROME,
                "The inbox option is not highlighted! It should have been!",
            )
        elif self.browser == "firefox":
            check.equal(
                self.pages.mess_system_user_navbar.get_inbox_option_background_value(),
                InboxPageMessages.NAVBAR_INBOX_SELECTED_BG_COLOR_FIREFOX,
                "The inbox option is not highlighted! It should have been!",
            )

        check.equal(
            self.pages.inbox_page.current_url(),
            InboxPageMessages.INBOX_PAGE_STAGE_URL,
            f"We are not on the correct page. Expected: {InboxPageMessages.INBOX_PAGE_STAGE_URL} "
            f"Received: {self.pages.inbox_page.current_url()}",
        )

        self.logger.info(
            "Navigating to the 'Sent Messages' page nad verifying that the message was not sent"
        )

        self.pages.mess_system_user_navbar.click_on_messaging_system_navbar_sent_messages()

        assert not (self.pages.sent_message_page.is_sent_message_displayed(username=user_two))

        self.logger.info("Signing out and signing in with the receiver account")

        self.pages.top_navbar.click_on_sign_out_button()
        self.pages.top_navbar.click_on_signin_signup_button()
        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_13"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.logger.info(
            "Navigating to the receiver inbox and verifying that no message was received"
        )

        self.pages.top_navbar.click_on_inbox_option()

        assert not (
            self.pages.inbox_page.is_message_displayed_inside_the_inbox_section(username=user_one)
        )

    # C891418
    @pytest.mark.messagingSystem
    def test_new_message_preview(self):
        test_user = super().username_extraction_from_email(
            super().user_secrets_data["TEST_ACCOUNT_13"]
        )

        self.logger.info("Signing in with a normal user account")

        self.pages.top_navbar.click_on_signin_signup_button()
        username = self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.logger.info("Accessing the inbox section")

        self.pages.top_navbar.click_on_inbox_option()

        self.logger.info("Navigating to the new message page")

        self.pages.mess_system_user_navbar.click_on_messaging_system_navbar_new_message()

        self.logger.info("Adding text inside the message content section")

        self.pages.messaging_system_flow.complete_send_message_form_with_data(
            recipient_username=test_user,
            message_body=super().user_message_test_data["valid_user_message"]["message"],
        )

        self.logger.info("Clicking on  the 'Preview' button")

        self.pages.new_message_page.click_on_new_message_preview_button()

        self.logger.info("Verifying that the preview section is successfully displayed")

        assert (
            self.pages.new_message_page.is_message_preview_section_displayed()
        ), " The message preview section is not displayed. It should be!"

        self.logger.info("Verifying that all the preview items are displayed")

        check.equal(
            self.pages.new_message_page.get_text_of_test_data_first_paragraph_text(),
            NewMessagePageMessages.PREVIEW_MESSAGE_CONTENT_FIRST_PARAGRAPH_TEXT,
            f"Wrong text displayed. "
            f"Expected: "
            f"{NewMessagePageMessages.PREVIEW_MESSAGE_CONTENT_FIRST_PARAGRAPH_TEXT} "
            f"Received: "
            f"{self.pages.new_message_page.get_text_of_test_data_first_paragraph_text()}",
        )

        check.equal(
            self.pages.new_message_page.get_text_of_test_data_first_paragraph_strong_text(),
            NewMessagePageMessages.PREVIEW_MESSAGE_CONTENT_FIRST_PARAGRAPH_STRONG_TEXT,
            f"Wrong text displayed. "
            f"Expected:"
            f"{NewMessagePageMessages.PREVIEW_MESSAGE_CONTENT_FIRST_PARAGRAPH_STRONG_TEXT} "
            f"Received: "
            f"{self.pages.new_message_page.get_text_of_test_data_first_paragraph_strong_text()}",
        )

        check.equal(
            self.pages.new_message_page.get_text_of_test_data_first_paragraph_italic_text(),
            NewMessagePageMessages.PREVIEW_MESSAGE_CONTENT_FIRST_PARAGRAPH_ITALIC_TEXT,
            f"Wrong text displayed. "
            f"Expected:"
            f"{NewMessagePageMessages.PREVIEW_MESSAGE_CONTENT_FIRST_PARAGRAPH_ITALIC_TEXT} "
            f"Received: "
            f"{self.pages.new_message_page.get_text_of_test_data_first_paragraph_italic_text()}",
        )

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

        check.equal(
            self.pages.new_message_page.get_text_of_numbered_list_items(),
            numbered_list_items,
            f"Wrong data displayed in the numbered list. Expected {numbered_list_items} "
            f"Received: {self.pages.new_message_page.get_text_of_numbered_list_items()}",
        )

        check.equal(
            self.pages.new_message_page.get_text_of_bulleted_list_items(),
            bulleted_list_items,
            f"Wrong data displayed in the numbered list. Expected {bulleted_list_items} "
            f"Received: {self.pages.new_message_page.get_text_of_numbered_list_items()}",
        )

        check.is_true(
            self.pages.new_message_page.is_new_message_preview_external_link_test_data_displayed(),
            "The external link data is not displayed! It should have been!",
        )

        check.is_true(
            self.pages.new_message_page.is_new_message_preview_internal_link_test_data_displayed(),
            "The internal link data is not displayed! It should have been!",
        )

        self.logger.info(
            "Clicking on the internal link and "
            "verifying that the user is redirected to the correct article"
        )

        self.pages.new_message_page.click_on_preview_internal_link()

        assert (
            self.pages.kb_article_page.get_text_of_article_title()
            == NewMessagePageMessages.PREVIEW_MESSAGE_INTERNAL_LINK_TITLE
        ), (
            f"Incorrect article title displayed! "
            f"Expected: {NewMessagePageMessages.PREVIEW_MESSAGE_INTERNAL_LINK_TITLE} "
            f"Received: {self.pages.kb_article_page.get_text_of_article_title()}"
        )

        self.logger.info(
            "Verifying that the message was no sent by checking the 'Sent Messages page'"
        )

        self.pages.top_navbar.click_on_inbox_option()

        self.pages.mess_system_user_navbar.click_on_messaging_system_navbar_sent_messages()

        assert not (
            self.pages.sent_message_page.is_sent_message_displayed(username=test_user)
        ), "The message is displayed. It shouldn't be"

        self.logger.info(
            "Signing in with the potential message receiver "
            "and verifying that no message was received"
        )

        self.pages.top_navbar.click_on_sign_out_button()
        self.pages.top_navbar.click_on_signin_signup_button()
        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_13"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )
        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.pages.top_navbar.click_on_inbox_option()

        assert not (
            self.pages.inbox_page.is_message_displayed_inside_the_inbox_section(username=username)
        ), "The message is displayed. It shouldn't be"

    # C891421, C891424
    @pytest.mark.messagingSystem
    def test_messages_can_be_selected_and_deleted(self):
        test_user = super().username_extraction_from_email(
            super().user_secrets_data["TEST_ACCOUNT_MESSAGE_6"]
        )

        self.logger.info("Signing in with a normal user account")

        self.pages.top_navbar.click_on_signin_signup_button()

        user_one = self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_MESSAGE_5"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.logger.info(
            "Accessing the 'New Message' page and sending a message to a different user"
        )

        self.pages.top_navbar.click_on_inbox_option()
        self.pages.mess_system_user_navbar.click_on_messaging_system_navbar_new_message()
        self.pages.messaging_system_flow.complete_send_message_form_with_data(
            recipient_username=test_user,
            message_body=super().user_message_test_data["valid_user_message"]["message"],
        )
        self.pages.new_message_page.click_on_new_message_send_button()

        self.logger.info("Navigating to the sent messages page")

        self.pages.mess_system_user_navbar.click_on_messaging_system_navbar_sent_messages()

        self.logger.info("Clicking on the 'Delete Selected' button")

        self.pages.sent_message_page.click_on_delete_selected_button()

        self.logger.info(
            "Verifying that the correct message is displayed "
            "and is no longer displayed when dismissed"
        )

        check.equal(
            self.pages.sent_message_page.get_sent_messages_page_deleted_banner_text(),
            SentMessagesPageMessages.NO_MESSAGES_SELECTED_BANNER_TEXT,
            f"Incorrect banner text displayed. "
            f"Expected: "
            f"{SentMessagesPageMessages.NO_MESSAGES_SELECTED_BANNER_TEXT} "
            f"Received: "
            f"{self.pages.sent_message_page.get_sent_messages_page_deleted_banner_text()}",
        )

        self.logger.info("Closing the banner and verifying that the banner is no longer displayed")

        self.pages.sent_message_page.click_on_sent_messages_page_banner_close_button()

        check.is_false(
            self.pages.sent_message_page.is_sent_message_banner_displayed(),
            "The banner is still displayed! It shouldn't be!",
        )

        self.logger.info(
            "Verifying that the message is still listed inside the sent messages section"
        )

        assert self.pages.sent_message_page.is_sent_message_displayed(
            username=test_user
        ), "The message is no longer displayed inside the sent messages page! It should be!"

        self.logger.info("Sending another message to self twice")

        for i in range(2):
            self.pages.mess_system_user_navbar.click_on_messaging_system_navbar_new_message()
            self.pages.messaging_system_flow.complete_send_message_form_with_data(
                recipient_username=user_one,
                message_body=super().user_message_test_data["valid_user_message"]["message"],
            )
            self.pages.new_message_page.click_on_new_message_send_button()

        self.logger.info(
            "Clicking on the 'delete selected' button while no messages is selected "
            "and verifying that the correct "
            "banner is displayed"
        )

        self.pages.inbox_page.click_on_inbox_delete_selected_button()

        check.equal(
            self.pages.inbox_page.get_text_inbox_page_message_banner_text(),
            InboxPageMessages.NO_MESSAGES_SELECTED_BANNER_TEXT,
            f"Incorrect messages displayed. "
            f"Expected: {InboxPageMessages.NO_MESSAGES_SELECTED_BANNER_TEXT} "
            f"Received: {self.pages.inbox_page.get_text_inbox_page_message_banner_text()}",
        )

        self.logger.info(
            "Closing the banner and verifying that it is no longer displayed and "
            "no messages were deleted"
        )

        self.pages.inbox_page.click_on_inbox_message_banner_close_button()

        check.is_false(
            self.pages.inbox_page.is_inbox_page_message_banner_displayed(),
            "The banner is still displayed! It shouldn't be!",
        )

        assert self.pages.inbox_page.is_message_displayed_inside_the_inbox_section(
            username=user_one
        ), "Messages are no longer displayed. They should have been!"

        self.logger.info("Selecting the messages and deleting it via the 'delete selected button'")

        self.pages.inbox_page.delete_all_displayed_inbox_messages_via_delete_selected_button()

        self.logger.info("Verifying that the messages are no longer displayed")

        assert not (
            self.pages.inbox_page.is_message_displayed_inside_the_inbox_section(username=user_one)
        )

        self.logger.info("Verifying that the correct banner is displayed")

        check.equal(
            self.pages.inbox_page.get_text_inbox_page_message_banner_text(),
            InboxPageMessages.MESSAGE_DELETED_BANNER_TEXT,
            f"Incorrect message banner displayed. "
            f"Expected: {InboxPageMessages.MESSAGE_DELETED_BANNER_TEXT} "
            f"Received: {self.pages.inbox_page.get_text_inbox_page_message_banner_text()}",
        )

        self.logger.info(
            "Navigating to the sent messages section and "
            "clearing all messages via the 'delete selected button'"
        )

        self.pages.mess_system_user_navbar.click_on_messaging_system_navbar_sent_messages()

        self.pages.sent_message_page.delete_all_sent_messages_via_delete_selected_button()

        self.logger.info("Verifying that the messages are no longer displayed")

        assert not (self.pages.sent_message_page.is_sent_message_displayed(username=test_user))

        self.logger.info("Verifying that the correct banner is displayed")

        check.equal(
            self.pages.sent_message_page.get_sent_messages_page_deleted_banner_text(),
            SentMessagesPageMessages.DELETE_MESSAGE_BANNER_TEXT,
            f"Incorrect message banner displayed. "
            f"Expected: "
            f"{SentMessagesPageMessages.DELETE_MESSAGE_BANNER_TEXT} "
            f"Received: "
            f"{self.pages.sent_message_page.get_sent_messages_page_deleted_banner_text()}",
        )

        self.logger.info(
            "Signing in with the receiver account and navigating to the inbox section"
        )

        self.pages.top_navbar.click_on_sign_out_button()
        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_MESSAGE_6"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.pages.top_navbar.click_on_inbox_option()

        self.logger.info("Verifying that the messages are displayed inside the inbox section")

        assert self.pages.inbox_page.is_message_displayed_inside_the_inbox_section(
            username=user_one
        ), "Messages are not displayed inside the inbox section. They should have been!"

        self.logger.info(
            "Deleting all messages from the inbox page via the 'delete selected button'"
        )

        self.pages.inbox_page.delete_all_displayed_inbox_messages_via_delete_selected_button()

        self.logger.info(
            "Verifying that the messages are no longer displayed inside the inbox section"
        )

        assert not (
            self.pages.inbox_page.is_message_displayed_inside_the_inbox_section(username=user_one)
        )

        self.logger.info("Verifying that the correct banner is displayed")

        check.equal(
            self.pages.inbox_page.get_text_inbox_page_message_banner_text(),
            InboxPageMessages.MESSAGE_DELETED_BANNER_TEXT,
            f"Incorrect message banner displayed. "
            f"Expected: {InboxPageMessages.MESSAGE_DELETED_BANNER_TEXT} "
            f"Received: {self.pages.inbox_page.get_text_inbox_page_message_banner_text()}",
        )
