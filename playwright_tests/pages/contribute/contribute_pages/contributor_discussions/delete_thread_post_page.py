from playwright_tests.core.basepage import BasePage


class DeleteThreadPostPage(BasePage):
    """ This class contains the locators and actions for the Delete Thread Post page."""

    def __init__(self, page):
        super().__init__(page)

        """Locators belonging to the delete thread post page."""
        self.delete_page_header = page.locator("article#confirm-delete h1")
        self.delete_button = page.locator("//input[@type='submit']")
        self.cancel_option = page.get_by_role("link", name="Cancel")


    """Actions against the delete thread post page."""
    def click_on_delete_button(self):
        """
            Click on the 'Delete' button.
        """
        self._click(self.delete_button)
