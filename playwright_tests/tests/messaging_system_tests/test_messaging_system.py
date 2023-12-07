import pytest
import pytest_check as check
from playwright.sync_api import expect

from playwright_tests.core.testutilities import TestUtilities
from playwright_tests.messages.mess_system_pages_messages.inbox_page_messages import (
    InboxPageMessages)
from playwright_tests.messages.mess_system_pages_messages.new_message_page_messages import (
    NewMessagePageMessages)
from playwright_tests.messages.mess_system_pages_messages.sent_messages_page_messages import (
    SentMessagesPageMessages)
from playwright_tests.messages.my_profile_pages_messages.my_profile_page_messages import (
    MyProfileMessages)


class TestMessagingSystem(TestUtilities):
    # C891415
    @pytest.mark.messagingSystem
    def test_there_are_no_messages_here_text_is_displayed_when_no_messages_are_available(self):
        self.logger.info("Signing in with a normal user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts['TEST_ACCOUNT_12']
        ))

        self.logger.info("Navigating to the inbox page")

        self.sumo_pages.top_navbar.click_on_inbox_option()

        self.logger.info(
            "Clearing the inbox if there are messages"
        )

        if self.sumo_pages.inbox_page.are_inbox_messages_displayed():
            self.sumo_pages.inbox_page.delete_all_displayed_inbox_messages()
            self.logger.info("Messages found. Clearing the list")

        self.logger.info("Verifying that the correct page message is displayed")

        check.equal(
            self.sumo_pages.inbox_page.get_text_of_inbox_no_message_header(),
            InboxPageMessages.NO_MESSAGES_IN_INBOX_TEXT,
            f"Incorrect message displayed. "
            f"Expected: "
            f"{InboxPageMessages.NO_MESSAGES_IN_INBOX_TEXT} "
            f"Received: "
            f"{self.sumo_pages.inbox_page.get_text_of_inbox_no_message_header()}",
        )

        self.logger.info("Navigating to the 'Sent Messages' page")

        self.sumo_pages.mess_system_user_navbar.click_on_messaging_system_navbar_sent_messages()

        self.logger.info(
            "Verifying if there are messages displayed inside the inbox section. "
            "If there are, we are clearing them all"
        )

        if self.sumo_pages.sent_message_page.are_sent_messages_displayed():
            self.sumo_pages.sent_message_page.delete_all_displayed_sent_messages()
            self.logger.info("Messages found. Clearing the list")

        self.logger.info("Verifying that the correct page message is displayed")

        check.equal(
            self.sumo_pages.sent_message_page.get_sent_messages_no_message_text(),
            SentMessagesPageMessages.NO_MESSAGES_IN_SENT_MESSAGES_TEXT,
            f"Incorrect message displayed. "
            f"Expected: "
            f"{SentMessagesPageMessages.NO_MESSAGES_IN_SENT_MESSAGES_TEXT} "
            f"Received: "
            f"{self.sumo_pages.sent_message_page.get_sent_messages_no_message_text()}",
        )

    # C2094292
    # This test needs to be updated to fetch the username from a different place
    @pytest.mark.messagingSystem
    def test_private_messages_can_be_sent_via_user_profiles(self):
        user_two = super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_2"]
        )

        self.logger.info("Signing in with user one")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_1"]
        ))

        user_one = self.sumo_pages.top_navbar.get_text_of_logged_in_username()

        self.navigate_to_link(
            MyProfileMessages.get_my_profile_stage_url(username=user_two)
        )

        self.logger.info("Clicking on the 'Private Message button'")
        self.sumo_pages.my_profile_page.click_on_private_message_button()

        self.logger.info(
            "Verifying that the receiver is automatically added inside the 'To' field"
        )
        # Firefox GH runner fails here. We are running this assertion only in Chrome for now
        if self.browser == "chrome":
            assert self.sumo_pages.new_message_page.get_user_to_text() == user_two, (
                f"Incorrect 'To' receiver. Expected: {user_two}. "
                f"Received: {self.sumo_pages.new_message_page.get_user_to_text()}"
            )

        self.logger.info("Adding text into the new message textarea field")
        self.sumo_pages.new_message_page.fill_into_new_message_body_textarea(
            self.user_message_test_data["valid_user_message"]["message"]
        )

        self.logger.info("Clicking on the 'Send' button")
        self.sumo_pages.new_message_page.click_on_new_message_send_button()

        self.logger.info("Verifying that the correct message sent banner is displayed")
        check.equal(
            self.sumo_pages.inbox_page.get_text_inbox_page_message_banner_text(),
            InboxPageMessages.MESSAGE_SENT_BANNER_TEXT,
            f"Incorrect banner text displayed. "
            f"Expected: "
            f"{InboxPageMessages.MESSAGE_SENT_BANNER_TEXT}. "
            f"Received: "
            f"{self.sumo_pages.inbox_page.get_text_inbox_page_message_banner_text()}",
        )

        self.logger.info(
            "Clicking on the 'Sent Messages option' "
            "and verifying that the message was successfully sent"
        )
        self.sumo_pages.mess_system_user_navbar.click_on_messaging_system_navbar_sent_messages()

        self.logger.info("Verifying that the sent message is displayed")
        expect(self.sumo_pages.sent_message_page.sent_messages(
            username=user_two
        )).to_be_visible()

        self.logger.info(
            "Deleting the message from the sent messages link "
            "and verifying that the message is no longer displayed"
        )

        self.sumo_pages.sent_message_page.click_on_sent_message_delete_button(username=user_two)
        self.sumo_pages.sent_message_page.click_on_delete_page_delete_button()

        self.logger.info("Verifying that the correct banner is displayed")
        check.equal(
            self.sumo_pages.sent_message_page.get_sent_messages_page_deleted_banner_text(),
            SentMessagesPageMessages.DELETE_MESSAGE_BANNER_TEXT,
            f"Wrong message displayed inside the banner. "
            f"Expected: "
            f"{SentMessagesPageMessages.DELETE_MESSAGE_BANNER_TEXT} "
            f"Received: "
            f"{self.sumo_pages.sent_message_page.get_sent_messages_page_deleted_banner_text()}",
        )

        expect(
            self.sumo_pages.sent_message_page.sent_messages(username=user_two)
        ).to_be_hidden()

        self.logger.info("Signing in with the user which received the message")
        self.delete_cookies()

        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_2"]
        ))

        self.logger.info(
            "Accessing the Inbox section " "and verifying that the message was received"
        )
        self.sumo_pages.top_navbar.click_on_inbox_option()

        expect(self.sumo_pages.inbox_page.inbox_message(
            username=user_one
        )).to_be_visible()

        self.logger.info(
            "Deleting the message and verifying that it "
            "is no longer displayed inside the inbox section"
        )
        self.sumo_pages.inbox_page.click_on_inbox_message_delete_button(username=user_one)

        self.sumo_pages.inbox_page.click_on_delete_page_delete_button()

        expect(
            self.sumo_pages.inbox_page.inbox_message(username=user_one)
        ).to_be_hidden()

        self.logger.info("Verifying that the correct banner is displayed")

        check.equal(
            self.sumo_pages.sent_message_page.get_sent_messages_page_deleted_banner_text(),
            SentMessagesPageMessages.DELETE_MESSAGE_BANNER_TEXT,
            f"Wrong message displayed inside the banner. "
            f"Expected: "
            f"{SentMessagesPageMessages.DELETE_MESSAGE_BANNER_TEXT} "
            f"Received: "
            f"{self.sumo_pages.sent_message_page.get_sent_messages_page_deleted_banner_text()}",
        )

    # C891419
    @pytest.mark.messagingSystem
    def test_private_message_can_be_sent_via_new_message_page(self):
        test_user = super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_4"]
        )

        self.logger.info("Signing in with a normal user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_3"]
        ))

        user_one = self.sumo_pages.top_navbar.get_text_of_logged_in_username()

        self.logger.info(
            "Accessing the 'New Message page " "and sending a message to another user'"
        )
        self.sumo_pages.top_navbar.click_on_inbox_option()
        self.sumo_pages.mess_system_user_navbar.click_on_messaging_system_navbar_new_message()
        self.sumo_pages.messaging_system_flow.complete_send_message_form_with_data(
            recipient_username=test_user,
            message_body=super().user_message_test_data["valid_user_message"]["message"],
        )
        self.sumo_pages.new_message_page.click_on_new_message_send_button()

        self.logger.info("Verifying that the correct banner is displayed")
        check.equal(
            self.sumo_pages.inbox_page.get_text_inbox_page_message_banner_text(),
            InboxPageMessages.MESSAGE_SENT_BANNER_TEXT,
            f"Incorrect banner text displayed. "
            f"Expected: "
            f"{InboxPageMessages.MESSAGE_SENT_BANNER_TEXT} "
            f"Received: "
            f"{self.sumo_pages.inbox_page.get_text_inbox_page_message_banner_text()}",
        )

        self.logger.info(
            "Verifying that the sent message is displayed inside the 'sent messages' page"
        )
        self.sumo_pages.mess_system_user_navbar.click_on_messaging_system_navbar_sent_messages()

        expect(self.sumo_pages.sent_message_page.sent_messages(test_user)).to_be_visible()

        self.logger.info("Clearing the sent messages list")
        self.sumo_pages.sent_message_page.delete_all_displayed_sent_messages()

        self.logger.info(
            "Signing in with the receiver account and verifying that the message "
            "is displayed inside the inbox section"
        )
        self.delete_cookies()

        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_4"]
        ))

        self.sumo_pages.top_navbar.click_on_inbox_option()

        expect(self.sumo_pages.inbox_page.inbox_message(
            username=user_one
        )).to_be_visible()

        self.logger.info("Clearing the inbox")

        self.sumo_pages.inbox_page.delete_all_displayed_inbox_messages()

    # C891412, C891413
    @pytest.mark.messagingSystem
    def test_navbar_options_redirect_to_the_correct_page_and_options_are_correctly_highlighted(
            self,
    ):

        self.logger.info("Signing in with a normal user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        self.logger.info("Accessing the inbox section via the top-navbar")
        self.sumo_pages.top_navbar.click_on_inbox_option()

        self.logger.info(
            "Verifying that we are on the correct page "
            "and the 'Inbox' navbar option is highlighted"
        )
        expect(self.page).to_have_url(InboxPageMessages.INBOX_PAGE_STAGE_URL)

        expect(
            self.sumo_pages.mess_system_user_navbar.get_inbox_navbar_element()
        ).to_have_css("background-color", InboxPageMessages.NAVBAR_INBOX_SELECTED_BG_COLOR)

        self.sumo_pages.mess_system_user_navbar.click_on_messaging_system_navbar_sent_messages()

        self.logger.info(
            "Verifying that we are on the correct page "
            "and the 'Sent Messages' page is successfully displayed"
        )
        expect(
            self.page
        ).to_have_url(SentMessagesPageMessages.SENT_MESSAGES_PAGE_URL)

        self.logger.info("Verifying that the 'Sent Messages' option is highlighted")
        expect(
            self.sumo_pages.mess_system_user_navbar.get_sent_messages_navbar_element()
        ).to_have_css("background-color",
                      SentMessagesPageMessages.NAVBAR_SENT_MESSAGES_SELECTED_BG_COLOR)

        self.logger.info("Clicking on the 'New message' navbar option")
        self.sumo_pages.mess_system_user_navbar.click_on_messaging_system_navbar_new_message()

        self.logger.info("Verifying that the 'New Message' page is displayed")
        expect(
            self.page
        ).to_have_url(NewMessagePageMessages.NEW_MESSAGE_PAGE_STAGE_URL)

        self.logger.info("Verifying that the 'New Message' navbar option is highlighted")
        expect(
            self.sumo_pages.mess_system_user_navbar.get_new_message_navbar_element()
        ).to_have_css("background-color",
                      NewMessagePageMessages.NAVBAR_NEW_MESSAGE_SELECTED_BG_COLOR)

        self.logger.info("Clicking on the navbar inbox messaging system navbar option")
        self.sumo_pages.mess_system_user_navbar.click_on_messaging_system_navbar_inbox()

        self.logger.info(
            "Verifying that we are on the correct page "
            "and the 'Inbox' navbar option is highlighted"
        )
        expect(self.page).to_have_url(InboxPageMessages.INBOX_PAGE_STAGE_URL)

        expect(
            self.sumo_pages.mess_system_user_navbar.get_inbox_navbar_element()
        ).to_have_css("background-color", InboxPageMessages.NAVBAR_INBOX_SELECTED_BG_COLOR)

    # C891416
    @pytest.mark.messagingSystem
    def test_new_message_field_validation(self):
        user_two = self.username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_1"]
        )
        self.logger.info("Signing in with normal user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        self.logger.info("Accessing the New Message page")
        self.sumo_pages.top_navbar.click_on_inbox_option()
        self.sumo_pages.mess_system_user_navbar.click_on_messaging_system_navbar_new_message()
        self.sumo_pages.new_message_page.click_on_new_message_send_button()

        self.logger.info("Verifying that we are still on the 'New Message page'")
        expect(self.page).to_have_url(NewMessagePageMessages.NEW_MESSAGE_PAGE_STAGE_URL)

        self.logger.info("Adding a valid user inside the 'To' field")
        self.sumo_pages.new_message_page.type_into_new_message_to_input_field(text=user_two)
        self.sumo_pages.new_message_page.click_on_a_searched_user(username=user_two)

        self.logger.info(
            "Clicking the 'Send' button and verifying that we are still on the same page"
        )
        self.sumo_pages.new_message_page.click_on_new_message_send_button()

        expect(self.page).to_have_url(NewMessagePageMessages.NEW_MESSAGE_PAGE_STAGE_URL)

        self.logger.info("Verifying that the default remaining characters is the correct one")
        check.equal(
            self.sumo_pages.new_message_page.get_characters_remaining_text(),
            NewMessagePageMessages.NEW_MESSAGE_DEFAULT_REMAINING_CHARACTERS,
            f" The default character remaining string is not the correct one! "
            f"Expected: {NewMessagePageMessages.NEW_MESSAGE_DEFAULT_REMAINING_CHARACTERS}"
            f"Received: {self.sumo_pages.new_message_page.get_characters_remaining_text()}",
        )

        self.logger.info("Verifying that the characters remaining color is the expected one")
        expect(
            self.sumo_pages.new_message_page.get_characters_remaining_text_element()
        ).to_have_css("color", NewMessagePageMessages.ENOUGH_CHARACTERS_REMAINING_COLOR)

        # To check if firefox container crashes. If not remove this part and uncomment the if
        # clause

        # if self.browser == "chrome":
        #     self.logger.info("Adding 9990 characters inside the input field")
        #
        #     self.pages.new_message_page.type_into_new_message_body_textarea(
        #         text=super().user_message_test_data["valid_user_message"][
        #             "9990_characters_long_message"
        #         ]
        #     )
        self.logger.info("Adding 9990 characters inside the input field")

        self.sumo_pages.new_message_page.fill_into_new_message_body_textarea(
            text=super().user_message_test_data["valid_user_message"][
                "9990_characters_long_message"
            ])
        check.equal(
            self.sumo_pages.new_message_page.get_characters_remaining_text(),
            NewMessagePageMessages.TEN_CHARACTERS_REMAINING_MESSAGE,
            f"Incorrect remaining characters string displayed. "
            f"Expected: {NewMessagePageMessages.TEN_CHARACTERS_REMAINING_MESSAGE}"
            f"Displayed: {self.sumo_pages.new_message_page.get_characters_remaining_text()}",
        )
        self.logger.info("Verifying that the characters remaining color is the expected one")
        expect(self.sumo_pages.new_message_page.get_characters_remaining_text_element()
               ).to_have_css("color", NewMessagePageMessages.ENOUGH_CHARACTERS_REMAINING_COLOR)

        # elif self.browser == "firefox":
        #     check.equal(
        #         self.pages.new_message_page.get_characters_remaining_text_color(),
        #         NewMessagePageMessages.ENOUGH_CHARACTERS_REMAINING_COLOR_FIREFOX,
        #         f"Incorrect color displayed. "
        #         f"Expected: {NewMessagePageMessages.ENOUGH_CHARACTERS_REMAINING_COLOR_FIREFOX} "
        #         f"Received: {self.pages.new_message_page.get_characters_remaining_text_color()}",
        #     )

        self.logger.info("Adding one character inside the textarea field")

        self.sumo_pages.new_message_page.type_into_new_message_body_textarea(
            text=super().user_message_test_data["valid_user_message"]["one_character_message"]
        )

        self.logger.info("Verifying that the char remaining string is updated accordingly")
        check.equal(
            self.sumo_pages.new_message_page.get_characters_remaining_text(),
            NewMessagePageMessages.NINE_CHARACTERS_REMAINING_MESSAGE,
            f"Incorrect remaining characters string displayed. "
            f"Expected:{NewMessagePageMessages.NINE_CHARACTERS_REMAINING_MESSAGE} "
            f"Displayed: {self.sumo_pages.new_message_page.get_characters_remaining_text()}",
        )

        self.logger.info("Verifying that the characters remaining color is the expected one")
        expect(self.sumo_pages.new_message_page.get_characters_remaining_text_element()
               ).to_have_css("color", NewMessagePageMessages.NO_CHARACTERS_REMAINING_COLOR)

        # elif self.browser == "firefox":
        #     check.equal(
        #         self.pages.new_message_page.get_characters_remaining_text_color(),
        #         NewMessagePageMessages.NO_CHARACTERS_REMAINING_COLOR_FIREFOX,
        #         f"Incorrect color displayed. "
        #         f"Expected: {NewMessagePageMessages.NO_CHARACTERS_REMAINING_COLOR_FIREFOX} "
        #         f"Received: {self.pages.new_message_page.get_characters_remaining_text_color()}",
        #     )

        self.logger.info("Adding 9 characters inside the textarea field")

        self.sumo_pages.new_message_page.type_into_new_message_body_textarea(
            text=super().user_message_test_data["valid_user_message"]["9_characters_message"]
        )

        self.logger.info("Verifying that the char remaining string is updated accordingly")
        expect(
            self.sumo_pages.new_message_page.get_characters_remaining_text_element()
        ).to_have_css("color", NewMessagePageMessages.NO_CHARACTERS_REMAINING_COLOR)
        # elif self.browser == "firefox":
        #     check.equal(
        #         self.pages.new_message_page.get_characters_remaining_text_color(),
        #         NewMessagePageMessages.NO_CHARACTERS_REMAINING_COLOR_FIREFOX,
        #         f"Incorrect color displayed. "
        #         f"Expected: {NewMessagePageMessages.NO_CHARACTERS_REMAINING_COLOR_FIREFOX} "
        #         f"Received: {self.pages.new_message_page.get_characters_remaining_text_color()}",
        #     )

        self.logger.info("Verifying that the characters remaining color is the expected one")
        expect(
            self.sumo_pages.new_message_page.get_characters_remaining_text_element()
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
    def test_new_message_cancel_button(self):
        user_two = super().username_extraction_from_email(
            super().user_secrets_accounts["TEST_ACCOUNT_13"]
        )
        self.logger.info("Signing in with a normal user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))
        user_one = self.sumo_pages.top_navbar.get_text_of_logged_in_username()

        self.logger.info("Accessing the 'New Message' section")
        self.sumo_pages.top_navbar.click_on_inbox_option()
        self.sumo_pages.mess_system_user_navbar.click_on_messaging_system_navbar_new_message()

        self.logger.info("Filling the new message form with data")
        self.sumo_pages.messaging_system_flow.complete_send_message_form_with_data(
            recipient_username=user_two,
            message_body=super().user_message_test_data["valid_user_message"]["message"],
        )

        self.logger.info("Clicking on the 'Cancel' button")
        self.sumo_pages.new_message_page.click_on_new_message_cancel_button()

        self.logger.info("Verifying that the user is redirected to the inbox page")
        expect(
            self.sumo_pages.mess_system_user_navbar.get_inbox_navbar_element()
        ).to_have_css("background-color", InboxPageMessages.NAVBAR_INBOX_SELECTED_BG_COLOR)

        expect(self.page).to_have_url(InboxPageMessages.INBOX_PAGE_STAGE_URL)

        self.logger.info(
            "Navigating to the 'Sent Messages' page nad verifying that the message was not sent"
        )
        self.sumo_pages.mess_system_user_navbar.click_on_messaging_system_navbar_sent_messages()

        expect(self.sumo_pages.sent_message_page.sent_messages(username=user_two)
               ).to_be_hidden()

        self.logger.info("Signing out and signing in with the receiver account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_13"]
        ))

        self.logger.info(
            "Navigating to the receiver inbox and verifying that no message was received"
        )
        self.sumo_pages.top_navbar.click_on_inbox_option()

        expect(
            self.sumo_pages.inbox_page.inbox_message(username=user_one)
        ).to_be_hidden()

    # C891418
    @pytest.mark.messagingSystem
    def test_new_message_preview(self):
        test_user = self.username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_13"]
        )

        self.logger.info("Signing in with a normal user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        username = self.sumo_pages.top_navbar.get_text_of_logged_in_username()

        self.logger.info("Accessing the inbox section")
        self.sumo_pages.top_navbar.click_on_inbox_option()

        self.logger.info("Navigating to the new message page")
        self.sumo_pages.mess_system_user_navbar.click_on_messaging_system_navbar_new_message()

        self.logger.info("Adding text inside the message content section")
        self.sumo_pages.messaging_system_flow.complete_send_message_form_with_data(
            recipient_username=test_user,
            message_body=super().user_message_test_data["valid_user_message"]["message"],
        )

        self.logger.info("Clicking on  the 'Preview' button")
        self.sumo_pages.new_message_page.click_on_new_message_preview_button()

        self.logger.info("Verifying that the preview section is successfully displayed")
        expect(
            self.sumo_pages.new_message_page.message_preview_section_element()
        ).to_be_visible()

        self.logger.info("Verifying that all the preview items are displayed")

        check.equal(
            self.sumo_pages.new_message_page.get_text_of_test_data_first_paragraph_text(),
            NewMessagePageMessages.PREVIEW_MESSAGE_CONTENT_FIRST_PARAGRAPH_TEXT,
            f"Wrong text displayed. "
            f"Expected: "
            f"{NewMessagePageMessages.PREVIEW_MESSAGE_CONTENT_FIRST_PARAGRAPH_TEXT} "
            f"Received: "
            f"{self.sumo_pages.new_message_page.get_text_of_test_data_first_paragraph_text()}",
        )

        check.equal(
            self.sumo_pages.new_message_page.get_text_of_test_data_first_p_strong_text(),
            NewMessagePageMessages.PREVIEW_MESSAGE_CONTENT_FIRST_PARAGRAPH_STRONG_TEXT,
            f"Wrong text displayed. "
            f"Expected:"
            f"{NewMessagePageMessages.PREVIEW_MESSAGE_CONTENT_FIRST_PARAGRAPH_STRONG_TEXT} "
            f"Received: "
            f"{self.sumo_pages.new_message_page.get_text_of_test_data_first_p_strong_text()}",
        )

        check.equal(
            self.sumo_pages.new_message_page.get_text_of_test_data_first_p_italic_text(),
            NewMessagePageMessages.PREVIEW_MESSAGE_CONTENT_FIRST_PARAGRAPH_ITALIC_TEXT,
            f"Wrong text displayed. "
            f"Expected:"
            f"{NewMessagePageMessages.PREVIEW_MESSAGE_CONTENT_FIRST_PARAGRAPH_ITALIC_TEXT} "
            f"Received: "
            f"{self.sumo_pages.new_message_page.get_text_of_test_data_first_p_italic_text()}",
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
            self.sumo_pages.new_message_page.get_text_of_numbered_list_items(),
            numbered_list_items,
            f"Wrong data displayed in the numbered list. Expected {numbered_list_items} "
            f"Received: {self.sumo_pages.new_message_page.get_text_of_numbered_list_items()}",
        )

        check.equal(
            self.sumo_pages.new_message_page.get_text_of_bulleted_list_items(),
            bulleted_list_items,
            f"Wrong data displayed in the numbered list. Expected {bulleted_list_items} "
            f"Received: {self.sumo_pages.new_message_page.get_text_of_numbered_list_items()}",
        )
        expect(
            self.sumo_pages.new_message_page.new_message_preview_external_link_test_data_element()
        ).to_be_visible()

        expect(
            self.sumo_pages.new_message_page.new_message_preview_internal_link_test_data_element()
        ).to_be_visible()

        self.logger.info(
            "Clicking on the internal link and "
            "verifying that the user is redirected to the correct article"
        )
        self.sumo_pages.new_message_page.click_on_preview_internal_link()

        assert (
            self.sumo_pages.kb_article_page.get_text_of_article_title()
            == NewMessagePageMessages.PREVIEW_MESSAGE_INTERNAL_LINK_TITLE
        ), (
            f"Incorrect article title displayed! "
            f"Expected: {NewMessagePageMessages.PREVIEW_MESSAGE_INTERNAL_LINK_TITLE} "
            f"Received: {self.sumo_pages.kb_article_page.get_text_of_article_title()}"
        )

        self.logger.info(
            "Verifying that the message was no sent by checking the 'Sent Messages page'"
        )
        self.sumo_pages.top_navbar.click_on_inbox_option()

        self.sumo_pages.mess_system_user_navbar.click_on_messaging_system_navbar_sent_messages()

        expect(
            self.sumo_pages.sent_message_page.sent_messages(username=test_user)
        ).to_be_hidden()

        self.logger.info(
            "Signing in with the potential message receiver "
            "and verifying that no message was received"
        )

        self.logger.info("Signing in with a normal user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_13"]
        ))

        self.sumo_pages.top_navbar.click_on_inbox_option()

        expect(
            self.sumo_pages.inbox_page.inbox_message(username=username)
        ).to_be_hidden()

    # C891421, C891424
    @pytest.mark.messagingSystem
    def test_messages_can_be_selected_and_deleted(self):
        test_user = self.username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_6"]
        )

        self.logger.info("Signing in with a normal user account")

        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_5"]
        ))

        user_one = self.sumo_pages.top_navbar.get_text_of_logged_in_username()

        self.logger.info(
            "Accessing the 'New Message' page and sending a message to a different user"
        )
        self.sumo_pages.top_navbar.click_on_inbox_option()
        self.sumo_pages.mess_system_user_navbar.click_on_messaging_system_navbar_new_message()
        self.sumo_pages.messaging_system_flow.complete_send_message_form_with_data(
            recipient_username=test_user,
            message_body=super().user_message_test_data["valid_user_message"]["message"],
        )
        self.sumo_pages.new_message_page.click_on_new_message_send_button()

        self.logger.info("Navigating to the sent messages page")

        self.sumo_pages.mess_system_user_navbar.click_on_messaging_system_navbar_sent_messages()

        self.logger.info("Clicking on the 'Delete Selected' button")

        self.sumo_pages.sent_message_page.click_on_delete_selected_button()

        self.logger.info(
            "Verifying that the correct message is displayed "
            "and is no longer displayed when dismissed"
        )

        check.equal(
            self.sumo_pages.sent_message_page.get_sent_messages_page_deleted_banner_text(),
            SentMessagesPageMessages.NO_MESSAGES_SELECTED_BANNER_TEXT,
            f"Incorrect banner text displayed. "
            f"Expected: "
            f"{SentMessagesPageMessages.NO_MESSAGES_SELECTED_BANNER_TEXT} "
            f"Received: "
            f"{self.sumo_pages.sent_message_page.get_sent_messages_page_deleted_banner_text()}",
        )

        self.logger.info(
            "Verifying that the message is still listed inside the sent messages section"
        )

        expect(
            self.sumo_pages.sent_message_page.sent_messages(username=test_user)
        ).to_be_visible()

        self.logger.info("Sending another message to self twice")

        for i in range(2):
            self.sumo_pages.mess_system_user_navbar.click_on_messaging_system_navbar_new_message()
            self.sumo_pages.messaging_system_flow.complete_send_message_form_with_data(
                recipient_username=user_one,
                message_body=super().user_message_test_data["valid_user_message"]["message"],
            )
            self.sumo_pages.new_message_page.click_on_new_message_send_button()

        self.logger.info(
            "Clicking on the 'delete selected' button while no messages is selected "
            "and verifying that the correct "
            "banner is displayed"
        )

        self.sumo_pages.inbox_page.click_on_inbox_delete_selected_button()

        check.equal(
            self.sumo_pages.inbox_page.get_text_inbox_page_message_banner_text(),
            InboxPageMessages.NO_MESSAGES_SELECTED_BANNER_TEXT,
            f"Incorrect messages displayed. "
            f"Expected: {InboxPageMessages.NO_MESSAGES_SELECTED_BANNER_TEXT} "
            f"Received: {self.sumo_pages.inbox_page.get_text_inbox_page_message_banner_text()}",
        )

        expect(
            self.sumo_pages.inbox_page.inbox_message(username=user_one).first
        ).to_be_visible()

        self.logger.info("Selecting the messages and deleting it via the 'delete selected button'")
        self.sumo_pages.inbox_page.delete_all_displayed_inbox_messages_via_delete_selected_button()

        self.logger.info("Verifying that the messages are no longer displayed")

        expect(
            self.sumo_pages.inbox_page.inbox_message(username=user_one)
        ).to_be_hidden()

        check.equal(
            self.sumo_pages.inbox_page.get_text_inbox_page_message_banner_text(),
            InboxPageMessages.MULTIPLE_MESSAGES_DELETION_BANNER_TEXT,
            f"Incorrect message banner displayed. "
            f"Expected: {InboxPageMessages.MULTIPLE_MESSAGES_DELETION_BANNER_TEXT} "
            f"Received: {self.sumo_pages.inbox_page.get_text_inbox_page_message_banner_text()}",
        )

        self.logger.info(
            "Navigating to the sent messages section and "
            "clearing all messages via the 'delete selected button'"
        )
        self.sumo_pages.mess_system_user_navbar.click_on_messaging_system_navbar_sent_messages()

        self.sumo_pages.sent_message_page.delete_all_sent_messages_via_delete_selected_button()

        self.logger.info("Verifying that the messages are no longer displayed")
        expect(
            self.sumo_pages.sent_message_page.sent_messages(username=user_one)
        ).to_be_hidden()

        expect(
            self.sumo_pages.sent_message_page.sent_messages(username=test_user)
        ).to_be_hidden()

        self.logger.info("Verifying that the correct banner is displayed")

        check.equal(
            self.sumo_pages.sent_message_page.get_sent_messages_page_deleted_banner_text(),
            SentMessagesPageMessages.MULTIPLE_MESSAGES_DELETION_BANNER_TEXT,
            f"Incorrect message banner displayed. "
            f"Expected: "
            f"{SentMessagesPageMessages.MULTIPLE_MESSAGES_DELETION_BANNER_TEXT} "
            f"Received: "
            f"{self.sumo_pages.sent_message_page.get_sent_messages_page_deleted_banner_text()}",
        )

        self.logger.info(
            "Signing in with the receiver account and navigating to the inbox section"
        )

        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_6"]
        ))

        self.sumo_pages.top_navbar.click_on_inbox_option()

        self.logger.info("Verifying that the messages are displayed inside the inbox section")

        expect(
            self.sumo_pages.inbox_page.inbox_message(username=user_one)
        ).to_be_visible()

        self.logger.info(
            "Deleting all messages from the inbox page via the 'delete selected button'"
        )
        self.sumo_pages.inbox_page.delete_all_displayed_inbox_messages_via_delete_selected_button()

        self.logger.info(
            "Verifying that the messages are no longer displayed inside the inbox section"
        )

        expect(
            self.sumo_pages.inbox_page.inbox_message(username=user_one)
        ).to_be_hidden()

        self.logger.info("Verifying that the correct banner is displayed")

        check.equal(
            self.sumo_pages.inbox_page.get_text_inbox_page_message_banner_text(),
            InboxPageMessages.MESSAGE_DELETED_BANNER_TEXT,
            f"Incorrect message banner displayed. "
            f"Expected: {InboxPageMessages.MESSAGE_DELETED_BANNER_TEXT} "
            f"Received: {self.sumo_pages.inbox_page.get_text_inbox_page_message_banner_text()}",
        )
