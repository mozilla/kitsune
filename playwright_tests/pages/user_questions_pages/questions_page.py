from playwright.sync_api import Page, ElementHandle, Locator
from playwright_tests.core.basepage import BasePage


class QuestionPage(BasePage):
    # "Posted successfully" green banner
    __posted_questions_success_banner_message = "//ul[@class='user-messages']/li/p"
    __posted_questions_success_banner_my_questions_link = "//ul[@class='user-messages']/li/p/a"
    __posted_questions_success_banner_close_button = "//ul[@class='user-messages']/li/button"

    # Lock this thread banner
    __lock_this_thread_banner = "//div[@class='notice mzp-c-notification-bar mzp-t-click']/p"
    __lock_this_thread_banner_link = ("//div[@class='notice mzp-c-notification-bar "
                                      "mzp-t-click']/p/a")

    # Marked as spam banner
    __marked_as_spam_banner = "//p[@class='is-spam']"

    # Question
    __question_author = "//div[@class='question']//span[@class='display-name']"
    __questions_header = "//h2[@class='sumo-callout-heading summary no-product-heading']"
    __question_body = "//div[@class='main-content']/div/p"
    __modified_question_section = "//p[@class='edited text-body-sm']"

    # Progress bar
    __complete_progress_items_label = ("//li[@class='progress--item is-complete']//span["
                                       "@class='progress--label']")

    # Breadcrumbs
    __aaq_page_breadcrumbs = "//ol[@id='breadcrumbs']/li/a"

    # Question details
    __question_details_button = "//button[@aria-controls='question-details']"
    __more_system_details_option = "//a[@id='show-more-details']"
    __close_additional_system_details_button = "//div[@class='mzp-c-modal-close']/button"
    __user_agent_information = "//div[@class='about-support']//li"

    # Searchbar
    __search_support_searchbar = "//form[@id='support-search-sidebar']/input"
    __search_support_search_button = "//form[@id='support-search-sidebar']/button"

    # Still need help widget
    __still_need_help_ask_now_button = "//a[@data-event-label='aaq widget']"

    # Question Tools
    __edit_this_question_option = "//ul[@id='related-content']/li[@class='edit']/a"
    __stop_email_updates_option = "//ul[@id='related-content']/li[@class='email']/a"
    __subscribe_to_feed_option = "//ul[@id='related-content']/li[@class='rss']/a"
    __delete_this_question_option = "//ul[@id='related-content']//a[@class='delete']"
    __lock_this_question_option = "//a[@data-form='lock-form']"
    __archive_this_question_option = "//a[@data-form='archive-form']"
    __system_details_options = "//div[@id='system-details']/ul[@class='system']/li"
    __mark_as_spam_option = "//ul[@id='related-content']//form[@class='spam-form cf']/a"

    # Tags section
    __question_tags_options = "//li[@class='tag']/a"
    __add_a_tag_input_field = "//input[@id='id_tag_input']"
    __add_a_tab_button = "//form[@class='tag-adder']/input[@type='submit']"

    # Post a reply section
    __post_a_reply_section_heading = "//h3[@class='sumo-card-heading']"
    __post_a_reply_textarea = "//textarea[@id='id_content']"
    __post_a_reply_textarea_bold_button = "//button[@title='Bold']"
    __post_a_reply_textarea_italic_button = "//button[@title='Italic']"
    __post_a_reply_textarea_link_button = "//button[@title='Insert a link...']"
    __post_a_reply_textarea_numbered_list_button = "//button[@title='Numbered List']"
    __post_a_reply_textarea_bulleted_list_button = "//button[@title='Bulleted List']"
    __common_responses_option = "//a[@title='Common responses']"

    # Needs more information from the user
    __needs_more_information_from_the_user_checkbox = "//input[@id='id_needs_info']"
    __more_information_panel_header = ("//section[@id='more-system-details']//h3[contains(text(),"
                                       "'More Information')]")

    # Attached image
    __attached_image = "//a[@class='image']/img"
    __add_image_button = "//div[@class='field add-attachment']"

    # Preview Reply button
    __preview_reply_button = "//input[@id='preview']"

    # Post Reply button
    __post_reply_button = "//button[contains(text(),'Post Reply')]"

    # Delete question
    __delete_question_delete_button = "//input[@value='Delete']"
    __delete_question_cancel_button = "//a[contains(text(),'Cancel')]"

    def __init__(self, page: Page):
        super().__init__(page)

    # Breadcrumbs actions.
    def get_current_breadcrumb_locator(self, question_title: str) -> Locator:
        xpath = f"//ol[@id='breadcrumbs']/li[text()='{question_title}']"
        return super()._get_element_locator(xpath)

    def click_on_breadcrumb_locator(self, element: Locator):
        super()._click(element)

    # Get email updates actions.
    def get_email_updates_option(self) -> Locator:
        return super()._get_element_locator(self.__stop_email_updates_option)

    # Page content actions.
    def get_question_header(self) -> str:
        return super()._get_text_of_element(self.__questions_header)

    def get_question_body(self) -> str:
        return super()._get_text_of_element(self.__question_body)

    def get_question_author_name(self) -> str:
        return super()._get_text_of_element(self.__question_author)

    def get_modified_question_locator(self) -> Locator:
        return super()._get_element_locator(self.__modified_question_section)

    def get_modified_by_text(self) -> str:
        return super()._get_text_of_element(self.__modified_question_section)

    def get_add_image_section_locator(self) -> Locator:
        return super()._get_element_locator(self.__add_image_button)

    def click_on_my_questions_banner_option(self):
        super()._click(self.__posted_questions_success_banner_my_questions_link)

    def click_on_solves_the_problem_button(self, target_reply_id: str):
        xpath = f"//div[@id='{target_reply_id}']/following-sibling::aside//input[@type='submit']"

        super()._click(xpath)

    def is_post_reply_button_visible(self) -> ElementHandle:
        super()._wait_for_selector(self.__post_reply_button)
        return super()._get_element_handle(self.__post_reply_button)

    def click_on_the_reply_author(self, reply_id: str):
        xpath = f"//div[@id='{reply_id}']//a[@class='author-name']"
        super()._click(xpath)

    # Question tag actions.
    def get_question_tag_options(self) -> list[str]:
        return super()._get_text_of_elements(self.__question_tags_options)

    def get_remove_tag_button_locator(self, tag_name: str) -> Locator:
        xpath = xpath = (f"//ul[@class='tag-list cf']//a[text()='{tag_name}']/following-sibling"
                         f"::button[@class='remover']")
        return super()._get_element_locator(xpath)

    def add_text_to_add_a_tag_input_field(self, text: str):
        super()._fill(self.__add_a_tag_input_field, text)
        dropdown_xpath = f"//li[@class='ui-menu-item']/div[text()='{text}']"
        super()._click(dropdown_xpath)

    def get_add_a_tag_input_field(self) -> Locator:
        return super()._get_element_locator(self.__add_a_tag_input_field)

    def get_add_a_tag_button(self) -> Locator:
        return super()._get_element_locator(self.__add_a_tab_button)

    def click_on_add_a_tag_button(self):
        super()._click(self.__add_a_tab_button)

    def click_on_a_certain_tag(self, tag_name: str):
        xpath = f"//li[@class='tag']//a[text()='{tag_name}']"
        super()._click(xpath)

    def get_a_certain_tag(self, tag_name: str) -> Locator:
        xpath = f"//li[@class='tag']//a[text()='{tag_name}']"
        return super()._get_element_locator(xpath)

    def click_on_tag_remove_button(self, tag_name: str):
        xpath = (f"//li[@class='tag']//a[text()='{tag_name}']/following-sibling::button["
                 f"@class='remover']")
        super()._click(xpath)

    # Attached image actions.
    def get_attached_image(self) -> Locator:
        return super()._get_element_locator(self.__attached_image)

    # Question more information actions.
    def get_more_information_with_text_locator(self, text: str) -> Locator:
        xpath = f"//div[@class='about-support']/p[text()='{text}']"
        return super()._get_element_locator(xpath)

    def get_question_details_button_locator(self) -> Locator:
        return super()._get_element_locator(self.__question_details_button)

    def get_more_information_locator(self) -> Locator:
        return super()._get_element_locator(self.__more_information_panel_header)

    def get_user_agent_information(self) -> str:
        return super()._get_text_of_element(self.__user_agent_information)

    def get_system_details_information(self) -> list[str]:
        return super()._get_text_of_elements(self.__system_details_options)

    def click_on_question_details_button(self):
        super()._click(self.__question_details_button)

    def click_on_more_system_details_option(self):
        super()._click(self.__more_system_details_option)

    def click_on_the_additional_system_panel_close_button(self):
        super()._click(self.__close_additional_system_details_button)

    # Post a reply actions.
    def add_text_to_post_a_reply_textarea(self, text: str):
        super()._fill(self.__post_a_reply_textarea, text)

    def get_post_a_reply_textarea_locator(self) -> Locator:
        return super()._get_element_locator(self.__post_a_reply_textarea)

    def get_posted_reply_locator(self, question_id: str) -> Locator:
        xpath = f"//div[@id='{question_id}']"
        return super()._get_element_locator(xpath)

    def click_on_post_reply_button(self, repliant_username) -> str:
        xpath_display_name = \
            f"//span[@class='display-name' and contains(text(), '{repliant_username}')]"

        xpath_reply_id = (f"//span[@class='display-name' and contains(text(), "
                          f"'{repliant_username}')]/ancestor::div[@class='answer ']")
        super()._click(self.__post_reply_button)
        super()._wait_for_selector(xpath_display_name)
        return super()._get_element_attribute_value(xpath_reply_id, "id")

    # Question Tools actions.
    def get_edit_this_question_option_locator(self) -> Locator:
        return super()._get_element_locator(self.__edit_this_question_option)

    def get_delete_this_question_locator(self) -> Locator:
        return super()._get_element_locator(self.__delete_this_question_option)

    def get_lock_this_question_locator(self) -> Locator:
        return super()._get_element_locator(self.__lock_this_question_option)

    # Stands for archived banner as well
    def get_thread_locked_text(self) -> str:
        return super()._get_text_of_element(self.__lock_this_thread_banner)

    def get_thread_locked_locator(self) -> Locator:
        return super()._get_element_locator(self.__lock_this_thread_banner)

    def get_archive_this_question_locator(self) -> Locator:
        return super()._get_element_locator(self.__archive_this_question_option)

    def get_needs_more_information_checkbox_locator(self) -> Locator:
        return super()._get_element_locator(self.__needs_more_information_from_the_user_checkbox)

    def get_mark_as_spam_locator(self) -> Locator:
        return super()._get_element_locator(self.__mark_as_spam_option)

    def get_marked_as_spam_banner_locator(self) -> Locator:
        return super()._get_element_locator(self.__marked_as_spam_banner)

    def get_marked_as_spam_banner_text(self) -> str:
        return super()._get_text_of_element(self.__marked_as_spam_banner)

    def click_on_thread_locked_link(self):
        super()._click(self.__lock_this_thread_banner_link)

    def click_on_lock_this_question_locator(self):
        super()._click(self.__lock_this_question_option)

    def click_on_subscribe_to_feed_option(self):
        super()._click(self.__subscribe_to_feed_option)

    def click_on_mark_as_spam_option(self):
        super()._click(self.__mark_as_spam_option)

    def click_on_edit_this_question_question_tools_option(self):
        super()._click(self.__edit_this_question_option)

    def click_delete_this_question_question_tools_option(self):
        super()._click(self.__delete_this_question_option)

    def click_on_archive_this_question_option(self):
        super()._click(self.__archive_this_question_option)

    def click_delete_this_question_button(self):
        super()._click(self.__delete_question_delete_button)
