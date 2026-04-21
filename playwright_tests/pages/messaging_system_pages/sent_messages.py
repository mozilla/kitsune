from playwright.sync_api import ElementHandle, Page

from playwright_tests.core.basepage import BasePage


class SentMessagePage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """Locators belonging to the breadcrumbs section."""
        self.all_breadcrumbs = page.locator("ol#breadcrumbs li")

        """Locators belonging to the Sent Messages banner."""
        self.banner_text = page.locator("ul.user-messages li p")
        self.banner_close_button = page.locator("button.mzp-c-notification-bar-button")

        """General locators belonging to the Sent Messages page."""
        self.page_header = page.locator("h1.sumo-page-subheading")
        self.no_messages_message = page.locator("article#outbox p")

        """Locators belonging to the Sent Messages buttons."""
        self.delete_selected_button = page.get_by_role("button").filter(has_text="Delete Selected")
        self.delete_button = page.locator("button[name='delete']")

        """Locators belonging to the Sent Messages delete confirmation page."""
        self.delete_confirmation_cancel_button = page.get_by_role("link").filter(
            has_text="Cancel")

        """Locators belonging to the Sent Messages table."""
        self.sent_messages = page.locator("li.email-row:not(.header)")
        self.sent_messages_section = page.locator("ol.outbox-table")
        self.sent_messages_delete_button = page.locator("ol.outbox-table a.delete")
        self.sent_messages_checkboxes = page.locator("div.checkbox label")
        self.sent_message_subject = lambda username: page.locator(
            f"//div[@class='email-cell to']//a[contains(text(),'{username}')]/../../div[@class="
            f"'email-cell excerpt']/a")
        self.delete_by_user_button = lambda username: page.locator(
            f"//div[@class='email-cell to']//a[contains(text(),'{username}')]/../..//a"
            f"[@class='delete']")
        self.delete_by_excerpt_button = lambda excerpt: page.locator(
            f"//div[@class='email-cell excerpt']/a[normalize-space(text())='{excerpt}']/../..//"
            f"a[contains(@class,'delete')]")
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
        self.recipient_based_on_excerpt = lambda excerpt: page.locator(
            f"//div[@class='email-cell excerpt']/a[normalize-space(text())='{excerpt}']/../../"
            f"div[@class='email-cell to']/a")
        self.deleted_user_recipient_based_on_excerpt = lambda excerpt: page.locator(
            f"//div[@class='email-cell excerpt']/a[normalize-space(text())='{excerpt}']/../../"
            f"div[@class='email-cell to']")

        """Locators belonging to the read Sent Messages page."""
        self.to_groups_list_items = page.locator("span.to-group a")
        self.to_user_list_items = page.locator("span.to a")
        self.to_deleted_user_list_item = page.locator("span.to")

        """Locators belonging to the pagination section"""
        self.paginator_section = page.locator("//ol[@class='pagination cf']")


    """Actions against the Sent Messages page buttons."""
    def click_on_delete_selected_button(self, expected_locator=None):
        """
            Click on the delete selected button from the Sent Messages page.
            Args:
                expected_locator (str) (optional): The expected locator after the click event.
        """
        self._click(self.delete_selected_button, expected_locator=expected_locator)

    """Actions against the Sent Messages table."""
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
        return self._get_element_handles(self.sent_messages_checkboxes)

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

    def click_on_delete_page_delete_button(self, expected_locator=None):
        """Click on the delete button on the delete message page.

        Args:
            expected_locator (str): The expected locator after the deletion.
        """
        self._click(self.delete_button, expected_locator=expected_locator)

    def click_on_delete_page_cancel_button(self):
        """Click on the cancel button on the delete message page."""
        self._click(self.delete_confirmation_cancel_button)

    def sent_messages_by_excerpt_element_handles(self, excerpt: str) -> list[ElementHandle]:
        """Get the element handle list of the sent messages by the excerpt of the message.

        Args:
            excerpt (str): The excerpt of the message.
        """
        return list(self._get_element_handles(
            self.sent_message_by_subject(excerpt)))

    def delete_all_sent_messages_via_delete_selected_button(self, excerpt='',
                                                            expected_locator=None):
        """Delete all the sent messages via the delete selected button.

        Args:
            excerpt (str): The excerpt of the message.
            expected_locator (str): The expected locator after the deletion.
        """
        self.wait_for_dom_to_load()
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
        self.click_on_delete_page_delete_button(expected_locator=expected_locator)
