from playwright.sync_api import Page, Locator, ElementHandle
from playwright_tests.core.basepage import BasePage


class SentMessagePage(BasePage):
    # Sent messages page locators.
    SENT_MESSAGE_PAGE_LOCATORS = {
        "sent_messages_breadcrumbs": "//ol[@id='breadcrumbs']/li",
        "sent_messages_page_header": "//h1[@class='sumo-page-subheading']",
        "sent_messages_no_messages_message": "//article[@id='outbox']/p",
        "sent_messages_delete_selected_button": "//button[contains(text(), 'Delete Selected')]",
        "sent_messages_delete_page_delete_button": "//button[@name='delete']",
        "sent_messages_delete_page_cancel_button": "//a[contains(text(), 'Cancel')]",
        "sent_messages_page_message_banner_text": "//ul[@class='user-messages']/li/p",
        "sent_message_page_message_banner_close_button": "//button[@class='mzp-c-notification-bar"
                                                         "-button']",
        "sent_messages": "//li[contains(@class,'email-row') and not(contains(@class, 'header'))]",
        "sent_messages_section": "//ol[@class='outbox-table']",
        "sent_messages_delete_button": "//ol[@class='outbox-table']//a[@class='delete']",
        "sent_messages_delete_checkbox": "//div[contains(@class,'checkbox')]/label"

    }

    # Read Sent Messages page
    READ_SENT_MESSAGES_PAGE_LOCATORS = {
        "to_groups_list_items": "//span[@class='to-group']//a",
        "to_user_list_items": "//span[@class='to']//a"
    }

    def __init__(self, page: Page):
        super().__init__(page)

    # Sent messages page actions.
    def get_sent_messages_page_deleted_banner_text(self) -> str:
        """Get the text of the banner that appears when a message is deleted."""
        return self._get_text_of_element(self.SENT_MESSAGE_PAGE_LOCATORS
                                         ["sent_messages_page_message_banner_text"])

    def get_sent_messages_page_header(self) -> str:
        """Get the header text of the sent messages page."""
        return self._get_text_of_element(self.SENT_MESSAGE_PAGE_LOCATORS
                                         ["sent_messages_page_header"])

    def get_sent_messages_no_message_text(self) -> str:
        """Get the text of the message that appears when there are no messages in the
        sent messages page.
        """
        return self._get_text_of_element(self.SENT_MESSAGE_PAGE_LOCATORS
                                         ["sent_messages_no_messages_message"])

    def get_sent_message_subject(self, username: str) -> str:
        """Get the subject of the sent message by the username of the recipient.

        Args:
            username (str): The username of the recipient.
        """
        return self._get_text_of_element(f"//div[@class='email-cell to']//a[contains(text(),"
                                         f"'{username}')]/../.."
                                         f"/div[@class='email-cell excerpt']/a")

    def click_on_delete_selected_button(self):
        """Click on the delete selected button on the sent messages page."""
        self._click(self.SENT_MESSAGE_PAGE_LOCATORS["sent_messages_delete_selected_button"])

    def click_on_sent_message_delete_button_by_user(self, username: str):
        """Click on the delete button of a sent message by the username of the recipient.

        Args:
            username (str): The username of the recipient.
        """
        self._click(f"//div[@class='email-cell to']//a[contains(text(),'{username}')]/../..//"
                    f"a[@class='delete']")

    def click_on_sent_message_delete_button_by_excerpt(self, excerpt: str):
        """Click on the delete button of a sent message by the excerpt of the message.

        Args:
            excerpt (str): The excerpt of the message.
        """
        self._click(f"//div[@class='email-cell excerpt']/a[normalize-space(text())='{excerpt}']"
                    f"/../..//a[@class='delete']")

    def click_on_sent_message_sender_username(self, username: str):
        """Click on the sender username of a sent message."""
        self._click(f"//div[@class='email-cell to']//a[contains(text(),'{username}')]")

    def sent_message_select_checkbox(self) -> list[ElementHandle]:
        """Get element handle list of the selected sent messages checkboxes."""
        return self._get_element_handles(self.SENT_MESSAGE_PAGE_LOCATORS
                                         ["sent_messages_delete_checkbox"])

    def sent_message_select_checkbox_element(self, excerpt: str) -> list[ElementHandle]:
        """Get element handle list of the selected sent messages checkboxes by excerpt.

        Args:
            excerpt (str): The excerpt of the message.
        """
        return self._get_element_handles(f"//div[@class='email-cell excerpt']/a[normalize-space"
                                         f"(text())='{excerpt}']/../.."
                                         f"/div[@class='email-cell field checkbox no-label']"
                                         f"/label")

    def click_on_sent_message_subject(self, text: str):
        """Click on the subject of a sent message by the text of the subject.

        Args:
            text (str): The text of the subject.
        """
        self._click(f"//div[@class='email-cell excerpt']/a[contains(text(),'{text}')]")

    def click_on_sent_messages_to_group_subject(self, group_name: str):
        """Click on the subject of a sent message by the group name of the recipient.

        Args:
            group_name (str): The name of the group.
        """
        self._click(f"//div[@class='email-cell to-groups']/a[text()='{group_name}']/../../"
                    f"div[@class='email-cell excerpt']")

    def click_on_delete_page_delete_button(self):
        """Click on the delete button on the delete message page."""
        self._click(self.SENT_MESSAGE_PAGE_LOCATORS["sent_messages_delete_page_delete_button"])

    def click_on_delete_page_cancel_button(self):
        """Click on the cancel button on the delete message page."""
        self._click(self.SENT_MESSAGE_PAGE_LOCATORS["sent_messages_delete_page_cancel_button"])

    def sent_messages(self, username: str) -> Locator:
        """Get the locator of the sent messages by the username of the recipient.

        Args:
            username (str): The username of the recipient.
        """
        return self._get_element_locator(f"//div[@class='email-cell to']//a[contains(text(),"
                                         f"'{username}')]")

    def sent_messages_by_excerpt_locator(self, excerpt: str) -> Locator:
        """Get the locator of the sent messages by the excerpt of the message.

        Args:
            excerpt (str): The excerpt of the message.
        """
        return self._get_element_locator(f"//div[@class='email-cell excerpt']/"
                                         f"a[normalize-space(text())='{excerpt}']")

    def sent_messages_by_excerpt_element_handles(self, excerpt: str) -> list[ElementHandle]:
        """Get the element handle list of the sent messages by the excerpt of the message.

        Args:
            excerpt (str): The excerpt of the message.
        """
        return self._get_element_handles(f"//div[@class='email-cell excerpt']/"
                                         f"a[normalize-space(text())='{excerpt}']")

    def sent_messages_to_group(self, group: str, excerpt: str) -> Locator:
        """Get the locator of the sent message by the group name of the recipient and the excerpt

        Args:
            group (str): The name of the group.
            excerpt (str): The excerpt of the message.
        """
        return self._get_element_locator(f"//div[@class='email-cell to-groups']//a[contains"
                                         f"(text(),'{group}')]/../../"
                                         f"div[@class='email-cell excerpt']/a[normalize-space"
                                         f"(text())='{excerpt}']")

    def sent_message_banner(self) -> Locator:
        """Get the locator of the sent message banner."""
        return self._get_element_locator(self.SENT_MESSAGE_PAGE_LOCATORS
                                         ["sent_messages_page_message_banner_text"])

    def are_sent_messages_displayed(self) -> bool:
        """Check if the sent messages are displayed."""
        return self._is_element_visible(self.SENT_MESSAGE_PAGE_LOCATORS["sent_messages_section"])

    def delete_all_displayed_sent_messages(self):
        """Delete all the displayed sent messages."""
        sent_elements_delete_button = self._get_element_handles(
            self.SENT_MESSAGE_PAGE_LOCATORS["sent_messages_delete_button"])
        for i in range(len(sent_elements_delete_button)):
            delete_button = sent_elements_delete_button[i]

            delete_button.click()
            self.click_on_delete_page_delete_button()

    def delete_all_sent_messages_via_delete_selected_button(self, excerpt=''):
        """Delete all the sent messages via the delete selected button.

        Args:
            excerpt (str): The excerpt of the message.
        """
        if excerpt != '':
            sent_messages_count = self.sent_messages_by_excerpt_element_handles(excerpt)
        else:
            sent_messages_count = self._get_element_handles(self.SENT_MESSAGE_PAGE_LOCATORS
                                                            ["sent_messages"])
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
        """Get the text of all the sent groups."""
        return self._get_text_of_elements(self.READ_SENT_MESSAGES_PAGE_LOCATORS
                                          ["to_groups_list_items"])

    def get_text_of_all_recipients(self) -> list[str]:
        """Get the text of all the recipients."""
        return self._get_text_of_elements(self.READ_SENT_MESSAGES_PAGE_LOCATORS
                                          ["to_user_list_items"])
