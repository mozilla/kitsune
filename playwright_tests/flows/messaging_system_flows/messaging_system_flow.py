from playwright.sync_api import Page
from playwright_tests.pages.messaging_system_pages.inbox_page import InboxPage
from playwright_tests.pages.messaging_system_pages.new_message import NewMessagePage
from playwright_tests.pages.messaging_system_pages.sent_messages import SentMessagePage


class MessagingSystemFlows:
    def __init__(self, page: Page):
        self.new_message_page = NewMessagePage(page)
        self.sent_message_page = SentMessagePage(page)
        self.inbox_page = InboxPage(page)

    # Send message form with data flow.
    def complete_send_message_form_with_data(self,
                                             recipient_username='',
                                             message_body='',
                                             submit_message=True,
                                             expected_url=None):
        """Complete the send message form with data.

        Args:
            recipient_username (str): The username of the recipient.
            message_body (str): The body of the message.
            submit_message (bool): Submit the message.
            expected_url (str): The expected URL after the click event.
        """
        if recipient_username:
            if isinstance(recipient_username, list):
                for recipient in recipient_username:
                    self.new_message_page.type_into_new_message_to_input_field(recipient)
                    self.new_message_page.click_on_a_searched_user(recipient)
            else:
                self.new_message_page.type_into_new_message_to_input_field(recipient_username)
                self.new_message_page.click_on_a_searched_user(recipient_username)

        if message_body:
            self.new_message_page.fill_into_new_message_body_textarea(message_body)

        if submit_message:
            self.new_message_page.click_on_new_message_send_button(
                expected_url=expected_url)

    def delete_message_flow(self, username='',
                            excerpt='',
                            delete_message=True,
                            from_sent_list=False,
                            from_inbox_list=False,
                            expected_url=None
                            ):
        """Delete a message flow.

        Args:
            username (str): The username of the recipient.
            excerpt (str): The excerpt of the message.
            delete_message (bool): Delete the message.
            from_sent_list (bool): Delete the message from the sent list.
            from_inbox_list (bool): Delete the message from the inbox list
            expected_url (str): The expected URL after the click event.
        """
        if from_sent_list:
            if username:
                self.sent_message_page.click_on_sent_message_delete_button_by_user(username)
            elif excerpt:
                self.sent_message_page.click_on_sent_message_delete_button_by_excerpt(excerpt)

        if from_inbox_list:
            if username:
                self.inbox_page.click_on_inbox_message_delete_button_by_username(username)
            elif excerpt:
                self.inbox_page.click_on_inbox_message_delete_button_by_excerpt(excerpt)

        if delete_message:
            self.sent_message_page.click_on_delete_page_delete_button(expected_url=expected_url)
