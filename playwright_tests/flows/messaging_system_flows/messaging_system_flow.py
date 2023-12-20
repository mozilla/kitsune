from playwright.sync_api import Page
from playwright_tests.core.testutilities import TestUtilities
from playwright_tests.pages.messaging_system_pages.new_message import NewMessagePage


class MessagingSystemFlows(TestUtilities, NewMessagePage):
    def __init__(self, page: Page):
        super().__init__(page)

    # Send message form with data flow.
    def complete_send_message_form_with_data(self, recipient_username: str, message_body: str):
        super().type_into_new_message_to_input_field(recipient_username)
        super().click_on_a_searched_user(recipient_username)
        super().fill_into_new_message_body_textarea(message_body)
