from playwright.sync_api import Locator, Page

from playwright_tests.core.basepage import BasePage


class NewMessagePage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        # New message page locators.
        self.new_message_page_header = page.locator("h1.sumo-page-heading")
        self.new_message_to_input_field = page.locator("input#token-input-id_to")
        self.new_message_textarea_input_field = page.locator("textarea#id_message")
        self.new_message_textarea_remaining_characters = page.locator("div#remaining-characters")
        self.new_message_cancel_button = page.get_by_role("link").filter(has_text="Cancel")
        self.new_message_send_button = page.locator("button[name='send']")
        self.new_message_preview_section = page.locator("section#preview")
        self.new_message_preview_section_content = page.locator("div.message")
        self.new_message_search_for_a_user_option = page.locator(
            "div.token-input-dropdown-facebook")
        self.new_message_search_results_bolded_characters = page.locator("div.name_search b")
        self.new_message_search_results_text = page.locator("div.name_search")
        self.sent_message_page_to_user_text = page.locator("li.token-input-token-facebook p")
        self.sent_messages_page_no_user_text = page.locator(
            "div.token-input-dropdown-facebook p").filter(has_text="No results")
        self.sent_message_page_to_user_delete_button = page.locator(
            "span.token-input-delete-token-facebook")
        self.searched_user = lambda username: page.locator(
            f"//div[@class='name_search' and text()='{username}']")

        #  Preview Section
        self.new_message_preview_username = page.locator("div[class*='user from'] a")
        self.new_message_preview_time = page.locator("div[class*='user from'] time")
        self.new_message_preview_data_first_paragraph_content = page.locator("div.message p").first
        self.new_message_preview_data_first_paragraph_strong_content = page.locator(
            "div.message p").first.locator("strong")
        self.new_message_preview_data_first_paragraph_italic_content = page.locator(
            "div.message p").first.locator("em")
        self.new_message_numbered_list_items = page.locator("div.message ol li")
        self.new_message_bulleted_list_items = page.locator("div.message ul li")
        self.new_message_preview_external_link = page.get_by_role("link").filter(
            has_text="Test external link")
        self.new_message_preview_internal_link = page.get_by_role("link").filter(
            has_text="Test internal Link")
        self.new_message_preview_button = page.locator("input#preview-btn")

    # New message page actions.
    def get_text_of_test_data_first_paragraph_text(self) -> str:
        """Get text of the first paragraph in the preview section."""
        return self._get_text_of_element(self.new_message_preview_data_first_paragraph_content)

    def get_text_of_test_data_first_p_strong_text(self) -> str:
        """Get text of the first bolded paragraph in the preview section."""
        return self._get_text_of_element(
            self.new_message_preview_data_first_paragraph_strong_content)

    def get_text_of_test_data_first_p_italic_text(self) -> str:
        """Get text of the first italicised paragraph in the preview section."""
        return self._get_text_of_element(
            self.new_message_preview_data_first_paragraph_italic_content)

    def get_text_of_numbered_list_items(self) -> list[str]:
        """Get text of the numbered list items in the preview section."""
        return self._get_text_of_elements(self.new_message_numbered_list_items)

    def get_text_of_bulleted_list_items(self) -> list[str]:
        """Get text of the bulleted list items in the preview section."""
        return self._get_text_of_elements(self.new_message_bulleted_list_items)

    def get_text_of_message_preview_username(self) -> str:
        """Get text of the username in the preview section."""
        return self._get_text_of_element(self.new_message_preview_username)

    def get_user_to_text(self) -> str:
        """Get text of the user to in the sent message page."""
        return self._get_text_of_element(self.sent_message_page_to_user_text)

    def get_no_user_to_locator(self) -> Locator:
        """Get locator of the no user to in the sent message page."""
        return self.sent_messages_page_no_user_text

    def get_new_message_page_header_text(self) -> str:
        """Get text of the new message page header."""
        return self._get_text_of_element(self.new_message_page_header)

    def get_characters_remaining_text(self) -> str:
        """Get text of the characters remaining in the textarea."""
        return self._get_text_of_element(self.new_message_textarea_remaining_characters)

    def get_characters_remaining_text_element(self) -> Locator:
        """Get locator of the characters remaining in the textarea."""
        return self.new_message_textarea_remaining_characters

    def get_text_of_new_message_preview_section(self) -> str:
        """Get text of the new message preview section."""
        return self._get_text_of_element(self.new_message_preview_section_content)

    def get_text_of_search_result_bolded_character(self) -> str:
        """Get text of the search result bolded character."""
        return self._get_text_of_element(self.new_message_search_results_bolded_characters)

    def get_tet_of_search_results_text(self) -> list[str]:
        """Get text of the search results."""
        return self._get_text_of_elements(self.new_message_search_results_text)

    def click_on_username_to_delete_button(self):
        """Click on the username to delete button."""
        self._click(self.sent_message_page_to_user_delete_button)

    def click_on_new_message_cancel_button(self):
        """Click on the new message cancel button."""
        self._click(self.new_message_cancel_button)

    def click_on_new_message_preview_button(self):
        """Click on the new message preview button."""
        self._click(self.new_message_preview_button)

    def click_on_new_message_send_button(self, expected_url=None):
        """Click on the new message send button.

        Args:
            expected_url (str): The expected URL after the click event.
        """
        self._click(self.new_message_send_button, expected_url=expected_url)

    def click_on_a_searched_user(self, username: str):
        """Click on a searched user.

        Args:
            username (str): The username to click on.
        """
        self._click(self.searched_user(username))

    def click_on_preview_internal_link(self):
        """Click on the preview internal link."""
        self._click(self.new_message_preview_internal_link)

    def type_into_new_message_to_input_field(self, text: str):
        """Type into the new message to input field.

        Args:
            text (str): The text to type into the input field.
        """
        self._type(self.new_message_to_input_field, text, 0)

    def fill_into_new_message_body_textarea(self, text: str):
        """Fill into the new message body textarea.

        Args:
            text (str): The text to fill into the textarea.
        """
        self._fill(self.new_message_textarea_input_field, text)

    def type_into_new_message_body_textarea(self, text: str):
        """Type into the new message body textarea.

        Args:
            text (str): The text to type into the textarea
        """
        self._type(self.new_message_textarea_input_field, text, 0)

    def message_preview_section_element(self) -> Locator:
        """Get locator of the message preview section."""
        return self.new_message_preview_section

    def is_message_preview_time_displayed(self) -> bool:
        """Check if the message preview time is displayed."""
        return self._is_element_visible(self.new_message_preview_time)

    def new_message_preview_internal_link_test_data_element(self) -> Locator:
        """Get locator of the new message preview internal link."""
        return self.new_message_preview_internal_link

    def new_message_preview_external_link_test_data_element(self) -> Locator:
        """Get locator of the new message preview external link."""
        return self.new_message_preview_external_link
