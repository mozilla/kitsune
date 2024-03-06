from playwright.sync_api import Page
from playwright_tests.core.testutilities import TestUtilities
from playwright_tests.pages.messaging_system_pages.inbox_page import InboxPage
from playwright_tests.pages.messaging_system_pages.new_message import NewMessagePage
from playwright_tests.pages.messaging_system_pages.sent_messages import SentMessagePage


class MessagingSystemFlows(TestUtilities, NewMessagePage, SentMessagePage, InboxPage):
    def __init__(self, page: Page):
        super().__init__(page)

    # Send message form with data flow.
    def complete_send_message_form_with_data(self,
                                             recipient_username='',
                                             message_body='',
                                             submit_message=True):
        if recipient_username != '':
            super()._type_into_new_message_to_input_field(recipient_username)
            super()._click_on_a_searched_user(recipient_username)

        if message_body != '':
            super()._fill_into_new_message_body_textarea(message_body)

        if submit_message:
            super()._click_on_new_message_send_button()

    def delete_message_flow(self, username: str,
                            delete_message=True,
                            from_sent_list=False,
                            from_inbox_list=False):
        if from_sent_list:
            super()._click_on_sent_message_delete_button(username)

        if from_inbox_list:
            super()._click_on_inbox_message_delete_button(username)

        if delete_message:
            super()._click_on_delete_page_delete_button()
