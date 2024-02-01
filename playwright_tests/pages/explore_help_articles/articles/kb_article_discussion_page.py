from playwright.sync_api import Page, Locator
from playwright_tests.core.basepage import BasePage
import re


class KBArticleDiscussionPage(BasePage):
    # Filters locators
    __article_thread_author_filter = "//th[contains(@class,'author')]/a"
    __article_thread_replies_filter = "//th[contains(@class,'replies')]/a"

    # Post a new thread locator.
    __post_a_new_thread_option = "//a[@id='new-thread']"

    # New Thread related locators.
    __new_thread_title_input_field = "//input[@id='id_title']"
    __new_thread_body_input_field = "//textarea[@id='id_content']"
    __new_thread_submit_button = "//button[text()='Post Thread']"
    __new_thread_cancel_button = "//a[text()='Cancel']"

    # Thread Editing tools
    __delete_thread = "//a[text()='Delete this thread']"
    __lock_this_thread = "//a[@data-form='thread-lock-form']"
    __sticky_this_thread = "//a[@data-form='thread-sticky-form']"

    # Thread content locators.
    __article_thread_edit_this_thread = "//a[text()='Edit this thread']"
    __article_thread_sticky_status = "//ul[@id='thread-meta']/li[text()='Sticky']"
    __article_thread_locked_status = "//ul[@id='thread-meta']/li[text()='Locked']"
    __thread_body_content = "//div[@class='content']/p"
    __thread_body_content_title = "//h1[@class='sumo-page-heading']"

    # Thread replies locators.
    __delete_thread_reply_confirmation_page_button = "//input[@value='Delete']"
    __thread_post_a_reply_textarea_field = "//textarea[@id='id_content']"
    __article_thread_locked_message = "//p[@id='thread-locked']"
    __thread_page_replies_counter = "//ul[@id='thread-meta']/li[1]"
    __thread_page_last_reply_by_text = "//ul[@id='thread-meta']/li[2]"
    __thread_post_a_new_reply_button = "//button[text()='Post Reply']"

    # Article discussions content locators.
    __all_article_threads_titles = "//td[@class='title']/a"
    __all_article_threads_authors = "//td[@class='author']"
    __all_article_thread_replies = "//td[@class='replies']"

    # Edit thread page
    __edit_article_thread_title_field = "//input[@id='id_title']"
    __edit_article_thread_cancel_button = "//a[text()='Cancel']"
    __edit_article_thread_update_thread_button = "//button[text()='Update thread']"

    def __init__(self, page: Page):
        super().__init__(page)

    # Edit thread page actions
    def _get_edit_this_thread_locator(self) -> Locator:
        return super()._get_element_locator(self.__article_thread_edit_this_thread)

    def _click_on_edit_this_thread_option(self):
        super()._click(self.__article_thread_edit_this_thread)

    def _add_text_to_edit_article_thread_title_field(self, text: str):
        super()._clear_field(self.__edit_article_thread_title_field)
        super()._fill(self.__edit_article_thread_title_field, text)

    def _click_on_edit_article_thread_cancel_button(self):
        super()._click(self.__edit_article_thread_cancel_button)

    def _click_on_edit_article_thread_update_button(self):
        super()._click(self.__edit_article_thread_update_thread_button)

    # Filter actions.
    def _click_on_article_thread_author_replies_filter(self):
        super()._click(self.__article_thread_author_filter)

    def _click_on_article_thread_replies_filter(self):
        super()._click(self.__article_thread_replies_filter)

    # Post a new thread button action.
    def _click_on_post_a_new_thread_option(self):
        super()._click(self.__post_a_new_thread_option)

    def _click_on_thread_post_reply_button(self):
        super()._click(self.__thread_post_a_new_reply_button)

    def _get_thread_reply_id(self, url: str) -> str:
        return re.search(r'post-(\d+)', url).group(0)

    # Actions related to posting a new thread.
    def _add_text_to_new_thread_title_field(self, text: str):
        super()._fill(self.__new_thread_title_input_field, text)

    def _clear_new_thread_title_field(self):
        super()._clear_field(self.__new_thread_title_input_field)

    def _add_text_to_new_thread_body_input_field(self, text: str):
        super()._fill(self.__new_thread_body_input_field, text)

    def _clear_new_thread_body_field(self):
        super()._clear_field(self.__new_thread_body_input_field)

    def _click_on_cancel_new_thread_button(self):
        super()._click(self.__new_thread_cancel_button)

    def _click_on_submit_new_thread_button(self):
        super()._click(self.__new_thread_submit_button)

    def _get_posted_thread_locator(self, thread_id: str) -> Locator:
        xpath = f"//tr[@class='threads']/td[@class='title']//a[contains(@href, '{thread_id}')]"
        return super()._get_element_locator(xpath)

    def _get_thread_by_title_locator(self, thread_title: str) -> Locator:
        xpath = f"//tr[@class='threads']/td[@class='title']/a[text()='{thread_title}']"
        return super()._get_element_locator(xpath)

    def _click_on_a_particular_thread(self, thread_id: str):
        xpath = f"//tr[@class='threads']/td[@class='title']//a[contains(@href, '{thread_id}')]"
        super()._click(xpath)

    # Actions related to thread content
    def _get_thread_title_text(self) -> str:
        return super()._get_text_of_element(self.__thread_body_content_title)

    def _get_locked_article_status(self) -> Locator:
        return super()._get_element_locator(self.__article_thread_locked_status)

    def _get_lock_this_article_thread_option_text(self) -> str:
        return super()._get_text_of_element(self.__lock_this_thread)

    def _get_lock_this_article_thread_locator(self) -> Locator:
        return super()._get_element_locator(self.__lock_this_thread)

    def _click_on_lock_this_article_thread_option(self):
        super()._click(self.__lock_this_thread)

    def _get_sticky_this_thread_locator(self) -> Locator:
        return super()._get_element_locator(self.__sticky_this_thread)

    def _get_text_of_sticky_this_thread_option(self) -> str:
        return super()._get_text_of_element(self.__sticky_this_thread)

    def _get_sticky_this_thread_status_locator(self) -> Locator:
        return super()._get_element_locator(self.__article_thread_sticky_status)

    def _click_on_sticky_this_thread_option(self):
        super()._click(self.__sticky_this_thread)

    def _get_thread_post_a_reply_textarea_field(self) -> Locator:
        return super()._get_element_locator(self.__thread_post_a_reply_textarea_field)

    def _fill_the_thread_post_a_reply_textarea_field(self, text: str):
        super()._fill(self.__thread_post_a_reply_textarea_field, text)

    def _get_thread_page_counter_replies_text(self) -> str:
        return super()._get_text_of_element(self.__thread_page_replies_counter)

    def _get_thread_page_replied_by_text(self) -> str:
        return super()._get_text_of_element(self.__thread_page_last_reply_by_text)

    # Article discussions page content actions
    def _get_article_discussions_thread_counter(self, thread_id: str) -> str:
        xpath = (f"//tr[@class='threads']/td[@class='title']//a[contains(@href, "
                 f"'{thread_id}')]/../following-sibling::td[@class='replies']")
        return super()._get_text_of_element(xpath)

    def _get_all_article_threads_titles(self) -> list[str]:
        return super()._get_text_of_elements(self.__all_article_threads_titles)

    def _get_all_article_threads_authors(self) -> list[str]:
        return super()._get_text_of_elements(self.__all_article_threads_authors)

    def _get_all_article_threads_replies(self) -> list[str]:
        return super()._get_text_of_elements(self.__all_article_thread_replies)

    def _get_text_of_locked_article_thread_text(self) -> str:
        return super()._get_text_of_element(self.__article_thread_locked_message)

    def _get_text_of_locked_article_thread_locator(self) -> Locator:
        return super()._get_element_locator(self.__article_thread_locked_message)

    # Actions related to thread replies.
    def _click_on_dotted_menu_for_a_certain_reply(self, thread_id: str):
        xpath = f"//li[@id='{thread_id}']//span[@class='icon-button is-summary']//button"
        super()._click(xpath)

    def _click_on_delete_this_thread_option(self):
        super()._click(self.__delete_thread)

    def _click_on_edit_this_thread_reply(self, thread_id: str):
        xpath = (f"//li[@id='{thread_id}']//div[@class='mzp-c-menu-list is-details']//a[text("
                 ")='Edit this post']")
        super()._click(xpath)

    def _click_on_delete_this_thread_reply(self, thread_id: str):
        xpath = (f"//li[@id='{thread_id}']//div[@class='mzp-c-menu-list is-details']//a[text("
                 ")='Delete this post']")
        super()._click(xpath)

    def _click_on_delete_this_thread_reply_confirmation_button(self):
        super()._click(self.__delete_thread_reply_confirmation_page_button)
