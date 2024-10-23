from playwright.sync_api import Page, Locator
from playwright_tests.core.basepage import BasePage


class NewMessagePage(BasePage):
    # New message page locators.
    NEW_MESSAGE_PAGE_LOCATORS = {
        "new_message_page_header": "//h1[@class='sumo-page-heading']",
        "new_message_to_input_field": "//input[@id='token-input-id_to']",
        "new_message_textarea_input_field": "//textarea[@id='id_message']",
        "new_message_textarea_remaining_characters": "//div[@id='remaining-characters']",
        "new_message_cancel_button": "//a[contains(text(),'Cancel')]",
        "new_message_send_button": "//button[@name='send']",
        "new_message_preview_section": "//section[@id='preview']",
        "new_message_preview_section_content": "//div[@class='message']",
        "new_message_search_for_a_user_option": "//div[@class='token-input-dropdown-facebook']",
        "new_message_search_results_bolded_characters": "//div[@class='name_search']/b",
        "new_message_search_results_text": "//div[@class='name_search']",
        "sent_message_page_to_user_text": "//li[@class='token-input-token-facebook']/p",
        "sent_messages_page_no_user_text": "//div[@class='token-input-dropdown-facebook']/p[text("
                                           ")='No results']",
        "sent_message_page_to_user_delete_button": "//span[@class='token-input-delete-token"
                                                   "-facebook']"
    }

    #  Preview Section
    PREVIEW_SECTION_LOCATORS = {
        "new_message_preview_username": "//div[contains(@class, 'user from')]/a",
        "new_message_preview_time": "//div[contains(@class, 'user from')]/time",
        "new_message_preview_data_first_paragraph_content": "//div[@class='message']/p[1]",
        "new_message_preview_data_first_paragraph_strong_content": "//div[@class='message']/p[1]"
                                                                   "/strong",
        "new_message_preview_data_first_paragraph_italic_content": "//div[@class='message']/p[1]/"
                                                                   "em",
        "new_message_numbered_list_items": "//div[@class='message']/ol/li",
        "new_message_bulleted_list_items": "//div[@class='message']/ul/li",
        "new_message_preview_external_link": "//a[contains(text(),'Test external link')]",
        "new_message_preview_internal_link": "//a[contains(text(),'Test internal Link')]",
        "new_message_preview_button": "//input[@id='preview-btn']"
    }

    def __init__(self, page: Page):
        super().__init__(page)

    # New message page actions.
    def get_text_of_test_data_first_paragraph_text(self) -> str:
        """Get text of the first paragraph in the preview section."""
        return self._get_text_of_element(
            self.PREVIEW_SECTION_LOCATORS["new_message_preview_data_first_paragraph_content"])

    def get_text_of_test_data_first_p_strong_text(self) -> str:
        """Get text of the first bolded paragraph in the preview section."""
        return self._get_text_of_element(
            self.PREVIEW_SECTION_LOCATORS
            ["new_message_preview_data_first_paragraph_strong_content"])

    def get_text_of_test_data_first_p_italic_text(self) -> str:
        """Get text of the first italicised paragraph in the preview section."""
        return self._get_text_of_element(
            self.PREVIEW_SECTION_LOCATORS
            ["new_message_preview_data_first_paragraph_italic_content"])

    def get_text_of_numbered_list_items(self) -> list[str]:
        """Get text of the numbered list items in the preview section."""
        return self._get_text_of_elements(self.PREVIEW_SECTION_LOCATORS
                                          ["new_message_numbered_list_items"])

    def get_text_of_bulleted_list_items(self) -> list[str]:
        """Get text of the bulleted list items in the preview section."""
        return self._get_text_of_elements(self.PREVIEW_SECTION_LOCATORS
                                          ["new_message_bulleted_list_items"])

    def get_text_of_message_preview_username(self) -> str:
        """Get text of the username in the preview section."""
        return self._get_text_of_element(self.PREVIEW_SECTION_LOCATORS
                                         ["new_message_preview_username"])

    def get_user_to_text(self) -> str:
        """Get text of the user to in the sent message page."""
        return self._get_text_of_element(self.NEW_MESSAGE_PAGE_LOCATORS
                                         ["sent_message_page_to_user_text"])

    def get_no_user_to_locator(self) -> Locator:
        """Get locator of the no user to in the sent message page."""
        return self._get_element_locator(self.NEW_MESSAGE_PAGE_LOCATORS
                                         ["sent_messages_page_no_user_text"])

    def get_new_message_page_header_text(self) -> str:
        """Get text of the new message page header."""
        return self._get_text_of_element(self.NEW_MESSAGE_PAGE_LOCATORS["new_message_page_header"])

    def get_characters_remaining_text(self) -> str:
        """Get text of the characters remaining in the textarea."""
        return self._get_text_of_element(self.NEW_MESSAGE_PAGE_LOCATORS
                                         ["new_message_textarea_remaining_characters"])

    def get_characters_remaining_text_element(self) -> Locator:
        """Get locator of the characters remaining in the textarea."""
        return self._get_element_locator(self.NEW_MESSAGE_PAGE_LOCATORS
                                         ["new_message_textarea_remaining_characters"])

    def get_text_of_new_message_preview_section(self) -> str:
        """Get text of the new message preview section."""
        return self._get_text_of_element(self.NEW_MESSAGE_PAGE_LOCATORS
                                         ["new_message_preview_section_content"])

    def get_text_of_search_result_bolded_character(self) -> str:
        """Get text of the search result bolded character."""
        return self._get_text_of_element(self.NEW_MESSAGE_PAGE_LOCATORS
                                         ["new_message_search_results_bolded_characters"])

    def get_tet_of_search_results_text(self) -> list[str]:
        """Get text of the search results."""
        return self._get_text_of_elements(self.NEW_MESSAGE_PAGE_LOCATORS
                                          ["new_message_search_results_text"])

    def click_on_username_to_delete_button(self):
        """Click on the username to delete button."""
        self._click(self.NEW_MESSAGE_PAGE_LOCATORS["sent_message_page_to_user_delete_button"])

    def click_on_new_message_cancel_button(self):
        """Click on the new message cancel button."""
        self._click(self.NEW_MESSAGE_PAGE_LOCATORS["new_message_cancel_button"])

    def click_on_new_message_preview_button(self):
        """Click on the new message preview button."""
        self._click(self.PREVIEW_SECTION_LOCATORS["new_message_preview_button"])

    def click_on_new_message_send_button(self):
        """Click on the new message send button."""
        self._click(self.NEW_MESSAGE_PAGE_LOCATORS["new_message_send_button"])

    def click_on_a_search_result(self, username: str):
        """Click on a search result.

        Args:
            username (str): The username to click on.
        """
        self._click(f"//div[@class='name_search' and text()='{username}']")

    def click_on_a_searched_user(self, username: str):
        """Click on a searched user.

        Args:
            username (str): The username to click on.
        """
        self._click(f"//div[@class='name_search' and text()='{username}']")

    def click_on_preview_internal_link(self):
        """Click on the preview internal link."""
        self._click(self.PREVIEW_SECTION_LOCATORS["new_message_preview_internal_link"])

    def type_into_new_message_to_input_field(self, text: str):
        """Type into the new message to input field.

        Args:
            text (str): The text to type into the input field.
        """
        self._type(self.NEW_MESSAGE_PAGE_LOCATORS["new_message_to_input_field"], text, 0)

    def fill_into_new_message_body_textarea(self, text: str):
        """Fill into the new message body textarea.

        Args:
            text (str): The text to fill into the textarea.
        """
        self._fill(self.NEW_MESSAGE_PAGE_LOCATORS["new_message_textarea_input_field"], text)

    def type_into_new_message_body_textarea(self, text: str):
        """Type into the new message body textarea.

        Args:
            text (str): The text to type into the textarea
        """
        self._type(self.NEW_MESSAGE_PAGE_LOCATORS["new_message_textarea_input_field"], text, 0)

    def message_preview_section_element(self) -> Locator:
        """Get locator of the message preview section."""
        return self._get_element_locator(self.NEW_MESSAGE_PAGE_LOCATORS
                                         ["new_message_preview_section"])

    def is_message_preview_time_displayed(self) -> bool:
        """Check if the message preview time is displayed."""
        return self._is_element_visible(self.PREVIEW_SECTION_LOCATORS["new_message_preview_time"])

    def new_message_preview_internal_link_test_data_element(self) -> Locator:
        """Get locator of the new message preview internal link."""
        return self._get_element_locator(self.PREVIEW_SECTION_LOCATORS
                                         ["new_message_preview_internal_link"])

    def new_message_preview_external_link_test_data_element(self) -> Locator:
        """Get locator of the new message preview external link."""
        return self._get_element_locator(self.PREVIEW_SECTION_LOCATORS
                                         ["new_message_preview_external_link"])
