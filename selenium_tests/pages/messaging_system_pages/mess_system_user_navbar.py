from selenium_tests.core.base_page import BasePage
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver


class MessagingSystemUserNavbar(BasePage):
    __messaging_system_user_navbar_inbox_option = (
        By.XPATH,
        "//ul[@id='pm-nav']//a[contains(text(),'Inbox')]",
    )
    __messaging_system_user_navbar_sent_messages_option = (
        By.XPATH,
        "//ul[@id='pm-nav']//a[contains(text(),'Sent Messages')]",
    )
    __messaging_system_user_navbar_new_message_option = (
        By.XPATH,
        "//ul[@id='pm-nav']//a[contains(text(),'New " "Message')]",
    )

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    def click_on_messaging_system_navbar_inbox(self):
        super()._click(self.__messaging_system_user_navbar_inbox_option)

    def click_on_messaging_system_navbar_sent_messages(self):
        super()._click(self.__messaging_system_user_navbar_sent_messages_option)

    def click_on_messaging_system_navbar_new_message(self):
        super()._click(self.__messaging_system_user_navbar_new_message_option)

    # Need to add logic for fetching the background color of selected navbar elements
    def get_inbox_option_background_value(self) -> str:
        return super()._get_value_of_css_property(
            self.__messaging_system_user_navbar_inbox_option, "background-color"
        )

    def get_sent_messages_option_background_value(self) -> str:
        return super()._get_value_of_css_property(
            self.__messaging_system_user_navbar_sent_messages_option, "background-color"
        )

    def get_new_message_option_background_value(self) -> str:
        return super()._get_value_of_css_property(
            self.__messaging_system_user_navbar_new_message_option, "background-color"
        )
