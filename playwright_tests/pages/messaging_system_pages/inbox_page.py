from playwright.sync_api import Page, Locator, ElementHandle
from playwright_tests.core.basepage import BasePage


class InboxPage(BasePage):

    # Breadcrumb locators.
    __inbox_page_breadcrumbs = "//ol[@id='breadcrumbs']/li"

    # Inbox page locators.
    __inbox_page_main_heading = "//h1[@class='sumo-page-heading']"
    __inbox_no_messages_text = "//article[@id='inbox']//p"
    __inbox_page_scam_alert_banner_text = "//div[@id='id_scam_alert']//p[@class='heading']"
    __inbox_page_scam_alert_close_button = "//button[@data-close-id='id_scam_alert']"
    __inbox_page_message_action_banner = "//ul[@class='user-messages']/li/p"
    __inbox_page_message_action_banner_close_button = ("//button[@class='mzp-c-notification-bar"
                                                       "-button']")

    # Inbox button locators.
    __inbox_new_message_button = "//article[@id='inbox']//a[contains(text(),'New Message')]"
    __inbox_mark_selected_as_read_button = "//input[@name='mark_read']"
    __inbox_delete_selected_button = "//input[@name='delete']"
    __inbox_delete_page_delete_button = "//button[@name='delete']"
    __inbox_delete_page_cancel_button = "//a[contains(text(), 'Cancel')]"

    # Inbox messages.
    __inbox_messages = "//ol[@class='message-list']/li"
    __inbox_messages_section = "//ol[@class='message-list']"
    __inbox_messages_delete_button = "//ol[@class='message-list']/li/a[@class='delete']"
    __inbox_delete_checkbox = ("//ol[@class='message-list']//a/ancestor::li/div[contains(@class, "
                               "'field checkbox no-label')]/label")

    def __init__(self, page: Page):
        super().__init__(page)

    # Breadcrumb actions.

    # Inbox page scam alert actions.
    def _get_text_inbox_scam_alert_banner_text(self) -> str:
        return super()._get_text_of_element(self.__inbox_page_scam_alert_banner_text)

    def _click_on_inbox_scam_alert_close_button(self):
        super()._click(self.__inbox_page_scam_alert_close_button)

    # Inbox page actions.
    def _get_text_inbox_page_message_banner_text(self) -> str:
        return super()._get_text_of_element(self.__inbox_page_message_action_banner)

    def _get_text_of_inbox_page_main_header(self) -> str:
        return super()._get_text_of_element(self.__inbox_page_main_heading)

    def _get_text_of_inbox_no_message_header(self) -> str:
        return super()._get_text_of_element(self.__inbox_no_messages_text)

    # Inbox messages actions.
    def _get_inbox_message_subject(self, username: str) -> str:
        xpath = (
            f"//ol[@class='message-list']//a[contains(text(),"
            f"'{username}')]/ancestor::li/a[@class='read']"
        )
        return super()._get_text_of_element(xpath)

    # This requires a change def click_on_inbox_message_banner_close_button(self):
    # self._page.locator(self.__inbox_page_message_action_banner_close_button).dispatch_event(
    # type='click')

    def _click_on_inbox_message_delete_button(self, username: str):
        xpath_to_hover = (
            f"//ol[@class='message-list']//a[contains(text(),'{username}')]"
        )
        super()._hover_over_element(xpath_to_hover)

        xpath_delete_button = (
            f"//ol[@class='message-list']//a[contains(text(),'{username}')]/ancestor::li"
            f"/a[@class='delete']"
        )
        super()._click(xpath_delete_button)

    def _click_on_inbox_new_message_button(self):
        super()._click(self.__inbox_new_message_button)

    def _click_on_inbox_mark_selected_as_read_button(self):
        super()._click(self.__inbox_mark_selected_as_read_button)

    def _click_on_inbox_delete_selected_button(self):
        super()._click(self.__inbox_delete_selected_button)

    def _click_on_inbox_message_sender_username(self, username: str):
        xpath = f"//ol[@class='message-list']//a[contains(text(),'{username}')]"
        super()._click(xpath)

    def _inbox_message_select_checkbox_element(self) -> list[ElementHandle]:
        return super()._get_element_handles(self.__inbox_delete_checkbox)

    def _click_on_inbox_message_subject(self, username: str):
        xpath = (f"//ol[@class='message-list']//a[contains(text(),'{username}')]/ancestor::li/a["
                 f"@class='read']")
        super()._click(xpath)

    def _click_on_delete_page_delete_button(self):
        super()._click(self.__inbox_delete_page_delete_button)

    def _click_on_delete_page_cancel_button(self):
        # Hitting the "Enter" button instead of click due to an issue (the banner does not close
        # on click)
        super()._press_a_key(self.__inbox_delete_page_cancel_button, 'Enter')

    def _is_no_message_header_displayed(self) -> bool:
        return super()._is_element_visible(self.__inbox_no_messages_text)

    def _inbox_message_banner(self) -> Locator:
        return super()._get_element_locator(self.__inbox_page_scam_alert_banner_text)

    def _inbox_message(self, username: str) -> Locator:
        return super()._get_element_locator(
            f"//ol[@class='message-list']//a[contains(text(),'{username}')]")

    def _are_inbox_messages_displayed(self) -> bool:
        return super()._is_element_visible(self.__inbox_messages_section)

    def _delete_all_inbox_messages(self):
        inbox_messages_count = super()._get_element_handles(self.__inbox_messages)
        counter = 0
        for i in range(len(inbox_messages_count)):
            inbox_messages = super()._get_element_handles(self.__inbox_messages)
            element = inbox_messages[counter]
            element.hover()

            inbox_elements_delete_button = super()._get_element_handles(
                self.__inbox_messages_delete_button)
            delete_button = inbox_elements_delete_button[counter]

            delete_button.click()
            self._click_on_delete_page_delete_button()

    def _delete_all_inbox_messages_via_delete_selected_button(self):
        inbox_messages_count = super()._get_element_handles(self.__inbox_messages)
        counter = 0
        for i in range(len(inbox_messages_count)):
            inbox_checkbox = self._inbox_message_select_checkbox_element()
            element = inbox_checkbox[counter]
            element.click()
            counter += 1

        self._click_on_inbox_delete_selected_button()
        self._click_on_delete_page_delete_button()
