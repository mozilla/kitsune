from playwright_tests.core.basepage import BasePage


class EditThreadTitle(BasePage):
    """
        This class contains the locators and actions for the Edit Thread Title page.
    """

    def __init__(self, page):
        super().__init__(page)

        # Locators related to the breadcrumbs section.
        self.edit_thread_title_breadcrumbs = page.locator("ol#breadcrumbs li a")
        self.edit_thread_title_breadcrumb = lambda breadcrumb : page.locator(
            "ol#breadcrumbs li").get_by_role("link", name=breadcrumb)

        # Locators related to the edit thread title page.
        self.edit_thread_title_page_title = page.locator("div#edit-thread h1")
        self.edit_thread_title_input_field = page.locator("input#id_title")
        self.edit_thread_title_update_thread_button = page.get_by_role(
            "button", name="Update thread")
        self.edit_thread_title_cancel_edit_button = page.get_by_role("link", name="Cancel")

    def get_text_of_thread_title_input_field(self) -> str:
        """
            Get the text of the thread title input field.
            returns:
                str: The text of the thread title input field.
        """
        return self._get_element_input_value(self.edit_thread_title_input_field)

    def fill_into_thread_title_input_field(self, text: str):
        """
            Fill into the thread title input field.
            Args:
                text (str): The text to fill into the thread title input field.
        """
        self._clear_field(self.edit_thread_title_input_field)
        self._fill(self.edit_thread_title_input_field, text)

    def click_on_update_thread_button(self):
        """
            Click on the 'Update thread' button.
        """
        self._click(self.edit_thread_title_update_thread_button)

    def click_on_cancel_button(self):
        """
            Click on the 'Cancel' button.
        """
        self._click(self.edit_thread_title_cancel_edit_button)
