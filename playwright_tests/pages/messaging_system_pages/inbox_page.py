from playwright.sync_api import Page, Locator, ElementHandle
from playwright_tests.core.basepage import BasePage


class InboxPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        # Breadcrumb locators.
        self.inbox_page_breadcrumbs = page.locator("ol#breadcrumbs li")

        # Inbox page locators.
        self.inbox_page_main_heading = page.locator("h1.sumo-page-heading")
        self.inbox_no_messages_text = page.locator("article#inbox p")
        self.inbox_page_scam_alert_banner_text = page.locator("div#id_scam_alert p.heading")
        self.inbox_page_scam_alert_close_button = page.locator(
            "button[data-close-id='id_scam_alert']")
        self.inbox_page_message_action_banner = page.locator("ul.user-messages li p")
        self.inbox_page_message_action_banner_close_button = page.locator(
            "button.mzp-c-notification-bar-button")

        # Inbox button locators.
        self.inbox_new_message_button = page.locator("article#inbox").get_by_role("link").filter(
            has_text="New Message")
        self.inbox_mark_selected_as_read_button = page.locator("input[name='mark_read']")
        self.inbox_delete_selected_button = page.locator("input[name='delete']")
        self.inbox_delete_page_delete_button = page.locator("button[name='delete']")
        self.inbox_delete_page_cancel_button = page.get_by_role("link").filter(has_text="Cancel")

        # Inbox messages.
        self.inbox_messages = page.locator("li.email-row:not(.header)")
        self.inbox_messages_section = page.locator("ol.inbox-table")
        self.inbox_messages_delete_button = page.locator("div[class='email-cell delete'] a.delete")
        self.inbox_delete_checkbox = page.locator("div[class='email-cell check'] input")
        self.all_unread_messages = page.locator("li[class='email-row unread']")
        self.all_read_messages_excerpt = page.locator(
            "ol.inbox-table li:not(.unread) div[class='email-cell excerpt'] a")
        self.inbox_subject = lambda username: page.locator(
            f"//div[@class='email-cell from']//a[contains(text(),'{username}')]/../..//"
            f"a[@class='read']")
        self.delete_by_username = lambda username: page.locator(
            f"//div[@class='email-cell from']//a[contains(text(),'{username}')]/../..//a[@class="
            f"'delete']")
        self.delete_by_excerpt = lambda excerpt: page.locator(
            f"//div[@class='email-cell excerpt']/a[normalize-space(text())='{excerpt}']/../..//a"
            f"[@class='delete']")
        self.sender_username = lambda username: page.locator(
            "div[class='email-cell from']").get_by_role("link").filter(has_text=username)
        self.message_checkbox_by_excerpt = lambda excerpt: page.locator(
            f"//div[@class='email-cell excerpt']/a[normalize-space(text())='{excerpt}']/../../"
            f"div[@class='email-cell check']/input")
        self.message_by_excerpt = lambda excerpt: page.locator(
            "div[class='email-cell excerpt']").get_by_role("link", name=excerpt, exact=True)

    # Inbox page scam alert actions.
    def get_text_inbox_scam_alert_banner_text(self) -> str:
        """Get the text of the scam alert banner."""
        return self._get_text_of_element(self.inbox_page_scam_alert_banner_text)

    def click_on_inbox_scam_alert_close_button(self):
        """Click on the close button of the scam alert banner."""
        self._click(self.inbox_page_scam_alert_close_button)

    # Inbox page actions.
    def get_text_inbox_page_message_banner_text(self) -> str:
        """Get the text of the message action banner."""
        return self._get_text_of_element(self.inbox_page_message_action_banner)

    def get_text_of_inbox_page_main_header(self) -> str:
        """Get the text of the main header of the inbox page."""
        return self._get_text_of_element(self.inbox_page_main_heading)

    def get_text_of_inbox_no_message_header(self) -> str:
        """Get the text of the no message header."""
        return self._get_text_of_element(self.inbox_no_messages_text)

    # Inbox messages actions.
    def get_inbox_message_subject(self, username: str) -> str:
        """Get the subject of the inbox message.

        Args:
            username: The username of the message sender.
        """
        return self._get_text_of_element(self.inbox_subject(username))

    def click_on_inbox_message_delete_button_by_username(self, username: str):
        """Click on the delete button of the inbox message.

        Args:
            username: The username of the message sender.
        """
        self._click(self.delete_by_username(username))

    def click_on_inbox_message_delete_button_by_excerpt(self, excerpt: str):
        """Click on the delete button of the inbox message.

        Args:
            excerpt: The excerpt of the message.
        """
        self._click(self.delete_by_excerpt(excerpt))

    def click_on_inbox_new_message_button(self):
        """Click on the new message button."""
        self._click(self.inbox_new_message_button)

    def click_on_inbox_mark_selected_as_read_button(self):
        """Click on the mark selected as read button."""
        self._click(self.inbox_mark_selected_as_read_button)

    def click_on_inbox_delete_selected_button(self, expected_locator=None):
        """Click on the delete selected button.

        Args:
            expected_locator: The expected locator after the click event.
        """
        self._click(self.inbox_delete_selected_button, expected_locator=expected_locator)

    def click_on_inbox_message_sender_username(self, username: str):
        """Click on the username of the message sender.

        Args:
            username: The username of the message sender.
        """
        self._click(self.sender_username(username))

    def inbox_message_select_checkbox_element(self, excerpt='') -> list[ElementHandle]:
        """Get the element handle of the inbox message select checkbox.

        Args:
            excerpt: The excerpt of the message.
        """
        if excerpt != '':
            return self._get_element_handles(self.message_checkbox_by_excerpt(excerpt))
        else:
            return self._get_element_handles(self.inbox_delete_checkbox)

    def click_on_inbox_message_subject(self, username: str):
        """Click on the subject of the inbox message.

        Args:
            username: The username of the message sender.
        """
        self._click(self.inbox_subject(username))

    def click_on_delete_page_delete_button(self, expected_url=None):
        """Click on the delete button on the delete message page.

        Args:
            expected_url: The expected URL after deleting the message.
        """
        self._click(self.inbox_delete_page_delete_button, expected_url=expected_url)

    def click_on_delete_page_cancel_button(self):
        """Click on the cancel button on the delete message page."""
        # Hitting the "Enter" button instead of click due to an issue (the banner does not close
        # on click)
        self._press_a_key(self.inbox_delete_page_cancel_button, 'Enter')

    def is_no_message_header_displayed(self) -> bool:
        """Check if the no message header is displayed."""
        return self._is_element_visible(self.inbox_no_messages_text)

    def inbox_message_banner(self) -> Locator:
        """Get the locator of the inbox message banner."""
        return self.inbox_page_scam_alert_banner_text

    def inbox_message(self, username: str) -> Locator:
        """Get the locator of the inbox message.

        Args:
            username: The username of the message sender.
        """
        return self.sender_username(username)

    def _inbox_message_based_on_excerpt(self, excerpt: str) -> Locator:
        """Get the locator of the inbox message based on the excerpt.

        Args:
            excerpt: The excerpt of the message.
        """
        return self.message_by_excerpt(excerpt)

    def _inbox_message_element_handles(self, excerpt: str) -> list[ElementHandle]:
        """Get the element handles of the inbox message based on the excerpt.

        Args:
            excerpt: The excerpt of the message.
        """
        return self._get_element_handles(self.message_by_excerpt(excerpt))

    def are_inbox_messages_displayed(self) -> bool:
        """Check if the inbox messages are displayed."""
        return self._is_element_visible(self.inbox_messages_section)

    def get_all_read_messages_excerpt(self) -> list[str]:
        """Get the excerpt of all the read messages."""
        return self._get_text_of_elements(self.all_read_messages_excerpt)

    def delete_all_inbox_messages(self, expected_url=None):
        """Delete all the inbox messages.

        Args:
            expected_url: The expected URL after deleting all the messages.
        """
        inbox_messages_count = self._get_element_handles(self.inbox_messages)
        for i in range(len(inbox_messages_count)):
            inbox_elements_delete_button = self._get_element_handles(
                self.inbox_messages_delete_button)
            delete_button = inbox_elements_delete_button[i]

            self._click(delete_button)
            self.click_on_delete_page_delete_button(expected_url=expected_url)

    def check_a_particular_message(self, excerpt=''):
        """Check a particular message.

        Args:
            excerpt: The excerpt of the message.
        """
        inbox_checkbox = self.inbox_message_select_checkbox_element(excerpt)
        self._checkbox_interaction(inbox_checkbox[0], True)

    def delete_all_inbox_messages_via_delete_selected_button(self, excerpt='', expected_url=None):
        """Delete all the inbox messages via the delete selected button.

        Args:
            excerpt: The excerpt of the message.
            expected_url: The expected URL after deleting all the messages.
        """
        self.wait_for_dom_to_load()
        if excerpt != '':
            inbox_messages_count = self._inbox_message_element_handles(excerpt)
        else:
            inbox_messages_count = self._get_element_handles(self.inbox_messages)
        counter = 0
        for i in range(len(inbox_messages_count)):
            if excerpt != '':
                inbox_checkbox = self.inbox_message_select_checkbox_element(excerpt)
            else:
                inbox_checkbox = self.inbox_message_select_checkbox_element()
            element = inbox_checkbox[counter]
            self._checkbox_interaction(element, True)
            counter += 1

        self.click_on_inbox_delete_selected_button()
        self.click_on_delete_page_delete_button(expected_url=expected_url)

    def get_all_unread_messages(self) -> list[Locator]:
        """Get all the unread messages."""
        return self.all_unread_messages.all()
