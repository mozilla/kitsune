from playwright.sync_api import ElementHandle, Locator, Page

from playwright_tests.core.basepage import BasePage


class InboxPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """Locators belonging to the Inbox page breadcrumbs."""
        self.page_breadcrumbs = page.locator("ol#breadcrumbs li")

        """Locators belonging to the Inbox scam banner."""
        self.scam_alert_banner_text = page.locator("div#id_scam_alert p.heading")
        self.scam_alert_close_button = page.locator(
            "button[data-close-id='id_scam_alert']")

        """Locators belonging to the Inbox action banner."""
        self.message_action_banner = page.locator("ul.user-messages li p")
        self.message_action_banner_close_button = page.locator(
            "button.mzp-c-notification-bar-button")

        """General locators for the Inbox page"""
        self.main_heading = page.locator("h1.sumo-page-heading")
        self.no_messages_text = page.locator("article#inbox p")

        """Locators for buttons belonging to the Inbox page."""
        self.new_message_button = page.locator("article#inbox").get_by_role("link").filter(
            has_text="New Message")
        self.mark_selected_as_read_button = page.locator("input[name='mark_read']")
        self.delete_selected_button = page.locator("input[name='delete']")

        """Locators belonging to the delete confirmation page."""
        self.delete_confirmation_page_delete_button = page.locator("button[name='delete']")
        self.delete_confirmation_page_cancel_button = page.get_by_role("link").filter(has_text="Cancel")

        """Locators belonging to the Inbox table."""
        self.inbox_messages = page.locator("li.email-row:not(.header)")
        self.inbox_messages_section = page.locator("ol.inbox-table")
        self.inbox_messages_delete_button = page.locator("div[class='email-cell delete'] a.delete")
        self.inbox_delete_checkbox = page.locator("div[class='email-cell check'] input")
        self.all_unread_messages = page.locator("li[class='email-row unread']")
        self.all_read_messages_excerpt = page.locator(
            "ol.inbox-table li:not(.unread) div[class='email-cell excerpt'] a")
        self.inbox_message_by_sender = lambda username: page.locator(
            f"//div[@class='email-cell from']//a[contains(text(),'{username}')]/../..//"
            f"a[@class='read']")
        self.inbox_message_by_excerpt = lambda excerpt: page.locator(
            "div[class='email-cell excerpt']").get_by_role("link", name=excerpt, exact=True)
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
        self.deleted_username_by_excerpt = lambda excerpt: page.locator(
            f"//div[@class='email-cell excerpt']/a[normalize-space(text())='{excerpt}']/../../"
            f"div[@class='email-cell from']")
        self.sender_by_message_excerpt = lambda excerpt: page.locator(
            f"//div[@class='email-cell excerpt']/a[normalize-space(text())='{excerpt}']/../../"
            f"div[@class='email-cell from']/a")
        self.deleted_sender_by_message_excerpt = lambda excerpt: page.locator(
            f"//div[@class='email-cell excerpt']/a[normalize-space(text())='{excerpt}']/../../"
            f"div[@class='email-cell from']")

        """Locators belonging to the read inbox messages page."""
        self.message_sender = page.locator("//div[@class='user from']/a")
        self.message_deleted_user_sender = page.locator("//div[@class='user from']")
        self.message_content = page.locator("//div[@class='message']")
        self.message_received_date = page.locator("div[@class='user from']/time")
        self.message_user_information = page.locator("//section[@id='read-message']/i")

    """Actions against the Inbox scam banner."""
    def get_scam_alert_banner_text(self) -> str:
        """Get the text of the scam alert banner."""
        return self._get_text_of_element(self.scam_alert_banner_text)

    def click_on_scam_alert_close_button(self):
        """Click on the close button of the scam alert banner."""
        self._click(self.scam_alert_close_button)

    def get_scam_banner_message_locator(self) -> Locator:
        """Get the locator of the inbox message scam banner."""
        return self.scam_alert_banner_text

    """Actions against the general Inbox page locators."""
    def get_text_of_main_header(self) -> str:
        """Get the text of the main header of the inbox page."""
        return self._get_text_of_element(self.main_heading)

    def get_text_of_no_message_header(self) -> str:
        """Get the text of the no message header."""
        return self._get_text_of_element(self.no_messages_text)

    def is_no_message_header_displayed(self) -> bool:
        """Check if the no message header is displayed."""
        return self._is_element_visible(self.no_messages_text)

    """Actions against the Inbox action-banner."""
    def get_action_banner_text(self) -> str:
        """Get the text of the message action banner."""
        return self._get_text_of_element(self.message_action_banner)

    """Actions against the general buttons inside the Inbox page."""
    def click_on_new_message_button(self):
        """Click on the new message button."""
        self._click(self.new_message_button)

    def click_on_mark_selected_as_read_button(self):
        """Click on the mark selected as read button."""
        self._click(self.mark_selected_as_read_button)

    def click_on_delete_selected_button(self, expected_locator=None):
        """
            Click on the delete selected button.
            Args:
                expected_locator (Locator) : The expected locator after the click event.
        """
        self._click(self.delete_selected_button, expected_locator=expected_locator)


    def delete_all_inbox_messages_via_delete_selected_button(self, excerpt='', expected_url=None):
        """
            Delete all the inbox messages via the delete selected button.
            Args:
                excerpt (str): The excerpt of the message.
                expected_url (str): The expected URL after deleting all the messages.
        """
        self.wait_for_dom_to_load()
        if excerpt != '':
            inbox_messages_count = self.get_inbox_message_element_handles_based_on_excerpt(excerpt)
        else:
            inbox_messages_count = self._get_element_handles(self.inbox_messages)
        counter = 0
        for i in range(len(inbox_messages_count)):
            if excerpt != '':
                inbox_checkbox = self.get_message_select_checkbox_element(excerpt)
            else:
                inbox_checkbox = self.get_message_select_checkbox_element()
            element = inbox_checkbox[counter]
            self._checkbox_interaction(element, True)
            counter += 1

        self.click_on_delete_selected_button()
        self.click_on_delete_button_inside_the_confirmation_page(expected_url=expected_url)

    """Actions against the Inbox table."""
    def get_sender_by_excerpt(self, excerpt: str) -> str:
        """
            Get the message sender based on a given excerpt.
            Args:
                excerpt (str): The excerpt of the message.
        """
        return self._get_text_of_element(self.deleted_sender_by_message_excerpt(excerpt))

    def get_message_subject(self, username: str) -> str:
        """
            Get the subject of the inbox message based on the sender's username.
            Args:
                username (str): The username of the message sender.
        """
        return self._get_text_of_element(self.inbox_message_by_sender(username))

    def click_on_message_delete_button_by_username(self, username: str):
        """
        Click on the delete button of the inbox message based on the sender's username.
            Args:
                username (str): The username of the message sender.
        """
        self._click(self.delete_by_username(username))

    def click_on_message_delete_button_by_excerpt(self, excerpt: str):
        """
            Click on the delete button of the inbox message based on the message excerpt.
            Args:
                excerpt (str): The excerpt of the message.
        """
        self._click(self.delete_by_excerpt(excerpt))

    def click_on_message_sender_username(self, username: str):
        """
            Click on the username of the message sender.
            Args:
                username (str): The username of the message sender.
        """
        self._click(self.sender_username(username))

    def get_message_select_checkbox_element(self, excerpt='') -> list[ElementHandle]:
        """
            Get the element handle of the select checkbox based on the message excerpt.
            Args:
                excerpt (str): The excerpt of the message.
        """
        if excerpt != '':
            return self._get_element_handles(self.message_checkbox_by_excerpt(excerpt))
        else:
            return self._get_element_handles(self.inbox_delete_checkbox)

    def click_on_message_by_username(self, username: str):
        """
            Click on the subject of the inbox message based on the sender's username.
            Args:
                username (str): The username of the message sender.
        """
        self._click(self.inbox_message_by_sender(username))

    def click_on_message_by_excerpt(self, excerpt: str):
        """
        Clicking on a message which has a certain excerpt.
        Args:
            excerpt (str): The message excerpt.
        """
        self._click(self.inbox_message_by_excerpt(excerpt))

    """Actions against the delete confirmation page."""
    def click_on_delete_button_inside_the_confirmation_page(self, expected_url=None):
        """
            Click on the delete button inside the delete message confirmation page.
            Args:
                expected_url (str): The expected URL after deleting the message.
        """
        self._click(self.delete_confirmation_page_delete_button, expected_url=expected_url)

    def click_on_cancel_button_inside_the_confirmation_page(self):
        """
            Click on the cancel button inside the delete message confirmation page.

            Note: Hitting the "Enter" key button instead of click due to an issue in which the
            banner does not close on click events).
        """
        self._press_a_key(self.delete_confirmation_page_cancel_button, 'Enter')

    def get_inbox_message_locator_based_on_sender(self, username: str) -> Locator:
        """
            Get the locator of the inbox message based on the sender's username.
            Args:
                username (str): The username of the message sender.
        """
        return self.sender_username(username)

    def get_inbox_message_locator_based_on_excerpt(self, excerpt: str) -> Locator:
        """
            Get the locator of the inbox message based on the excerpt.
            Args:
                excerpt (str): The excerpt of the message.
        """
        return self.inbox_message_by_excerpt(excerpt)


    def get_inbox_message_element_handles_based_on_excerpt(self,
                                                           excerpt: str) -> list[ElementHandle]:
        """
            Get the element handles of the inbox messages based on the excerpt.
            Args:
                excerpt (str): The excerpt of the messages.
        """
        return self._get_element_handles(self.inbox_message_by_excerpt(excerpt))

    def are_inbox_messages_displayed(self) -> bool:
        """Check if the inbox messages are displayed."""
        return self._is_element_visible(self.inbox_messages_section)

    def get_all_read_messages_excerpt(self) -> list[str]:
        """Get the excerpt of all the read messages."""
        return self._get_text_of_elements(self.all_read_messages_excerpt)

    def check_a_particular_message_based_on_excerpt(self, excerpt=''):
        """
            Click on the checkbox for an inbox message based on the excerpt.
            Args:
                excerpt (str): The excerpt of the message.
        """
        inbox_checkbox = self.get_message_select_checkbox_element(excerpt)
        self._checkbox_interaction(inbox_checkbox[0], True)

    def get_all_unread_messages(self) -> list[Locator]:
        """Get all the unread messages."""
        return self.all_unread_messages.all()


    """Actions against the read inbox message page."""
    def get_the_deleted_user_message_sender_text(self) -> str:
        """Returns the name of the message sender (which should be the deleted user)"""
        return self._get_text_of_element(self.message_deleted_user_sender)

    def get_the_deleted_user_information_text(self) -> str:
        """Returns the deleted user information message"""
        return self._get_text_of_element(self.message_user_information)
