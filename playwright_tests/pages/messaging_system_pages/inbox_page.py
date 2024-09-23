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
    __inbox_messages = "//li[contains(@class,'email-row') and not(contains(@class, 'header'))]"
    __inbox_messages_section = "//ol[@class='inbox-table']"
    __inbox_messages_delete_button = "//div[@class='email-cell delete']//a[@class='delete']"
    __inbox_delete_checkbox = "//div[@class='email-cell check']/input"

    def __init__(self, page: Page):
        super().__init__(page)

    # Breadcrumb actions.

    # Inbox page scam alert actions.
    def get_text_inbox_scam_alert_banner_text(self) -> str:
        return self._get_text_of_element(self.__inbox_page_scam_alert_banner_text)

    def click_on_inbox_scam_alert_close_button(self):
        self._click(self.__inbox_page_scam_alert_close_button)

    # Inbox page actions.
    def get_text_inbox_page_message_banner_text(self) -> str:
        return self._get_text_of_element(self.__inbox_page_message_action_banner)

    def get_text_of_inbox_page_main_header(self) -> str:
        return self._get_text_of_element(self.__inbox_page_main_heading)

    def get_text_of_inbox_no_message_header(self) -> str:
        return self._get_text_of_element(self.__inbox_no_messages_text)

    # Inbox messages actions.
    def get_inbox_message_subject(self, username: str) -> str:
        return self._get_text_of_element((
            f"//div[@class='email-cell from']//a[contains(text(),'{username}')]/../..//"
            f"a[@class='read']"
        ))

    # This requires a change def click_on_inbox_message_banner_close_button(self):
    # self._page.locator(self.__inbox_page_message_action_banner_close_button).dispatch_event(
    # type='click')

    def click_on_inbox_message_delete_button_by_username(self, username: str):
        self._click((
            f"//div[@class='email-cell from']//a[contains(text(),'{username}')]/../..//"
            f"a[@class='delete']"
        ))

    def click_on_inbox_message_delete_button_by_excerpt(self, excerpt: str):
        self._click(f"//div[@class='email-cell excerpt']/a[normalize-space(text())='{excerpt}']"
                    f"/../..//a[@class='delete']")

    def click_on_inbox_new_message_button(self):
        self._click(self.__inbox_new_message_button)

    def click_on_inbox_mark_selected_as_read_button(self):
        self._click(self.__inbox_mark_selected_as_read_button)

    def click_on_inbox_delete_selected_button(self):
        self._click(self.__inbox_delete_selected_button)

    def click_on_inbox_message_sender_username(self, username: str):
        self._click(f"//div[@class='email-cell from']//a[contains(text(),'{username}')]")

    def inbox_message_select_checkbox_element(self, excerpt='') -> list[ElementHandle]:
        if excerpt != '':
            return self._get_element_handles(f"//div[@class='email-cell excerpt']"
                                             f"/a[normalize-space(text())='{excerpt}']/../.."
                                             f"/div[@class='email-cell check']/input")
        else:
            return self._get_element_handles(self.__inbox_delete_checkbox)

    def click_on_inbox_message_subject(self, username: str):
        self._click((f"//div[@class='email-cell from']//a[contains(text(),'{username}')]/../.."
                     f"//a[@class='read']"))

    def click_on_delete_page_delete_button(self):
        self._click(self.__inbox_delete_page_delete_button)

    def click_on_delete_page_cancel_button(self):
        # Hitting the "Enter" button instead of click due to an issue (the banner does not close
        # on click)
        self._press_a_key(self.__inbox_delete_page_cancel_button, 'Enter')

    def is_no_message_header_displayed(self) -> bool:
        return self._is_element_visible(self.__inbox_no_messages_text)

    def inbox_message_banner(self) -> Locator:
        return self._get_element_locator(self.__inbox_page_scam_alert_banner_text)

    def inbox_message(self, username: str) -> Locator:
        return self._get_element_locator(f"//div[@class='email-cell from']//a[contains(text(),"
                                         f"'{username}')]")

    def _inbox_message_based_on_excerpt(self, excerpt: str) -> Locator:
        return self._get_element_locator(f"//div[@class='email-cell excerpt']/a[normalize-space"
                                         f"(text())='{excerpt}']")

    def _inbox_message_element_handles(self, excerpt: str) -> list[ElementHandle]:
        return self._get_element_handles(f"//div[@class='email-cell excerpt']/a[normalize-space"
                                         f"(text())='{excerpt}']")

    def are_inbox_messages_displayed(self) -> bool:
        return self._is_element_visible(self.__inbox_messages_section)

    def delete_all_inbox_messages(self):
        inbox_messages_count = self._get_element_handles(self.__inbox_messages)
        for i in range(len(inbox_messages_count)):
            inbox_elements_delete_button = self._get_element_handles(
                self.__inbox_messages_delete_button)
            delete_button = inbox_elements_delete_button[i]

            delete_button.click()
            self.click_on_delete_page_delete_button()

    def delete_all_inbox_messages_via_delete_selected_button(self, excerpt=''):
        if excerpt != '':
            inbox_messages_count = self._inbox_message_element_handles(excerpt)
        else:
            inbox_messages_count = self._get_element_handles(self.__inbox_messages)
        counter = 0
        for i in range(len(inbox_messages_count)):
            if excerpt != '':
                inbox_checkbox = self.inbox_message_select_checkbox_element(excerpt)
            else:
                inbox_checkbox = self.inbox_message_select_checkbox_element()
            element = inbox_checkbox[counter]
            element.click()
            counter += 1

        self.click_on_inbox_delete_selected_button()
        self.click_on_delete_page_delete_button()
