from playwright.sync_api import ElementHandle, Locator, Page

from playwright_tests.core.basepage import BasePage


class QuestionPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        # Breadcrumb locators.
        self.question_breadcrumb = lambda question_title: page.locator(
            "ol#breadcrumbs").get_by_role("listitem", name=question_title, exact=True)
        # "Posted successfully" green banner locators.
        self.posted_questions_success_banner_message = page.locator(
            "ul[class='user-messages'] li p")
        self.posted_questions_success_banner_my_questions_link = page.locator(
            "ul[class='user-messages'] li p a")
        self.posted_questions_success_banner_close_button = page.locator(
            "ul[class='user-messages'] li button")
        self.reply_flagged_as_spam_banner = page.locator(
            "li[class='mzp-c-notification-bar mzp-t-warning'] p")
        self.marked_as_spam_banner = page.locator("p[class='is-spam']")
        self.lock_this_thread_banner = page.locator(
            "div[class='notice mzp-c-notification-bar mzp-t-click'] p")
        self.lock_this_thread_banner_link = page.locator(
            "div[class='notice mzp-c-notification-bar mzp-t-click'] p a")
        self.problem_solved_banner_text = page.locator(
            "li[class='mzp-c-notification-bar mzp-t-success'] p")

        # Problem solved locators.
        self.problem_solved_reply_text = page.locator("div[class='reply'] p")
        self.problem_solved_reply_section = page.locator("div[class='solution card elevation-00']")
        self.problem_solved_reply_section_header = page.locator("h4[class='is-solution']")
        self.problem_solved_reply_reply_link = page.locator("div[class='reply'] a")
        self.undo_solves_problem = page.locator("input[value='Undo']")
        self.reply_solves_the_problem = lambda target_reply_id: page.locator(
            f"div#{target_reply_id} + aside input[type='submit']")
        self.reply_solution_header = lambda reply_id: page.locator(
            f"div#{reply_id} h3[class='is-solution']")

        # Question locators.
        self.question_author = page.locator("div[class='question'] span[class='display-name']")
        self.questions_header = page.locator(
            "h2[class='sumo-callout-heading summary no-product-heading']")
        self.question_body = page.locator("div[class='main-content'] div p")
        self.modified_question_section = page.locator("p[class='edited text-body-sm']")
        self.question = lambda question_id: page.locator(f"div#{question_id}")

        # Progress bar locators.
        self.complete_progress_items_label = page.locator(
            "li[class='progress--item is-complete'] span[class='progress--label']")

        # Breadcrumbs locators.
        self.aaq_page_breadcrumbs = page.locator("ol#breadcrumbs li a")

        # Question details locators.
        self.question_details_button = page.locator("button[aria-controls='question-details']")
        self.more_system_details_modal = page.locator("div[class='mzp-c-modal']")
        self.more_system_details_option = page.locator("a#show-more-details")
        self.close_additional_system_details_button = page.locator(
            "div[class='mzp-c-modal-close'] button")
        self.user_agent_information = page.locator("div[class='about-support'] li")
        self.more_information_with_text = lambda text: page.locator(
            "div[class='about-support'] p").get_by_text(text, exact=True)
        self.question_section = page.locator("article div[class='question']")

        # Searchbar locators.
        self.search_support_searchbar = page.locator("form#support-search-sidebar input")
        self.search_support_search_button = page.locator("form#support-search-sidebar button")

        # Question Tools locators.
        self.edit_this_question_option = page.locator("ul#related-content li[class='edit'] a")
        self.stop_email_updates_option = page.locator("ul#related-content li[class='email'] a")
        self.subscribe_to_feed_option = page.locator("ul#related-content li[class='rss'] a")
        self.delete_this_question_option = page.locator("ul#related-content a[class='delete']")
        self.lock_this_question_option = page.locator("a[data-form='lock-form']")
        self.archive_this_question_option = page.locator("a[data-form='archive-form']")
        self.system_details_options = page.locator("div#system-details ul[class='system'] li")
        self.mark_as_spam_option = page.locator("ul#related-content form[class='spam-form cf'] a")

        # Tags section locators.
        self.question_tags_options_for_non_moderators = page.locator("li[class='tag'] a")
        self.question_tags_options_for_moderators = page.locator("div[class='ts-control'] div")
        self.add_a_tag_input_field = page.locator("input[id*='tag-select']")
        self.tag_by_name = lambda tag_name:page.locator("li[class='tag']").get_by_role(
            "link", name=tag_name, exact=True)
        self.remove_tag_button = lambda tag_name: page.locator(
            f"//div[@class='ts-control']/div[normalize-space(text())='{tag_name}']/a"
            f"[@class='remove']")
        self.tag = lambda tag_name: page.locator(
            f"//div[@class='ts-control']/div[@class='item' and normalize-space("
            f"text())='{tag_name}']")
        self.delete_tag = lambda tag_name: page.locator(
            f"//div[@class='item' and normalize-space(text())='{tag_name}']/a[@class='remove']")

        # Post a reply section locators.
        self.post_a_reply_section_heading = page.locator("h3[class='sumo-card-heading']")
        self.post_a_reply_textarea = page.locator("textarea#id_content")
        self.post_a_reply_textarea_bold_button = page.locator("button[title='Bold']")
        self.post_a_reply_textarea_italic_button = page.locator("button[title='Italic']")
        self.post_a_reply_textarea_link_button = page.locator("button[title='Insert a link...']")
        self.post_a_reply_textarea_numbered_list_button = page.locator(
            "button[title='Numbered List']")
        self.post_a_reply_textarea_bulleted_list_button = page.locator(
            "button[title='Bulleted List']")
        self.last_reply_by = page.locator("span[class='forum--meta-val visits no-border']")
        self.reply_author = lambda reply_id: page.locator(f"div#{reply_id} a[class='author-name']")
        self.reply_context = lambda reply_id: page.locator(f"div#{reply_id} div[class='content']")
        self.reply_author_display_name = lambda reply_id: page.locator(
            f"div#{reply_id} a[class='author-name'] span[class='display-name']")
        self.reply_user_title = lambda reply_id: page.locator(
            f"div#{reply_id} a[class='author-name'] span[class='user-title']")
        self.reply_section = lambda answer_id: page.locator(f"div#{answer_id}")
        self.more_options_for_answer = lambda answer_id: page.locator(
            f"div#{answer_id}").get_by_role("button", name="more options", exact=True)
        self.quote_reply = lambda answer_id: page.locator(f"div#{answer_id}").get_by_role(
            "link", name="Quote", exact=True)
        self.mark_reply_as_spam = lambda answer_id: page.locator(
            f"//div[@id='{answer_id}']//form[@class='spam-form cf']/a")
        self.marked_as_spam = lambda answer_id: page.locator(
            f"//div[@id='{answer_id}']//h3[@class='is-spam']")
        self.edit_this_post_for_answer = lambda answer_id: page.locator(
            f"div#{answer_id}").get_by_role("link", name="Edit this post", exact=True)
        self.delete_this_post_for_answer = lambda answer_id: page.locator(
            f"div#{answer_id}").get_by_role("link", name="Delete this post", exact=True)
        self.posted_reply_text = lambda reply_id: page.locator(
            f"//div[@id='{reply_id}']//div[@class='content']/p")
        self.username_of_posted_quote_owner = lambda reply_id: page.locator(
            f"div#{reply_id} div[class='content'] em p")
        self.posted_reply_said_link = lambda reply_id: page.locator(
            f"div#{reply_id} div[class='content'] a")
        self.blockquote_reply = lambda reply_id: page.locator(
            f"div#{reply_id} div[class='content'] blockquote")
        self.modified_by_text = lambda reply_id: page.locator(
            f"div#{reply_id} p[class='edited text-body-sm'] em")
        self.repliant_username = lambda repliant_username: page.locator(
            f"(//div[contains(@id,'answer')]//span[@class='display-name' and contains("
            f"text(), '{repliant_username}')])[last()]")
        self.answer_by_username = lambda repliant_username: page.locator(
            f"(//span[@class='display-name' and contains(text(), '{repliant_username}')]"
            f"/ancestor::div[@class='answer '])[last()]"
        )
        self.reply = lambda reply_id: page.locator(f"div#{reply_id}")
        self.reply_by_content = lambda reply_content: page.locator(
            "div[class='content'] p").get_by_text(reply_content, exact=True)
        self.reply_vote_section = lambda reply_id: page.locator(
            f"div#{reply_id} form[class='document-vote--form helpful']")
        self.reply_vote_heading = lambda reply_id: page.locator(
            f"div#{reply_id} h4[class='document-vote--heading']")
        self.reply_vote_thumbs_up = lambda reply_id: page.locator(
            f"div#{reply_id} button[name='helpful']")
        self.reply_vote_thumbs_up_message = lambda reply_id: page.locator(
            f"div#{reply_id} p[class='msg document-vote--heading']")
        self.reply_vote_thumbs_down = lambda reply_id: page.locator(
            f"div#{reply_id} button[name='not-helpful']")
        self.helpful_count = lambda reply_id: page.locator(
            f"div#{reply_id} button[name='helpful'] strong[class='helpful-count']")
        self.unhelpful_count = lambda reply_id: page.locator(
            f"div#{reply_id} button[name='not-helpful'] strong[class='helpful-count']")
        self.response_time = lambda reply_id: page.locator(f"div#{reply_id} time time")

        # Common Responses locators.
        self.common_responses_option = page.locator("a[title='Common responses']")
        self.common_responses_search_field = page.locator("input#filter-responses-field")
        self.common_responses_modal_close_button = page.locator("div#media-modal a")
        self.common_responses_categories_options = page.locator("div#responses-area li")
        self.common_responses_responses_options = page.locator(
            "//ul[@class='sidebar-nav']/li[@class='response' and not(@style='display: none;')]")
        self.common_responses_no_cat_selected = page.locator("h4[class='nocat-label']")
        self.common_responses_switch_to_mode = page.locator("div#response-content-area button")
        self.common_responses_response_preview = page.locator(
            "p[class='response-preview-rendered'] div[class='main-content'] div[class='content']")
        self.common_responses_textarea_field = page.locator("textarea#response-content")
        self.common_responses_insert_response_button = page.locator("button#insert-response")
        self.common_responses_cancel_button = page.locator("div#response-submit-area a")
        self.category_option = lambda option: page.locator(
            "ul[class='category-list'] li").get_by_text(option, exact=True)
        self.response_option = lambda option: page.locator(
            "ul[class='sidebar-nav'] li").get_by_text(option, exact=True)

        # I have this problem too locators.
        self.i_have_this_problem_too_button = page.locator("div[class='me-too'] button")
        self.i_have_this_problem_too_counter = page.locator(
            "span[class='forum--meta-val have-problem']")

        # Needs more information from the user locators.
        self.needs_more_information_from_the_user_checkbox = page.locator("input#id_needs_info")
        self.more_information_panel_header = page.locator(
            "section#more-system-details").get_by_role("heading").filter(
            has_text="More Information")

        # Attached image locators.
        self.attached_image = page.locator("a[class='image'] img")
        self.add_image_button = page.locator("div[class='field add-attachment']")

        # Preview Reply button locators.
        self.preview_reply_button = page.locator("input#preview")

        # Post Reply button locators.
        self.post_reply_button = page.get_by_role("button", name="Post Reply", exact=True)

        # Delete question locators.
        self.delete_question_delete_button = page.locator("input[value='Delete']")
        self.delete_question_cancel_button = page.get_by_role("link").filter(has_text="Cancel")

        # Report abuse section.
        self.report_abuse_submit_button = page.locator(
            "div[class='mzp-c-modal-inner'] button[type='submit']")
        self.report_abuse_textarea = page.locator("div[class='mzp-c-modal-inner'] textarea")
        self.report_abuse_flagged_this_content_message = page.locator(
            "div[class='mzp-c-modal-inner'] span[class='message']")
        self.report_abuse_modal_close_button = page.locator(
            "div[class='mzp-c-modal-inner'] button[class='mzp-c-modal-button-close']")
        self.report_answer_as_abuse = lambda answer_id: page.locator(
            f"div#{answer_id}").get_by_role("link", name="Report Abuse", exact=True)

        # Signed out card locators.
        self.log_in_to_your_account_signed_out_card_option = page.locator(
            "div[class='question-tools ask-a-question card is-shaded'] p").get_by_role(
            "link", name="log in to your account", exact=True)
        self.start_a_new_question_signed_out_card_option = page.locator(
            "div[class='question-tools ask-a-question card is-shaded'] p").get_by_role(
            "link", name="start a new question", exact=True)
        self.ask_a_question_signed_out_card_option = page.locator(
            "div[class='question-tools ask-a-question card is-shaded']").get_by_role(
            "link", name="Ask a question", exact=True)
        self.i_have_this_problem_too_signed_out_card_option = page.locator(
            "div[class='question-tools ask-a-question card is-shaded']").get_by_role(
            "button", name="I have this problem, too", exact=True)

    # Spam marked banner actions.
    def get_text_of_spam_marked_banner(self) -> str:
        return self._get_text_of_element(self.reply_flagged_as_spam_banner)

    def is_spam_marked_banner_displayed(self) -> bool:
        return self._is_element_visible(self.reply_flagged_as_spam_banner)

    # Report abuse actions.
    def click_abuse_modal_close_button(self):
        self._click(self.report_abuse_modal_close_button)

    def get_successful_flagged_this_content_text(self) -> str:
        return self._get_text_of_element(self.report_abuse_flagged_this_content_message)

    def add_text_to_report_abuse_textarea(self, text: str):
        self._fill(self.report_abuse_textarea, text)

    def click_on_report_abuse_submit_button(self):
        self._click(self.report_abuse_submit_button)

    # Breadcrumbs actions.
    def get_current_breadcrumb_locator(self, question_title: str) -> Locator:
        return self.question_breadcrumb(question_title)

    def click_on_breadcrumb(self, breadcrumb_xpath: str):
        self._click(breadcrumb_xpath)

    # Get email updates actions.
    def get_email_updates_option(self) -> Locator:
        return self.stop_email_updates_option

    # Problem solved actions.
    def get_problem_solved_section_header_text(self) -> str:
        return self._get_text_of_element(self.problem_solved_reply_section_header)

    def click_on_undo_button(self):
        self._click(self.undo_solves_problem)

    def get_undo_button_locator(self) -> Locator:
        return self.undo_solves_problem

    def click_read_this_answer_in_context_link(self):
        self._click(self.problem_solved_reply_reply_link)

    def get_chosen_solution_text(self) -> str:
        return self._get_text_of_element(self.problem_solved_reply_text)

    def get_chosen_solution_section_locator(self) -> Locator:
        return self.problem_solved_reply_section

    def get_solved_problem_banner_text(self) -> str:
        return self._get_text_of_element(self.problem_solved_banner_text)

    def get_solved_the_problem_button_locator(self, target_reply_id: str) -> Locator:
        return self.reply_solves_the_problem(target_reply_id)

    def get_chosen_solution_reply_message(self, reply_id: str) -> str:
        return self._get_text_of_element(self.reply_solution_header(reply_id))

    def get_chosen_solution_reply_message_locator(self, reply_id: str) -> Locator:
        return self.reply_solution_header(reply_id)

    # I have this problem too actions.
    def get_i_have_this_problem_too_locator(self) -> Locator:
        return self.i_have_this_problem_too_button

    def click_i_have_this_problem_too_button(self):
        self._click(self.i_have_this_problem_too_button)

    def get_i_have_this_problem_too_counter(self) -> int:
        return int(self._get_text_of_element(self.i_have_this_problem_too_counter))

    def get_last_reply_by_text(self) -> str:
        return self._get_text_of_element(self.last_reply_by)

    # Page content actions.
    def get_question_header(self) -> str:
        return self._get_text_of_element(self.questions_header)

    def click_last_reply_by(self):
        self._click(self.last_reply_by)

    def get_question_body(self) -> str:
        return self._get_text_of_element(self.question_body)

    def get_question_author_name(self) -> str:
        return self._get_text_of_element(self.question_author)

    def get_question_id(self) -> str:
        return self._get_element_attribute_value(self.question_section, 'id')

    def get_modified_question_locator(self) -> Locator:
        return self.modified_question_section

    def get_modified_by_text(self) -> str:
        return self._get_text_of_element(self.modified_question_section)

    def get_add_image_section_locator(self) -> Locator:
        return self.add_image_button

    def click_on_my_questions_banner_option(self):
        self._click(self.posted_questions_success_banner_my_questions_link)

    def click_on_solves_the_problem_button(self, target_reply_id: str):
        self._click(self.reply_solves_the_problem(target_reply_id))

    def is_post_reply_button_visible(self) -> ElementHandle:
        self._wait_for_locator(self.post_reply_button)
        return self._get_element_handle(self.post_reply_button)

    def click_on_the_reply_author(self, reply_id: str):
        self._click(self.reply_author(reply_id))

    def get_text_content_of_reply(self, reply_id: str) -> str:
        return self._get_text_of_element(self.reply_context(reply_id))

    def get_display_name_of_question_reply_author(self, reply_id: str) -> str:
        return self._get_text_of_element(self.reply_author_display_name(reply_id))

    def get_displayed_user_title_of_question_reply_locator(self, reply_id: str) -> Locator:
        return self.reply_user_title(reply_id)

    def get_displayed_user_title_of_question_reply(self, reply_id: str) -> str:
        return self._get_text_of_element(self.reply_user_title(reply_id))

    # Question tag actions.
    def get_question_tag_options(self, is_moderator: bool) -> list[str]:
        return [tag.replace("\n×", "") for tag in self._get_text_of_elements(
            self.question_tags_options_for_moderators if is_moderator else self
            .question_tags_options_for_non_moderators)]

    def get_remove_tag_button_locator(self, tag_name: str) -> Locator:
        return self.remove_tag_button(tag_name)

    def add_text_to_add_a_tag_input_field(self, text: str):
        self._fill(self.add_a_tag_input_field, text)
        self._wait_for_given_timeout(2000)
        self._press_a_key(self.add_a_tag_input_field, "Enter")

    def get_add_a_tag_input_field(self) -> Locator:
        return self.add_a_tag_input_field

    def click_on_a_certain_tag(self, tag_name: str, expected_locator):
        self._click(self.tag_by_name(tag_name), expected_locator=expected_locator)

    def get_a_certain_tag(self, tag_name: str) -> Locator:
        return self.tag(tag_name)

    def click_on_tag_remove_button(self, tag_name: str):
        self._click(self.delete_tag(tag_name))

    # Attached image actions.
    def get_attached_image(self) -> Locator:
        return self.attached_image

    # Question more information actions.
    def get_more_information_with_text_locator(self, text: str) -> Locator:
        return self.more_information_with_text(text)

    def get_question_details_button_locator(self) -> Locator:
        return self.question_details_button

    def get_more_information_locator(self) -> Locator:
        return self.more_information_panel_header

    def get_user_agent_information(self) -> str:
        self._wait_for_locator(self.more_system_details_modal)
        return self._get_text_of_element(self.user_agent_information)

    def get_system_details_information(self) -> list[str]:
        return self._get_text_of_elements(self.system_details_options)

    def click_on_question_details_button(self):
        self._click(self.question_details_button)

    def click_on_more_system_details_option(self):
        self._click(self.more_system_details_option)

    def click_on_the_additional_system_panel_close(self):
        self._click(self.close_additional_system_details_button)

    def get_reply_section_locator(self, answer_id: str) -> Locator:
        return self.reply_section(answer_id)

    def click_on_reply_more_options_button(self, answer_id: str):
        self._click(self.more_options_for_answer(answer_id))

    def click_on_report_abuse_for_a_certain_reply(self, answer_id: str):
        self._click(self.report_answer_as_abuse(answer_id))

    def get_click_on_report_abuse_reply_locator(self, answer_id: str) -> Locator:
        return self.report_answer_as_abuse(answer_id)

    def click_on_quote_for_a_certain_reply(self, answer_id: str):
        self._click(self.quote_reply(answer_id))

    def get_quote_reply_locator(self, answer_id: str) -> Locator:
        return self.quote_reply(answer_id)

    def click_on_mark_as_spam_for_a_certain_reply(self, answer_id: str):
        self._click(self.mark_reply_as_spam(answer_id))

    def get_mark_as_spam_reply_locator(self, answer_id: str) -> Locator:
        return self.mark_reply_as_spam(answer_id)

    def get_marked_as_spam_locator(self, answer_id: str) -> Locator:
        return self.marked_as_spam(answer_id)

    def get_marked_as_spam_text(self, answer_id: str) -> str:
        return self._get_text_of_element(self.marked_as_spam(answer_id))

    def click_on_edit_this_post_for_a_certain_reply(self, answer_id: str):
        self._click(self.edit_this_post_for_answer(answer_id))

    def get_edit_this_post_reply_locator(self, answer_id: str) -> Locator:
        return self.edit_this_post_for_answer(answer_id)

    def click_on_delete_this_post_for_a_certain_reply(self, answer_id: str):
        self._click(self.delete_this_post_for_answer(answer_id))

    def get_delete_this_post_reply_locator(self, answer_id: str) -> Locator:
        return self.delete_this_post_for_answer(answer_id)

    def click_on_cancel_delete_button(self):
        self._click(self.delete_question_cancel_button)

    # Post a reply actions.
    def add_text_to_post_a_reply_textarea(self, text: str):
        self._fill(self.post_a_reply_textarea, text)

    def type_inside_the_post_a_reply_textarea(self, text: str):
        self._type(self.post_a_reply_textarea, text, 100)

    def get_post_a_reply_textarea_locator(self) -> Locator:
        return self.post_a_reply_textarea

    def get_post_a_reply_textarea_text(self) -> str:
        return self._get_text_of_element(self.post_a_reply_textarea)

    def get_post_a_reply_textarea_value(self) -> str:
        return self._get_element_input_value(self.post_a_reply_textarea)

    def get_posted_reply_locator(self, question_id: str) -> Locator:
        return self.question(question_id)

    def get_posted_reply_text(self, reply_id: str) -> str:
        return self._get_text_of_element(self.posted_reply_text(reply_id))

    def get_posted_quote_reply_username_text(self, reply_id: str) -> str:
        return self._get_text_of_element(self.username_of_posted_quote_owner(reply_id))

    def click_posted_reply_said_link(self, reply_id: str):
        self._click(self.posted_reply_said_link(reply_id))

    def get_blockquote_reply_text(self, reply_id: str) -> str:
        return self._get_text_of_element(self.blockquote_reply(reply_id))

    def get_posted_reply_modified_by_text(self, reply_id: str) -> str:
        return self._get_text_of_element(self.modified_by_text(reply_id))

    def get_posted_reply_modified_by_locator(self, reply_id: str) -> Locator:
        return self.modified_by_text(reply_id)

    def click_on_post_reply_button(self, repliant_username) -> str:
        self._click(self.post_reply_button,
                    expected_locator=self.repliant_username(repliant_username))
        return self._get_element_attribute_value(self.answer_by_username(repliant_username), "id")

    # Question Tools actions.
    def get_edit_this_question_option_locator(self) -> Locator:
        return self.edit_this_question_option

    def get_delete_this_question_locator(self) -> Locator:
        return self.delete_this_question_option

    def get_lock_this_question_locator(self) -> Locator:
        return self.lock_this_question_option

    # Stands for archived banner as well
    def get_thread_locked_text(self) -> str:
        return self._get_text_of_element(self.lock_this_thread_banner)

    def get_thread_locked_locator(self) -> Locator:
        return self.lock_this_thread_banner

    def get_archive_this_question_locator(self) -> Locator:
        return self.archive_this_question_option

    def get_needs_more_information_checkbox_locator(self) -> Locator:
        return self.needs_more_information_from_the_user_checkbox

    def get_mark_as_spam_locator(self) -> Locator:
        return self.mark_as_spam_option

    def get_marked_as_spam_banner_locator(self) -> Locator:
        return self.marked_as_spam_banner

    def get_marked_as_spam_banner_text(self) -> str:
        return self._get_text_of_element(self.marked_as_spam_banner)

    def click_on_thread_locked_link(self):
        self._click(self.lock_this_thread_banner_link)

    def click_on_lock_this_question_locator(self):
        self._click(self.lock_this_question_option)

    def click_on_subscribe_to_feed_option(self):
        self._click(self.subscribe_to_feed_option)

    def click_on_mark_as_spam_option(self):
        self._click(self.mark_as_spam_option)

    def click_on_edit_this_question_question_tools_option(self):
        self._click(self.edit_this_question_option)

    def click_delete_this_question_question_tools_option(self):
        self._click(self.delete_this_question_option)

    def click_on_archive_this_question_option(self):
        self._click(self.archive_this_question_option)

    def click_delete_this_question_button(self):
        self._click(self.delete_question_delete_button)

    def is_reply_displayed(self, reply_id: str) -> bool:
        return self._is_element_visible(self.reply(reply_id))

    def is_reply_with_content_displayed(self, reply_content: str) -> bool:
        return self._is_element_visible(self.reply_by_content(reply_content))

    # Votes reply section
    def get_reply_votes_section_locator(self, reply_id: str) -> Locator:
        return self.reply_vote_section(reply_id)

    def get_reply_vote_heading(self, reply_id: str) -> str:
        return self._get_text_of_element(self.reply_vote_heading(reply_id))

    def click_reply_vote_thumbs_up_button(self, reply_id: str):
        return self._click(self.reply_vote_thumbs_up(reply_id))

    def get_thumbs_up_vote_message(self, reply_id: str) -> str:
        return self._get_text_of_element(self.reply_vote_thumbs_up_message(reply_id))

    def get_thumbs_up_button_locator(self, reply_id: str) -> Locator:
        return self.reply_vote_thumbs_up(reply_id)

    def get_thumbs_down_button_locator(self, reply_id: str) -> Locator:
        return self.reply_vote_thumbs_down(reply_id)

    def click_reply_vote_thumbs_down_button(self, reply_id):
        self._click(self.reply_vote_thumbs_down(reply_id))

    def get_helpful_count(self, reply_id) -> str:
        return self._get_text_of_element(self.helpful_count(reply_id))

    def get_not_helpful_count(self, reply_id) -> str:
        return self._get_text_of_element(self.unhelpful_count(reply_id))

    # Signed out card actions.
    def click_on_log_in_to_your_account_signed_out_card_link(self):
        self._click(self.log_in_to_your_account_signed_out_card_option)

    def click_on_start_a_new_question_signed_out_card_link(self):
        self._click(self.start_a_new_question_signed_out_card_option)

    def click_on_ask_a_question_signed_out_card_option(self):
        self._click(self.ask_a_question_signed_out_card_option)

    def ask_a_question_signed_out_card_option_locator(self) -> Locator:
        return self.ask_a_question_signed_out_card_option

    def click_on_i_have_this_problem_too_signed_out_card_option(self):
        self._click(self.i_have_this_problem_too_signed_out_card_option)

    def get_i_have_this_problem_too_signed_out_card_locator(self) -> Locator:
        return self.i_have_this_problem_too_signed_out_card_option

    # Common responses actions.

    def click_on_common_responses_option(self):
        self._click(self.common_responses_option)

    def type_into_common_responses_search_field(self, text: str):
        self._type(self.common_responses_search_field, text, 100)

    def get_text_of_no_cat_responses(self) -> str:
        return self._get_text_of_element(self.common_responses_no_cat_selected)

    def get_list_of_categories(self) -> list[str]:
        return self._get_text_of_elements(self.common_responses_categories_options)

    def get_list_of_responses(self) -> list[str]:
        return self._get_text_of_elements(self.common_responses_responses_options)

    def click_on_a_particular_category_option(self, option: str):
        self._click(self.category_option(option))

    def click_on_a_particular_response_option(self, option: str):
        self._click(self.response_option(option))

    # Removing both newline characters and link syntax format.
    def get_text_of_response_editor_textarea_field(self) -> str:
        return (self._get_element_input_value(self.common_responses_textarea_field)
                .replace("\n", "")
                .replace("[", "")
                .replace("]", "")
                )

    def get_text_of_response_preview(self) -> str:
        return self._get_text_of_element(self.common_responses_response_preview)

    def click_on_switch_to_mode(self):
        self._click(self.common_responses_switch_to_mode)

    def click_on_common_responses_cancel_button(self):
        self._click(self.common_responses_cancel_button)

    def click_on_common_responses_insert_response_button(self):
        self._click(self.common_responses_insert_response_button)

    def get_time_from_reply(self, reply_id: str) -> str:
        """Returns the time displayed inside the question for when a reply was made.

        Args:
            reply_id (str): The reply id.
        """
        return self._get_text_of_element(self.response_time(reply_id))
