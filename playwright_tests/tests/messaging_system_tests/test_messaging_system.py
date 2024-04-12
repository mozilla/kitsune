import allure
import pytest
from pytest_check import check
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
        with allure.step("Signing in with a non-admin user account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_12']
            ))

        with allure.step("Navigating to the inbox page"):
            self.sumo_pages.top_navbar._click_on_inbox_option()

        if self.sumo_pages.inbox_page._are_inbox_messages_displayed():
            with allure.step("Clearing the inbox since there are some existing messages"):
                self.sumo_pages.inbox_page._delete_all_inbox_messages()

        with check, allure.step("Verifying that the correct message is displayed"):
            assert self.sumo_pages.inbox_page._get_text_of_inbox_no_message_header(
            ) == InboxPageMessages.NO_MESSAGES_IN_INBOX_TEXT

        with allure.step("Navigating to the 'Sent Messages' page"):
            self.sumo_pages.mess_system_user_navbar._click_on_messaging_system_nav_sent_messages()

        if self.sumo_pages.sent_message_page._are_sent_messages_displayed():
            with allure.step("Clearing sent messages list since there are some existing messages"):
                self.sumo_pages.sent_message_page._delete_all_displayed_sent_messages()

        with check, allure.step("Verifying that the correct page message is displayed"):
            assert self.sumo_pages.sent_message_page._get_sent_messages_no_message_text(
            ) == SentMessagesPageMessages.NO_MESSAGES_IN_SENT_MESSAGES_TEXT
        self.logger.info("Verifying that the correct page message is displayed")

    # C2094292
    # This test needs to be updated to fetch the username from a different place
    @pytest.mark.messagingSystem
    def test_private_messages_can_be_sent_via_user_profiles(self):
        user_two = super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_2"]
        )

        with allure.step("Signing in with a non-admin user account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_1"]
            ))

        user_one = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        with allure.step("Navigating to the profile page for user two"):
            self.navigate_to_link(
                MyProfileMessages.get_my_profile_stage_url(username=user_two)
            )

        with allure.step("Clicking on the 'Private Message button'"):
            self.sumo_pages.my_profile_page._click_on_private_message_button()

        with allure.step("Verifying that the receiver is automatically added inside the 'To' "
                         "field"):
            # Firefox GH runner fails here. We are running this assertion only in Chrome for now
            if self.requested_browser == "chrome":
                assert self.sumo_pages.new_message_page._get_user_to_text() == user_two, (
                    f"Incorrect 'To' receiver. Expected: {user_two}. "
                    f"Received: {self.sumo_pages.new_message_page._get_user_to_text()}"
                )

        with allure.step("Sending a message to the user"):
            self.sumo_pages.messaging_system_flow.complete_send_message_form_with_data(
                message_body=self.user_message_test_data["valid_user_message"]["message"]
            )

        with check, allure.step("Verifying that the correct message sent banner is displayed"):
            assert self.sumo_pages.inbox_page._get_text_inbox_page_message_banner_text(
            ) == InboxPageMessages.MESSAGE_SENT_BANNER_TEXT

        with allure.step("Clicking on the 'Sent Messages option"):
            self.sumo_pages.mess_system_user_navbar._click_on_messaging_system_nav_sent_messages()

        with allure.step("Verifying that the sent message is displayed"):
            expect(self.sumo_pages.sent_message_page._sent_messages(
                username=user_two
            )).to_be_visible()

        with allure.step("Deleting the message from the sent messages page"):
            self.sumo_pages.messaging_system_flow.delete_message_flow(
                username=user_two, from_sent_list=True
            )

        with check, allure.step("Verifying that the correct banner is displayed"):
            assert self.sumo_pages.sent_message_page._get_sent_messages_page_deleted_banner_text(
            ) == SentMessagesPageMessages.DELETE_MESSAGE_BANNER_TEXT
        self.logger.info("Verifying that the correct banner is displayed")

        with allure.step("Verifying that messages from user two are not displayed"):
            expect(
                self.sumo_pages.sent_message_page._sent_messages(username=user_two)
            ).to_be_hidden()

        with allure.step("Signing in with the user which received the message"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_2"]
            ))

        with allure.step("Accessing the Inbox section"):
            self.sumo_pages.top_navbar._click_on_inbox_option()

        with allure.step("Verifying that the inbox contains the previously sent messages"):
            expect(self.sumo_pages.inbox_page._inbox_message(
                username=user_one
            )).to_be_visible()

        with allure.step("Deleting the messages from the inbox section"):
            self.sumo_pages.messaging_system_flow.delete_message_flow(
                username=user_one, from_inbox_list=True
            )

        with allure.step("Verifying that the messages are no longer displayed inside the inbox"):
            expect(
                self.sumo_pages.inbox_page._inbox_message(username=user_one)
            ).to_be_hidden()

        with check, allure.step("Verifying that the correct banner is displayed"):
            assert self.sumo_pages.sent_message_page._get_sent_messages_page_deleted_banner_text(
            ) == SentMessagesPageMessages.DELETE_MESSAGE_BANNER_TEXT

    # C891419
    @pytest.mark.messagingSystem
    def test_private_message_can_be_sent_via_new_message_page(self):
        test_user = super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_4"]
        )

        with allure.step("Signing in with a non-admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_3"]
            ))

        user_one = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        with allure.step("Accessing the New Message page and sending a message to another user"):
            self.sumo_pages.top_navbar._click_on_inbox_option()
            self.sumo_pages.mess_system_user_navbar._click_on_messaging_system_nav_new_message()
            self.sumo_pages.messaging_system_flow.complete_send_message_form_with_data(
                recipient_username=test_user,
                message_body=super().user_message_test_data["valid_user_message"]["message"],
            )

        with check, allure.step("Verifying that the correct banner is displayed"):
            assert self.sumo_pages.inbox_page._get_text_inbox_page_message_banner_text(
            ) == InboxPageMessages.MESSAGE_SENT_BANNER_TEXT
        self.logger.info("Verifying that the correct banner is displayed")

        with allure.step("Verifying that the sent message is displayed inside the sent messages "
                         "page"):
            self.sumo_pages.mess_system_user_navbar._click_on_messaging_system_nav_sent_messages()
            expect(self.sumo_pages.sent_message_page._sent_messages(test_user)).to_be_visible()

        with allure.step("Clearing the sent messages list"):
            self.sumo_pages.sent_message_page._delete_all_displayed_sent_messages()

        with allure.step("Signing in with the receiver account and verifying that the message is "
                         "displayed inside the inbox section"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_4"]
            ))
            self.sumo_pages.top_navbar._click_on_inbox_option()
            expect(self.sumo_pages.inbox_page._inbox_message(
                username=user_one
            )).to_be_visible()

        with allure.step("Clearing the inbox"):
            self.sumo_pages.inbox_page._delete_all_inbox_messages()

    # C891412, C891413
    @pytest.mark.messagingSystem
    def test_navbar_options_redirect_to_the_correct_page_and_options_are_correctly_highlighted(
            self,
    ):
        with allure.step("Signing in with a non-admin user account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))

        with allure.step("Accessing the inbox section via the top-navbar"):
            self.sumo_pages.top_navbar._click_on_inbox_option()

        with allure.step("Verifying that we are on the correct page and the 'Inbox' navbar "
                         "option is highlighted"):
            expect(self.page).to_have_url(InboxPageMessages.INBOX_PAGE_STAGE_URL)
            expect(
                self.sumo_pages.mess_system_user_navbar._get_inbox_navbar_element()
            ).to_have_css("background-color", InboxPageMessages.NAVBAR_INBOX_SELECTED_BG_COLOR)

        with allure.step("Clicking on the sent messages navbar option"):
            self.sumo_pages.mess_system_user_navbar._click_on_messaging_system_nav_sent_messages()

        with allure.step("Verifying that we are on the correct page and the 'Sent Messages' "
                         "navbar option is highlighted"):
            expect(
                self.page
            ).to_have_url(SentMessagesPageMessages.SENT_MESSAGES_PAGE_URL)
            expect(
                self.sumo_pages.mess_system_user_navbar._get_sent_messages_navbar_element()
            ).to_have_css("background-color",
                          SentMessagesPageMessages.NAVBAR_SENT_MESSAGES_SELECTED_BG_COLOR)

        with allure.step("Clicking on the 'New message' navbar option"):
            self.sumo_pages.mess_system_user_navbar._click_on_messaging_system_nav_new_message()

        with allure.step("Verifying that we are on the correct page and the 'New Message' navbar "
                         "option is successfully highlighted"):
            expect(
                self.page
            ).to_have_url(NewMessagePageMessages.NEW_MESSAGE_PAGE_STAGE_URL)
            expect(
                self.sumo_pages.mess_system_user_navbar._get_new_message_navbar_element()
            ).to_have_css("background-color",
                          NewMessagePageMessages.NAVBAR_NEW_MESSAGE_SELECTED_BG_COLOR)

        with allure.step("Clicking on the navbar inbox messaging system navbar option"):
            self.sumo_pages.mess_system_user_navbar._click_on_messaging_system_navbar_inbox()

        with allure.step("Verifying that we are on the correct page and the 'Inbox' navbar "
                         "option is highlighted"):
            expect(self.page).to_have_url(InboxPageMessages.INBOX_PAGE_STAGE_URL)
            expect(
                self.sumo_pages.mess_system_user_navbar._get_inbox_navbar_element()
            ).to_have_css("background-color", InboxPageMessages.NAVBAR_INBOX_SELECTED_BG_COLOR)

    # C891416
    @pytest.mark.messagingSystem
    def test_new_message_field_validation(self):
        user_two = self.username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_1"]
        )

        with allure.step("Signing in with a non-admin user account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))

        with allure.step("Accessing the New Message page"):
            self.sumo_pages.top_navbar._click_on_inbox_option()
            self.sumo_pages.mess_system_user_navbar._click_on_messaging_system_nav_new_message()

        with allure.step("Trying to submit the form without any data and verifying that we are "
                         "still on the 'New Message' page"):
            self.sumo_pages.messaging_system_flow.complete_send_message_form_with_data()
            expect(self.page).to_have_url(NewMessagePageMessages.NEW_MESSAGE_PAGE_STAGE_URL)

        with allure.step("Adding a recipient inside the 'To' field and trying to submit the form "
                         "without any message body"):
            self.sumo_pages.messaging_system_flow.complete_send_message_form_with_data(
                recipient_username=user_two
            )
            expect(self.page).to_have_url(NewMessagePageMessages.NEW_MESSAGE_PAGE_STAGE_URL)

        with check, allure.step("Verifying that the default remaining characters is the correct "
                                "one"):
            assert (self.sumo_pages.new_message_page
                    ._get_characters_remaining_text() in NewMessagePageMessages
                    .NEW_MESSAGE_DEFAULT_REMAINING_CHARACTERS)

        with allure.step("Verifying that the characters remaining color is the expected one"):
            expect(
                self.sumo_pages.new_message_page._get_characters_remaining_text_element()
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

        with allure.step("Adding 9990 characters inside the input field"):
            self.sumo_pages.new_message_page._fill_into_new_message_body_textarea(
                text=super().user_message_test_data["valid_user_message"][
                    "9990_characters_long_message"
                ])

        with check, allure.step("Verifying that the correct remaining characters left message is "
                                "displayed"):
            assert self.sumo_pages.new_message_page._get_characters_remaining_text(
            ) in NewMessagePageMessages.TEN_CHARACTERS_REMAINING_MESSAGE

        with allure.step("Verifying that the characters remaining color is the expected one"):
            expect(self.sumo_pages.new_message_page._get_characters_remaining_text_element()
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
            self.sumo_pages.new_message_page._type_into_new_message_body_textarea(
                text=super().user_message_test_data["valid_user_message"]["one_character_message"]
            )

        with check, allure.step("Verifying that the char remaining string is updated accordingly"):
            assert self.sumo_pages.new_message_page._get_characters_remaining_text(
            ) in NewMessagePageMessages.NINE_CHARACTERS_REMAINING_MESSAGE

        with allure.step("Verifying that the characters remaining color is the expected one"):
            expect(self.sumo_pages.new_message_page._get_characters_remaining_text_element()
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
            self.sumo_pages.new_message_page._type_into_new_message_body_textarea(
                text=super().user_message_test_data["valid_user_message"]["9_characters_message"]
            )

        with allure.step("Verifying that the char remaining string is updated accordingly"):
            expect(
                self.sumo_pages.new_message_page._get_characters_remaining_text_element()
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
                self.sumo_pages.new_message_page._get_characters_remaining_text_element()
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

        with allure.step("Signing in with a non-admin user account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))

        user_one = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        with allure.step("Accessing the 'New Message' section"):
            self.sumo_pages.top_navbar._click_on_inbox_option()
            self.sumo_pages.mess_system_user_navbar._click_on_messaging_system_nav_new_message()

        with allure.step("Filling the new message form with data"):
            self.sumo_pages.messaging_system_flow.complete_send_message_form_with_data(
                recipient_username=user_two,
                message_body=super().user_message_test_data["valid_user_message"]["message"],
                submit_message=False
            )

        with allure.step("Clicking on the 'Cancel' button and verifying that the user is "
                         "redirected back to the inbox page"):
            self.sumo_pages.new_message_page._click_on_new_message_cancel_button()
            expect(
                self.sumo_pages.mess_system_user_navbar._get_inbox_navbar_element()
            ).to_have_css("background-color", InboxPageMessages.NAVBAR_INBOX_SELECTED_BG_COLOR)
            expect(self.page).to_have_url(InboxPageMessages.INBOX_PAGE_STAGE_URL)

        with allure.step("Navigating to the 'Sent Messages' page and verifying that the message "
                         "was not sent"):
            self.sumo_pages.mess_system_user_navbar._click_on_messaging_system_nav_sent_messages()
            expect(self.sumo_pages.sent_message_page._sent_messages(username=user_two)
                   ).to_be_hidden()

        with allure.step("Signing out and signing in with the receiver account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_13"]
            ))

        with allure.step("Navigating to the receiver inbox and verifying that no message was "
                         "received"):
            self.sumo_pages.top_navbar._click_on_inbox_option()
            expect(
                self.sumo_pages.inbox_page._inbox_message(username=user_one)
            ).to_be_hidden()

    # C891418
    @pytest.mark.messagingSystem
    def test_new_message_preview(self):
        test_user = self.username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_13"]
        )

        with allure.step("Signing in with a non-admin user account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))

        username = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        with allure.step("Accessing the inbox section and navigating to the new message page"):
            self.sumo_pages.top_navbar._click_on_inbox_option()
            self.sumo_pages.mess_system_user_navbar._click_on_messaging_system_nav_new_message()

        with allure.step("Adding text inside the message content section"):
            self.sumo_pages.messaging_system_flow.complete_send_message_form_with_data(
                recipient_username=test_user,
                message_body=super().user_message_test_data["valid_user_message"]["message"],
                submit_message=False
            )

        with allure.step("Clicking on the 'Preview' button and verifying that the preview "
                         "section is successfully displayed"):
            self.sumo_pages.new_message_page._click_on_new_message_preview_button()
            expect(
                self.sumo_pages.new_message_page._message_preview_section_element()
            ).to_be_visible()

        with check, allure.step("Verifying that all the preview items are displayed"):
            assert self.sumo_pages.new_message_page._get_text_of_test_data_first_paragraph_text(
            ) in NewMessagePageMessages.PREVIEW_MESSAGE_CONTENT_FIRST_PARAGRAPH_TEXT

            assert self.sumo_pages.new_message_page._get_text_of_test_data_first_p_strong_text(
            ) in NewMessagePageMessages.PREVIEW_MESSAGE_CONTENT_FIRST_PARAGRAPH_STRONG_TEXT

            assert self.sumo_pages.new_message_page._get_text_of_test_data_first_p_italic_text(
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

            assert self.sumo_pages.new_message_page._get_text_of_numbered_list_items(
            ) == numbered_list_items

            assert self.sumo_pages.new_message_page._get_text_of_bulleted_list_items(
            ) == bulleted_list_items

            expect(
                self.sumo_pages.new_message_page.
                _new_message_preview_external_link_test_data_element()
            ).to_be_visible()

            expect(
                self.sumo_pages.new_message_page.
                _new_message_preview_internal_link_test_data_element()
            ).to_be_visible()

        with allure.step("Clicking on the internal link and verifying that the user is "
                         "redirected to the correct article"):
            self.sumo_pages.new_message_page._click_on_preview_internal_link()
            assert (
                self.sumo_pages.kb_article_page._get_text_of_article_title()
                == NewMessagePageMessages.PREVIEW_MESSAGE_INTERNAL_LINK_TITLE
            ), (
                f"Incorrect article title displayed! "
                f"Expected: {NewMessagePageMessages.PREVIEW_MESSAGE_INTERNAL_LINK_TITLE} "
                f"Received: {self.sumo_pages.kb_article_page._get_text_of_article_title()}"
            )

        with allure.step("Verifying that the message was no sent by checking the "
                         "'Sent Messages page'"):
            self.sumo_pages.top_navbar._click_on_inbox_option()
            self.sumo_pages.mess_system_user_navbar._click_on_messaging_system_nav_sent_messages()
            expect(
                self.sumo_pages.sent_message_page._sent_messages(username=test_user)
            ).to_be_hidden()

        with allure.step("Signing in with the potential message receiver and verifying that no "
                         "message were received"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_13"]
            ))
            self.sumo_pages.top_navbar._click_on_inbox_option()
            expect(
                self.sumo_pages.inbox_page._inbox_message(username=username)
            ).to_be_hidden()

    # C891421, C891424
    @pytest.mark.messagingSystem
    def test_messages_can_be_selected_and_deleted(self):
        test_user = self.username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_6"]
        )

        with allure.step("Signing in with a non-admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_5"]
            ))

        user_one = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        with allure.step("Accessing the 'New Message' page and sending a message to a different "
                         "user"):
            self.sumo_pages.top_navbar._click_on_inbox_option()
            self.sumo_pages.mess_system_user_navbar._click_on_messaging_system_nav_new_message()
            self.sumo_pages.messaging_system_flow.complete_send_message_form_with_data(
                recipient_username=test_user,
                message_body=super().user_message_test_data["valid_user_message"]["message"],
            )

        with allure.step("Navigating to the sent messages page"):
            self.sumo_pages.mess_system_user_navbar._click_on_messaging_system_nav_sent_messages()

        with allure.step("Clicking on the 'Delete Selected' button"):
            self.sumo_pages.sent_message_page._click_on_delete_selected_button()

        with check, allure.step("Verifying that the correct message is displayed"):
            assert self.sumo_pages.sent_message_page._get_sent_messages_page_deleted_banner_text(
            ) in SentMessagesPageMessages.NO_MESSAGES_SELECTED_BANNER_TEXT

        with allure.step("Verifying that the message is still listed inside the sent messages "
                         "section"):
            expect(
                self.sumo_pages.sent_message_page._sent_messages(username=test_user)
            ).to_be_visible()

        with allure.step("Sending another message to self twice"):
            for i in range(2):
                self.sumo_pages.mess_system_user_navbar._click_on_messaging_system_nav_new_message(
                )
                self.sumo_pages.messaging_system_flow.complete_send_message_form_with_data(
                    recipient_username=user_one,
                    message_body=super().user_message_test_data["valid_user_message"]["message"],
                )

        with check, allure.step("Clicking on the 'delete selected' button while no messages is "
                                "selected and verifying that the correct banner is displayed"):
            self.sumo_pages.mess_system_user_navbar._click_on_messaging_system_navbar_inbox()
            self.sumo_pages.inbox_page._click_on_inbox_delete_selected_button()
            assert self.sumo_pages.inbox_page._get_text_inbox_page_message_banner_text(
            ) in InboxPageMessages.NO_MESSAGES_SELECTED_BANNER_TEXT
            expect(
                self.sumo_pages.inbox_page._inbox_message(username=user_one).first
            ).to_be_visible()

        with allure.step("Selecting the messages and deleting it via the delete selected button"):
            self.sumo_pages.inbox_page._delete_all_inbox_messages_via_delete_selected_button()

        with check, allure.step("Verifying that the messages are no longer displayed"):
            expect(
                self.sumo_pages.inbox_page._inbox_message(username=user_one)
            ).to_be_hidden()
            assert self.sumo_pages.inbox_page._get_text_inbox_page_message_banner_text(
            ) in InboxPageMessages.MULTIPLE_MESSAGES_DELETION_BANNER_TEXT

        with allure.step("Navigating to the sent messages section and clearing all messages via "
                         "the 'delete selected button'"):
            self.sumo_pages.mess_system_user_navbar._click_on_messaging_system_nav_sent_messages()
            self.sumo_pages.sent_message_page._delete_all_sent_messages_via_delete_selected_button(
            )

        with allure.step("Verifying that the messages are no longer displayed"):
            expect(
                self.sumo_pages.sent_message_page._sent_messages(username=user_one)
            ).to_be_hidden()
            expect(
                self.sumo_pages.sent_message_page._sent_messages(username=test_user)
            ).to_be_hidden()

        with check, allure.step("Verifying that the correct banner is displayed"):
            assert self.sumo_pages.sent_message_page._get_sent_messages_page_deleted_banner_text(
            ) in SentMessagesPageMessages.MULTIPLE_MESSAGES_DELETION_BANNER_TEXT

        with allure.step("Signing in with the receiver account and navigating to the inbox"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_6"]
            ))
            self.sumo_pages.top_navbar._click_on_inbox_option()

        with allure.step("Verifying that the messages are displayed inside the inbox section"):
            expect(
                self.sumo_pages.inbox_page._inbox_message(username=user_one)
            ).to_be_visible()

        with allure.step("Deleting all messages from the inbox page via the delete selected "
                         "button'"):
            self.sumo_pages.inbox_page._delete_all_inbox_messages_via_delete_selected_button()

        with check, allure.step("Verifying that the messages are no longer displayed inside the "
                                "inbox section and the correct banner is displayed"):
            expect(
                self.sumo_pages.inbox_page._inbox_message(username=user_one)
            ).to_be_hidden()
            assert self.sumo_pages.inbox_page._get_text_inbox_page_message_banner_text(
            ) in InboxPageMessages.MESSAGE_DELETED_BANNER_TEXT
