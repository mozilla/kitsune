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
    __sent_messages = "//li[contains(@class,'email-row') and not(contains(@class, 'header'))]"
    __sent_messages_section = "//ol[@class='outbox-table']"
    __sent_messages_delete_button = "//ol[@class='outbox-table']//a[@class='delete']"
    __sent_messages_delete_checkbox = "//div[contains(@class,'checkbox')]/label"

    # Read Sent Messages page
    __to_groups_list_items = "//span[@class='to-group']//a"
    __to_user_list_items = "//span[@class='to']//a"

    def __init__(self, page: Page):
        super().__init__(page)

    # Sent messages page actions.
    def get_sent_messages_page_deleted_banner_text(self) -> str:
        return self._get_text_of_element(self.__sent_messages_page_message_banner_text)

    def get_sent_messages_page_header(self) -> str:
        return self._get_text_of_element(self.__sent_messages_page_header)

    def get_sent_messages_no_message_text(self) -> str:
        return self._get_text_of_element(self.__sent_messages_no_messages_message)

    def get_sent_message_subject(self, username: str) -> str:
        return self._get_text_of_element(f"//div[@class='email-cell to']//a[contains(text(),"
                                         f"'{username}')]/../.."
                                         f"/div[@class='email-cell excerpt']/a")

    # Need to update this def click_on_sent_messages_page_banner_close_button(self): Hitting the
    # click twice because of an issue with closing the banner self._page.locator(
    # self.__sent_message_page_message_banner_close_button).dispatch_event(type='click')

    def click_on_delete_selected_button(self):
        self._click(self.__sent_messages_delete_selected_button)

    def click_on_sent_message_delete_button_by_user(self, username: str):
        self._click(f"//div[@class='email-cell to']//a[contains(text(),'{username}')]/../..//"
                    f"a[@class='delete']")

    def click_on_sent_message_delete_button_by_excerpt(self, excerpt: str):
        self._click(f"//div[@class='email-cell excerpt']/a[normalize-space(text())='{excerpt}']"
                    f"/../..//a[@class='delete']")

    def click_on_sent_message_sender_username(self, username: str):
        self._click(f"//div[@class='email-cell to']//a[contains(text(),'{username}')]")

    def sent_message_select_checkbox(self) -> list[ElementHandle]:
        return self._get_element_handles(self.__sent_messages_delete_checkbox)

    def sent_message_select_checkbox_element(self, excerpt: str) -> list[ElementHandle]:
        return self._get_element_handles(f"//div[@class='email-cell excerpt']/a[normalize-space"
                                         f"(text())='{excerpt}']/../.."
                                         f"/div[@class='email-cell field checkbox no-label']"
                                         f"/label")

    def click_on_sent_message_subject(self, text: str):
        self._click(f"//div[@class='email-cell excerpt']/a[contains(text(),'{text}')]")

    def click_on_sent_messages_to_group_subject(self, group_name: str):
        self._click(f"//div[@class='email-cell to-groups']/a[text()='{group_name}']/../../"
                    f"div[@class='email-cell excerpt']")

    def click_on_delete_page_delete_button(self):
        self._click(self.__sent_messages_delete_page_delete_button)

    def click_on_delete_page_cancel_button(self):
        self._click(self.__sent_messages_delete_page_cancel_button)

    def sent_messages(self, username: str) -> Locator:
        return self._get_element_locator(f"//div[@class='email-cell to']//a[contains(text(),"
                                         f"'{username}')]")

    def sent_messages_by_excerpt_locator(self, excerpt: str) -> Locator:
        return self._get_element_locator(f"//div[@class='email-cell excerpt']/"
                                         f"a[normalize-space(text())='{excerpt}']")

    def sent_messages_by_excerpt_element_handles(self, excerpt: str) -> list[ElementHandle]:
        return self._get_element_handles(f"//div[@class='email-cell excerpt']/"
                                         f"a[normalize-space(text())='{excerpt}']")

    def sent_messages_to_group(self, group: str, excerpt: str) -> Locator:
        return self._get_element_locator(f"//div[@class='email-cell to-groups']//a[contains"
                                         f"(text(),'{group}')]/../../"
                                         f"div[@class='email-cell excerpt']/a[normalize-space"
                                         f"(text())='{excerpt}']")

    def sent_message_banner(self) -> Locator:
        return self._get_element_locator(self.__sent_messages_page_message_banner_text)

    def are_sent_messages_displayed(self) -> bool:
        return self._is_element_visible(self.__sent_messages_section)

    def delete_all_displayed_sent_messages(self):
        sent_elements_delete_button = self._get_element_handles(
            self.__sent_messages_delete_button)
        for i in range(len(sent_elements_delete_button)):
            delete_button = sent_elements_delete_button[i]

            delete_button.click()
            self.click_on_delete_page_delete_button()

    def delete_all_sent_messages_via_delete_selected_button(self, excerpt=''):
        if excerpt != '':
            sent_messages_count = self.sent_messages_by_excerpt_element_handles(excerpt)
        else:
            sent_messages_count = self._get_element_handles(self.__sent_messages)
        counter = 0
        for i in range(len(sent_messages_count)):
            if excerpt != '':
                checkbox = self.sent_message_select_checkbox_element(excerpt)
            else:
                checkbox = self.sent_message_select_checkbox()
            element = checkbox[counter]
            element.click()
            counter += 1

        self.click_on_delete_selected_button()
        self.click_on_delete_page_delete_button()

    # Read Sent Message page
    def get_text_of_all_sent_groups(self) -> list[str]:
        return self._get_text_of_elements(self.__to_groups_list_items)

    def get_text_of_all_recipients(self) -> list[str]:
        return self._get_text_of_elements(self.__to_user_list_items)
