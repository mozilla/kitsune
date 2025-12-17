from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class MyProfileEditSettingsPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """Locators belonging to the edit profile settings page."""
        self.edit_settings_page_header = page.locator("h3[class='sumo-page-heading']")
        self.edit_settings_checkbox_options_label = page.locator(
            "div[class='field checkbox'] label")
        self.watch_forum_threads_I_start_checkbox = page.locator(
            "//input[@id='id_forums_watch_new_thread']/following-sibling::label")
        self.watch_forum_threads_I_comment_in_checkbox = page.locator(
            "//input[@id='id_forums_watch_after_reply']/following-sibling::label")
        self.watch_kb_discussions_threads_I_start_checkbox = page.locator(
            "//input[@id='id_kbforums_watch_new_thread']/following-sibling::label")
        self.watch_kb_discussion_threads_I_comment_in_checkbox = page.locator(
            "//input[@id='id_kbforums_watch_after_reply']/following-sibling::label")
        self.watch_question_threads_I_comment_in_checkbox = page.locator(
            "//input[@id='id_questions_watch_after_reply']/following-sibling::label")
        self.send_emails_for_private_messages_checkbox = page.locator(
            "//input[@id='id_email_private_messages']/following-sibling::label")
        self.edit_settings_update_button = page.locator(
            "article#edit-settings form button[type='submit']")
        self.your_settings_have_been_saved_notification_banner = page.locator(
            "ul[class='user-messages'] li")
        self.your_settings_have_been_saved_notification_banner_text = page.locator(
            "ul[class='user-messages'] li p")
        self.your_settings_have_been_saved_notification_banner_close_button = page.locator(
            "ul[class='user-messages'] button")
        self.my_profile_user_navbar = page.locator("ul#user-nav li")
        self.my_profile_user_navbar_selected_element = page.locator("a[class='selected']")

    """Actions against the edit profile settings page locators."""
    def get_edit_settings_page_header(self) -> str:
        """Get edit settings page header text"""
        return self._get_text_of_element(self.edit_settings_page_header)

    def get_text_of_checkbox_options(self) -> list[str]:
        """Get text of all checkbox options"""
        return self._get_text_of_elements(self.edit_settings_checkbox_options_label)

    def settings_saved_notif_banner_txt(self) -> str:
        """Get text of the settings saved notification banner"""
        return self._get_text_of_element(
            self.your_settings_have_been_saved_notification_banner_text)

    def click_settings_saved_notification_banner(self):
        self._click(self.your_settings_have_been_saved_notification_banner_close_button)

    def click_on_all_settings_checkboxes(self):
        """Click on all settings checkboxes"""
        for checkbox in self._get_element_handles(self.edit_settings_checkbox_options_label):
            checkbox.click()

    def click_on_watch_forum_threads_i_start_checkbox(self):
        """Click on watch forum threads I start checkbox"""
        self._click(self.watch_forum_threads_I_start_checkbox)

    def click_on_watch_forum_threads_i_comment_in_checkbox(self):
        """Click on watch forum threads I comment in checkbox"""
        self._click(self.watch_forum_threads_I_comment_in_checkbox)

    def click_on_watch_kb_discussions_threads_i_start_checkbox(self):
        """Click on watch kb discussions threads I start checkbox"""
        self._click(self.watch_kb_discussions_threads_I_start_checkbox)

    def click_on_watch_kb_discussions_threads_i_comment_checkbox(self):
        """Click on watch kb discussions threads I comment in checkbox"""
        self._click(self.watch_kb_discussion_threads_I_comment_in_checkbox)

    def click_on_watch_question_threads_i_comment(self):
        """Click on watch question threads I comment in checkbox"""
        self._click(self.watch_question_threads_I_comment_in_checkbox)

    def click_on_send_emails_for_private_messages(self):
        """Click on send emails for private messages checkbox"""
        self._click(self.send_emails_for_private_messages_checkbox)

    def click_on_update_button(self):
        """Click on update button"""
        self._click(self.edit_settings_update_button)

    def is_watch_forum_threads_i_start_checkbox_checked(self) -> bool:
        """Check if watch forum threads I start checkbox is checked"""
        return self._is_checkbox_checked(self.watch_forum_threads_I_start_checkbox)

    def is_watch_forum_threads_i_comment_checkbox_checked(self) -> bool:
        """Check if watch forum threads I comment in checkbox is checked"""
        return self._is_checkbox_checked(self.watch_forum_threads_I_comment_in_checkbox)

    def is_watch_kb_discussion_threads_i_start_checkbox_checked(self) -> bool:
        """Check if watch kb discussion threads I start checkbox is checked"""
        return self._is_checkbox_checked(self.watch_kb_discussions_threads_I_start_checkbox)

    def is_watch_kb_discussion_threads_i_comment_checkbox_checked(self) -> bool:
        """Check if watch kb discussion threads I comment in checkbox is checked"""
        return self._is_checkbox_checked(self.watch_kb_discussion_threads_I_comment_in_checkbox)

    def is_watch_question_threads_i_comment_checkbox_checked(self) -> bool:
        """Check if watch question threads I comment in checkbox is checked"""
        return self._is_checkbox_checked(self.watch_question_threads_I_comment_in_checkbox)

    def is_send_emails_for_private_messages_checkbox_checked(self) -> bool:
        """Check if send emails for private messages checkbox is checked"""
        return self._is_checkbox_checked(self.send_emails_for_private_messages_checkbox)

    def are_all_checkbox_checked(self) -> bool:
        """Check if all checkboxes are checked"""
        return all([
            self.is_watch_forum_threads_i_start_checkbox_checked(),
            self.is_watch_forum_threads_i_comment_checkbox_checked(),
            self.is_watch_kb_discussion_threads_i_start_checkbox_checked(),
            self.is_watch_kb_discussion_threads_i_comment_checkbox_checked(),
            self.is_watch_question_threads_i_comment_checkbox_checked(),
            self.is_send_emails_for_private_messages_checkbox_checked(),
        ])
