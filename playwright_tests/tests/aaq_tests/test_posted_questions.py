import os

import pytest
import pytest_check as check
from playwright_tests.core.testutilities import TestUtilities
from playwright.sync_api import expect

from playwright_tests.messages.AAQ_messages.edit_question_page_messages import (
    EditQuestionPageMessages)
from playwright_tests.messages.auth_pages_messages.fxa_page_messages import (
    FxAPageMessages)
from playwright_tests.messages.contact_support_page_messages.contact_support_messages import (
    ContactSupportMessages)


class TestPostedQuestions(TestUtilities):

    # C2191086, C2191094, C2191263,  C2191263
    @pytest.mark.postedQuestions
    def test_posted_question_details_for_admin_users(self):
        self.logger.info("Signing in with a non admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        self.logger.info("Posting a Firefox product question")
        self.navigate_to_link(super().aaq_question_test_data["products_aaq_url"]["Firefox"])

        question_info = self.sumo_pages.aaq_flow.submit_an_aaq_question_for_a_product(
            subject=super().aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=self.sumo_pages.aaq_form_page.get_aaq_form_topic_options()[0],
            body=super().aaq_question_test_data["valid_firefox_question"]["question_body"],
            attach_image=False
        )

        self.logger.info("Deleting session cookies and signing in with an admin account")
        super().delete_cookies()

        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.navigate_to_link(question_info['question_page_url'])

        self.logger.info("Navigating to the posted question")

        self.logger.info("Verifying that the scam banner is not displayed")
        expect(
            self.sumo_pages.product_solutions_page.get_scam_banner_locator()
        ).to_be_visible()

        self.logger.info("Verifying that the still need help banner is not displayed")
        expect(
            self.sumo_pages.product_solutions_page.get_still_need_help_locator()
        ).to_be_hidden()

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page.click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page.click_delete_this_question_button()

    # C2191092,  C2191263
    @pytest.mark.postedQuestions
    def test_edit_this_question_functionality_not_signed_in(self):
        self.logger.info("Signing in with an admin account")

        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Posting a Firefox product question")
        self.navigate_to_link(super().aaq_question_test_data["products_aaq_url"]["Firefox"])

        self.sumo_pages.aaq_flow.submit_an_aaq_question_for_a_product(
            subject=super().aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=self.sumo_pages.aaq_form_page.get_aaq_form_topic_options()[0],
            body=super().aaq_question_test_data["valid_firefox_question"]["simple_body_text"],
            attach_image=False
        )

        self.logger.info("Deleting session cookies")
        self.delete_cookies()

        self.logger.info("Verifying that the 'edit this question' nav option is not available")

        expect(
            self.sumo_pages.question_page.get_edit_this_question_option_locator()
        ).to_be_hidden()

        self.logger.info("Navigating to the edit endpoint")
        self.navigate_to_link(
            self.get_page_url() + EditQuestionPageMessages.EDIT_QUESTION_URL_ENDPOINT
        )

        self.logger.info("Verifying that the user is to the auth page")
        assert (
            FxAPageMessages.AUTH_PAGE_URL in self.get_page_url()
        )

        self.logger.info("Navigating back to the question")
        self.navigate_back()

        self.logger.info("Signing in with an admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page.click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page.click_delete_this_question_button()

    # C2191262, C2436105,  C2191263
    # To add image tests
    @pytest.mark.postedQuestions
    @pytest.mark.parametrize("username", ['TEST_ACCOUNT_12', 'TEST_ACCOUNT_MODERATOR'])
    def test_cancel_edit_this_question_functionality(self, username):
        self.logger.info("Signing in with a non admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        self.logger.info("Posting a Firefox product question")
        self.navigate_to_link(super().aaq_question_test_data["products_aaq_url"]["Firefox"])

        question_info = self.sumo_pages.aaq_flow.submit_an_aaq_question_for_a_product(
            subject=super().aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=self.sumo_pages.aaq_form_page.get_aaq_form_topic_options()[0],
            body=super().aaq_question_test_data["valid_firefox_question"]["simple_body_text"],
            attach_image=False
        )

        if username == 'TEST_ACCOUNT_MODERATOR':
            self.logger.info("Deleting session cookies and signing in with an admin account")
            super().delete_cookies()

            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        self.navigate_to_link(question_info['question_page_url'])
        self.logger.info("Clicking on the 'Edit this question' option")
        self.sumo_pages.question_page.click_on_edit_this_question_question_tools_option()

        self.logger.info("Verifying that the subject field contains the correct value")
        check.equal(
            self.sumo_pages.aaq_form_page.get_value_of_subject_input_field(),
            question_info['aaq_subject'],
            f"Incorrect question subject displayed. "
            f"Expected: {question_info['aaq_subject']} "
            f"Received: {self.sumo_pages.aaq_form_page.get_value_of_subject_input_field()}"
        )

        self.logger.info("Verifying that the question body contains the correct value")
        check.equal(
            self.sumo_pages.aaq_form_page.get_value_of_question_body_textarea_field(),
            question_info['question_body']

        )

        self.logger.info("Adding text inside the Subject field")
        self.sumo_pages.aaq_form_page.clear_subject_input_field()
        self.sumo_pages.aaq_form_page.add_text_to_aaq_form_subject_field(
            super().aaq_question_test_data['valid_firefox_question']['subject_updated']
        )

        self.logger.info("Adding text inside the body field")
        self.sumo_pages.aaq_form_page.clear_the_question_body_textarea_field()
        self.sumo_pages.aaq_form_page.add_text_to_aaq_textarea_field(
            super().aaq_question_test_data['valid_firefox_question']['body_updated']
        )

        self.logger.info("Adding information inside the troubleshoot information textarea")
        self.sumo_pages.aaq_form_page.add_text_to_troubleshooting_information_textarea(
            super().aaq_question_test_data['troubleshooting_information_textarea_field']
        )

        self.logger.info("Clicking on the 'Cancel' button")
        self.sumo_pages.aaq_form_page.click_aaq_form_cancel_button()

        self.logger.info("Verifying that the 'Modified' text is not displayed")
        expect(
            self.sumo_pages.question_page.get_modified_question_locator()
        ).to_be_hidden()

        self.logger.info("Verifying that the subject and body fields are the same")
        check.equal(
            self.sumo_pages.question_page.get_question_header(),
            question_info['aaq_subject']
        )

        check.equal(
            self.sumo_pages.question_page.get_question_body(),
            question_info['question_body'] + '\n'
        )

        if username == 'TEST_ACCOUNT_12':
            self.logger.info("Verifying that the additional question details option is hidden")
            expect(
                self.sumo_pages.question_page.get_question_details_button_locator()
            ).to_be_hidden()
        elif username == "TEST_ACCOUNT_MODERATOR":
            self.logger.info("Clicking on the 'Question Details' option")
            self.sumo_pages.question_page.click_on_question_details_button()

            self.logger.info("Clicking on the 'More system details' option")
            self.sumo_pages.question_page.click_on_more_system_details_option()

            self.logger.info("Verifying that the more information section is not displayed")
            expect(
                self.sumo_pages.question_page.get_more_information_locator()
            ).to_be_hidden()

            self.logger.info("Closing the more information panel")
            self.sumo_pages.question_page.click_on_the_additional_system_panel_close_button()

        if username != 'TEST_ACCOUNT_MODERATOR':
            self.logger.info("Deleting session cookies and signing in with an admin account")
            super().delete_cookies()

            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page.click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page.click_delete_this_question_button()

    # C2191263
    @pytest.mark.postedQuestions
    def test_edit_other_user_question_non_admin(self):
        self.logger.info("Signing in with a non admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_13"]
        ))

        self.logger.info("Posting a Firefox product question")
        self.navigate_to_link(super().aaq_question_test_data["products_aaq_url"]["Firefox"])

        question_info = self.sumo_pages.aaq_flow.submit_an_aaq_question_for_a_product(
            subject=super().aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=self.sumo_pages.aaq_form_page.get_aaq_form_topic_options()[0],
            body=super().aaq_question_test_data["valid_firefox_question"]["simple_body_text"],
            attach_image=False
        )

        self.logger.info("Deleting session cookies")
        self.delete_cookies()

        self.logger.info("Signing in with a non admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        self.logger.info("Verifying that the 'Edit this question' option is not available")
        expect(
            self.sumo_pages.question_page.get_edit_this_question_option_locator()
        ).to_be_hidden()

        self.logger.info("Manually navigating to the '/edit' endpoint and verifying that 403 is "
                         "returned")

        with self.page.expect_navigation() as navigation_info:
            self.navigate_to_link(question_info['question_page_url'] + EditQuestionPageMessages.
                                  EDIT_QUESTION_URL_ENDPOINT)
        response = navigation_info.value
        check.equal(
            response.status,
            403
        )

        self.logger.info("Navigating back to the posted question")
        self.navigate_back()

        self.logger.info("Signing in with an admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page.click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page.click_delete_this_question_button()

    # C2191262, C2436105, C2191263
    # To add image tests
    @pytest.mark.postedQuestions
    @pytest.mark.parametrize("username", ['TEST_ACCOUNT_12', 'TEST_ACCOUNT_MODERATOR'])
    def test_edit_this_question_functionality(self, username):
        self.logger.info("Signing in with a non admin user account")
        user = super().username_extraction_from_email(
            self.user_secrets_accounts[username]
        )
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        self.logger.info("Posting a Firefox product question")
        self.navigate_to_link(super().aaq_question_test_data["products_aaq_url"]["Firefox"])

        question_info = self.sumo_pages.aaq_flow.submit_an_aaq_question_for_a_product(
            subject=super().aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=self.sumo_pages.aaq_form_page.get_aaq_form_topic_options()[0],
            body=super().aaq_question_test_data["valid_firefox_question"]["simple_body_text"],
            attach_image=False
        )

        if username == 'TEST_ACCOUNT_MODERATOR':
            self.logger.info("Deleting session cookies and signing in with an admin account")
            super().delete_cookies()

            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        self.navigate_to_link(question_info['question_page_url'])
        self.logger.info("Clicking on the 'Edit this question' option")
        self.sumo_pages.question_page.click_on_edit_this_question_question_tools_option()

        self.logger.info("Verifying that the subject field contains the correct value")
        check.equal(
            self.sumo_pages.aaq_form_page.get_value_of_subject_input_field(),
            question_info['aaq_subject'],
            f"Incorrect question subject displayed. "
            f"Expected: {question_info['aaq_subject']} "
            f"Received: {self.sumo_pages.aaq_form_page.get_value_of_subject_input_field()}"
        )

        self.logger.info("Verifying that the question body contains the correct value")
        check.equal(
            self.sumo_pages.aaq_form_page.get_value_of_question_body_textarea_field(),
            question_info['question_body']

        )

        self.logger.info("Adding text inside the Subject field")
        self.sumo_pages.aaq_form_page.clear_subject_input_field()
        self.sumo_pages.aaq_form_page.add_text_to_aaq_form_subject_field(
            super().aaq_question_test_data['valid_firefox_question']['subject_updated']
        )

        self.logger.info("Adding text inside the body field")
        self.sumo_pages.aaq_form_page.clear_the_question_body_textarea_field()
        self.sumo_pages.aaq_form_page.add_text_to_aaq_textarea_field(
            super().aaq_question_test_data['valid_firefox_question']['body_updated']
        )

        self.logger.info("Adding information inside the troubleshoot information textarea")
        self.sumo_pages.aaq_form_page.add_text_to_troubleshooting_information_textarea(
            super().aaq_question_test_data['troubleshooting_information_textarea_field']
        )

        self.logger.info("Clicking on the 'Submit' button")
        self.sumo_pages.aaq_form_page.click_aaq_edit_submit_button()

        self.logger.info("Verifying that the 'Modified' text is displayed")
        expect(
            self.sumo_pages.question_page.get_modified_question_locator()
        ).to_be_visible()

        self.logger.info("Verifying that the username is displayed inside the modified by text")
        check.is_in(
            user,
            self.sumo_pages.question_page.get_modified_by_text()
        )

        self.logger.info("Verifying that the subject and body are modified")
        check.equal(
            self.sumo_pages.question_page.get_question_header(),
            super().aaq_question_test_data['valid_firefox_question']['subject_updated']
        )

        check.equal(
            self.sumo_pages.question_page.get_question_body(),
            super().aaq_question_test_data['valid_firefox_question']['body_updated'] + '\n'
        )

        if username == 'TEST_ACCOUNT_12':
            self.logger.info("Verifying that the additional question details option is hidden")
            expect(
                self.sumo_pages.question_page.get_question_details_button_locator()
            ).to_be_hidden()
        elif username == "TEST_ACCOUNT_MODERATOR":
            self.logger.info("Clicking on the 'Question Details' option")
            self.sumo_pages.question_page.click_on_question_details_button()

            self.logger.info("Clicking on the 'More system details' option")
            self.sumo_pages.question_page.click_on_more_system_details_option()

            self.logger.info("Verifying that the more information section displays the update")
            expect(
                self.sumo_pages.question_page.get_more_information_with_text_locator(
                    super().aaq_question_test_data['troubleshooting_information_textarea_field']
                )
            ).to_be_visible()

            self.logger.info("Closing the more information panel")
            self.sumo_pages.question_page.click_on_the_additional_system_panel_close_button()

        if username != 'TEST_ACCOUNT_MODERATOR':
            self.logger.info("Deleting session cookies and signing in with an admin account")
            super().delete_cookies()

            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page.click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page.click_delete_this_question_button()

    # C2191263
    @pytest.mark.postedQuestions
    def test_delete_question_cancel_button(self):
        self.logger.info("Signing in with a non admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_13"]
        ))

        self.logger.info("Posting a Firefox product question")
        self.navigate_to_link(super().aaq_question_test_data["products_aaq_url"]["Firefox"])

        question_info_one = self.sumo_pages.aaq_flow.submit_an_aaq_question_for_a_product(
            subject=super().aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=self.sumo_pages.aaq_form_page.get_aaq_form_topic_options()[0],
            body=super().aaq_question_test_data["valid_firefox_question"]["simple_body_text"],
            attach_image=False
        )

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Signing in with a different non admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        self.logger.info("Posting a Firefox product question")
        self.navigate_to_link(super().aaq_question_test_data["products_aaq_url"]["Firefox"])

        question_info_two = self.sumo_pages.aaq_flow.submit_an_aaq_question_for_a_product(
            subject=super().aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=self.sumo_pages.aaq_form_page.get_aaq_form_topic_options()[0],
            body=super().aaq_question_test_data["valid_firefox_question"]["simple_body_text"],
            attach_image=False
        )

        self.navigate_to_link(
            question_info_one['question_page_url']
        )

        self.logger.info("Verifying that the 'Delete this question' option is not available")
        expect(
            self.sumo_pages.question_page.get_delete_this_question_locator()
        ).to_be_hidden()

        self.logger.info("Manually navigating to the delete endpoint and verifying that 403 is "
                         "returned")

        with self.page.expect_navigation() as navigation_info:
            self.navigate_to_link(
                question_info_one['question_page_url'] + EditQuestionPageMessages.
                DELETE_QUESTION_URL_ENDPOINT)
        response = navigation_info.value
        check.equal(
            response.status,
            403
        )

        self.navigate_to_link(
            question_info_two['question_page_url']
        )

        self.logger.info("Verifying that the 'Delete this question' option is not available")
        expect(
            self.sumo_pages.question_page.get_delete_this_question_locator()
        ).to_be_hidden()

        self.logger.info("Manually navigating to the delete endpoint and verifying that 403 is "
                         "returned")

        with self.page.expect_navigation() as navigation_info:
            self.navigate_to_link(
                question_info_one['question_page_url'] + EditQuestionPageMessages.
                DELETE_QUESTION_URL_ENDPOINT)
        response = navigation_info.value
        check.equal(
            response.status,
            403
        )

        self.logger.info("Navigating back to the question page and deleting session cookies")
        self.navigate_back()
        self.delete_cookies()

        self.logger.info("Signing in with a admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Clicking on the 'Delete this question option'")
        self.sumo_pages.question_page.click_delete_this_question_question_tools_option()

        self.logger.info("Clicking on the 'Cancel' button and verifying that we are on the "
                         "question page")

        self.sumo_pages.aaq_form_page.click_aaq_form_cancel_button()

        expect(
            self.page
        ).to_have_url(question_info_two['question_page_url'])

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page.click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page.click_delete_this_question_button()

        self.navigate_to_link(
            question_info_one['question_page_url']
        )

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page.click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page.click_delete_this_question_button()

    # C2191264, C2191265
    # To add coverage for images as well
    @pytest.mark.postedQuestions
    @pytest.mark.parametrize("status", ['locked', 'archived'])
    def test_lock_and_archive_this_question(self, status):
        self.logger.info(f"Executing the {status} question tests")
        self.logger.info("Signing in with a non admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_13"]
        ))

        self.logger.info("Posting a Firefox product question")
        self.navigate_to_link(super().aaq_question_test_data["products_aaq_url"]["Firefox"])

        question_info_one = self.sumo_pages.aaq_flow.submit_an_aaq_question_for_a_product(
            subject=super().aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=self.sumo_pages.aaq_form_page.get_aaq_form_topic_options()[0],
            body=super().aaq_question_test_data["valid_firefox_question"]["simple_body_text"],
            attach_image=False
        )

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Signing in with a different non admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        self.logger.info("Posting a Firefox product question")
        self.navigate_to_link(super().aaq_question_test_data["products_aaq_url"]["Firefox"])

        question_info_two = self.sumo_pages.aaq_flow.submit_an_aaq_question_for_a_product(
            subject=super().aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=self.sumo_pages.aaq_form_page.get_aaq_form_topic_options()[0],
            body=super().aaq_question_test_data["valid_firefox_question"]["simple_body_text"],
            attach_image=False
        )

        self.navigate_to_link(
            question_info_one['question_page_url']
        )

        if status == "locked":
            self.logger.info("Verifying that the 'Lock this question' option is not available for "
                             "other posted questions")
            expect(
                self.sumo_pages.question_page.get_lock_this_question_locator()
            ).to_be_hidden()
        elif status == "archived":
            expect(
                self.sumo_pages.question_page.get_archive_this_question_locator()
            ).to_be_hidden()

        self.navigate_to_link(
            question_info_two['question_page_url']
        )

        if status == "locked":
            self.logger.info("Verifying that the 'Lock this question is not available for self "
                             "posted questions")
            expect(
                self.sumo_pages.question_page.get_lock_this_question_locator()
            ).to_be_hidden()
        elif status == "archived":
            expect(
                self.sumo_pages.question_page.get_archive_this_question_locator()
            ).to_be_hidden()

        self.logger.info("Deleting session cookies and signing in with an admin account")
        super().delete_cookies()

        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        if status == "locked":
            self.logger.info("Clicking on the 'Lock this question' option")
            self.sumo_pages.question_page.click_on_lock_this_question_locator()
        elif status == "archived":
            self.logger.info("Clicking on the 'Archive this question' option")
            self.sumo_pages.question_page.click_on_archive_this_question_option()

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Signing in with a different non admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        if status == "locked":
            self.logger.info("Verifying that correct locked thread banner text is displayed")
            check.equal(
                self.sumo_pages.question_page.get_thread_locked_text(),
                EditQuestionPageMessages.LOCKED_THREAD_BANNER
            )
        elif status == "archived":
            self.logger.info("Verifying that correct archived thread banner text is displayed")
            check.equal(
                self.sumo_pages.question_page.get_thread_locked_text(),
                EditQuestionPageMessages.ARCHIVED_THREAD_BANNER
            )

        self.logger.info("Clicking on the locked thread link and verifying that we are "
                         "redirected to the correct page")
        self.sumo_pages.question_page.click_on_thread_locked_link()

        expect(
            self.page
        ).to_have_url(ContactSupportMessages.PAGE_URL)

        self.logger.info("Navigating back to the question page")
        self.navigate_back()

        if status == "locked":
            self.logger.info("Verifying that the 'Unlock this question option is not available'")
            expect(
                self.sumo_pages.question_page.get_lock_this_question_locator()
            ).to_be_hidden()
        elif status == "archived":
            expect(
                self.sumo_pages.question_page.get_archive_this_question_locator()
            ).to_be_hidden()

        self.logger.info("Verifying that the post a reply textarea field is not displayed")
        expect(
            self.sumo_pages.question_page.get_post_a_reply_textarea_locator()
        ).to_be_hidden()

        self.logger.info("Verifying that the 'needs more information from the user' checkbox is "
                         "not displayed")
        expect(
            self.sumo_pages.question_page.get_needs_more_information_checkbox_locator()
        ).to_be_hidden()

        self.logger.info("Verifying that the 'Add images section is not displayed'")
        expect(
            self.sumo_pages.question_page.get_add_image_section_locator()
        ).to_be_hidden()

        self.logger.info("Deleting session cookies and signing in with an admin account")
        super().delete_cookies()

        repliant_username = super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        )

        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Adding text inside the textarea field")
        self.sumo_pages.question_page.add_text_to_post_a_reply_textarea(
            super().aaq_question_test_data['valid_firefox_question']['question_reply']
        )

        self.logger.info("Verifying that the 'needs more information from the user' checkbox is "
                         "available")
        expect(
            self.sumo_pages.question_page.get_needs_more_information_checkbox_locator()
        ).to_be_visible()

        self.logger.info("Verifying that the 'Add images' section is available")
        expect(
            self.sumo_pages.question_page.get_add_image_section_locator()
        ).to_be_visible()

        self.logger.info("Clicking on the 'Post a reply button'")
        reply_id = self.sumo_pages.question_page.click_on_post_reply_button(repliant_username)

        self.logger.info("Verifying that posted reply is visible")
        expect(
            self.sumo_pages.question_page.get_posted_reply_locator(reply_id)
        ).to_be_visible()

        self.logger.info("Signing in with a normal user account and verifying that the admin's "
                         "reply is visible")

        self.logger.info("Deleting session cookies and signing in with an admin account")
        super().delete_cookies()

        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        expect(
            self.sumo_pages.question_page.get_posted_reply_locator(reply_id)
        ).to_be_visible()

        self.logger.info("Deleting session cookies and signing in with an admin account")
        super().delete_cookies()

        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        if status == "locked":
            self.logger.info("Unlocking the question")
            self.sumo_pages.question_page.click_on_lock_this_question_locator()
        elif status == "archived":
            self.logger.info("Clicking on the 'Archive this question' option")
            self.sumo_pages.question_page.click_on_archive_this_question_option()

        self.logger.info("Deleting session cookies and signing in with an admin account")
        super().delete_cookies()

        second_repliant = super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        )
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        self.logger.info("Verifying that the 'Thread locked' banner is not displayed")
        expect(
            self.sumo_pages.question_page.get_thread_locked_locator()
        ).to_be_hidden()

        self.logger.info("Posting a question reply")
        self.logger.info("Adding text inside the textarea field")
        self.sumo_pages.question_page.add_text_to_post_a_reply_textarea(
            super().aaq_question_test_data['valid_firefox_question']['question_reply']
        )

        self.logger.info("Clicking on the 'Post a reply button'")
        reply_id_two = self.sumo_pages.question_page.click_on_post_reply_button(second_repliant)

        self.logger.info("Verifying that the posted reply is visible")

        expect(
            self.sumo_pages.question_page.get_posted_reply_locator(reply_id_two)
        ).to_be_visible()

        self.logger.info("Deleting session cookies and signing in with an admin account")
        super().delete_cookies()

        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page.click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page.click_delete_this_question_button()

        self.navigate_to_link(
            question_info_one['question_page_url']
        )

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page.click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page.click_delete_this_question_button()

    # C2191267, C2191116, C2134136, C2191091
    @pytest.mark.postedQuestions
    def test_subscribe_to_feed_option(self):
        self.logger.info("Signing in with a non admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_13"]
        ))

        self.logger.info("Posting a Firefox product question")
        self.navigate_to_link(super().aaq_question_test_data["products_aaq_url"]["Firefox"])

        question_info_one = self.sumo_pages.aaq_flow.submit_an_aaq_question_for_a_product(
            subject=super().aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=self.sumo_pages.aaq_form_page.get_aaq_form_topic_options()[0],
            body=super().aaq_question_test_data["valid_firefox_question"]["simple_body_text"],
            attach_image=False
        )

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Signing in with a different non admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        self.logger.info("Posting a Firefox product question")
        self.navigate_to_link(super().aaq_question_test_data["products_aaq_url"]["Firefox"])

        question_info_two = self.sumo_pages.aaq_flow.submit_an_aaq_question_for_a_product(
            subject=super().aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=self.sumo_pages.aaq_form_page.get_aaq_form_topic_options()[0],
            body=super().aaq_question_test_data["valid_firefox_question"]["simple_body_text"],
            attach_image=False
        )

        self.navigate_to_link(
            question_info_one['question_page_url']
        )

        self.logger.info("Clicking on the 'Subscribe to feed' option from different user posted "
                         "question")
        if self.browser == "chrome":
            self.sumo_pages.question_page.click_on_subscribe_to_feed_option()
            self.logger.info("Verifying that the url is updated to the feed endpoint")
            expect(
                self.page
            ).to_have_url(
                question_info_one['question_page_url'] + EditQuestionPageMessages.FEED_FILE_PATH
            )
        else:
            with self.page.expect_download() as download_info:
                self.sumo_pages.question_page.click_on_subscribe_to_feed_option()
            download = download_info.value

            self.logger.info("Verifying that the received file contains the correct name")
            check.is_in(
                EditQuestionPageMessages.FEED_FILE_NAME,
                download.suggested_filename,
                f"Incorrect file name. "
                f"Expected: {EditQuestionPageMessages.FEED_FILE_NAME} "
                f"Received: {download.suggested_filename}"
            )

            self.logger.info("Verifying that the received file is not empty")
            assert (
                os.path.getsize(download.path()) > 0
            )

        self.navigate_to_link(
            question_info_two['question_page_url']
        )
        if self.browser == "chrome":
            self.sumo_pages.question_page.click_on_subscribe_to_feed_option()
            self.logger.info("Verifying that the url is updated to the feed endpoint")
            expect(
                self.page
            ).to_have_url(
                question_info_two['question_page_url'] + EditQuestionPageMessages.FEED_FILE_PATH
            )
            self.navigate_back()
        else:
            with self.page.expect_download() as download_info:
                self.sumo_pages.question_page.click_on_subscribe_to_feed_option()
            download = download_info.value

            self.logger.info("Verifying that the received file contains the correct name")
            check.is_in(
                EditQuestionPageMessages.FEED_FILE_NAME,
                download.suggested_filename,
                f"Incorrect file name. "
                f"Expected: {EditQuestionPageMessages.FEED_FILE_NAME} "
                f"Received: {download.suggested_filename}"
            )

            self.logger.info("Verifying that the received file is not empty")
            assert (
                os.path.getsize(download.path()) > 0
            )

        self.logger.info("Signing out")
        super().delete_cookies()

        if self.browser == "chrome":
            self.sumo_pages.question_page.click_on_subscribe_to_feed_option()
            self.logger.info("Verifying that the url is updated to the feed endpoint")
            expect(
                self.page
            ).to_have_url(
                question_info_two['question_page_url'] + EditQuestionPageMessages.FEED_FILE_PATH
            )
            self.navigate_back()
        else:
            with self.page.expect_download() as download_info:
                self.sumo_pages.question_page.click_on_subscribe_to_feed_option()
            download = download_info.value

            self.logger.info("Verifying that the received file contains the correct name")
            check.is_in(
                EditQuestionPageMessages.FEED_FILE_NAME,
                download.suggested_filename,
                f"Incorrect file name. "
                f"Expected: {EditQuestionPageMessages.FEED_FILE_NAME} "
                f"Received: {download.suggested_filename}"
            )

            self.logger.info("Verifying that the received file is not empty")
            assert (
                os.path.getsize(download.path()) > 0
            )

        self.logger.info("Signing in with an admin account")

        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        if self.browser == "chrome":
            self.sumo_pages.question_page.click_on_subscribe_to_feed_option()
            self.logger.info("Verifying that the url is updated to the feed endpoint")
            expect(
                self.page
            ).to_have_url(
                question_info_two['question_page_url'] + EditQuestionPageMessages.FEED_FILE_PATH
            )
            self.navigate_back()
        else:
            with self.page.expect_download() as download_info:
                self.sumo_pages.question_page.click_on_subscribe_to_feed_option()
            download = download_info.value

            self.logger.info("Verifying that the received file contains the correct name")
            check.is_in(
                EditQuestionPageMessages.FEED_FILE_NAME,
                download.suggested_filename,
                f"Incorrect file name. "
                f"Expected: {EditQuestionPageMessages.FEED_FILE_NAME} "
                f"Received: {download.suggested_filename}"
            )

            self.logger.info("Verifying that the received file is not empty")
            assert (
                os.path.getsize(download.path()) > 0
            )

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page.click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page.click_delete_this_question_button()

        self.navigate_to_link(
            question_info_one['question_page_url']
        )

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page.click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page.click_delete_this_question_button()

    # To work on adding a check inside the moderate forum content page
    # C2191491
    @pytest.mark.postedQuestions
    def test_mark_as_spam_functionality(self):
        self.logger.info("Signing in with a non admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_13"]
        ))

        self.logger.info("Posting a Firefox product question")
        self.navigate_to_link(super().aaq_question_test_data["products_aaq_url"]["Firefox"])

        question_info = self.sumo_pages.aaq_flow.submit_an_aaq_question_for_a_product(
            subject=super().aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=self.sumo_pages.aaq_form_page.get_aaq_form_topic_options()[0],
            body=super().aaq_question_test_data["valid_firefox_question"]["simple_body_text"],
            attach_image=False
        )

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Verifying that the 'Mark as spam' option is not displayed")
        expect(
            self.sumo_pages.question_page.get_mark_as_spam_locator()
        ).to_be_hidden()

        self.logger.info("Signing in with a non admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        self.logger.info("Verifying that the 'Mark as spam' option is not displayed")
        expect(
            self.sumo_pages.question_page.get_mark_as_spam_locator()
        ).to_be_hidden()

        self.logger.info("Deleting user session")
        self.delete_cookies()

        username = super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        )
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Clicking on the 'Mark as spam' option")
        self.sumo_pages.question_page.click_on_mark_as_spam_option()

        self.logger.info("Verifying that the correct spam banner message is displayed")
        check.is_in(
            EditQuestionPageMessages.MARKED_AS_SPAM_BANNER + username,
            self.sumo_pages.question_page.get_marked_as_spam_banner_text()
        )

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Navigating to the posted question and verifying that the 404 is "
                         "returned while signed out")
        with self.page.expect_navigation() as navigation_info:
            self.navigate_to_link(
                question_info['question_page_url']
            )
        response = navigation_info.value
        check.equal(
            response.status,
            404
        )

        self.logger.info("Signing in with a non admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        self.logger.info("Navigating to the posted question and verifying that 404 is returned")
        with self.page.expect_navigation() as navigation_info:
            self.navigate_to_link(
                question_info['question_page_url']
            )
        response = navigation_info.value
        check.equal(
            response.status,
            404
        )

        self.delete_cookies()
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Clicking on the 'Mark as spam' option")
        self.sumo_pages.question_page.click_on_mark_as_spam_option()

        self.logger.info("Verifying that the 'Marked as spam' banner is not displayed")
        expect(
            self.sumo_pages.question_page.get_marked_as_spam_banner_locator()
        ).to_be_hidden()

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Verifying that the 'Marked as spam' banner is not displayed")
        expect(
            self.sumo_pages.question_page.get_marked_as_spam_banner_locator()
        ).to_be_hidden()

        self.logger.info("Signing in with a non admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        self.logger.info("Verifying that the 'Marked as spam' banner is not displayed")
        expect(
            self.sumo_pages.question_page.get_marked_as_spam_banner_locator()
        ).to_be_hidden()

        self.delete_cookies()
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page.click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page.click_delete_this_question_button()

    # C2191096
    @pytest.mark.postedQuestions
    @pytest.mark.parametrize("username", ['', 'TEST_ACCOUNT_13'])
    def test_question_topics(self, username):
        self.logger.info("Signing in with a non admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        self.logger.info("Posting a Firefox product question")
        self.navigate_to_link(super().aaq_question_test_data["products_aaq_url"]["Firefox"])

        question_info = self.sumo_pages.aaq_flow.submit_an_aaq_question_for_a_product(
            subject=super().aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=self.sumo_pages.aaq_form_page.get_aaq_form_topic_options()[0],
            body=super().aaq_question_test_data["valid_firefox_question"]["simple_body_text"],
            attach_image=False
        )

        self.logger.info("Verifying that the 'Add a tag' input field is not displayed for OP")
        expect(
            self.sumo_pages.question_page.get_add_a_tag_input_field()
        ).to_be_hidden()

        self.logger.info("Verifying that the 'Add' topic section button is not displayed for OP")
        expect(
            self.sumo_pages.question_page.get_add_a_tag_button()
        ).to_be_hidden()

        self.logger.info("Deleting user session")
        super().delete_cookies()

        if username == 'TEST_ACCOUNT_13':
            self.logger.info("Signing in with a non admin user account")
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_13"]
            ))

        self.logger.info("Verifying that the 'Add a tag' input field is not displayed")
        expect(
            self.sumo_pages.question_page.get_add_a_tag_input_field()
        ).to_be_hidden()

        self.logger.info("Verifying that the 'Add' topic section button is not displayed")
        expect(
            self.sumo_pages.question_page.get_add_a_tag_button()
        ).to_be_hidden()

        self.logger.info("Verifying that the remove tag button is not displayed")
        for tag in self.sumo_pages.question_page.get_question_tag_options():
            expect(
                self.sumo_pages.question_page.get_remove_tag_button_locator(tag)
            ).to_be_hidden()

        if username == 'TEST_ACCOUNT_13':
            super().delete_cookies()

        self.logger.info("Signing in with a admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Adding data inside the 'Add a tag' input field and selecting the "
                         "option from the dropdown menu")
        self.sumo_pages.question_page.add_text_to_add_a_tag_input_field(
            super().aaq_question_test_data['valid_firefox_question']['custom_tag']
        )

        self.logger.info("Clicking on the 'Add' button")
        self.sumo_pages.question_page.click_on_add_a_tag_button()

        self.logger.info("Verifying that the newly added tag is displayed for all users")
        super().delete_cookies()

        if username == 'TEST_ACCOUNT_13':
            self.logger.info("Signing in with a non admin user account")
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_13"]
            ))

        self.page.reload()
        check.is_in(
            super().aaq_question_test_data['valid_firefox_question']['custom_tag'],
            self.sumo_pages.question_page.get_question_tag_options()
        )

        for question in self.sumo_pages.question_page.get_question_tag_options():
            self.logger.info(f"Clicking on the {question} tag")
            self.sumo_pages.question_page.click_on_a_certain_tag(question)
            self.logger.info("Verifying that the filter is applied to the clicked tag")
            check.equal(
                question,
                self.sumo_pages.product_support_forum._get_text_of_selected_tag_filter_option()
            )

            self.logger.info("Verifying that each listed question inside the product forum "
                             "contains the filtered tab")
            for article_id in self.sumo_pages.product_support_forum._extract_question_ids():
                check.is_in(
                    question,
                    self.sumo_pages.product_support_forum._get_all_question_list_tags(article_id)
                )
            self.navigate_back()

        self.logger.info("Navigate back to the posted question")
        self.navigate_to_link(
            question_info['question_page_url']
        )

        if username == 'TEST_ACCOUNT_13':
            super().delete_cookies()

        self.logger.info("Signing in with a admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.page.reload()
        self.logger.info("Removing the newly added tag")
        self.sumo_pages.question_page.click_on_tag_remove_button(
            super().aaq_question_test_data['valid_firefox_question']['custom_tag']
        )

        self.logger.info("Verifying that the tag was removed")
        expect(
            self.sumo_pages.question_page.get_a_certain_tag(
                super().aaq_question_test_data['valid_firefox_question']['custom_tag']
            )
        ).to_be_hidden()

        self.logger.info("Deleting the user session")
        super().delete_cookies()

        if username == "TEST_ACCOUNT_13":
            self.logger.info("Signing in with a non admin user account")
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_13"]
            ))

        self.logger.info("Verifying that the tag was removed")
        expect(
            self.sumo_pages.question_page.get_a_certain_tag(
                super().aaq_question_test_data['valid_firefox_question']['custom_tag']
            )
        ).to_be_hidden()

        if username == "TEST_ACCOUNT_13":
            super().delete_cookies()

        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page.click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page.click_delete_this_question_button()

    # C2191091
    @pytest.mark.postedQuestions
    def test_email_updates_option_visibility(self):
        self.logger.info("Signing in with a non admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_13"]
        ))

        self.logger.info("Posting a Firefox product question")
        self.navigate_to_link(super().aaq_question_test_data["products_aaq_url"]["Firefox"])

        self.sumo_pages.aaq_flow.submit_an_aaq_question_for_a_product(
            subject=super().aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=self.sumo_pages.aaq_form_page.get_aaq_form_topic_options()[0],
            body=super().aaq_question_test_data["valid_firefox_question"]["simple_body_text"],
            attach_image=False
        )

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Verifying that the 'Get email updates' option is displayed")
        expect(
            self.sumo_pages.question_page.get_email_updates_option()
        ).to_be_visible()

        self.logger.info("Signing in with another non admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        self.logger.info("Verifying that the 'Get email updates' option is displayed")
        expect(
            self.sumo_pages.question_page.get_email_updates_option()
        ).to_be_visible()

        self.logger.info("Deleting user session")
        super().delete_cookies()

        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Verifying that the 'Get email updates' option is displayed")
        expect(
            self.sumo_pages.question_page.get_email_updates_option()
        ).to_be_visible()

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page.click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page.click_delete_this_question_button()
