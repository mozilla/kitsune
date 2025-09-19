from playwright.sync_api import Page
from playwright_tests.core.utilities import Utilities, retry_on_502
from playwright_tests.pages.ask_a_question.aaq_pages.aaq_form_page import AAQFormPage
from playwright_tests.pages.ask_a_question.posted_question_pages.questions_page import QuestionPage
from playwright_tests.pages.auth_page import AuthPage
from playwright_tests.pages.top_navbar import TopNavbar


class AAQFlow:
    def __init__(self, page: Page):
        self.page = page
        self.aaq_form_page = AAQFormPage(page)
        self.utilities = Utilities(page)
        self.question_page = QuestionPage(page)
        self.top_navbar = TopNavbar(page)
        self.auth_page = AuthPage(page)


    # Submitting an aaq question for a product flow.
    # Mozilla VPN has an extra optional dropdown menu for choosing an operating system.
    @retry_on_502
    def submit_an_aaq_question(self, subject: str, body: str, topic_name='', attach_image=False,
                               is_premium=False, email="", is_loginless=False,
                               expected_locator=None, form_url=None):
        question_subject = ''
        if form_url and self.utilities.get_page_url() != form_url:
            self.utilities.navigate_to_link(form_url)
        if is_premium:
            self.add_valid_data_to_all_premium_products_aaq_fields(subject, body, is_loginless,
                                                                   email)
        else:
            question_subject = self.add__valid_data_to_all_aaq_fields_without_submitting(
                subject, topic_name, body, attach_image)

        # Submitting the question.
        self.aaq_form_page.click_aaq_form_submit_button(expected_locator=expected_locator)

        # If the submission was done for freemium products we are retrieving the Question Subject,
        # Question url & Question Body for further test usage.
        if not is_premium:
            # Waiting for submitted question reply button visibility.
            self.question_page.is_post_reply_button_visible()
            current_page_url = self.page.url
            return {"aaq_subject": question_subject, "question_page_url": current_page_url,
                    "question_body": body}

    # Populating the aaq form fields for freemium products with given values without submitting the
    # form.
    def add__valid_data_to_all_aaq_fields_without_submitting(self, subject: str, topic_value: str,
                                                             body_text: str, attach_image=False):
        aaq_subject = subject + self.utilities.generate_random_number(min_value=0, max_value=5000)
        # Adding text to subject field.
        self.aaq_form_page.add_text_to_aaq_form_subject_field(aaq_subject)
        # Selecting a topic.
        self.aaq_form_page.select_aaq_form_topic_value(
            topic_value
        )
        # Adding text to question body.
        self.aaq_form_page.add_text_to_aaq_textarea_field(
            body_text
        )

        if attach_image:
            # Uploading an image to the aaq question form.
            self.aaq_form_page.get_upload_image_button_locator().set_input_files(
                self.utilities.aaq_question_test_data["valid_firefox_question"]["image_path"]
            )

            # Waiting for the image preview to be displayed.
            self.aaq_form_page.uploaded_image_locator()

        # Returning the entered question subject for further usage.
        return aaq_subject

    # Flow for adding valid data to premium products forms without submitting the ticket.
    # We are currently choosing one random topic & os for each product ticket submission.
    # Note: Some premium products forms (example: Mozilla VPN) has an extra "os" dropdown.
    def add_valid_data_to_all_premium_products_aaq_fields(self, subject: str, body: str,
                                                          is_loginless: bool, email: str):
        if is_loginless:
            if self.top_navbar.is_sign_in_up_button_displayed():
                self.top_navbar.click_on_signin_signup_button()
                self.auth_page.click_on_cant_sign_in_to_my_mozilla_account_link()
            self.aaq_form_page.fill_contact_email_field(email)

        self.aaq_form_page.select_random_topic_by_value()

        if self.aaq_form_page.is_os_dropdown_menu_visible():
            self.aaq_form_page.select_random_os_by_value()
        self.aaq_form_page.add_text_to_premium_aaq_form_subject_field(subject)
        self.aaq_form_page.add_text_to_premium_aaq_textarea_body_field(body)

    # Adding an image to the aaq form.
    def adding_an_image_to_aaq_form(self):
        self.aaq_form_page.get_upload_image_button_locator().set_input_files(
            self.utilities.aaq_question_test_data["valid_firefox_question"]["image_path"]
        )

    @retry_on_502
    def deleting_question_flow(self):
        self.question_page.click_delete_this_question_question_tools_option()
        self.question_page.click_delete_this_question_button()

    @retry_on_502
    def editing_question_flow(self, subject='', body='', troubleshoot='', submit_edit=True):
        if subject:
            self.aaq_form_page.clear_subject_input_field()
            self.aaq_form_page.add_text_to_aaq_form_subject_field(subject)

        if body:
            self.aaq_form_page.clear_the_question_body_textarea_field()
            self.aaq_form_page.add_text_to_aaq_textarea_field(body)

        if troubleshoot:
            self.aaq_form_page.add_text_to_troubleshooting_information_textarea(troubleshoot)

        if submit_edit:
            self.aaq_form_page.click_aaq_edit_submit_button()

    @retry_on_502
    def editing_reply_flow(self, reply_body: str, submit_reply=True):
        self.aaq_form_page.clear_the_question_body_textarea_field()
        self.aaq_form_page.add_text_to_aaq_textarea_field(reply_body)

        self.aaq_form_page.click_on_update_answer_button() if submit_reply else (
            self.aaq_form_page.click_aaq_form_cancel_button())

    @retry_on_502
    def delete_question_reply(self, answer_id: str, delete_reply: bool):
        self.question_page.click_on_reply_more_options_button(answer_id)
        self.question_page.click_on_delete_this_post_for_a_certain_reply(answer_id)

        self.question_page.click_delete_this_question_button() if delete_reply else (
            self.question_page.click_on_cancel_delete_button())

    @retry_on_502
    def post_question_reply_flow(self, repliant_username: str, reply='', submit_reply=True,
                                 quoted_reply=False, reply_for_id='') -> str:

        if quoted_reply:
            self.question_page.click_on_reply_more_options_button(reply_for_id)
            self.question_page.click_on_quote_for_a_certain_reply(reply_for_id)

        if reply and quoted_reply:
            self.question_page.type_inside_the_post_a_reply_textarea(reply)
        elif reply and not quoted_reply:
            self.question_page.add_text_to_post_a_reply_textarea(reply)

        if submit_reply:
            return self.question_page.click_on_post_reply_button(repliant_username)

    def report_question_abuse(self, answer_id: str, text=''):
        self.question_page.click_on_reply_more_options_button(answer_id)
        self.question_page.click_on_report_abuse_for_a_certain_reply(answer_id)

        if text:
            self.question_page.add_text_to_report_abuse_textarea(text)

        self.question_page.click_on_report_abuse_submit_button()
        self.question_page.click_abuse_modal_close_button()

    def spam_marking_a_reply(self, reply_id: str):
        self.question_page.click_on_reply_more_options_button(reply_id)
        self.question_page.click_on_mark_as_spam_for_a_certain_reply(reply_id)
