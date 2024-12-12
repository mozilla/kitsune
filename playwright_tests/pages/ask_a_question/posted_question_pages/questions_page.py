from playwright.sync_api import Page, ElementHandle, Locator
from playwright_tests.core.basepage import BasePage
from playwright_tests.pages.community_forums.forums_pages.product_support_forum import \
    ProductSupportForum


class QuestionPage(BasePage):
    # "Posted successfully" green banner locators.
    BANNER_LOCATORS = {
        "posted_questions_success_banner_message": "//ul[@class='user-messages']/li/p",
        "posted_questions_success_banner_my_questions_link": "//ul[@class='user-messages']/li/p/a",
        "posted_questions_success_banner_close_button": "//ul[@class='user-messages']/li/button",
        "reply_flagged_as_spam_banner": "//li[@class='mzp-c-notification-bar mzp-t-warning']/p",
        "marked_as_spam_banner": "//p[@class='is-spam']",
        "lock_this_thread_banner": "//div[@class='notice mzp-c-notification-bar mzp-t-click']/p",
        "lock_this_thread_banner_link": ("//div[@class='notice mzp-c-notification-bar "
                                         "mzp-t-click']/p/a"),
        "problem_solved_banner_text": "//li[@class='mzp-c-notification-bar mzp-t-success']/p"
    }

    # Problem solved locators.
    PROBLEM_SOLVED_LOCATORS = {
        "problem_solved_reply_text": "//div[@class='reply']/p",
        "problem_solved_reply_section": "//div[@class='solution card elevation-00']",
        "problem_solved_reply_section_header": "//h4[@class='is-solution']",
        "problem_solved_reply_reply_link": "//div[@class='reply']/a",
        "undo_solves_problem": "//input[@value='Undo']"
    }

    # Question locators.
    QUESTION_LOCATORS = {
        "question_author": "//div[@class='question']//span[@class='display-name']",
        "questions_header": "//h2[@class='sumo-callout-heading summary no-product-heading']",
        "question_body": "//div[@class='main-content']/div/p",
        "modified_question_section": "//p[@class='edited text-body-sm']"
    }

    # Progress bar locators.
    PROGRESS_BAR_LOCATORS = {
        "complete_progress_items_label": ("//li[@class='progress--item is-complete']//span"
                                          "[@class='progress--label']")
    }

    # Breadcrumbs locators.
    BREADCRUMB_LOCATORS = {
        "aaq_page_breadcrumbs": "//ol[@id='breadcrumbs']/li/a"
    }

    # Question details locators.
    QUESTION_DETAILS_LOCATORS = {
        "question_details_button": "//button[@aria-controls='question-details']",
        "more_system_details_modal": "//div[normalize-space(@class)='mzp-c-modal']",
        "more_system_details_option": "//a[@id='show-more-details']",
        "close_additional_system_details_button": "//div[@class='mzp-c-modal-close']/button",
        "user_agent_information": "//div[@class='about-support']//li",
        "question_section": "//article/div[@class='question']"
    }

    # Searchbar locators.
    SEARCHBAR_LOCATORS = {
        "search_support_searchbar": "//form[@id='support-search-sidebar']/input",
        "search_support_search_button": "//form[@id='support-search-sidebar']/button"
    }

    # Still need help widget locators.
    STILL_NEED_HELP_WIDGET_LOCATORS = {
        "still_need_help_ask_now_button": "//div[contains(@class,'aaq-widget')]//a"
    }

    # Question Tools locators.
    QUESTION_TOOLS_LOCATORS = {
        "edit_this_question_option": "//ul[@id='related-content']/li[@class='edit']/a",
        "stop_email_updates_option": "//ul[@id='related-content']/li[@class='email']/a",
        "subscribe_to_feed_option": "//ul[@id='related-content']/li[@class='rss']/a",
        "delete_this_question_option": "//ul[@id='related-content']//a[@class='delete']",
        "lock_this_question_option": "//a[@data-form='lock-form']",
        "archive_this_question_option": "//a[@data-form='archive-form']",
        "system_details_options": "//div[@id='system-details']/ul[@class='system']/li",
        "mark_as_spam_option": "//ul[@id='related-content']//form[@class='spam-form cf']/a"
    }

    # Tags section locators.
    TAGS_SECTION_LOCATORS = {
        "question_tags_options_for_non_moderators": "//li[@class='tag']/a",
        "question_tags_options_for_moderators": "//div[@class='ts-control']/div",
        "add_a_tag_input_field": "//input[contains(@id, 'tag-select')]"
    }

    # Post a reply section locators.
    POST_A_REPLY_SECTION_LOCATORS = {
        "post_a_reply_section_heading": "//h3[@class='sumo-card-heading']",
        "post_a_reply_textarea": "//textarea[@id='id_content']",
        "post_a_reply_textarea_bold_button": "//button[@title='Bold']",
        "post_a_reply_textarea_italic_button": "//button[@title='Italic']",
        "post_a_reply_textarea_link_button": "//button[@title='Insert a link...']",
        "post_a_reply_textarea_numbered_list_button": "//button[@title='Numbered List']",
        "post_a_reply_textarea_bulleted_list_button": "//button[@title='Bulleted List']",
        "last_reply_by": "//span[@class='forum--meta-val visits no-border']"
    }

    # Common Responses locators.
    COMMON_RESPONSES_LOCATORS = {
        "common_responses_option": "//a[@title='Common responses']",
        "common_responses_search_field": "//input[@id='filter-responses-field']",
        "common_responses_modal_close_button": "//div[@id='media-modal']/a",
        "common_responses_categories_options": "//div[@id='responses-area']//li",
        "common_responses_responses_options": ("//ul[@class='sidebar-nav']/li[@class='response' "
                                               "and not(@style='display: none;')]"),
        "common_responses_no_cat_selected": "//h4[@class='nocat-label']",
        "common_responses_switch_to_mode": "//div[@id='response-content-area']//button",
        "common_responses_response_preview": ("//p[@class='response-preview-rendered']//div["
                                              "@class='main-content']/div[@class='content']"),
        "common_responses_textarea_field": "//textarea[@id='response-content']",
        "common_responses_insert_response_button": "//button[@id='insert-response']",
        "common_responses_cancel_button": "//div[@id='response-submit-area']/a"
    }

    # I have this problem too locators.
    I_HAVE_THIS_PROBLEM_TOO_LOCATORS = {
        "i_have_this_problem_too_button": "//div[@class='me-too']//button",
        "i_have_this_problem_too_counter": "//span[@class='forum--meta-val have-problem']"
    }

    # Needs more information from the user locators.
    NEEDS_MORE_INFORMATION_LOCATORS = {
        "needs_more_information_from_the_user_checkbox": "//input[@id='id_needs_info']",
        "more_information_panel_header": ("//section[@id='more-system-details']//h3["
                                          "contains(text(),'More Information')]")
    }

    # Attached image locators.
    ATTACHED_IMAGE_LOCATORS = {
        "attached_image": "//a[@class='image']/img",
        "add_image_button": "//div[@class='field add-attachment']"
    }

    # Preview Reply button locators.
    PREVIEW_REPLY_LOCATORS = {
        "preview_reply_button": "//input[@id='preview']"
    }

    # Post Reply button locators.
    POST_REPLY_LOCATORS = {
        "post_reply_button": "//button[normalize-space(text())='Post Reply']"
    }

    # Delete question locators.
    DELETE_QUESTION_LOCATORS = {
        "delete_question_delete_button": "//input[@value='Delete']",
        "delete_question_cancel_button": "//a[contains(text(),'Cancel')]"
    }

    # Report abuse section.
    REPORT_ABUSE_LOCATORS = {
        "report_abuse_submit_button": "//div[@class='mzp-c-modal-inner']//button[@type='submit']",
        "report_abuse_textarea": "//div[@class='mzp-c-modal-inner']//textarea",
        "report_abuse_flagged_this_content_message": ("//div[@class='mzp-c-modal-inner']//span["
                                                      "@class='message']"),
        "report_abuse_modal_close_button": ("//div[@class='mzp-c-modal-inner']//button["
                                            "@class='mzp-c-modal-button-close']")
    }

    # Signed out card locators.
    SIGNED_OUT_CARD_LOCATORS = {
        "log_in_to_your_account_signed_out_card_option": ("//div[@class='question-tools "
                                                          "ask-a-question card is-shaded']/p/a["
                                                          "text()='log in to your account']"),
        "start_a_new_question_signed_out_card_option": ("//div[@class='question-tools "
                                                        "ask-a-question card is-shaded']/p/a"
                                                        "[text()='start a new question']"),
        "ask_a_question_signed_out_card_option": ("//div[@class='question-tools ask-a-question "
                                                  "card is-shaded']//a[text()='Ask a question']"),
        "i_have_this_problem_too_signed_out_card_option": ("//div[@class='question-tools "
                                                           "ask-a-question card is-shaded']//"
                                                           "button[text()='I have this problem, "
                                                           "too']")
    }

    def __init__(self, page: Page):
        super().__init__(page)

    # Spam marked banner actions.
    def get_text_of_spam_marked_banner(self) -> str:
        return self._get_text_of_element(self.BANNER_LOCATORS["reply_flagged_as_spam_banner"])

    def is_spam_marked_banner_displayed(self) -> bool:
        return self._is_element_visible(self.BANNER_LOCATORS["reply_flagged_as_spam_banner"])

    # Report abuse actions.
    def click_abuse_modal_close_button(self):
        self._click(self.REPORT_ABUSE_LOCATORS["report_abuse_modal_close_button"])

    def get_successful_flagged_this_content_text(self) -> str:
        return self._get_text_of_element(
            self.REPORT_ABUSE_LOCATORS["report_abuse_flagged_this_content_message"])

    def add_text_to_report_abuse_textarea(self, text: str):
        self._fill(self.REPORT_ABUSE_LOCATORS["report_abuse_textarea"], text)

    def click_on_report_abuse_submit_button(self):
        self._click(self.REPORT_ABUSE_LOCATORS["report_abuse_submit_button"])

    # Breadcrumbs actions.
    def get_current_breadcrumb_locator(self, question_title: str) -> Locator:
        return self._get_element_locator(f"//ol[@id='breadcrumbs']/li[text()='{question_title}'"
                                         f"]")

    def click_on_breadcrumb(self, breadcrumb_xpath: str):
        self._click(breadcrumb_xpath)

    # Get email updates actions.
    def get_email_updates_option(self) -> Locator:
        return self._get_element_locator(self.QUESTION_TOOLS_LOCATORS["stop_email_updates_option"])

    # Problem solved actions.
    def get_problem_solved_section_header_text(self) -> str:
        return self._get_text_of_element(
            self.PROBLEM_SOLVED_LOCATORS["problem_solved_reply_section_header"])

    def click_on_undo_button(self):
        self._click(self.PROBLEM_SOLVED_LOCATORS["undo_solves_problem"])

    def get_undo_button_locator(self) -> Locator:
        return self._get_element_locator(self.PROBLEM_SOLVED_LOCATORS["undo_solves_problem"])

    def click_read_this_answer_in_context_link(self):
        self._click(self.PROBLEM_SOLVED_LOCATORS["problem_solved_reply_reply_link"])

    def get_chosen_solution_text(self) -> str:
        return self._get_text_of_element(self.PROBLEM_SOLVED_LOCATORS["problem_solved_reply_text"])

    def get_chosen_solution_section_locator(self) -> Locator:
        return self._get_element_locator(
            self.PROBLEM_SOLVED_LOCATORS["problem_solved_reply_section"])

    def get_solved_problem_banner_text(self) -> str:
        return self._get_text_of_element(self.BANNER_LOCATORS["problem_solved_banner_text"])

    def get_solved_the_problem_button_locator(self, target_reply_id: str) -> Locator:
        return self._get_element_locator(f"//div[@id='{target_reply_id}']/"
                                         f"following-sibling::aside//input[@type='submit']")

    def get_chosen_solution_reply_message(self, reply_id: str) -> str:
        return self._get_text_of_element(f"//div[@id='{reply_id}']//h3[@class='is-solution']")

    def get_chosen_solution_reply_message_locator(self, reply_id: str) -> Locator:
        return self._get_element_locator(f"//div[@id='{reply_id}']//h3[@class='is-solution']")

    # I have this problem too actions.
    def get_i_have_this_problem_too_locator(self) -> Locator:
        return self._get_element_locator(
            self.I_HAVE_THIS_PROBLEM_TOO_LOCATORS["i_have_this_problem_too_button"])

    def click_i_have_this_problem_too_button(self):
        self._click(self.I_HAVE_THIS_PROBLEM_TOO_LOCATORS["i_have_this_problem_too_button"])

    def get_i_have_this_problem_too_counter(self) -> int:
        return int(self._get_text_of_element(
            self.I_HAVE_THIS_PROBLEM_TOO_LOCATORS["i_have_this_problem_too_counter"]))

    def get_last_reply_by_text(self) -> str:
        return self._get_text_of_element(self.POST_A_REPLY_SECTION_LOCATORS["last_reply_by"])

    # Page content actions.
    def get_question_header(self) -> str:
        return self._get_text_of_element(self.QUESTION_LOCATORS["questions_header"])

    def click_last_reply_by(self):
        self._click(self.POST_A_REPLY_SECTION_LOCATORS["last_reply_by"])

    def get_question_body(self) -> str:
        return self._get_text_of_element(self.QUESTION_LOCATORS["question_body"])

    def get_question_author_name(self) -> str:
        return self._get_text_of_element(self.QUESTION_LOCATORS["question_author"])

    def get_question_id(self) -> str:
        return self._get_element_attribute_value(
            self.QUESTION_DETAILS_LOCATORS["question_section"], 'id')

    def get_modified_question_locator(self) -> Locator:
        return self._get_element_locator(self.QUESTION_LOCATORS["modified_question_section"])

    def get_modified_by_text(self) -> str:
        return self._get_text_of_element(self.QUESTION_LOCATORS["modified_question_section"])

    def get_add_image_section_locator(self) -> Locator:
        return self._get_element_locator(self.ATTACHED_IMAGE_LOCATORS["add_image_button"])

    def click_on_my_questions_banner_option(self):
        self._click(self.BANNER_LOCATORS["posted_questions_success_banner_my_questions_link"])

    def click_on_solves_the_problem_button(self, target_reply_id: str):
        self._click(f"//div[@id='{target_reply_id}']/following-sibling::aside//"
                    f"input[@type='submit']")

    def is_post_reply_button_visible(self) -> ElementHandle:
        self._wait_for_selector(self.POST_REPLY_LOCATORS["post_reply_button"])
        return self._get_element_handle(self.POST_REPLY_LOCATORS["post_reply_button"])

    def click_on_the_reply_author(self, reply_id: str):
        self._click(f"//div[@id='{reply_id}']//a[@class='author-name']")

    def get_text_content_of_reply(self, reply_id: str) -> str:
        return self._get_text_of_element(f"//div[@id='{reply_id}']//div[@class='content']")

    def get_display_name_of_question_reply_author(self, reply_id: str) -> str:
        return self._get_text_of_element(f"//div[@id='{reply_id}']//a[@class='author-name']/"
                                         f"span[@class='display-name']")

    def get_displayed_user_title_of_question_reply_locator(self, reply_id: str) -> Locator:
        return self._get_element_locator(f"//div[@id='{reply_id}']//a[@class='author-name']/"
                                         f"span[@class='user-title']")

    def get_displayed_user_title_of_question_reply(self, reply_id: str) -> str:
        return self._get_text_of_element(f"//div[@id='{reply_id}']//a[@class='author-name']/"
                                         f"span[@class='user-title']")

    # Question tag actions.
    def get_question_tag_options(self, is_moderator: bool) -> list[str]:
        return [tag.replace("\n×", "") for tag in self._get_text_of_elements(
            self.
            TAGS_SECTION_LOCATORS["question_tags_options_for_moderators"] if is_moderator else self
            .TAGS_SECTION_LOCATORS["question_tags_options_for_non_moderators"])]

    def get_remove_tag_button_locator(self, tag_name: str) -> Locator:
        return self._get_element_locator(f"//div[@class='ts-control']/div[normalize-space("
                                         f"text())='{tag_name}']/a[@class='remove']")

    def add_text_to_add_a_tag_input_field(self, text: str):
        self._fill(self.TAGS_SECTION_LOCATORS["add_a_tag_input_field"], text)
        self._wait_for_given_timeout(2000)
        self._press_a_key(self.TAGS_SECTION_LOCATORS["add_a_tag_input_field"], "Enter")

    def get_add_a_tag_input_field(self) -> Locator:
        return self._get_element_locator(self.TAGS_SECTION_LOCATORS["add_a_tag_input_field"])

    def click_on_a_certain_tag(self, tag_name: str):
        self._click(f"//li[@class='tag']//a[text()='{tag_name}']",
                    expected_locator=ProductSupportForum.PAGE_LOCATORS["ask_the_community_button"])

    def get_a_certain_tag(self, tag_name: str) -> Locator:
        return self._get_element_locator(f"//div[@class='ts-control']/div[@class='item' and "
                                         f"normalize-space(text())='{tag_name}']")

    def click_on_tag_remove_button(self, tag_name: str):
        self._click(f"//div[@class='item' and normalize-space(text())='{tag_name}']/"
                    f"a[@class='remove']")

    # Attached image actions.
    def get_attached_image(self) -> Locator:
        return self._get_element_locator(self.ATTACHED_IMAGE_LOCATORS["attached_image"])

    # Question more information actions.
    def get_more_information_with_text_locator(self, text: str) -> Locator:
        return self._get_element_locator(f"//div[@class='about-support']/p[text()='{text}']")

    def get_question_details_button_locator(self) -> Locator:
        return self._get_element_locator(self.QUESTION_DETAILS_LOCATORS["question_details_button"])

    def get_more_information_locator(self) -> Locator:
        return self._get_element_locator(
            self.NEEDS_MORE_INFORMATION_LOCATORS["more_information_panel_header"])

    def get_user_agent_information(self) -> str:
        self._wait_for_selector(self.QUESTION_DETAILS_LOCATORS["more_system_details_modal"])
        return self._get_text_of_element(self.QUESTION_DETAILS_LOCATORS["user_agent_information"])

    def get_system_details_information(self) -> list[str]:
        return self._get_text_of_elements(self.QUESTION_TOOLS_LOCATORS["system_details_options"])

    def click_on_question_details_button(self):
        self._click(self.QUESTION_DETAILS_LOCATORS["question_details_button"])

    def click_on_more_system_details_option(self):
        self._click(self.QUESTION_DETAILS_LOCATORS["more_system_details_option"])

    def click_on_the_additional_system_panel_close(self):
        self._click(self.QUESTION_DETAILS_LOCATORS["close_additional_system_details_button"])

    def get_reply_section_locator(self, answer_id: str) -> Locator:
        return self._get_element_locator(f"//div[@id='{answer_id}']")

    def click_on_reply_more_options_button(self, answer_id: str):
        self._click(f"//div[@id='{answer_id}']//button[text()='more options']")

    def click_on_report_abuse_for_a_certain_reply(self, answer_id: str):
        self._click(f"//div[@id='{answer_id}']//a[text()='Report Abuse']")

    def get_click_on_report_abuse_reply_locator(self, answer_id: str) -> Locator:
        return self._get_element_locator(f"//div[@id='{answer_id}']//a[text()='Report Abuse']")

    def click_on_quote_for_a_certain_reply(self, answer_id: str):
        self._click(f"//div[@id='{answer_id}']//a[text()='Quote']")

    def get_quote_reply_locator(self, answer_id: str) -> Locator:
        return self._get_element_locator(f"//div[@id='{answer_id}']//a[text()='Quote']")

    def click_on_mark_as_spam_for_a_certain_reply(self, answer_id: str):
        self._click(f"//div[@id='{answer_id}']//form[@class='spam-form cf']/a")

    def get_mark_as_spam_reply_locator(self, answer_id: str) -> Locator:
        return self._get_element_locator(f"//div[@id='{answer_id}']//"
                                         f"form[@class='spam-form cf']/a")

    def get_marked_as_spam_locator(self, answer_id: str) -> Locator:
        return self._get_element_locator(f"//div[@id='{answer_id}']//h3[@class='is-spam']")

    def get_marked_as_spam_text(self, answer_id: str) -> str:
        return self._get_text_of_element(f"//div[@id='{answer_id}']//h3[@class='is-spam']")

    def click_on_edit_this_post_for_a_certain_reply(self, answer_id: str):
        self._click(f"//div[@id='{answer_id}']//a[text()='Edit this post']")

    def get_edit_this_post_reply_locator(self, answer_id: str) -> Locator:
        return self._get_element_locator(f"//div[@id='{answer_id}']//"
                                         f"a[text()='Edit this post']")

    def click_on_delete_this_post_for_a_certain_reply(self, answer_id: str):
        self._click(f"//div[@id='{answer_id}']//a[text()='Delete this post']")

    def get_delete_this_post_reply_locator(self, answer_id: str) -> Locator:
        return self._get_element_locator(f"//div[@id='{answer_id}']//"
                                         f"a[text()='Delete this post']")

    def click_on_cancel_delete_button(self):
        self._click(self.DELETE_QUESTION_LOCATORS["delete_question_cancel_button"])

    # Post a reply actions.
    def add_text_to_post_a_reply_textarea(self, text: str):
        self._fill(self.POST_A_REPLY_SECTION_LOCATORS["post_a_reply_textarea"], text)

    def type_inside_the_post_a_reply_textarea(self, text: str):
        self._type(self.POST_A_REPLY_SECTION_LOCATORS["post_a_reply_textarea"], text, 100)

    def get_post_a_reply_textarea_locator(self) -> Locator:
        return self._get_element_locator(
            self.POST_A_REPLY_SECTION_LOCATORS["post_a_reply_textarea"])

    def get_post_a_reply_textarea_text(self) -> str:
        return self._get_text_of_element(
            self.POST_A_REPLY_SECTION_LOCATORS["post_a_reply_textarea"])

    def get_post_a_reply_textarea_value(self) -> str:
        return self._get_element_input_value(
            self.POST_A_REPLY_SECTION_LOCATORS["post_a_reply_textarea"])

    def get_posted_reply_locator(self, question_id: str) -> Locator:
        return self._get_element_locator(f"//div[@id='{question_id}']")

    def get_posted_reply_text(self, reply_id: str) -> str:
        return self._get_text_of_element(f"//div[@id='{reply_id}']//div[@class='content']/p")

    def get_posted_quote_reply_username_text(self, reply_id: str) -> str:
        return self._get_text_of_element(f"//div[@id='{reply_id}']//div[@class='content']/em/p")

    def click_posted_reply_said_link(self, reply_id: str):
        self._click(f"//div[@id='{reply_id}']//div[@class='content']//a")

    def get_blockquote_reply_text(self, reply_id: str) -> str:
        return self._get_text_of_element(f"//div[@id='{reply_id}']//div[@class='content']//"
                                         f"blockquote")

    def get_posted_reply_modified_by_text(self, reply_id: str) -> str:
        return self._get_text_of_element(f"//div[@id='{reply_id}']//"
                                         f"p[@class='edited text-body-sm']/em")

    def get_posted_reply_modified_by_locator(self, reply_id: str) -> Locator:
        return self._get_element_locator(f"//div[@id='{reply_id}']//"
                                         f"p[@class='edited text-body-sm']/em")

    def click_on_post_reply_button(self, repliant_username) -> str:
        self._click(self.POST_REPLY_LOCATORS["post_reply_button"],
                    expected_locator=f"//span[@class='display-name' and contains(text(), "
                                     f"'{repliant_username}')]")
        return self._get_element_attribute_value("(//span[@class='display-name' and "
                                                 f"contains(text(), '{repliant_username}')]"
                                                 "/ancestor::div[@class='answer '])[last()]",
                                                 "id")

    # Question Tools actions.
    def get_edit_this_question_option_locator(self) -> Locator:
        return self._get_element_locator(self.QUESTION_TOOLS_LOCATORS["edit_this_question_option"])

    def get_delete_this_question_locator(self) -> Locator:
        return self._get_element_locator(
            self.QUESTION_TOOLS_LOCATORS["delete_this_question_option"])

    def get_lock_this_question_locator(self) -> Locator:
        return self._get_element_locator(self.QUESTION_TOOLS_LOCATORS["lock_this_question_option"])

    # Stands for archived banner as well
    def get_thread_locked_text(self) -> str:
        return self._get_text_of_element(self.BANNER_LOCATORS["lock_this_thread_banner"])

    def get_thread_locked_locator(self) -> Locator:
        return self._get_element_locator(self.BANNER_LOCATORS["lock_this_thread_banner"])

    def get_archive_this_question_locator(self) -> Locator:
        return self._get_element_locator(
            self.QUESTION_TOOLS_LOCATORS["archive_this_question_option"])

    def get_needs_more_information_checkbox_locator(self) -> Locator:
        return self._get_element_locator(
            self.NEEDS_MORE_INFORMATION_LOCATORS["needs_more_information_from_the_user_checkbox"])

    def get_mark_as_spam_locator(self) -> Locator:
        return self._get_element_locator(self.QUESTION_TOOLS_LOCATORS["mark_as_spam_option"])

    def get_marked_as_spam_banner_locator(self) -> Locator:
        return self._get_element_locator(self.BANNER_LOCATORS["marked_as_spam_banner"])

    def get_marked_as_spam_banner_text(self) -> str:
        return self._get_text_of_element(self.BANNER_LOCATORS["marked_as_spam_banner"])

    def click_on_thread_locked_link(self):
        self._click(self.BANNER_LOCATORS["lock_this_thread_banner_link"])

    def click_on_lock_this_question_locator(self):
        self._click(self.QUESTION_TOOLS_LOCATORS["lock_this_question_option"])

    def click_on_subscribe_to_feed_option(self):
        self._click(self.QUESTION_TOOLS_LOCATORS["subscribe_to_feed_option"])

    def click_on_mark_as_spam_option(self):
        self._click(self.QUESTION_TOOLS_LOCATORS["mark_as_spam_option"])

    def click_on_edit_this_question_question_tools_option(self):
        self._click(self.QUESTION_TOOLS_LOCATORS["edit_this_question_option"])

    def click_delete_this_question_question_tools_option(self):
        self._click(self.QUESTION_TOOLS_LOCATORS["delete_this_question_option"])

    def click_on_archive_this_question_option(self):
        self._click(self.QUESTION_TOOLS_LOCATORS["archive_this_question_option"])

    def click_delete_this_question_button(self):
        self._click(self.DELETE_QUESTION_LOCATORS["delete_question_delete_button"])

    def is_reply_displayed(self, reply_id: str) -> bool:
        return self._is_element_visible(f"//div[@id='{reply_id}']")

    def is_reply_with_content_displayed(self, reply_content: str) -> bool:
        return self._is_element_visible(f"//div[@class='content']/p[normalize-space(text()"
                                        f")='{reply_content}']")

    # Votes reply section
    def get_reply_votes_section_locator(self, reply_id: str) -> Locator:
        return self._get_element_locator(f"//div[@id='{reply_id}']//"
                                         f"form[@class='document-vote--form helpful']")

    def get_reply_vote_heading(self, reply_id: str) -> str:
        return self._get_text_of_element(f"//div[@id='{reply_id}']//"
                                         f"h4[@class='document-vote--heading']")

    def click_reply_vote_thumbs_up_button(self, reply_id: str):
        return self._click(f"//div[@id='{reply_id}']//button[@name='helpful']")

    def get_thumbs_up_vote_message(self, reply_id: str) -> str:
        return self._get_text_of_element(f"//div[@id='{reply_id}']//"
                                         f"p[@class='msg document-vote--heading']")

    def get_thumbs_up_button_locator(self, reply_id: str) -> Locator:
        return self._get_element_locator(f"//div[@id='{reply_id}']//button[@name='helpful']")

    def get_thumbs_down_button_locator(self, reply_id: str) -> Locator:
        return self._get_element_locator(f"//div[@id='{reply_id}']//"
                                         f"button[@name='not-helpful']")

    def click_reply_vote_thumbs_down_button(self, reply_id):
        self._click(f"//div[@id='{reply_id}']//button[@name='not-helpful']")

    def get_helpful_count(self, reply_id) -> str:
        return self._get_text_of_element(f"//div[@id='{reply_id}']//"
                                         f"button[@name='helpful']//"
                                         f"strong[@class='helpful-count']")

    def get_not_helpful_count(self, reply_id) -> str:
        return self._get_text_of_element(f"//div[@id='{reply_id}']//"
                                         f"button[@name='not-helpful']//"
                                         f"strong[@class='helpful-count']")

    # Signed out card actions.
    def click_on_log_in_to_your_account_signed_out_card_link(self):
        self._click(self.SIGNED_OUT_CARD_LOCATORS["log_in_to_your_account_signed_out_card_option"])

    def click_on_start_a_new_question_signed_out_card_link(self):
        self._click(self.SIGNED_OUT_CARD_LOCATORS["start_a_new_question_signed_out_card_option"])

    def click_on_ask_a_question_signed_out_card_option(self):
        self._click(self.SIGNED_OUT_CARD_LOCATORS["ask_a_question_signed_out_card_option"])

    def ask_a_question_signed_out_card_option_locator(self) -> Locator:
        return self._get_element_locator(
            self.SIGNED_OUT_CARD_LOCATORS["ask_a_question_signed_out_card_option"])

    def click_on_i_have_this_problem_too_signed_out_card_option(self):
        self._click(
            self.SIGNED_OUT_CARD_LOCATORS["i_have_this_problem_too_signed_out_card_option"])

    def get_i_have_this_problem_too_signed_out_card_locator(self) -> Locator:
        return self._get_element_locator(
            self.SIGNED_OUT_CARD_LOCATORS["i_have_this_problem_too_signed_out_card_option"])

    # Common responses actions.

    def click_on_common_responses_option(self):
        self._click(self.COMMON_RESPONSES_LOCATORS["common_responses_option"])

    def type_into_common_responses_search_field(self, text: str):
        self._type(
            self.COMMON_RESPONSES_LOCATORS["common_responses_search_field"], text, 100)

    def get_text_of_no_cat_responses(self) -> str:
        return self._get_text_of_element(
            self.COMMON_RESPONSES_LOCATORS["common_responses_no_cat_selected"])

    def get_list_of_categories(self) -> list[str]:
        return self._get_text_of_elements(
            self.COMMON_RESPONSES_LOCATORS["common_responses_categories_options"])

    def get_list_of_responses(self) -> list[str]:
        return self._get_text_of_elements(
            self.COMMON_RESPONSES_LOCATORS["common_responses_responses_options"])

    def click_on_a_particular_category_option(self, option: str):
        self._click(f"//ul[@class='category-list']/li[text()='{option}']")

    def click_on_a_particular_response_option(self, option: str):
        self._click(f"//ul[@class='sidebar-nav']/li[text()='{option}']")

    # Removing both newline characters and link syntax format.
    def get_text_of_response_editor_textarea_field(self) -> str:
        return (self._get_element_input_value(
            self.COMMON_RESPONSES_LOCATORS["common_responses_textarea_field"])
            .replace("\n", "")
            .replace("[", "")
            .replace("]", "")
        )

    def get_text_of_response_preview(self) -> str:
        return self._get_text_of_element(
            self.COMMON_RESPONSES_LOCATORS["common_responses_response_preview"])

    def click_on_switch_to_mode(self):
        self._click(self.COMMON_RESPONSES_LOCATORS["common_responses_switch_to_mode"])

    def click_on_common_responses_cancel_button(self):
        self._click(self.COMMON_RESPONSES_LOCATORS["common_responses_cancel_button"])

    def click_on_common_responses_insert_response_button(self):
        self._click(self.COMMON_RESPONSES_LOCATORS["common_responses_insert_response_button"])

    def get_time_from_reply(self, reply_id: str) -> str:
        """Returns the time displayed inside the question for when a reply was made.

        Args:
            reply_id (str): The reply id.
        """
        return self._get_text_of_element(f"//div[@id='{reply_id}']//time/time")
