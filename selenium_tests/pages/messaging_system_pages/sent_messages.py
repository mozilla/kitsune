from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium_tests.core.base_page import BasePage


class SentMessagePage(BasePage):
    __sent_messages_breadcrumbs = (By.XPATH, "//ol[@id='breadcrumbs']/li")
    __sent_messages_page_header = (By.XPATH, "//h1[@class='sumo-page-subheading']")
    __sent_messages_no_messages_message = (By.XPATH, "//article[@id='outbox']/p")
    __sent_messages_delete_selected_button = (
        By.XPATH,
        "//button[contains(text(), 'Delete Selected')]",
    )
    __sent_messages_delete_page_delete_button = (By.XPATH, "//button[@name='delete']")
    __sent_messages_delete_page_cancel_button = (By.XPATH, "//a[contains(text(), 'Cancel')]")
    __sent_messages_page_message_banner_text = (By.XPATH, "//ul[@class='user-messages']/li/p")
    __sent_message_page_message_banner_close_button = (
        By.XPATH,
        "//ul[@class='user-messages']/li/button",
    )
    __sent_messages = (By.XPATH, "//ol[@class='message-list']/li")
    __sent_messages_delete_button = (By.XPATH, "//ol[@class='message-list']/li/a[@class='delete']")

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    def get_sent_messages_page_deleted_banner_text(self) -> str:
        return super()._get_text_of_element(self.__sent_messages_page_message_banner_text)

    def get_sent_messages_page_header(self) -> str:
        return super()._get_text_of_element(self.__sent_messages_page_header)

    def get_sent_messages_no_message_text(self) -> str:
        return super()._get_text_of_element(self.__sent_messages_no_messages_message)

    def get_sent_message_subject(self, username: str) -> str:
        xpath = (
            By.XPATH,
            f"//ol[@class='message-list']//a[contains(text(),"
            f"'{username}')]/ancestor::li/a[@class='read']",
        )
        return super()._get_text_of_element(xpath)

    def click_on_sent_messages_page_banner_close_button(self):
        super()._click(self.__sent_message_page_message_banner_close_button)

    def click_on_delete_selected_button(self):
        super()._click(self.__sent_messages_delete_selected_button)

    def click_on_sent_message_delete_button(self, username: str):
        xpath_to_hover = (
            By.XPATH,
            f"//ol[@class='message-list']//a[contains(text(),'{username}')]",
        )
        super()._mouseover_element(xpath_to_hover)

        xpath_delete_button = (
            By.XPATH,
            f"//ol[@class='message-list']//a[contains(text(),'{username}')]/ancestor::li"
            f"/a[@class='delete']",
        )

        super()._click(xpath_delete_button)

    def click_on_sent_message_sender_username(self, username: str):
        xpath = (By.XPATH, f"//ol[@class='message-list']//a[contains(text(),'{username}')]")
        super()._click(xpath)

    def click_on_sent_message_select_checkbox(self):
        xpath = (
            By.XPATH,
            "//ol[@class='message-list']//a/ancestor::li/div[contains("
            "@class, 'field checkbox no-label')]/label",
        )
        super()._click(xpath)

    def click_on_sent_message_subject(self, username: str):
        xpath = (
            By.XPATH,
            f"//ol[@class='message-list']//a[contains(text(),'{username}')]/ancestor::li/a["
            f"@class='read']",
        )
        super()._click(xpath)

    def click_on_delete_page_delete_button(self):
        super()._click(self.__sent_messages_delete_page_delete_button)

    def click_on_delete_page_cancel_button(self):
        super()._click(self.__sent_messages_delete_page_cancel_button)

    def is_sent_message_displayed(self, username: str) -> bool:
        xpath = (By.XPATH, f"//ol[@class='message-list']//a[contains(text(),'{username}')]")
        return super()._is_element_displayed(xpath)

    def is_sent_message_banner_displayed(self) -> bool:
        return super()._is_element_displayed(self.__sent_messages_page_message_banner_text)

    def are_sent_messages_displayed(self) -> bool:
        return super()._is_element_displayed(self.__sent_messages)

    def delete_all_displayed_sent_messages(self):
        sent_messages = super()._find_elements(self.__sent_messages)
        counter = 0
        for i in range(len(sent_messages), 0, -1):
            sent_messages = super()._find_elements(self.__sent_messages)
            element = sent_messages[counter]
            super()._mouseover_web_element(element)

            sent_elements_delete_button = super()._find_elements(
                self.__sent_messages_delete_button
            )
            delete_button = sent_elements_delete_button[counter]

            super()._click_on_web_element(delete_button)
            self.click_on_delete_page_delete_button()

    def delete_all_sent_messages_via_delete_selected_button(self):
        inbox_messages_count = super()._find_elements(self.__sent_messages)
        counter = 0
        for i in range(len(inbox_messages_count)):
            self.click_on_sent_message_select_checkbox()

            inbox_elements_delete_button = super()._find_elements(
                self.__sent_messages_delete_selected_button
            )
            delete_button = inbox_elements_delete_button[counter]

            super()._click_on_web_element(delete_button)
            self.click_on_delete_page_delete_button()
