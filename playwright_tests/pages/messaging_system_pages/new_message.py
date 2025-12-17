from playwright.sync_api import Page

from playwright_tests.core.basepage import BasePage


class NewMessagePage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """General locators belonging to the New Message page."""
        self.page_header = page.locator("h1.sumo-page-heading")

        """Locators belonging to the New Message page input fields."""
        self.to_input_field = page.locator("input#token-input-id_to")
        self.search_for_a_user_dropdown = page.locator("div.token-input-dropdown-facebook")
        self.user_search_results_bolded_characters = page.locator("div.name_search b")
        self.user_search_results_text = page.locator("div.name_search")
        self.added_to_user_text = page.locator("li.token-input-token-facebook p")
        self.no_user_search_results_text = page.locator(
            "div.token-input-dropdown-facebook p").filter(has_text="No results")
        self.added_user_delete_button = page.locator("span.token-input-delete-token-facebook")
        self.searched_user = lambda username: page.locator(
            f"//div[@class='name_search' and text()='{username}']")
        self.textarea_input_field = page.locator("textarea#id_message")
        self.textarea_remaining_characters_message = page.locator("div#remaining-characters")
        self.cancel_button = page.get_by_role("link").filter(has_text="Cancel")
        self.send_button = page.locator("button[name='send']")

        """Locators belonging to the New Message preview section."""
        self.preview_section = page.locator("section#preview")
        self.preview_section_content = page.locator("div.message")

        """Locators belonging to the New Message preview section."""
        self.preview_username = page.locator("div[class*='user from'] a")
        self.preview_deleted_username = page.locator("div[class*='user from']")
        self.preview_time = page.locator("div[class*='user from'] time")
        self.preview_data_first_paragraph_content = page.locator("div.message p").first
        self.preview_data_first_paragraph_strong_content = page.locator(
            "div.message p").first.locator("strong")
        self.preview_data_first_paragraph_italic_content = page.locator(
            "div.message p").first.locator("em")
        self.preview_numbered_list_items = page.locator("div.message ol li")
        self.preview_bulleted_list_items = page.locator("div.message ul li")
        self.preview_external_link = page.get_by_role("link").filter(has_text="Test external link")
        self.preview_internal_link = page.get_by_role("link").filter(has_text="Test internal Link")
        self.preview_button = page.locator("input#preview-btn")

    """Actions against the general New Message page locators."""
    def get_header_text(self) -> str:
        """Get the text of the new message page header."""
        return self._get_text_of_element(self.page_header)

    """Actions against the New Message "To" input field."""
    def get_to_user_text(self) -> str:
        """Get the text of the targeted user from the 'To' field."""
        return self._get_text_of_element(self.added_to_user_text)

    def get_text_of_search_result_bolded_character(self) -> str:
        """Get the text of the search result bolded character."""
        return self._get_text_of_element(self.user_search_results_bolded_characters)

    def get_text_of_search_results(self) -> list[str]:
        """Get the text of the 'To' search results."""
        return self._get_text_of_elements(self.user_search_results_text)

    def click_on_username_to_delete_button(self):
        """Click on the delete button from an added user inside the 'To' field."""
        self._click(self.added_user_delete_button)

    def click_on_a_searched_user(self, username: str):
        """
            Click on a searched user.
            Args:
                username (str): The username to click on.
        """
        self._click(self.searched_user(username))

    def type_into_to_input_field(self, text: str):
        """
            Type into the 'To' field from the New Messages page.
            Args:
                text (str): The text to type into the input field.
        """
        self._type(self.to_input_field, text, 0)

    """Actions against the New Message textarea field."""
    def get_characters_remaining_text(self) -> str:
        """Get the text of the characters remaining message from the New Message textarea."""
        return self._get_text_of_element(self.textarea_remaining_characters_message)

    def click_cancel_button(self):
        """Click on the 'Cancel' button from the New Messages page."""
        self._click(self.cancel_button)

    def click_on_preview_button(self):
        """Click on the 'Preview' button from the New Messages page."""
        self._click(self.preview_button)

    def click_on_send_button(self, expected_url=None):
        """
            Click on the 'Send' button from the New Messages page.
            Args:
                expected_url (str) (optional): The expected URL after the click event.
        """
        self._click(self.send_button, expected_url=expected_url)


    def fill_into_message_textarea(self, text: str):
        """
            Fill into the 'Message' textarea from the New Message page.
            Args:
                text (str): The text to fill into the textarea.
        """
        self._fill(self.textarea_input_field, text)

    def type_into_textarea_body(self, text: str):
        """
            Type into the 'Message' textarea from the New Message page.
            Args:
                text (str): The text to type into the textarea.
        """
        self._type(self.textarea_input_field, text, 0)

    """Actions against the New message preview section."""
    def get_text_of_previewed_data_first_paragraph(self) -> str:
        """Get the text of the first paragraph in the preview section."""
        return self._get_text_of_element(self.preview_data_first_paragraph_content)

    def get_text_of_previewed_data_first_p_strong(self) -> str:
        """Get the text of the first bolded paragraph in the preview section."""
        return self._get_text_of_element(self.preview_data_first_paragraph_strong_content)

    def get_text_of_previewed_data_first_p_italic(self) -> str:
        """Get the text of the first italicised paragraph in the preview section."""
        return self._get_text_of_element(self.preview_data_first_paragraph_italic_content)

    def get_text_of_previewed_data_numbered_list_items(self) -> list[str]:
        """Get the text of the numbered list items in the preview section."""
        return self._get_text_of_elements(self.preview_numbered_list_items)

    def get_text_of_previewed_data_bulleted_list_items(self) -> list[str]:
        """Get the text of the bulleted list items in the preview section."""
        return self._get_text_of_elements(self.preview_bulleted_list_items)

    def get_text_of_preview_data_username(self) -> str:
        """Get the text of the username in the preview section."""
        return self._get_text_of_element(self.preview_username)

    def get_text_of_new_message_preview_section(self) -> str:
        """Get the text of the whole New Message preview section."""
        return self._get_text_of_element(self.preview_section_content)

    def click_on_preview_internal_link(self):
        """Click on the internal link from the New Message preview section."""
        self._click(self.preview_internal_link)

    def is_message_preview_time_displayed(self) -> bool:
        """Check if the message preview time is displayed."""
        return self._is_element_visible(self.preview_time)
