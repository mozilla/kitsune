from playwright.sync_api import Page, Locator
from playwright_tests.core.basepage import BasePage


class MyProfileEditSettingsPage(BasePage):

    # My profile edit settings page locators.
    __edit_settings_page_header = "//h3[@class='sumo-page-heading']"
    __edit_settings_checkbox_options_label = "//div[@class='field checkbox']/label"
    __watch_forum_threads_I_start_checkbox = ("//input[@id='id_forums_watch_new_thread"
                                              "']/following-sibling::label")
    __watch_forum_threads_I_comment_in_checkbox = ("//input[@id='id_forums_watch_after_reply"
                                                   "']/following-sibling::label")
    __watch_kb_discussions_threads_I_start_checkbox = (
        "//input[@id='id_kbforums_watch_new_thread']/following-sibling::label")
    __watch_kb_discussion_threads_I_comment_in_checkbox = (
        "//input[@id='id_kbforums_watch_after_reply']/following-sibling::label")
    __watch_question_threads_I_comment_in_checkbox = (
        "//input[@id='id_questions_watch_after_reply']/following-sibling::label")
    __send_emails_for_private_messages_checkbox = ("//input[@id='id_email_private_messages"
                                                   "']/following-sibling::label")
    __edit_settings_update_button = "//article[@id='edit-settings']/form//button[@type='submit']"
    __your_settings_have_been_saved_notification_banner = "//ul[@class='user-messages']//li"
    __your_settings_have_been_saved_notification_banner_text = "//ul[@class='user-messages']//li/p"
    __your_settings_have_been_saved_notification_banner_close_button = ("//ul[@class='user"
                                                                        "-messages']//button")
    __my_profile_user_navbar = "//ul[@id='user-nav']/li"
    __my_profile_user_navbar_selected_element = "//a[@class='selected']"

    def __init__(self, page: Page):
        super().__init__(page)

    # My profile edit settings page actions.
    def _get_edit_settings_page_header(self) -> str:
        return super()._get_text_of_element(self.__edit_settings_page_header)

    def _get_text_of_checkbox_options(self) -> list[str]:
        return super()._get_text_of_elements(self.__edit_settings_checkbox_options_label)

    def _settings_saved_notif_banner_txt(self) -> str:
        return super()._get_text_of_element(
            self.__your_settings_have_been_saved_notification_banner_text)

    def _click_settings_saved_notification_banner(self):
        super()._click(self.__your_settings_have_been_saved_notification_banner_close_button)

    def _click_on_all_settings_checkboxes(self):
        for checkbox in super()._get_element_handles(self.__edit_settings_checkbox_options_label):
            checkbox.click()

    def _click_on_watch_forum_threads_i_start_checkbox(self):
        super()._click(self.__watch_forum_threads_I_start_checkbox)

    def _click_on_watch_forum_threads_i_comment_in_checkbox(self):
        super()._click(self.__watch_forum_threads_I_comment_in_checkbox)

    def _click_on_watch_kb_discussions_threads_i_start_checkbox(self):
        super()._click(self.__watch_kb_discussions_threads_I_start_checkbox)

    def _click_on_watch_kb_discussions_threads_i_comment_checkbox(self):
        super()._click(self.__watch_kb_discussion_threads_I_comment_in_checkbox)

    def _click_on_watch_question_threads_i_comment(self):
        super()._click(self.__watch_question_threads_I_comment_in_checkbox)

    def _click_on_send_emails_for_private_messages(self):
        super()._click(self.__send_emails_for_private_messages_checkbox)

    def _click_on_update_button(self):
        super()._click(self.__edit_settings_update_button)

    def _is_watch_forum_threads_i_start_checkbox_checked(self) -> bool:
        return super()._is_checkbox_checked(self.__watch_forum_threads_I_start_checkbox)

        # checkbox_background_color = super()._get_css_value_of_pseudo_html_element(
        #     "label[" 'for="id_forums_watch_new_thread"]', ":before", "background-color"
        # )
        # if checkbox_background_color == EditSettingsPageMessages.CHECKBOX_CHECKED_COLOR:
        #     return True
        # else:
        #     return False

    def _is_watch_forum_threads_i_comment_checkbox_checked(self) -> bool:
        return super()._is_checkbox_checked(self.__watch_forum_threads_I_comment_in_checkbox)

        # checkbox_background_color = super()._get_css_value_of_pseudo_html_element(
        #     "label[" 'for="id_forums_watch_after_reply"]', ":before", "background-color"
        # )
        # if checkbox_background_color == EditSettingsPageMessages.CHECKBOX_CHECKED_COLOR:
        #     return True
        # else:
        #     return False

    def _is_watch_kb_discussion_threads_i_start_checkbox_checked(self) -> bool:
        return super()._is_checkbox_checked(self.__watch_kb_discussions_threads_I_start_checkbox)
        # checkbox_background_color = super()._get_css_value_of_pseudo_html_element(
        #     "label[" 'for="id_kbforums_watch_new_thread"]', ":before", "background-color"
        # )
        # if checkbox_background_color == EditSettingsPageMessages.CHECKBOX_CHECKED_COLOR:
        #     return True
        # else:
        #     return False

    def _is_watch_kb_discussion_threads_i_comment_checkbox_checked(self) -> bool:
        return super()._is_checkbox_checked(
            self.__watch_kb_discussion_threads_I_comment_in_checkbox)
        # checkbox_background_color = super()._get_css_value_of_pseudo_html_element(
        #     "label[" 'for="id_kbforums_watch_after_reply"]', ":before", "background-color"
        # )
        # if checkbox_background_color == EditSettingsPageMessages.CHECKBOX_CHECKED_COLOR:
        #     return True
        # else:
        #     return False

    def _is_watch_question_threads_i_comment_checkbox_checked(self) -> bool:
        return super()._is_checkbox_checked(self.__watch_question_threads_I_comment_in_checkbox)
        # checkbox_background_color = super()._get_css_value_of_pseudo_html_element(
        #     "label[" 'for="id_questions_watch_after_reply"]', ":before", "background-color"
        # )
        # if checkbox_background_color == EditSettingsPageMessages.CHECKBOX_CHECKED_COLOR:
        #     return True
        # else:
        #     return False

    def _is_send_emails_for_private_messages_checkbox_checked(self) -> bool:
        return super()._is_checkbox_checked(self.__send_emails_for_private_messages_checkbox)
        # checkbox_background_color = super()._get_css_value_of_pseudo_html_element(
        #     "label[" 'for="id_email_private_messages"]', ":before", "background-color"
        # )
        # if checkbox_background_color == EditSettingsPageMessages.CHECKBOX_CHECKED_COLOR:
        #     return True
        # else:
        #     return False

    def _notification_banner_element(self) -> Locator:
        return super()._get_element_locator(
            self.__your_settings_have_been_saved_notification_banner)

    def _are_all_checkbox_checked(self) -> bool:
        is_checked = [
            self._is_watch_forum_threads_i_start_checkbox_checked(),
            self._is_watch_forum_threads_i_comment_checkbox_checked(),
            self._is_watch_kb_discussion_threads_i_start_checkbox_checked(),
            self._is_watch_kb_discussion_threads_i_comment_checkbox_checked(),
            self._is_watch_question_threads_i_comment_checkbox_checked(),
            self._is_watch_question_threads_i_comment_checkbox_checked(),
            self._is_watch_question_threads_i_comment_checkbox_checked(),
            self._is_send_emails_for_private_messages_checkbox_checked(),
        ]

        if False in is_checked:
            return False
        else:
            return True
