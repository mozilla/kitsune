from playwright_tests.core.basepage import BasePage


class NewThreadPage(BasePage):
    def __init__(self, page):
        super().__init__(page)

        # Locators related to the create a new thread page
        self.title_input_field = page.locator("input#id_title")
        self.content_textarea_field = page.locator("textarea#id_content")
        self.cancel_button = page.get_by_role("link", name="Cancel")
        self.preview_button = page.locator("button#preview")
        self.post_thread_button = page.get_by_role("button").filter(has_text="Post Thread")

    def fill_title_input_field(self, title: str):
        self._fill(self.title_input_field, title)

    def clear_title_input_field(self):
        self._clear_field(self.title_input_field)

    def fill_content_textarea_field(self, content: str):
        self._fill(self.content_textarea_field, content)

    def clear_content_textarea_field(self):
        self._clear_field(self.content_textarea_field)

    def click_on_post_thread_button(self):
        self._click(self.post_thread_button)

    def click_on_cancel_button(self):
        self._click(self.cancel_button)
