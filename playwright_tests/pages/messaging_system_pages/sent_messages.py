from playwright.sync_api import ElementHandle, Locator, Page

from playwright_tests.core.basepage import BasePage


class SentMessagePage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        # Sent messages page locators.
        self.sent_messages_breadcrumbs = page.locator("ol#breadcrumbs li")
        self.sent_messages_page_header = page.locator("h1.sumo-page-subheading")
        self.sent_messages_no_messages_message = page.locator("article#outbox p")
        self.sent_messages_delete_selected_button = page.get_by_role("button").filter(
            has_text="Delete Selected")
        self.sent_messages_delete_page_delete_button = page.locator("button[name='delete']")
        self.sent_messages_delete_page_cancel_button = page.get_by_role("link").filter(
            has_text="Cancel")
        self.sent_messages_page_message_banner_text = page.locator("ul.user-messages li p")
        self.sent_message_page_message_banner_close_button = page.locator(
            "button.mzp-c-notification-bar-button")
        self.sent_messages = page.locator("li.email-row:not(.header)")
        self.sent_messages_section = page.locator("ol.outbox-table")
        self.sent_messages_delete_button = page.locator("ol.outbox-table a.delete")
        self.sent_messages_delete_checkbox = page.locator("div.checkbox label")
        self.sent_message_subject = lambda username: page.locator(
            f"//div[@class='email-cell to']//a[contains(text(),'{username}')]/../../div[@class="
            f"'email-cell excerpt']/a")
        self.delete_by_user_button = lambda username: page.locator(
            f"//div[@class='email-cell to']//a[contains(text(),'{username}')]/../..//a"
            f"[@class='delete']")
        self.delete_by_excerpt_button = lambda excerpt: page.locator(
            f"//div[@class='email-cell excerpt']/a[normalize-space(text())='{excerpt}']/../..//"
            f"a[@class='delete']")
        self.sender_username = lambda username: page.locator(
            "div[class='email-cell to']").get_by_role("link", name=username, exact=True)
        self.sent_message_checkbox = lambda excerpt: page.locator(
            f"//div[@class='email-cell excerpt']/a[normalize-space(text())='{excerpt}']/../../div"
            f"[@class='email-cell field checkbox no-label']/label")
        self.sent_message_by_subject = lambda subject: page.locator(
            "div[class='email-cell excerpt']").get_by_role("link", name=subject, exact=True)
        self.sent_message_to_group = lambda group_name: page.locator(
            f"//div[@class='email-cell to-groups']/a[text()='{group_name}']/../../div[@class='"
            f"email-cell excerpt']")
        self.sent_message_by_group = lambda group_name, excerpt: page.locator(
            f"//div[@class='email-cell to-groups']//a[contains(text(),'{group_name}')]/../../div[@"
            f"class='email-cell excerpt']/a[normalize-space(text())='{excerpt}']")

        # Read Sent Messages page
        self.to_groups_list_items = page.locator("span.to-group a")
        self.to_user_list_items = page.locator("span.to a")

    # Sent messages page actions.
    def get_sent_messages_page_deleted_banner_text(self) -> str:
        """Get the text of the banner that appears when a message is deleted."""
        return self._get_text_of_element(self.sent_messages_page_message_banner_text)

    def get_sent_messages_page_header(self) -> str:
        """Get the header text of the sent messages page."""
        return self._get_text_of_element(self.sent_messages_page_header)

    def get_sent_messages_no_message_text(self) -> str:
        """Get the text of the message that appears when there are no messages in the
        sent messages page.
        """
        return self._get_text_of_element(self.sent_messages_no_messages_message)

    def get_sent_message_subject(self, username: str) -> str:
        """Get the subject of the sent message by the username of the recipient.

        Args:
            username (str): The username of the recipient.
        """
        return self._get_text_of_element(self.sent_message_subject(username))

    def click_on_delete_selected_button(self, expected_locator=None):
        """Click on the delete selected button on the sent messages page.

        Args:
            expected_locator (str): The expected locator after the click event.
        """
        self._click(self.sent_messages_delete_selected_button, expected_locator=expected_locator)

    def click_on_sent_message_delete_button_by_user(self, username: str):
        """Click on the delete button of a sent message by the username of the recipient.

        Args:
            username (str): The username of the recipient.
        """
        self._click(self.delete_by_user_button(username))

    def click_on_sent_message_delete_button_by_excerpt(self, excerpt: str):
        """Click on the delete button of a sent message by the excerpt of the message.

        Args:
            excerpt (str): The excerpt of the message.
        """
        self._click(self.delete_by_excerpt_button(excerpt))

    def click_on_sent_message_sender_username(self, username: str):
        """Click on the sender username of a sent message."""
        self._click(self.sender_username(username))

    def sent_message_select_checkbox(self) -> list[ElementHandle]:
        """Get element handle list of the selected sent messages checkboxes."""
        return self._get_element_handles(self.sent_messages_delete_checkbox)

    def sent_message_select_checkbox_element(self, excerpt: str) -> list[ElementHandle]:
        """Get element handle list of the selected sent messages checkboxes by excerpt.

        Args:
            excerpt (str): The excerpt of the message.
        """
        return self._get_element_handles(self.sent_message_checkbox(excerpt))

    def click_on_sent_message_subject(self, text: str):
        """Click on the subject of a sent message by the text of the subject.

        Args:
            text (str): The text of the subject.
        """
        self._click(self.sent_message_by_subject(text))

    def click_on_sent_messages_to_group_subject(self, group_name: str):
        """Click on the subject of a sent message by the group name of the recipient.

        Args:
            group_name (str): The name of the group.
        """
        self._click(self.sent_message_to_group(group_name))

    def click_on_delete_page_delete_button(self, expected_url=None):
        """Click on the delete button on the delete message page.

        Args:
            expected_url (str): The expected URL after the deletion.
        """
        self._click(self.sent_messages_delete_page_delete_button, expected_url=expected_url)

    def click_on_delete_page_cancel_button(self):
        """Click on the cancel button on the delete message page."""
        self._click(self.sent_messages_delete_page_cancel_button)

    def sent_messages_by_username(self, username: str) -> Locator:
        """Get the locator of the sent messages by the username of the recipient.

        Args:
            username (str): The username of the recipient.
        """
        return self.sender_username(username)

    def sent_messages_by_excerpt_locator(self, excerpt: str) -> Locator:
        """Get the locator of the sent messages by the excerpt of the message.

        Args:
            excerpt (str): The excerpt of the message.
        """
        return self.sent_message_by_subject(excerpt)

    def sent_messages_by_excerpt_element_handles(self, excerpt: str) -> list[ElementHandle]:
        """Get the element handle list of the sent messages by the excerpt of the message.

        Args:
            excerpt (str): The excerpt of the message.
        """
        return list(self._get_element_handles(
            self.sent_message_by_subject(excerpt)))

    def sent_messages_to_group(self, group: str, excerpt: str) -> Locator:
        """Get the locator of the sent message by the group name of the recipient and the excerpt

        Args:
            group (str): The name of the group.
            excerpt (str): The excerpt of the message.
        """
        return self.sent_message_by_group(group, excerpt)

    def sent_message_banner(self) -> Locator:
        """Get the locator of the sent message banner."""
        return self.sent_messages_page_message_banner_text

    def are_sent_messages_displayed(self) -> bool:
        """Check if the sent messages are displayed."""
        return self._is_element_visible(self.sent_messages_section)

    def delete_all_displayed_sent_messages(self, expected_url=None):
        """Delete all the displayed sent messages.

        Args:
            expected_url (str): The expected URL after the deletion.
        """
        sent_elements_delete_button = self._get_element_handles(self.sent_messages_delete_button)
        for i in range(len(sent_elements_delete_button)):
            delete_button = sent_elements_delete_button[i]

            self._click(delete_button)
            self.click_on_delete_page_delete_button(expected_url=expected_url)

    def delete_all_sent_messages_via_delete_selected_button(self, excerpt='', expected_url=None):
        """Delete all the sent messages via the delete selected button.

        Args:
            excerpt (str): The excerpt of the message.
            expected_url (str): The expected URL after the deletion.
        """
        if excerpt != '':
            sent_messages_count = self.sent_messages_by_excerpt_element_handles(excerpt)
        else:
            sent_messages_count = self._get_element_handles(self.sent_messages)
        counter = 0
        for i in range(len(sent_messages_count)):
            if excerpt != '':
                checkbox = self.sent_message_select_checkbox_element(excerpt)
            else:
                checkbox = self.sent_message_select_checkbox()
            element = checkbox[counter]
            self._checkbox_interaction(element, True)
            counter += 1

        self.click_on_delete_selected_button()
        self.click_on_delete_page_delete_button(expected_url=expected_url)

    # Read Sent Message page
    def get_text_of_all_sent_groups(self) -> list[str]:
        """Get the text of all the sent groups."""
        return self._get_text_of_elements(self.to_groups_list_items)

    def get_text_of_all_recipients(self) -> list[str]:
        """Get the text of all the recipients."""
        return self._get_text_of_elements(self.to_user_list_items)
