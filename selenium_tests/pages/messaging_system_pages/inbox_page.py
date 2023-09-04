from selenium_tests.core.base_page import BasePage
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver


class InboxPage(BasePage):
    __inbox_page_breadcrumbs = (By.XPATH, "//ol[@id='breadcrumbs']/li")
    __inbox_page_main_heading = (By.XPATH, "//h1[@class='sumo-page-heading']")
    __inbox_new_message_button = (
        By.XPATH,
        "//article[@id='inbox']//a[contains(text(),'New Message')]",
    )
    __inbox_no_messages_text = (By.XPATH, "//article[@id='inbox']//p")
    __inbox_mark_selected_as_read_button = (By.XPATH, "//input[@name='mark_read']")
    __inbox_delete_selected_button = (By.XPATH, "//input[@name='delete']")
    __inbox_delete_page_delete_button = (By.XPATH, "//button[@name='delete']")
    __inbox_delete_page_cancel_button = (By.XPATH, "//a[contains(text(), 'Cancel')]")
    __inbox_page_message_banner_text = (By.XPATH, "//ul[@class='user-messages']/li/p")
    __inbox_page_message_banner_close_button = (By.XPATH, "//ul[@class='user-messages']/li/button")
    __inbox_messages = (By.XPATH, "//ol[@class='message-list']/li")
    __inbox_messages_delete_button = (
        By.XPATH,
        "//ol[@class='message-list']/li/a[@class='delete']",
    )

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    def get_text_inbox_page_message_banner_text(self) -> str:
        return super()._get_text_of_element(self.__inbox_page_message_banner_text)

    def get_text_of_inbox_page_main_header(self) -> str:
        return super()._get_text_of_element(self.__inbox_page_main_heading)

    def get_text_of_inbox_no_message_header(self) -> str:
        return super()._get_text_of_element(self.__inbox_no_messages_text)

    def get_inbox_message_subject(self, username: str) -> str:
        xpath = (
            By.XPATH,
            f"//ol[@class='message-list']//a[contains(text(),"
            f"'{username}')]/ancestor::li/a[@class='read']",
        )
        return super()._get_text_of_element(xpath)

    def click_on_inbox_message_banner_close_button(self):
        super()._click(self.__inbox_page_message_banner_close_button)

    def click_on_inbox_message_delete_button(self, username: str):
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

    def click_on_inbox_new_message_button(self):
        super()._click(self.__inbox_new_message_button)

    def click_on_inbox_mark_selected_as_read_button(self):
        super()._click(self.__inbox_mark_selected_as_read_button)

    def click_on_inbox_delete_selected_button(self):
        super()._click(self.__inbox_delete_selected_button)

    def click_on_inbox_message_sender_username(self, username: str):
        xpath = (By.XPATH, f"//ol[@class='message-list']//a[contains(text(),'{username}')]")
        super()._click(xpath)

    def click_on_inbox_message_select_checkbox(self):
        xpath = (
            By.XPATH,
            "//ol[@class='message-list']//a/ancestor::li/div"
            "[contains(@class, 'field checkbox no-label')]/label",
        )
        super()._click(xpath)

    def click_on_inbox_message_subject(self, username: str):
        xpath = (
            By.XPATH,
            f"//ol[@class='message-list']//a[contains(text(),"
            f"'{username}')]/ancestor::li/a[@class='read']",
        )
        super()._click(xpath)

    def click_on_delete_page_delete_button(self):
        super()._click(self.__inbox_delete_page_delete_button)

    def click_on_delete_page_cancel_button(self):
        super()._click(self.__inbox_delete_page_cancel_button)

    def is_no_message_header_displayed(self) -> bool:
        return super()._is_element_displayed(self.__inbox_no_messages_text)

    def is_inbox_page_message_banner_displayed(self) -> bool:
        return super()._is_element_displayed(self.__inbox_page_message_banner_text)

    def is_message_displayed_inside_the_inbox_section(self, username: str) -> bool:
        xpath = (By.XPATH, f"//ol[@class='message-list']//a[contains(text(),'{username}')]")
        return super()._is_element_displayed(xpath)

    def are_inbox_messages_displayed(self) -> bool:
        return super()._is_element_displayed(self.__inbox_messages)

    def delete_all_displayed_inbox_messages(self):
        inbox_messages_count = super()._find_elements(self.__inbox_messages)
        counter = 0
        for i in range(len(inbox_messages_count)):
            inbox_messages = super()._find_elements(self.__inbox_messages)
            element = inbox_messages[counter]
            super()._mouseover_web_element(element)

            inbox_elements_delete_button = super()._find_elements(
                self.__inbox_messages_delete_button
            )
            delete_button = inbox_elements_delete_button[counter]

            super()._click_on_web_element(delete_button)
            self.click_on_delete_page_delete_button()

    def delete_all_displayed_inbox_messages_via_delete_selected_button(self):
        inbox_messages_count = super()._find_elements(self.__inbox_messages)
        counter = 0
        for i in range(len(inbox_messages_count)):
            self.click_on_inbox_message_select_checkbox()

            inbox_elements_delete_button = super()._find_elements(
                self.__inbox_delete_selected_button
            )
            delete_button = inbox_elements_delete_button[counter]

            super()._click_on_web_element(delete_button)
            self.click_on_delete_page_delete_button()
