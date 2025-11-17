from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class MessagingSystemUserNavbar(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """Locators belonging to the messaging system navbar."""
        self.messaging_system_user_navbar_inbox_option = page.locator(
            "ul#pm-nav").get_by_role("link").filter(has_text="Inbox")
        self.messaging_system_user_navbar_sent_messages_option = page.locator(
            "ul#pm-nav").get_by_role("link").filter(has_text="Sent Messages")
        self.messaging_system_user_navbar_new_message_option = page.locator(
            "ul#pm-nav").get_by_role("link").filter(has_text="New Message")

    """Actions against the messaging system navbar locators."""
    def click_on_messaging_system_navbar_inbox(self):
        """Click on the inbox option in the messaging system navbar."""
        self._click(self.messaging_system_user_navbar_inbox_option)

    def click_on_messaging_system_nav_sent_messages(self):
        """Click on the sent messages option in the messaging system navbar."""
        self._click(self.messaging_system_user_navbar_sent_messages_option)

    def click_on_messaging_system_nav_new_message(self):
        """Click on the new message option in the messaging system navbar."""
        self._click(self.messaging_system_user_navbar_new_message_option)
