from playwright.sync_api import Page, Locator, ElementHandle
from playwright_tests.core.basepage import BasePage


class SentMessagePage(BasePage):

    # Sent messages page locators.
    __sent_messages_breadcrumbs = "//ol[@id='breadcrumbs']/li"
    __sent_messages_page_header = "//h1[@class='sumo-page-subheading']"
    __sent_messages_no_messages_message = "//article[@id='outbox']/p"
    __sent_messages_delete_selected_button = "//button[contains(text(), 'Delete Selected')]"
    __sent_messages_delete_page_delete_button = "//button[@name='delete']"
    __sent_messages_delete_page_cancel_button = "//a[contains(text(), 'Cancel')]"
    __sent_messages_page_message_banner_text = "//ul[@class='user-messages']/li/p"
    __sent_message_page_message_banner_close_button = ("//button[@class='mzp-c-notification-bar"
                                                       "-button']")
    __sent_messages = "//ol[@class='message-list']/li"
    __sent_messages_section = "//ol[@class='message-list']"
    __sent_messages_delete_button = "//ol[@class='message-list']/li/a[@class='delete']"
    __sent_messages_delete_checkbox = ("//ol[@class='message-list']//a/ancestor::li/div["
                                       "contains(@class, 'field checkbox no-label')]/label")

    def __init__(self, page: Page):
        super().__init__(page)

    # Sent messages page actions.
    def _get_sent_messages_page_deleted_banner_text(self) -> str:
        return super()._get_text_of_element(self.__sent_messages_page_message_banner_text)

    def _get_sent_messages_page_header(self) -> str:
        return super()._get_text_of_element(self.__sent_messages_page_header)

    def _get_sent_messages_no_message_text(self) -> str:
        return super()._get_text_of_element(self.__sent_messages_no_messages_message)

    def _get_sent_message_subject(self, username: str) -> str:
        xpath = (f"//ol[@class='message-list']//a[contains(text(),'{username}')]/ancestor::li/a["
                 f"@class='read']")
        return super()._get_text_of_element(xpath)

    # Need to update this def click_on_sent_messages_page_banner_close_button(self): Hitting the
    # click twice because of an issue with closing the banner self._page.locator(
    # self.__sent_message_page_message_banner_close_button).dispatch_event(type='click')

    def _click_on_delete_selected_button(self):
        super()._click(self.__sent_messages_delete_selected_button)

    def _click_on_sent_message_delete_button(self, username: str):
        xpath_to_hover = f"//ol[@class='message-list']//a[contains(text(),'{username}')]"
        super()._hover_over_element(xpath_to_hover)
        xpath_delete_button = (f"//ol[@class='message-list']//a[contains(text(),"
                               f"'{username}')]/ancestor::li/a["
                               f"@class='delete']")
        super()._click(xpath_delete_button)

    def _click_on_sent_message_sender_username(self, username: str):
        xpath = f"//ol[@class='message-list']//a[contains(text(),'{username}')]"
        super()._click(xpath)

    def _sent_message_select_checkbox(self) -> list[ElementHandle]:
        return super()._get_element_handles(self.__sent_messages_delete_checkbox)

    def _click_on_sent_message_subject(self, username: str):
        xpath = (f"//ol[@class='message-list']//a[contains(text(),'{username}')]/ancestor::li/a["
                 f"@class='read']")
        super()._click(xpath)

    def _click_on_delete_page_delete_button(self):
        super()._click(self.__sent_messages_delete_page_delete_button)

    def _click_on_delete_page_cancel_button(self):
        super()._click(self.__sent_messages_delete_page_cancel_button)

    def _sent_messages(self, username: str) -> Locator:
        return super()._get_element_locator(f"//ol[@class='message-list']//a[contains(text(),"
                                            f"'{username}')]")

    def _sent_message_banner(self) -> Locator:
        return super()._get_element_locator(self.__sent_messages_page_message_banner_text)

    def _are_sent_messages_displayed(self) -> bool:
        return super()._is_element_visible(self.__sent_messages_section)

    def _delete_all_displayed_sent_messages(self):
        sent_messages = super()._get_element_handles(self.__sent_messages)
        counter = 0
        for i in range(len(sent_messages), 0, -1):
            sent_messages = super()._get_element_handles(self.__sent_messages)
            element = sent_messages[counter]
            element.hover()

            sent_elements_delete_button = super()._get_element_handles(
                self.__sent_messages_delete_button)
            delete_button = sent_elements_delete_button[counter]

            delete_button.click()
            self._click_on_delete_page_delete_button()

    def _delete_all_sent_messages_via_delete_selected_button(self):
        sent_messages_count = super()._get_element_handles(self.__sent_messages)
        counter = 0
        for i in range(len(sent_messages_count)):
            checkbox = self._sent_message_select_checkbox()
            element = checkbox[counter]
            element.click()
            counter += 1

        self._click_on_delete_selected_button()
        self._click_on_delete_page_delete_button()
