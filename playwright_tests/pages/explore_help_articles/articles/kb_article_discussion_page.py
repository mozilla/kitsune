import re

from playwright.sync_api import Locator, Page

from playwright_tests.core.basepage import BasePage


class KBArticleDiscussionPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        # Filters locators
        self.article_thread_author_filter = page.locator("th[class*='author'] a")
        self.article_thread_replies_filter = page.locator("th[class*='replies'] a")

        # Post a new thread locator.
        self.post_a_new_thread_option = page.locator("a#new-thread")

        # New Thread related locators.
        self.new_thread_title_input_field = page.locator("input#id_title")
        self.new_thread_body_input_field = page.locator("textarea#id_content")
        self.new_thread_submit_button = page.get_by_role("button", name="Post Thread", exact=True)
        self.new_thread_cancel_button = page.get_by_role("link", name="Cancel", exact=True)

        # Thread Editing tools
        self.delete_thread = page.get_by_role("link", name="Delete this thread", exact=True)
        self.lock_this_thread = page.locator("a[data-form='thread-lock-form']")
        self.sticky_this_thread = page.locator("a[data-form='thread-sticky-form']")

        # Thread content locators.
        self.article_thread_edit_this_thread = page.get_by_role(
            "link", name="Edit this thread", exact=True)
        self.article_thread_sticky_status = page.locator(
            "//ul[@id='thread-meta']/li[text()='Sticky']")
        self.posted_thread = lambda thread_id: page.locator(
            f"tr[class='threads'] td[class='title'] a[href*='{thread_id}']")
        self.thread_by_title = lambda thread_title: page.locator(
            "tr[class='threads'] td[class='title']").get_by_role(
            "link", name=thread_title, exact=True)

        self.article_thread_locked_status = page.locator(
            "//ul[@id='thread-meta']/li[text()='Locked']")
        self.thread_body_content = page.locator("div[class='content'] p")
        self.thread_body_content_title = page.locator("h1[class='sumo-page-heading']")

        # Thread replies locators.
        self.delete_thread_reply_confirmation_page_button = page.locator("input[value='Delete']")
        self.thread_post_a_reply_textarea_field = page.locator("textarea#id_content")
        self.article_thread_locked_message = page.locator("p#thread-locked")
        self.thread_page_replies_counter = page.locator("//ul[@id='thread-meta']/li[1]")
        self.thread_page_last_reply_by_text = page.locator("//ul[@id='thread-meta']/li[2]")
        self.thread_post_a_new_reply_button = page.get_by_role(
            "button", name="Post Reply", exact=True)
        self.dotted_menu_for_thread = lambda thread_id: page.locator(
            f"li#{thread_id} span[class='icon-button is-summary'] button")
        self.edit_this_thread = lambda thread_id: page.locator(
            f"li#{thread_id} div[class='mzp-c-menu-list is-details']").get_by_role(
            "link", name="Edit this post", exact=True)
        self.delete_this_thread = lambda thread_id: page.locator(
            f"li#{thread_id} div[class='mzp-c-menu-list is-details']").get_by_role(
            "link", name="Delete this post", exact=True)

        # Article discussions content locators.
        self.all_article_threads_titles = page.locator("td[class='title'] a")
        self.all_article_threads_authors = page.locator("td[class='author'] a")
        self.all_article_thread_replies = page.locator("td[class='replies']")
        self.discussions_thread_counter = lambda thread_id: page.locator(
            f"//tr[@class='threads']/td[@class='title']//a[contains(@href, '{thread_id}')]/../"
            f"following-sibling::td[@class='replies']")

        # Edit thread page
        self.edit_article_thread_title_field = page.locator("input#id_title")
        self.edit_article_thread_cancel_button = page.get_by_role(
            "link", name="Cancel", exact=True)
        self.edit_article_thread_update_thread_button = page.get_by_role(
            "button", name="Update thread", exact=True)

    # Edit thread page actions
    def get_edit_this_thread_locator(self) -> Locator:
        return self.article_thread_edit_this_thread

    def click_on_edit_this_thread_option(self):
        self._click(self.article_thread_edit_this_thread)

    def add_text_to_edit_article_thread_title_field(self, text: str):
        self._clear_field(self.edit_article_thread_title_field)
        self._fill(self.edit_article_thread_title_field, text)

    def click_on_edit_article_thread_cancel_button(self):
        self._click(self.edit_article_thread_cancel_button)

    def click_on_edit_article_thread_update_button(self):
        self._click(self.edit_article_thread_update_thread_button)

    # Filter actions.
    def click_on_article_thread_author_replies_filter(self):
        self._click(self.article_thread_author_filter)

    def click_on_article_thread_replies_filter(self):
        self._click(self.article_thread_replies_filter)

    # Post a new thread button action.
    def click_on_post_a_new_thread_option(self):
        self._click(self.post_a_new_thread_option)

    def click_on_thread_post_reply_button(self):
        self._click(self.thread_post_a_new_reply_button)

    def get_thread_reply_id(self, url: str) -> str:
        return re.search(r'post-(\d+)', url).group(0)

    # Actions related to posting a new thread.
    def add_text_to_new_thread_title_field(self, text: str):
        self._fill(self.new_thread_title_input_field, text)

    def clear_new_thread_title_field(self):
        self._clear_field(self.new_thread_title_input_field)

    def add_text_to_new_thread_body_input_field(self, text: str):
        self._fill(self.new_thread_body_input_field, text)

    def clear_new_thread_body_field(self):
        self._clear_field(self.new_thread_body_input_field)

    def click_on_cancel_new_thread_button(self):
        self._click(self.new_thread_cancel_button)

    def click_on_submit_new_thread_button(self):
        self._click(self.new_thread_submit_button)

    def get_posted_thread_locator(self, thread_id: str) -> Locator:
        return self.posted_thread(thread_id)

    def get_thread_by_title_locator(self, thread_title: str) -> Locator:
        return self.thread_by_title(thread_title)

    def click_on_a_particular_thread(self, thread_id: str):
        self._click(self.posted_thread(thread_id))

    # Actions related to thread content
    def get_thread_title_text(self) -> str:
        return self._get_text_of_element(self.thread_body_content_title)

    def get_locked_article_status(self) -> Locator:
        return self.article_thread_locked_status

    def get_lock_this_article_thread_option_text(self) -> str:
        return self._get_text_of_element(self.lock_this_thread)

    def get_lock_this_article_thread_locator(self) -> Locator:
        return self.lock_this_thread

    def click_on_lock_this_article_thread_option(self):
        self._click(self.lock_this_thread)

    def get_sticky_this_thread_locator(self) -> Locator:
        return self.sticky_this_thread

    def get_text_of_sticky_this_thread_option(self) -> str:
        return self._get_text_of_element(self.sticky_this_thread)

    def get_sticky_this_thread_status_locator(self) -> Locator:
        return self.article_thread_sticky_status

    def click_on_sticky_this_thread_option(self):
        self._click(self.sticky_this_thread)

    def get_thread_post_a_reply_textarea_field(self) -> Locator:
        return self.thread_post_a_reply_textarea_field

    def fill_the_thread_post_a_reply_textarea(self, text: str):
        self._fill(self.thread_post_a_reply_textarea_field, text)

    def get_thread_page_counter_replies_text(self) -> str:
        return self._get_text_of_element(self.thread_page_replies_counter)

    def get_thread_page_replied_by_text(self) -> str:
        return self._get_text_of_element(self.thread_page_last_reply_by_text)

    # Article discussions page content actions
    def get_article_discussions_thread_counter(self, thread_id: str) -> str:
        return self._get_text_of_element(self.discussions_thread_counter(thread_id))

    def get_all_article_threads_titles(self) -> list[str]:
        return self._get_text_of_elements(self.all_article_threads_titles)

    def get_all_article_threads_authors(self) -> list[str]:
        return self._get_text_of_elements(self.all_article_threads_authors)

    def get_all_article_threads_replies(self) -> list[str]:
        return self._get_text_of_elements(self.all_article_thread_replies)

    def get_text_of_locked_article_thread_text(self) -> str:
        return self._get_text_of_element(self.article_thread_locked_message)

    def get_text_of_locked_article_thread_locator(self) -> Locator:
        return self.article_thread_locked_message

    # Actions related to thread replies.
    def click_on_dotted_menu_for_a_certain_reply(self, thread_id: str):
        self._click(self.dotted_menu_for_thread(thread_id))

    def click_on_delete_this_thread_option(self):
        self._click(self.delete_thread)

    def click_on_edit_this_thread_reply(self, thread_id: str):
        self._click(self.edit_this_thread(thread_id))

    def click_on_delete_this_thread_reply(self, thread_id: str):
        self._click(self.delete_this_thread(thread_id))

    def click_on_delete_this_thread_reply_confirmation_button(self):
        self._click(self.delete_thread_reply_confirmation_page_button)
