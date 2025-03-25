from playwright.sync_api import Page, Locator
from playwright_tests.core.basepage import BasePage


class MessagingSystemUserNavbar(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        # Messaging system navbar locators.
        self.messaging_system_user_navbar_inbox_option = page.locator(
            "ul#pm-nav").get_by_role("link").filter(has_text="Inbox")
        self.messaging_system_user_navbar_sent_messages_option = page.locator(
            "ul#pm-nav").get_by_role("link").filter(has_text="Sent Messages")
        self.messaging_system_user_navbar_new_message_option = page.locator(
            "ul#pm-nav").get_by_role("link").filter(has_text="New Message")

    # Messaging system navbar actions.
    def click_on_messaging_system_navbar_inbox(self):
        """Click on the inbox option in the messaging system navbar."""
        self._click(self.messaging_system_user_navbar_inbox_option)

    def click_on_messaging_system_nav_sent_messages(self):
        """Click on the sent messages option in the messaging system navbar."""
        self._click(self.messaging_system_user_navbar_sent_messages_option)

    def click_on_messaging_system_nav_new_message(self):
        """Click on the new message option in the messaging system navbar."""
        self._click(self.messaging_system_user_navbar_new_message_option)

    # Need to add logic for fetching the background color of selected navbar elements
    def get_inbox_navbar_element(self) -> Locator:
        """Get the locator for the inbox option in the messaging system navbar."""
        return self.messaging_system_user_navbar_inbox_option

    def get_sent_messages_navbar_element(self) -> Locator:
        """Get the locator for the sent messages option in the messaging system navbar."""
        return self.messaging_system_user_navbar_sent_messages_option

    def get_new_message_navbar_element(self) -> Locator:
        """Get the locator for the new message option in the messaging system navbar."""
        return self.messaging_system_user_navbar_new_message_option
