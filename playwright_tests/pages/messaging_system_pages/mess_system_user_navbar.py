from playwright.sync_api import Page, Locator
from playwright_tests.core.basepage import BasePage


class MessagingSystemUserNavbar(BasePage):

    # Messaging system navbar locators.
    __messaging_system_user_navbar_inbox_option = "//ul[@id='pm-nav']//a[contains(text(),'Inbox')]"
    __messaging_system_user_navbar_sent_messages_option = ("//ul[@id='pm-nav']//a[contains(text("
                                                           "),'Sent Messages')]")
    __messaging_system_user_navbar_new_message_option = ("//ul[@id='pm-nav']//a[contains(text(),"
                                                         "'New Message')]")

    def __init__(self, page: Page):
        super().__init__(page)

    # Messaging system navbar actions.
    def _click_on_messaging_system_navbar_inbox(self):
        super()._click(self.__messaging_system_user_navbar_inbox_option)

    def _click_on_messaging_system_navbar_sent_messages(self):
        super()._click(self.__messaging_system_user_navbar_sent_messages_option)

    def _click_on_messaging_system_navbar_new_message(self):
        super()._click(self.__messaging_system_user_navbar_new_message_option)

    # Need to add logic for fetching the background color of selected navbar elements
    def _get_inbox_navbar_element(self) -> Locator:
        return super()._get_element_locator(self.__messaging_system_user_navbar_inbox_option)

    def _get_sent_messages_navbar_element(self) -> Locator:
        return super()._get_element_locator(
            self.__messaging_system_user_navbar_sent_messages_option)

    def _get_new_message_navbar_element(self) -> Locator:
        return super()._get_element_locator(self.__messaging_system_user_navbar_new_message_option)
