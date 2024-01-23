from playwright.sync_api import Page, Locator
from playwright_tests.core.basepage import BasePage


class KBArticleDiscussionPage(BasePage):
    # Post a new thread locator.
    __post_a_new_thread_option = "//a[@id='new-thread']"

    # New Thread related locators.
    __new_thread_title_input_field = "//input[@id='id_title']"
    __new_thread_body_input_field = "//textarea[@id='id_content']"
    __new_thread_submit_button = "//button[text()='Post Thread']"

    # Thread content locators.
    __thread_body_content = "//div[@class='content']/p"
    __thread_post_a_reply_textarea_field = "//textarea[@id='id_content']"

    def __init__(self, page: Page):
        super().__init__(page)

    # Post a new thread button action.
    def _click_on_post_a_new_thread_option(self):
        super()._click(self.__post_a_new_thread_option)

    # Actions related to posting a new thread.
    def _add_text_to_new_thread_title_field(self, text: str):
        super()._fill(self.__new_thread_title_input_field, text)

    def _add_text_to_new_thread_body_input_field(self, text: str):
        super()._fill(self.__new_thread_body_input_field, text)

    def _click_on_submit_new_thread_button(self):
        super()._click(self.__new_thread_submit_button)

    def _get_posted_thread_locator(self, thread_id: str) -> Locator:
        xpath = f"//tr[@class='threads']/td[@class='title']//a[contains(@href, '{thread_id}')]"
        return super()._get_element_locator(xpath)

    def _click_on_a_particular_thread(self, thread_id: str):
        xpath = f"//tr[@class='threads']/td[@class='title']//a[contains(@href, '{thread_id}')]"
        super()._click(xpath)

    # Actions related to thread content
    def _get_post_a_reply_textarea_field(self) -> Locator:
        return super()._get_element_locator(self.__thread_post_a_reply_textarea_field)
