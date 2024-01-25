from playwright.sync_api import Page, ElementHandle, Locator
from playwright_tests.core.basepage import BasePage


class QuestionPage(BasePage):
    # "Posted successfully" green banner locators.
    __posted_questions_success_banner_message = "//ul[@class='user-messages']/li/p"
    __posted_questions_success_banner_my_questions_link = "//ul[@class='user-messages']/li/p/a"
    __posted_questions_success_banner_close_button = "//ul[@class='user-messages']/li/button"

    # Lock this thread banner locators.
    __lock_this_thread_banner = "//div[@class='notice mzp-c-notification-bar mzp-t-click']/p"
    __lock_this_thread_banner_link = ("//div[@class='notice mzp-c-notification-bar "
                                      "mzp-t-click']/p/a")

    # Marked as spam banner locators.
    __marked_as_spam_banner = "//p[@class='is-spam']"

    # Solved problem banner
    __problem_solved_banner_text = "//li[@class='mzp-c-notification-bar mzp-t-success']/p"
    __problem_solved_reply_text = "//div[@class='reply']/p"
    __problem_solved_reply_section = "//div[@class='solution card elevation-00']"
    __problem_solved_reply_section_header = "//h4[@class='is-solution']"
    __problem_solved_reply_reply_link = "//div[@class='reply']/a"
    __undo_solves_problem = "//input[@value='Undo']"

    # Question locators.
    __question_author = "//div[@class='question']//span[@class='display-name']"
    __questions_header = "//h2[@class='sumo-callout-heading summary no-product-heading']"
    __question_body = "//div[@class='main-content']/div/p"
    __modified_question_section = "//p[@class='edited text-body-sm']"

    # Progress bar locators.
    __complete_progress_items_label = ("//li[@class='progress--item is-complete']//span["
                                       "@class='progress--label']")

    # Breadcrumbs locators.
    __aaq_page_breadcrumbs = "//ol[@id='breadcrumbs']/li/a"

    # Question details locators.
    __question_details_button = "//button[@aria-controls='question-details']"
    __more_system_details_option = "//a[@id='show-more-details']"
    __close_additional_system_details_button = "//div[@class='mzp-c-modal-close']/button"
    __user_agent_information = "//div[@class='about-support']//li"
    __question_section = "//article/div[@class='question']"

    # Searchbar locators.
    __search_support_searchbar = "//form[@id='support-search-sidebar']/input"
    __search_support_search_button = "//form[@id='support-search-sidebar']/button"

    # Still need help widget locators.
    __still_need_help_ask_now_button = "//a[@data-event-label='aaq widget']"

    # Question Tools locators.
    __edit_this_question_option = "//ul[@id='related-content']/li[@class='edit']/a"
    __stop_email_updates_option = "//ul[@id='related-content']/li[@class='email']/a"
    __subscribe_to_feed_option = "//ul[@id='related-content']/li[@class='rss']/a"
    __delete_this_question_option = "//ul[@id='related-content']//a[@class='delete']"
    __lock_this_question_option = "//a[@data-form='lock-form']"
    __archive_this_question_option = "//a[@data-form='archive-form']"
    __system_details_options = "//div[@id='system-details']/ul[@class='system']/li"
    __mark_as_spam_option = "//ul[@id='related-content']//form[@class='spam-form cf']/a"

    # Tags section locators.
    __question_tags_options = "//li[@class='tag']/a"
    __add_a_tag_input_field = "//input[@id='id_tag_input']"
    __add_a_tab_button = "//form[@class='tag-adder']/input[@type='submit']"

    # Post a reply section locators.
    __post_a_reply_section_heading = "//h3[@class='sumo-card-heading']"
    __post_a_reply_textarea = "//textarea[@id='id_content']"
    __post_a_reply_textarea_bold_button = "//button[@title='Bold']"
    __post_a_reply_textarea_italic_button = "//button[@title='Italic']"
    __post_a_reply_textarea_link_button = "//button[@title='Insert a link...']"
    __post_a_reply_textarea_numbered_list_button = "//button[@title='Numbered List']"
    __post_a_reply_textarea_bulleted_list_button = "//button[@title='Bulleted List']"
    __last_reply_by = "//span[@class='forum--meta-val visits no-border']"

    # Common Responses locators.
    __common_responses_option = "//a[@title='Common responses']"
    __common_responses_search_field = "//input[@id='filter-responses-field']"
    __common_responses_modal_close_button = "//div[@id='media-modal']/a"
    __common_responses_categories_options = "//div[@id='responses-area']//li"
    __common_responses_responses_options = ("//ul[@class='sidebar-nav']/li[@class='response' and "
                                            "not(@style='display: none;')]")
    __common_responses_no_cat_selected = "//h4[@class='nocat-label']"
    __common_responses_switch_to_mode = "//div[@id='response-content-area']//button"
    __common_responses_response_preview = ("//p[@class='response-preview-rendered']//div["
                                           "@class='main-content']/div[@class='content']")
    __common_responses_textarea_field = "//textarea[@id='response-content']"
    __common_responses_insert_response_button = "//button[@id='insert-response']"
    __common_responses_cancel_button = "//div[@id='response-submit-area']/a"

    # I have this problem too locators.
    __i_have_this_problem_too_button = "//div[@class='me-too']//button"
    __i_have_this_problem_too_counter = "//span[@class='forum--meta-val have-problem']"

    # Needs more information from the user locators.
    __needs_more_information_from_the_user_checkbox = "//input[@id='id_needs_info']"
    __more_information_panel_header = ("//section[@id='more-system-details']//h3[contains(text(),"
                                       "'More Information')]")

    # Attached image locators.
    __attached_image = "//a[@class='image']/img"
    __add_image_button = "//div[@class='field add-attachment']"

    # Preview Reply button locators.
    __preview_reply_button = "//input[@id='preview']"

    # Post Reply button locators.
    __post_reply_button = "//button[text()='Post Reply']"

    # Delete question locators.
    __delete_question_delete_button = "//input[@value='Delete']"
    __delete_question_cancel_button = "//a[contains(text(),'Cancel')]"

    # Report abuse section.
    __report_abuse_submit_button = "//div[@class='mzp-c-modal-inner']//button[@type='submit']"
    __report_abuse_textarea = "//div[@class='mzp-c-modal-inner']//textarea"
    __report_abuse_flagged_this_content_message = ("//div[@class='mzp-c-modal-inner']//span["
                                                   "@class='message']")
    __report_abuse_modal_close_button = ("//div[@class='mzp-c-modal-inner']//button["
                                         "@class='mzp-c-modal-button-close']")

    # Signed out card locators.
    __log_in_to_your_account_signed_out_card_option = ("//div[@class='question-tools "
                                                       "ask-a-question card is-shaded']/p/a["
                                                       "text()='log in to your account']")
    __start_a_new_question_signed_out_card_option = ("//div[@class='question-tools ask-a-question "
                                                     "card is-shaded']/p/a[text()='start a new "
                                                     "question']")
    __ask_a_question_signed_out_card_option = ("//div[@class='question-tools ask-a-question card "
                                               "is-shaded']//a[text()='Ask a question']")
    __i_have_this_problem_too_signed_out_card_option = ("//div[@class='question-tools "
                                                        "ask-a-question card "
                                                        "is-shaded']//button[text()='I have this "
                                                        "problem, too']")

    def __init__(self, page: Page):
        super().__init__(page)

    # Report abuse actions.
    def _click_abuse_modal_close_button(self):
        super()._click(self.__report_abuse_modal_close_button)

    def _get_successful_flagged_this_content_text(self) -> str:
        return super()._get_text_of_element(self.__report_abuse_flagged_this_content_message)

    def _add_text_to_report_abuse_textarea(self, text: str):
        super()._fill(self.__report_abuse_textarea, text)

    def _click_on_report_abuse_submit_button(self):
        super()._click(self.__report_abuse_submit_button)

    # Breadcrumbs actions.
    def _get_current_breadcrumb_locator(self, question_title: str) -> Locator:
        xpath = f"//ol[@id='breadcrumbs']/li[text()='{question_title}']"
        return super()._get_element_locator(xpath)

    def _click_on_breadcrumb_locator(self, element: Locator):
        super()._click(element)

    # Get email updates actions.
    def _get_email_updates_option(self) -> Locator:
        return super()._get_element_locator(self.__stop_email_updates_option)

    # Problem solved actions.
    def _get_problem_solved_section_header_text(self) -> str:
        return super()._get_text_of_element(self.__problem_solved_reply_section_header)

    def _click_on_undo_button(self):
        super()._click(self.__undo_solves_problem)

    def _get_undo_button_locator(self) -> Locator:
        return super()._get_element_locator(self.__undo_solves_problem)

    def _click_read_this_answer_in_context_link(self):
        super()._click(self.__problem_solved_reply_reply_link)

    def _get_chosen_solution_text(self) -> str:
        return super()._get_text_of_element(self.__problem_solved_reply_text)

    def _get_chosen_solution_section_locator(self) -> Locator:
        return super()._get_element_locator(self.__problem_solved_reply_section)

    def _get_solved_problem_banner_text(self) -> str:
        return super()._get_text_of_element(self.__problem_solved_banner_text)

    def _get_solved_the_problem_button_locator(self, target_reply_id: str) -> Locator:
        xpath = f"//div[@id='{target_reply_id}']/following-sibling::aside//input[@type='submit']"
        return super()._get_element_locator(xpath)

    def _get_chosen_solution_reply_message(self, reply_id: str) -> str:
        xpath = f"//div[@id='{reply_id}']//h3[@class='is-solution']"
        return super()._get_text_of_element(xpath)

    def _get_chosen_solution_reply_message_locator(self, reply_id: str) -> Locator:
        xpath = f"//div[@id='{reply_id}']//h3[@class='is-solution']"
        return super()._get_element_locator(xpath)

    # I have this problem too actions.
    def _get_i_have_this_problem_too_locator(self) -> Locator:
        return super()._get_element_locator(self.__i_have_this_problem_too_button)

    def _click_i_have_this_problem_too_button(self):
        super()._click(self.__i_have_this_problem_too_button)

    def _get_i_have_this_problem_too_counter(self) -> int:
        return int(super()._get_text_of_element(self.__i_have_this_problem_too_counter))

    def _get_last_reply_by_text(self) -> str:
        return super()._get_text_of_element(self.__last_reply_by)

    # Page content actions.
    def _get_question_header(self) -> str:
        return super()._get_text_of_element(self.__questions_header)

    def _click_last_reply_by(self):
        super()._click(self.__last_reply_by)

    def _get_question_body(self) -> str:
        return super()._get_text_of_element(self.__question_body)

    def _get_question_author_name(self) -> str:
        return super()._get_text_of_element(self.__question_author)

    def _get_question_id(self) -> str:
        return super()._get_element_attribute_value(self.__question_section, 'id')

    def _get_modified_question_locator(self) -> Locator:
        return super()._get_element_locator(self.__modified_question_section)

    def _get_modified_by_text(self) -> str:
        return super()._get_text_of_element(self.__modified_question_section)

    def _get_add_image_section_locator(self) -> Locator:
        return super()._get_element_locator(self.__add_image_button)

    def _click_on_my_questions_banner_option(self):
        super()._click(self.__posted_questions_success_banner_my_questions_link)

    def _click_on_solves_the_problem_button(self, target_reply_id: str):
        xpath = f"//div[@id='{target_reply_id}']/following-sibling::aside//input[@type='submit']"

        super()._click(xpath)

    def _is_post_reply_button_visible(self) -> ElementHandle:
        super()._wait_for_selector(self.__post_reply_button)
        return super()._get_element_handle(self.__post_reply_button)

    def _click_on_the_reply_author(self, reply_id: str):
        xpath = f"//div[@id='{reply_id}']//a[@class='author-name']"
        super()._click(xpath)

    def _get_text_content_of_reply(self, reply_id: str) -> str:
        xpath = f"//div[@id='{reply_id}']//div[@class='content']"
        return super()._get_text_of_element(xpath)

    def _get_display_name_of_question_reply_author(self, reply_id: str) -> str:
        xpath = f"//div[@id='{reply_id}']//a[@class='author-name']/span[@class='display-name']"
        return super()._get_text_of_element(xpath)

    def _get_displayed_user_title_of_question_reply_locator(self, reply_id: str) -> Locator:
        xpath = f"//div[@id='{reply_id}']//a[@class='author-name']/span[@class='user-title']"
        return super()._get_element_locator(xpath)

    def _get_displayed_user_title_of_question_reply(self, reply_id: str) -> str:
        xpath = f"//div[@id='{reply_id}']//a[@class='author-name']/span[@class='user-title']"
        return super()._get_text_of_element(xpath)

    # Question tag actions.
    def _get_question_tag_options(self) -> list[str]:
        return super()._get_text_of_elements(self.__question_tags_options)

    def _get_remove_tag_button_locator(self, tag_name: str) -> Locator:
        xpath = xpath = (f"//ul[@class='tag-list cf']//a[text()='{tag_name}']/following-sibling"
                         f"::button[@class='remover']")
        return super()._get_element_locator(xpath)

    def _add_text_to_add_a_tag_input_field(self, text: str):
        super()._fill(self.__add_a_tag_input_field, text)
        dropdown_xpath = f"//li[@class='ui-menu-item']/div[text()='{text}']"
        super()._click(dropdown_xpath)

    def _get_add_a_tag_input_field(self) -> Locator:
        return super()._get_element_locator(self.__add_a_tag_input_field)

    def _get_add_a_tag_button(self) -> Locator:
        return super()._get_element_locator(self.__add_a_tab_button)

    def _click_on_add_a_tag_button(self):
        super()._click(self.__add_a_tab_button)

    def _click_on_a_certain_tag(self, tag_name: str):
        xpath = f"//li[@class='tag']//a[text()='{tag_name}']"
        super()._click(xpath)

    def _get_a_certain_tag(self, tag_name: str) -> Locator:
        xpath = f"//li[@class='tag']//a[text()='{tag_name}']"
        return super()._get_element_locator(xpath)

    def _click_on_tag_remove_button(self, tag_name: str):
        xpath = (f"//li[@class='tag']//a[text()='{tag_name}']/following-sibling::button["
                 f"@class='remover']")
        super()._click(xpath)

    # Attached image actions.
    def _get_attached_image(self) -> Locator:
        return super()._get_element_locator(self.__attached_image)

    # Question more information actions.
    def _get_more_information_with_text_locator(self, text: str) -> Locator:
        xpath = f"//div[@class='about-support']/p[text()='{text}']"
        return super()._get_element_locator(xpath)

    def _get_question_details_button_locator(self) -> Locator:
        return super()._get_element_locator(self.__question_details_button)

    def _get_more_information_locator(self) -> Locator:
        return super()._get_element_locator(self.__more_information_panel_header)

    def _get_user_agent_information(self) -> str:
        return super()._get_text_of_element(self.__user_agent_information)

    def _get_system_details_information(self) -> list[str]:
        return super()._get_text_of_elements(self.__system_details_options)

    def _click_on_question_details_button(self):
        super()._click(self.__question_details_button)

    def _click_on_more_system_details_option(self):
        super()._click(self.__more_system_details_option)

    def _click_on_the_additional_system_panel_close_button(self):
        super()._click(self.__close_additional_system_details_button)

    def _get_reply_section_locator(self, answer_id: str) -> Locator:
        xpath = f"//div[@id='{answer_id}']"
        return super()._get_element_locator(xpath)

    def _click_on_reply_more_options_button(self, answer_id: str):
        xpath = f"//div[@id='{answer_id}']//button[text()='more options']"
        super()._click(xpath)

    def _click_on_report_abuse_for_a_certain_reply(self, answer_id: str):
        xpath = f"//div[@id='{answer_id}']//a[text()='Report Abuse']"
        super()._click(xpath)

    def _get_click_on_report_abuse_reply_locator(self, answer_id: str) -> Locator:
        xpath = f"//div[@id='{answer_id}']//a[text()='Report Abuse']"
        return super()._get_element_locator(xpath)

    def _click_on_quote_for_a_certain_reply(self, answer_id: str):
        xpath = f"//div[@id='{answer_id}']//a[text()='Quote']"
        super()._click(xpath)

    def _get_quote_reply_locator(self, answer_id: str) -> Locator:
        xpath = f"//div[@id='{answer_id}']//a[text()='Quote']"
        return super()._get_element_locator(xpath)

    def _click_on_mark_as_spam_for_a_certain_reply(self, answer_id: str):
        xpath = f"//div[@id='{answer_id}']//form[@class='spam-form cf']/a"
        super()._click(xpath)

    def _get_mark_as_spam_reply_locator(self, answer_id: str) -> Locator:
        xpath = f"//div[@id='{answer_id}']//form[@class='spam-form cf']/a"
        return super()._get_element_locator(xpath)

    def _get_marked_as_spam_locator(self, answer_id: str) -> Locator:
        xpath = f"//div[@id='{answer_id}']//h3[@class='is-spam']"
        return super()._get_element_locator(xpath)

    def _get_marked_as_spam_text(self, answer_id: str) -> str:
        xpath = f"//div[@id='{answer_id}']//h3[@class='is-spam']"
        return super()._get_text_of_element(xpath)

    def _click_on_edit_this_post_for_a_certain_reply(self, answer_id: str):
        xpath = f"//div[@id='{answer_id}']//a[text()='Edit this post']"
        super()._click(xpath)

    def _get_edit_this_post_reply_locator(self, answer_id: str) -> Locator:
        xpath = f"//div[@id='{answer_id}']//a[text()='Edit this post']"
        return super()._get_element_locator(xpath)

    def _click_on_delete_this_post_for_a_certain_reply(self, answer_id: str):
        xpath = f"//div[@id='{answer_id}']//a[text()='Delete this post']"
        super()._click(xpath)

    def _get_delete_this_post_reply_locator(self, answer_id: str) -> Locator:
        xpath = f"//div[@id='{answer_id}']//a[text()='Delete this post']"
        return super()._get_element_locator(xpath)

    def _click_on_cancel_delete_button(self):
        super()._click(self.__delete_question_cancel_button)

    # Post a reply actions.
    def _add_text_to_post_a_reply_textarea(self, text: str):
        super()._fill(self.__post_a_reply_textarea, text)

    def _type_inside_the_post_a_reply_textarea(self, text: str):
        super()._type(self.__post_a_reply_textarea, text, 100)

    def _get_post_a_reply_textarea_locator(self) -> Locator:
        return super()._get_element_locator(self.__post_a_reply_textarea)

    def _get_post_a_reply_textarea_text(self) -> str:
        return super()._get_text_of_element(self.__post_a_reply_textarea)

    def _get_post_a_reply_textarea_value(self) -> str:
        return super()._get_element_input_value(self.__post_a_reply_textarea)

    def _get_posted_reply_locator(self, question_id: str) -> Locator:
        xpath = f"//div[@id='{question_id}']"
        return super()._get_element_locator(xpath)

    def _get_posted_reply_text(self, reply_id: str) -> str:
        xpath = f"//div[@id='{reply_id}']//div[@class='content']/p"
        return super()._get_text_of_element(xpath)

    def _get_posted_quote_reply_username_text(self, reply_id: str) -> str:
        xpath = f"//div[@id='{reply_id}']//div[@class='content']/em/p"
        return super()._get_text_of_element(xpath)

    def _click_posted_reply_said_link(self, reply_id: str) -> str:
        xpath = f"//div[@id='{reply_id}']//div[@class='content']//a"
        super()._click(xpath)

    def _get_blockquote_reply_text(self, reply_id: str) -> str:
        xpath = f"//div[@id='{reply_id}']//div[@class='content']//blockquote"
        return super()._get_text_of_element(xpath)

    def _get_posted_reply_modified_by_text(self, reply_id: str) -> str:
        xpath = f"//div[@id='{reply_id}']//p[@class='edited text-body-sm']/em"
        return super()._get_text_of_element(xpath)

    def _get_posted_reply_modified_by_locator(self, reply_id: str) -> Locator:
        xpath = f"//div[@id='{reply_id}']//p[@class='edited text-body-sm']/em"
        return super()._get_element_locator(xpath)

    def _click_on_post_reply_button(self, repliant_username) -> str:
        xpath_display_name = \
            f"//span[@class='display-name' and contains(text(), '{repliant_username}')]"

        xpath_reply_id = (f"//span[@class='display-name' and contains(text(), "
                          f"'{repliant_username}')]/ancestor::div[@class='answer ']")
        super()._click(self.__post_reply_button)
        super()._wait_for_selector(xpath_display_name)
        return super()._get_element_attribute_value(xpath_reply_id, "id")

    # Question Tools actions.
    def _get_edit_this_question_option_locator(self) -> Locator:
        return super()._get_element_locator(self.__edit_this_question_option)

    def _get_delete_this_question_locator(self) -> Locator:
        return super()._get_element_locator(self.__delete_this_question_option)

    def _get_lock_this_question_locator(self) -> Locator:
        return super()._get_element_locator(self.__lock_this_question_option)

    # Stands for archived banner as well
    def _get_thread_locked_text(self) -> str:
        return super()._get_text_of_element(self.__lock_this_thread_banner)

    def _get_thread_locked_locator(self) -> Locator:
        return super()._get_element_locator(self.__lock_this_thread_banner)

    def _get_archive_this_question_locator(self) -> Locator:
        return super()._get_element_locator(self.__archive_this_question_option)

    def _get_needs_more_information_checkbox_locator(self) -> Locator:
        return super()._get_element_locator(self.__needs_more_information_from_the_user_checkbox)

    def _get_mark_as_spam_locator(self) -> Locator:
        return super()._get_element_locator(self.__mark_as_spam_option)

    def _get_marked_as_spam_banner_locator(self) -> Locator:
        return super()._get_element_locator(self.__marked_as_spam_banner)

    def _get_marked_as_spam_banner_text(self) -> str:
        return super()._get_text_of_element(self.__marked_as_spam_banner)

    def _click_on_thread_locked_link(self):
        super()._click(self.__lock_this_thread_banner_link)

    def _click_on_lock_this_question_locator(self):
        super()._click(self.__lock_this_question_option)

    def _click_on_subscribe_to_feed_option(self):
        super()._click(self.__subscribe_to_feed_option)

    def _click_on_mark_as_spam_option(self):
        super()._click(self.__mark_as_spam_option)

    def _click_on_edit_this_question_question_tools_option(self):
        super()._click(self.__edit_this_question_option)

    def _click_delete_this_question_question_tools_option(self):
        super()._click(self.__delete_this_question_option)

    def _click_on_archive_this_question_option(self):
        super()._click(self.__archive_this_question_option)

    def _click_delete_this_question_button(self):
        super()._click(self.__delete_question_delete_button)

    # Votes reply section
    def _get_reply_votes_section_locator(self, reply_id: str) -> Locator:
        xpath = f"//div[@id='{reply_id}']//form[@class='document-vote--form helpful']"
        return super()._get_element_locator(xpath)

    def _get_reply_vote_heading(self, reply_id: str) -> str:
        xpath = f"//div[@id='{reply_id}']//h4[@class='document-vote--heading']"
        return super()._get_text_of_element(xpath)

    def _click_reply_vote_thumbs_up_button(self, reply_id: str):
        xpath = f"//div[@id='{reply_id}']//button[@name='helpful']"
        return super()._click(xpath)

    def _get_thumbs_up_vote_message(self, reply_id: str) -> str:
        xpath = f"//div[@id='{reply_id}']//p[@class='msg document-vote--heading']"
        return super()._get_text_of_element(xpath)

    def _get_thumbs_up_button_locator(self, reply_id: str) -> Locator:
        xpath = f"//div[@id='{reply_id}']//button[@name='helpful']"
        return super()._get_element_locator(xpath)

    def _get_thumbs_down_button_locator(self, reply_id: str) -> Locator:
        xpath = f"//div[@id='{reply_id}']//button[@name='not-helpful']"
        return super()._get_element_locator(xpath)

    def _click_reply_vote_thumbs_down_button(self, reply_id):
        xpath = f"//div[@id='{reply_id}']//button[@name='not-helpful']"
        super()._click(xpath)

    def _get_helpful_count(self, reply_id) -> str:
        xpath = f"//div[@id='{reply_id}']//button[@name='helpful']//strong[@class='helpful-count']"
        return super()._get_text_of_element(xpath)

    def _get_not_helpful_count(self, reply_id) -> str:
        xpath = (f"//div[@id='{reply_id}']//button[@name='not-helpful']//strong["
                 f"@class='helpful-count']")
        return super()._get_text_of_element(xpath)

    # Signed out card actions.
    def _click_on_log_in_to_your_account_signed_out_card_link(self):
        super()._click(self.__log_in_to_your_account_signed_out_card_option)

    def _click_on_start_a_new_question_signed_out_card_link(self):
        super()._click(self.__start_a_new_question_signed_out_card_option)

    def _click_on_ask_a_question_signed_out_card_option(self):
        super()._click(self.__ask_a_question_signed_out_card_option)

    def _ask_a_question_signed_out_card_option_locator(self) -> Locator:
        return super()._get_element_locator(self.__ask_a_question_signed_out_card_option)

    def _click_on_i_have_this_problem_too_signed_out_card_option(self):
        super()._click(self.__i_have_this_problem_too_signed_out_card_option)

    def _get_i_have_this_problem_too_signed_out_card_locator(self) -> Locator:
        return super()._get_element_locator(self.__i_have_this_problem_too_signed_out_card_option)

    # Common responses actions.

    def _click_on_common_responses_option(self):
        super()._click(self.__common_responses_option)

    def _type_into_common_responses_search_field(self, text: str):
        super()._type(self.__common_responses_search_field, text, 100)

    def _get_text_of_no_cat_responses(self) -> str:
        return super()._get_text_of_element(self.__common_responses_no_cat_selected)

    def _get_list_of_categories(self) -> list[str]:
        return super()._get_text_of_elements(self.__common_responses_categories_options)

    def _get_list_of_responses(self) -> list[str]:
        return super()._get_text_of_elements(self.__common_responses_responses_options)

    def _click_on_a_particular_category_option(self, option: str):
        xpath = f"//ul[@class='category-list']/li[text()='{option}']"
        super()._click(xpath)

    def _click_on_a_particular_response_option(self, option: str):
        xpath = f"//ul[@class='sidebar-nav']/li[text()='{option}']"
        super()._click(xpath)

    # Removing both newline characters and link syntax format.
    def _get_text_of_response_editor_textarea_field(self) -> str:
        return (super()._get_element_input_value(self.__common_responses_textarea_field)
                .replace("\n", "")
                .replace("[", "")
                .replace("]", "")
                )

    def _get_text_of_response_preview(self) -> str:
        return super()._get_text_of_element(self.__common_responses_response_preview)

    def _click_on_switch_to_mode(self):
        super()._click(self.__common_responses_switch_to_mode)

    def _click_on_common_responses_cancel_button(self):
        super()._click(self.__common_responses_cancel_button)

    def _click_on_common_responses_insert_response_button(self):
        super()._click(self.__common_responses_insert_response_button)
