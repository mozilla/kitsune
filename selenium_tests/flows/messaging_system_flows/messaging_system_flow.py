from selenium_tests.core.test_utilities import TestUtilities
from selenium_tests.pages.messaging_system_pages.new_message import NewMessagePage
from selenium.webdriver.remote.webdriver import WebDriver


class MessagingSystemFlows(TestUtilities, NewMessagePage):
    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    def complete_send_message_form_with_data(self, recipient_username: str, message_body: str):
        super().type_into_new_message_to_input_field(recipient_username)
        super().click_on_a_searched_user(recipient_username)
        super().type_into_new_message_body_textarea(message_body)
