from playwright_tests.core.basepage import BasePage


class EditThreadPostPage(BasePage):
    """
        This class contains the locators and actions for the Edit Thread Post page.
    """
    def __init__(self, page):
        super().__init__(page)
        self.edit_post_header = page.locator("div#edit-post h1")
        self.edit_post_textarea = page.locator("textarea#id_content")
        self.edit_post_cancel_button = page.get_by_role("link", name="Cancel")
        self.edit_post_update_post_button = page.get_by_role("button", name="Update post")
        self.edit_post_preview_button = page.get_by_role("button", name="Preview")

    def add_text_inside_the_edit_post_textarea(self, text: str):
        """
            Add text inside the edit post textarea.
            Args:
                text (str): The text to be added inside the edit post textarea.
        """
        self._fill(self.edit_post_textarea, text)

    def click_on_update_post_button(self):
        """
            Click on the 'Update post' button.
        """
        self._click(self.edit_post_update_post_button)
