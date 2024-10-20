from playwright.sync_api import Page, Locator
from playwright_tests.core.basepage import BasePage


class MyProfileEditSettingsPage(BasePage):
    # My profile edit settings page locators.
    PROFILE_EDIT_SETTINGS_LOCATORS = {
        "edit_settings_page_header": "//h3[@class='sumo-page-heading']",
        "edit_settings_checkbox_options_label": "//div[@class='field checkbox']/label",
        "watch_forum_threads_I_start_checkbox": "//input[@id='id_forums_watch_new_thread']/"
                                                "following-sibling::label",
        "watch_forum_threads_I_comment_in_checkbox": "//input[@id='id_forums_watch_after_reply']"
                                                     "/following-sibling::label",
        "watch_kb_discussions_threads_I_start_checkbox": "//input[@id='id_kbforums_watch_new_"
                                                         "thread']/following-sibling::label",
        "watch_kb_discussion_threads_I_comment_in_checkbox": "//input[@id='id_kbforums_watch_after"
                                                             "_reply']/following-sibling::label",
        "watch_question_threads_I_comment_in_checkbox": "//input[@id='id_questions_watch_after_"
                                                        "reply']/following-sibling::label",
        "send_emails_for_private_messages_checkbox": "//input[@id='id_email_private_messages']/"
                                                     "following-sibling::label",
        "edit_settings_update_button": "//article[@id='edit-settings']/form//button[@type='"
                                       "submit']",
        "your_settings_have_been_saved_notification_banner": "//ul[@class='user-messages']//li",
        "your_settings_have_been_saved_notification_banner_text": "//ul[@class='user-messages']//"
                                                                  "li/p",
        "your_settings_have_been_saved_notification_banner_close_button": "//ul[@class='user-"
                                                                          "messages']//button",
        "my_profile_user_navbar": "//ul[@id='user-nav']/li",
        "my_profile_user_navbar_selected_element": "//a[@class='selected']"
    }

    def __init__(self, page: Page):
        super().__init__(page)

    # My profile edit settings page actions.
    def get_edit_settings_page_header(self) -> str:
        """Get edit settings page header text"""
        return self._get_text_of_element(self.PROFILE_EDIT_SETTINGS_LOCATORS["edit_settings_page_"
                                                                             "header"])

    def get_text_of_checkbox_options(self) -> list[str]:
        """Get text of all checkbox options"""
        return self._get_text_of_elements(
            self.PROFILE_EDIT_SETTINGS_LOCATORS["edit_settings_checkbox_options_label"])

    def settings_saved_notif_banner_txt(self) -> str:
        """Get text of the settings saved notification banner"""
        return self._get_text_of_element(
            self.PROFILE_EDIT_SETTINGS_LOCATORS["your_settings_have_been_saved_notification_"
                                                "banner_text"])

    def click_settings_saved_notification_banner(self):
        self._click(self.PROFILE_EDIT_SETTINGS_LOCATORS["your_settings_have_been_saved_"
                                                        "notification_banner_close_button"])

    def click_on_all_settings_checkboxes(self):
        """Click on all settings checkboxes"""
        for checkbox in self._get_element_handles(
                self.PROFILE_EDIT_SETTINGS_LOCATORS["edit_settings_checkbox_options_label"]):
            checkbox.click()

    def click_on_watch_forum_threads_i_start_checkbox(self):
        """Click on watch forum threads I start checkbox"""
        self._click(self.PROFILE_EDIT_SETTINGS_LOCATORS["watch_forum_threads_I_start_checkbox"])

    def click_on_watch_forum_threads_i_comment_in_checkbox(self):
        """Click on watch forum threads I comment in checkbox"""
        self._click(self.PROFILE_EDIT_SETTINGS_LOCATORS["watch_forum_threads_I_comment_in_"
                                                        "checkbox"])

    def click_on_watch_kb_discussions_threads_i_start_checkbox(self):
        """Click on watch kb discussions threads I start checkbox"""
        self._click(self.PROFILE_EDIT_SETTINGS_LOCATORS["watch_kb_discussions_threads_I_start_"
                                                        "checkbox"])

    def click_on_watch_kb_discussions_threads_i_comment_checkbox(self):
        """Click on watch kb discussions threads I comment in checkbox"""
        self._click(self.PROFILE_EDIT_SETTINGS_LOCATORS["watch_kb_discussion_threads_I_comment_"
                                                        "in_checkbox"])

    def click_on_watch_question_threads_i_comment(self):
        """Click on watch question threads I comment in checkbox"""
        self._click(self.PROFILE_EDIT_SETTINGS_LOCATORS["watch_question_threads_I_comment_in_"
                                                        "checkbox"])

    def click_on_send_emails_for_private_messages(self):
        """Click on send emails for private messages checkbox"""
        self._click(self.PROFILE_EDIT_SETTINGS_LOCATORS["send_emails_for_private_messages_"
                                                        "checkbox"])

    def click_on_update_button(self):
        """Click on update button"""
        self._click(self.PROFILE_EDIT_SETTINGS_LOCATORS["edit_settings_update_button"])

    def is_watch_forum_threads_i_start_checkbox_checked(self) -> bool:
        """Check if watch forum threads I start checkbox is checked"""
        return self._is_checkbox_checked(self.PROFILE_EDIT_SETTINGS_LOCATORS["watch_forum_threads_"
                                                                             "I_start_checkbox"])

    def is_watch_forum_threads_i_comment_checkbox_checked(self) -> bool:
        """Check if watch forum threads I comment in checkbox is checked"""
        return self._is_checkbox_checked(
            self.PROFILE_EDIT_SETTINGS_LOCATORS["watch_forum_threads_I_comment_in_checkbox"])

    def is_watch_kb_discussion_threads_i_start_checkbox_checked(self) -> bool:
        """Check if watch kb discussion threads I start checkbox is checked"""
        return self._is_checkbox_checked(
            self.PROFILE_EDIT_SETTINGS_LOCATORS["watch_kb_discussions_threads_I_start_checkbox"])

    def is_watch_kb_discussion_threads_i_comment_checkbox_checked(self) -> bool:
        """Check if watch kb discussion threads I comment in checkbox is checked"""
        return self._is_checkbox_checked(
            self.PROFILE_EDIT_SETTINGS_LOCATORS["watch_kb_discussion_threads_I_comment_in_"
                                                "checkbox"])

    def is_watch_question_threads_i_comment_checkbox_checked(self) -> bool:
        """Check if watch question threads I comment in checkbox is checked"""
        return self._is_checkbox_checked(
            self.PROFILE_EDIT_SETTINGS_LOCATORS["watch_question_threads_I_comment_in_checkbox"])

    def is_send_emails_for_private_messages_checkbox_checked(self) -> bool:
        """Check if send emails for private messages checkbox is checked"""
        return self._is_checkbox_checked(
            self.PROFILE_EDIT_SETTINGS_LOCATORS["send_emails_for_private_messages_checkbox"])

    def notification_banner_element(self) -> Locator:
        """Get the notification banner element"""
        return self._get_element_locator(
            self.PROFILE_EDIT_SETTINGS_LOCATORS["your_settings_have_been_saved_notification_"
                                                "banner"])

    def are_all_checkbox_checked(self) -> bool:
        """Check if all checkboxes are checked"""
        print([
            self.is_watch_forum_threads_i_start_checkbox_checked(),
            self.is_watch_forum_threads_i_comment_checkbox_checked(),
            self.is_watch_kb_discussion_threads_i_start_checkbox_checked(),
            self.is_watch_kb_discussion_threads_i_comment_checkbox_checked(),
            self.is_watch_question_threads_i_comment_checkbox_checked(),
            self.is_send_emails_for_private_messages_checkbox_checked(),
        ])
        return all([
            self.is_watch_forum_threads_i_start_checkbox_checked(),
            self.is_watch_forum_threads_i_comment_checkbox_checked(),
            self.is_watch_kb_discussion_threads_i_start_checkbox_checked(),
            self.is_watch_kb_discussion_threads_i_comment_checkbox_checked(),
            self.is_watch_question_threads_i_comment_checkbox_checked(),
            self.is_send_emails_for_private_messages_checkbox_checked(),
        ])
