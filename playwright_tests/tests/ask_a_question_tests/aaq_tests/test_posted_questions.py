import os

import pytest
import pytest_check as check
from playwright_tests.core.testutilities import TestUtilities
from playwright.sync_api import expect

from playwright_tests.messages.contribute_messages.con_tools.moderate_forum_messages import (
    ModerateForumContentPageMessages)
from playwright_tests.messages.ask_a_question_messages.AAQ_messages.question_page_messages import (
    QuestionPageMessages)
from playwright_tests.messages.auth_pages_messages.fxa_page_messages import (
    FxAPageMessages)
from playwright_tests.messages.ask_a_question_messages.contact_support_messages import (
    ContactSupportMessages)


class TestPostedQuestions(TestUtilities):
    # C2191086, C2191094, C2191263,  C2191263, C2191087, C2191088
    @pytest.mark.postedQuestions
    @pytest.mark.parametrize("username", ['TEST_ACCOUNT_13', ''])
    def test_posted_question_details(self, username):
        self.logger.info("Signing in with an admin user account and posting a Firefox product "
                         "question")
        self.post_firefox_product_question_flow('TEST_ACCOUNT_12')

        self.logger.info("Deleting session cookies and signing in with an admin account")
        super().delete_cookies()

        if username == 'TEST_ACCOUNT_13':
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_13"]
            ))
            self.page.reload()

        self.logger.info("Verifying that the scam banner is displayed")
        expect(
            self.sumo_pages.product_solutions_page._get_scam_banner_locator()
        ).to_be_visible()

        self.logger.info("Verifying that the still need help banner is not displayed")
        expect(
            self.sumo_pages.product_solutions_page._get_still_need_help_locator()
        ).to_be_hidden()

        self.logger.info(
            "Verifying that the 'Learn More' button contains the correct link")
        check.equal(
            self.sumo_pages.product_solutions_page._get_scam_alert_banner_link(),
            QuestionPageMessages.AVOID_SCAM_SUPPORT_LEARN_MORE_LINK
        )

        self.logger.info("Deleting session cookies")
        super().delete_cookies()

        self.logger.info("Signing in with an admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Verifying that the scam banner is displayed")
        expect(
            self.sumo_pages.product_solutions_page._get_scam_banner_locator()
        ).to_be_visible()

        self.logger.info("Verifying that the still need help banner is not displayed")
        expect(
            self.sumo_pages.product_solutions_page._get_still_need_help_locator()
        ).to_be_hidden()

        self.logger.info(
            "Verifying that the 'Learn More' button contains the correct link")
        check.equal(
            self.sumo_pages.product_solutions_page._get_scam_alert_banner_link(),
            QuestionPageMessages.AVOID_SCAM_SUPPORT_LEARN_MORE_LINK
        )

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page._click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page._click_delete_this_question_button()

    # C2191092,  C2191263
    @pytest.mark.postedQuestions
    def test_edit_this_question_functionality_not_signed_in(self):
        self.logger.info("Signing in with an admin user account and posting a Firefox product "
                         "question")
        self.post_firefox_product_question_flow('TEST_ACCOUNT_MODERATOR')

        self.logger.info("Deleting session cookies")
        self.delete_cookies()

        self.logger.info("Verifying that the 'edit this question' nav option is not available")

        expect(
            self.sumo_pages.question_page._get_edit_this_question_option_locator()
        ).to_be_hidden()

        self.logger.info("Navigating to the edit endpoint")
        self.navigate_to_link(
            self.get_page_url() + QuestionPageMessages.EDIT_QUESTION_URL_ENDPOINT
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
        self.sumo_pages.question_page._click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page._click_delete_this_question_button()

    # C2191262, C2436105,  C2191263
    # To add image tests
    @pytest.mark.postedQuestions
    @pytest.mark.parametrize("username", ['TEST_ACCOUNT_12', 'TEST_ACCOUNT_MODERATOR'])
    def test_cancel_edit_this_question_functionality(self, username):
        self.logger.info("Signing in with a non admin user account and posting a Firefox product "
                         "question")
        posted_question = self.post_firefox_product_question_flow('TEST_ACCOUNT_12')

        if username == 'TEST_ACCOUNT_MODERATOR':
            self.logger.info("Deleting session cookies and signing in with an admin account")
            super().delete_cookies()

            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        self.navigate_to_link(posted_question['question_details']['question_page_url'])
        self.logger.info("Clicking on the 'Edit this question' option")
        self.sumo_pages.question_page._click_on_edit_this_question_question_tools_option()

        self.logger.info("Verifying that the subject field contains the correct value")
        check.equal(
            self.sumo_pages.aaq_form_page._get_value_of_subject_input_field(),
            posted_question['question_details']['aaq_subject'],
            f"Incorrect question subject displayed. "
            f"Expected: {posted_question['question_details']['aaq_subject']} "
            f"Received: {self.sumo_pages.aaq_form_page._get_value_of_subject_input_field()}"
        )

        self.logger.info("Verifying that the question body contains the correct value")
        check.equal(
            self.sumo_pages.aaq_form_page._get_value_of_question_body_textarea_field(),
            posted_question['question_details']['question_body']
        )

        self.logger.info("Adding text inside the Subject field")
        self.sumo_pages.aaq_form_page._clear_subject_input_field()
        self.sumo_pages.aaq_form_page._add_text_to_aaq_form_subject_field(
            super().aaq_question_test_data['valid_firefox_question']['subject_updated']
        )

        self.logger.info("Adding text inside the body field")
        self.sumo_pages.aaq_form_page._clear_the_question_body_textarea_field()
        self.sumo_pages.aaq_form_page._add_text_to_aaq_textarea_field(
            super().aaq_question_test_data['valid_firefox_question']['body_updated']
        )

        self.logger.info("Adding information inside the troubleshoot information textarea")
        self.sumo_pages.aaq_form_page._add_text_to_troubleshooting_information_textarea(
            super().aaq_question_test_data['troubleshooting_information_textarea_field']
        )

        self.logger.info("Clicking on the 'Cancel' button")
        self.sumo_pages.aaq_form_page._click_aaq_form_cancel_button()

        self.logger.info("Verifying that the 'Modified' text is not displayed")
        expect(
            self.sumo_pages.question_page._get_modified_question_locator()
        ).to_be_hidden()

        self.logger.info("Verifying that the subject and body fields are the same")
        check.equal(
            self.sumo_pages.question_page._get_question_header(),
            posted_question['question_details']['aaq_subject']
        )

        check.equal(
            self.sumo_pages.question_page._get_question_body(),
            posted_question['question_details']['question_body'] + '\n'
        )

        if username == 'TEST_ACCOUNT_12':
            self.logger.info("Verifying that the additional question details option is hidden")
            expect(
                self.sumo_pages.question_page._get_question_details_button_locator()
            ).to_be_hidden()
        elif username == "TEST_ACCOUNT_MODERATOR":
            self.logger.info("Clicking on the 'Question Details' option")
            self.sumo_pages.question_page._click_on_question_details_button()

            self.logger.info("Clicking on the 'More system details' option")
            self.sumo_pages.question_page._click_on_more_system_details_option()

            self.logger.info("Verifying that the more information section is not displayed")
            expect(
                self.sumo_pages.question_page._get_more_information_locator()
            ).to_be_hidden()

            self.logger.info("Closing the more information panel")
            self.sumo_pages.question_page._click_on_the_additional_system_panel_close_button()

        if username != 'TEST_ACCOUNT_MODERATOR':
            self.logger.info("Deleting session cookies and signing in with an admin account")
            super().delete_cookies()

            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page._click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page._click_delete_this_question_button()

    # C2191263
    @pytest.mark.postedQuestions
    def test_edit_other_user_question_non_admin(self):
        self.logger.info("Signing in with a non admin user account and posting a Firefox product "
                         "question")
        posted_question = self.post_firefox_product_question_flow('TEST_ACCOUNT_13')

        self.logger.info("Deleting session cookies")
        self.delete_cookies()

        self.logger.info("Signing in with a non admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        self.logger.info("Verifying that the 'Edit this question' option is not available")
        expect(
            self.sumo_pages.question_page._get_edit_this_question_option_locator()
        ).to_be_hidden()

        self.logger.info("Manually navigating to the '/edit' endpoint and verifying that 403 is "
                         "returned")

        with self.page.expect_navigation() as navigation_info:
            self.navigate_to_link(
                posted_question['question_details']['question_page_url'] + QuestionPageMessages.
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
        self.sumo_pages.question_page._click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page._click_delete_this_question_button()

    # C2191262, C2436105, C2191263
    # To add image tests
    @pytest.mark.postedQuestions
    @pytest.mark.parametrize("username", ['TEST_ACCOUNT_12', 'TEST_ACCOUNT_MODERATOR'])
    def test_edit_this_question_functionality(self, username):
        self.logger.info("Signing in with a non admin user account and posting a Firefox product "
                         "question")
        posted_question = self.post_firefox_product_question_flow('TEST_ACCOUNT_12')
        user = super().username_extraction_from_email(
            self.user_secrets_accounts[username]
        )

        if username == 'TEST_ACCOUNT_MODERATOR':
            self.logger.info("Deleting session cookies and signing in with an admin account")
            super().delete_cookies()

            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        self.navigate_to_link(posted_question['question_details']['question_page_url'])
        self.logger.info("Clicking on the 'Edit this question' option")
        self.sumo_pages.question_page._click_on_edit_this_question_question_tools_option()

        self.logger.info("Verifying that the subject field contains the correct value")
        check.equal(
            self.sumo_pages.aaq_form_page._get_value_of_subject_input_field(),
            posted_question['question_details']['aaq_subject'],
            f"Incorrect question subject displayed. "
            f"Expected: {posted_question['question_details']['aaq_subject']} "
            f"Received: {self.sumo_pages.aaq_form_page._get_value_of_subject_input_field()}"
        )

        self.logger.info("Verifying that the question body contains the correct value")
        check.equal(
            self.sumo_pages.aaq_form_page._get_value_of_question_body_textarea_field(),
            posted_question['question_details']['question_body']

        )

        self.logger.info("Adding text inside the Subject field")
        self.sumo_pages.aaq_form_page._clear_subject_input_field()
        self.sumo_pages.aaq_form_page._add_text_to_aaq_form_subject_field(
            super().aaq_question_test_data['valid_firefox_question']['subject_updated']
        )

        self.logger.info("Adding text inside the body field")
        self.sumo_pages.aaq_form_page._clear_the_question_body_textarea_field()
        self.sumo_pages.aaq_form_page._add_text_to_aaq_textarea_field(
            super().aaq_question_test_data['valid_firefox_question']['body_updated']
        )

        self.logger.info("Adding information inside the troubleshoot information textarea")
        self.sumo_pages.aaq_form_page._add_text_to_troubleshooting_information_textarea(
            super().aaq_question_test_data['troubleshooting_information_textarea_field']
        )

        self.logger.info("Clicking on the 'Submit' button")
        self.sumo_pages.aaq_form_page._click_aaq_edit_submit_button()

        self.logger.info("Verifying that the 'Modified' text is displayed")
        expect(
            self.sumo_pages.question_page._get_modified_question_locator()
        ).to_be_visible()

        self.logger.info("Verifying that the username is displayed inside the modified by text")
        check.is_in(
            user,
            self.sumo_pages.question_page._get_modified_by_text()
        )

        self.logger.info("Verifying that the subject and body are modified")
        check.equal(
            self.sumo_pages.question_page._get_question_header(),
            super().aaq_question_test_data['valid_firefox_question']['subject_updated']
        )

        check.equal(
            self.sumo_pages.question_page._get_question_body(),
            super().aaq_question_test_data['valid_firefox_question']['body_updated'] + '\n'
        )

        if username == 'TEST_ACCOUNT_12':
            self.logger.info("Verifying that the additional question details option is hidden")
            expect(
                self.sumo_pages.question_page._get_question_details_button_locator()
            ).to_be_hidden()
        elif username == "TEST_ACCOUNT_MODERATOR":
            self.logger.info("Clicking on the 'Question Details' option")
            self.sumo_pages.question_page._click_on_question_details_button()

            self.logger.info("Clicking on the 'More system details' option")
            self.sumo_pages.question_page._click_on_more_system_details_option()

            self.logger.info("Verifying that the more information section displays the update")
            expect(
                self.sumo_pages.question_page._get_more_information_with_text_locator(
                    super().aaq_question_test_data['troubleshooting_information_textarea_field']
                )
            ).to_be_visible()

            self.logger.info("Closing the more information panel")
            self.sumo_pages.question_page._click_on_the_additional_system_panel_close_button()

        if username != 'TEST_ACCOUNT_MODERATOR':
            self.logger.info("Deleting session cookies and signing in with an admin account")
            super().delete_cookies()

            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page._click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page._click_delete_this_question_button()

    # C2191263
    @pytest.mark.postedQuestions
    def test_delete_question_cancel_button(self):
        self.logger.info("Signing in with a non admin user account and posting a Firefox product "
                         "question")
        posted_question_one = self.post_firefox_product_question_flow('TEST_ACCOUNT_13')

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Signing in with a non admin user account and posting a Firefox product "
                         "question")
        posted_question_two = self.post_firefox_product_question_flow('TEST_ACCOUNT_12')

        self.navigate_to_link(
            posted_question_one['question_details']['question_page_url']
        )

        self.logger.info("Verifying that the 'Delete this question' option is not available")
        expect(
            self.sumo_pages.question_page._get_delete_this_question_locator()
        ).to_be_hidden()

        self.logger.info("Manually navigating to the delete endpoint and verifying that 403 is "
                         "returned")

        with self.page.expect_navigation() as navigation_info:
            self.navigate_to_link(
                posted_question_one['question_details']
                ['question_page_url'] + QuestionPageMessages.DELETE_QUESTION_URL_ENDPOINT)
        response = navigation_info.value
        check.equal(
            response.status,
            403
        )

        self.navigate_to_link(
            posted_question_two['question_details']['question_page_url']
        )

        self.logger.info("Verifying that the 'Delete this question' option is not available")
        expect(
            self.sumo_pages.question_page._get_delete_this_question_locator()
        ).to_be_hidden()

        self.logger.info("Manually navigating to the delete endpoint and verifying that 403 is "
                         "returned")

        with self.page.expect_navigation() as navigation_info:
            self.navigate_to_link(
                posted_question_one['question_details']
                ['question_page_url'] + QuestionPageMessages.DELETE_QUESTION_URL_ENDPOINT)
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
        self.sumo_pages.question_page._click_delete_this_question_question_tools_option()

        self.logger.info("Clicking on the 'Cancel' button and verifying that we are on the "
                         "question page")

        self.sumo_pages.aaq_form_page._click_aaq_form_cancel_button()

        expect(
            self.page
        ).to_have_url(posted_question_two['question_details']['question_page_url'])

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page._click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page._click_delete_this_question_button()

        self.navigate_to_link(
            posted_question_one['question_details']['question_page_url']
        )

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page._click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page._click_delete_this_question_button()

    # C2191264, C2191265
    # To add coverage for images as well
    @pytest.mark.postedQuestions
    @pytest.mark.parametrize("status", ['locked', 'archived'])
    def test_lock_and_archive_this_question(self, status):
        self.logger.info(f"Executing the {status} question tests")
        self.logger.info("Signing in with a non admin user account")
        self.logger.info("Signing in with a non admin user account and posting a Firefox product "
                         "question")
        posted_question = self.post_firefox_product_question_flow('TEST_ACCOUNT_13')

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
            topic_name=self.sumo_pages.aaq_form_page._get_aaq_form_topic_options()[0],
            body=super().aaq_question_test_data["valid_firefox_question"]["simple_body_text"],
            attach_image=False
        )

        self.navigate_to_link(
            posted_question['question_details']['question_page_url']
        )

        if status == "locked":
            self.logger.info("Verifying that the 'Lock this question' option is not available for "
                             "other posted questions")
            expect(
                self.sumo_pages.question_page._get_lock_this_question_locator()
            ).to_be_hidden()
        elif status == "archived":
            expect(
                self.sumo_pages.question_page._get_archive_this_question_locator()
            ).to_be_hidden()

        self.navigate_to_link(
            question_info_two['question_page_url']
        )

        if status == "locked":
            self.logger.info("Verifying that the 'Lock this question is not available for self "
                             "posted questions")
            expect(
                self.sumo_pages.question_page._get_lock_this_question_locator()
            ).to_be_hidden()
        elif status == "archived":
            expect(
                self.sumo_pages.question_page._get_archive_this_question_locator()
            ).to_be_hidden()

        self.logger.info("Deleting session cookies and signing in with an admin account")
        super().delete_cookies()

        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        if status == "locked":
            self.logger.info("Clicking on the 'Lock this question' option")
            self.sumo_pages.question_page._click_on_lock_this_question_locator()
        elif status == "archived":
            self.logger.info("Clicking on the 'Archive this question' option")
            self.sumo_pages.question_page._click_on_archive_this_question_option()

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Signing in with a different non admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        if status == "locked":
            self.logger.info("Verifying that correct locked thread banner text is displayed")
            check.equal(
                self.sumo_pages.question_page._get_thread_locked_text(),
                QuestionPageMessages.LOCKED_THREAD_BANNER
            )
        elif status == "archived":
            self.logger.info("Verifying that correct archived thread banner text is displayed")
            check.equal(
                self.sumo_pages.question_page._get_thread_locked_text(),
                QuestionPageMessages.ARCHIVED_THREAD_BANNER
            )

        self.logger.info("Clicking on the locked thread link and verifying that we are "
                         "redirected to the correct page")
        self.sumo_pages.question_page._click_on_thread_locked_link()

        expect(
            self.page
        ).to_have_url(ContactSupportMessages.PAGE_URL)

        self.logger.info("Navigating back to the question page")
        self.navigate_back()

        if status == "locked":
            self.logger.info("Verifying that the 'Unlock this question option is not available'")
            expect(
                self.sumo_pages.question_page._get_lock_this_question_locator()
            ).to_be_hidden()
        elif status == "archived":
            expect(
                self.sumo_pages.question_page._get_archive_this_question_locator()
            ).to_be_hidden()

        self.logger.info("Verifying that the post a reply textarea field is not displayed")
        expect(
            self.sumo_pages.question_page._get_post_a_reply_textarea_locator()
        ).to_be_hidden()

        self.logger.info("Verifying that the 'needs more information from the user' checkbox is "
                         "not displayed")
        expect(
            self.sumo_pages.question_page._get_needs_more_information_checkbox_locator()
        ).to_be_hidden()

        self.logger.info("Verifying that the 'Add images section is not displayed'")
        expect(
            self.sumo_pages.question_page._get_add_image_section_locator()
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
        self.sumo_pages.question_page._add_text_to_post_a_reply_textarea(
            super().aaq_question_test_data['valid_firefox_question']['question_reply']
        )

        self.logger.info("Verifying that the 'needs more information from the user' checkbox is "
                         "available")
        expect(
            self.sumo_pages.question_page._get_needs_more_information_checkbox_locator()
        ).to_be_visible()

        self.logger.info("Verifying that the 'Add images' section is available")
        expect(
            self.sumo_pages.question_page._get_add_image_section_locator()
        ).to_be_visible()

        self.logger.info("Clicking on the 'Post a reply button'")
        reply_id = self.sumo_pages.question_page._click_on_post_reply_button(repliant_username)

        self.logger.info("Verifying that posted reply is visible")
        expect(
            self.sumo_pages.question_page._get_posted_reply_locator(reply_id)
        ).to_be_visible()

        self.logger.info("Signing in with a normal user account and verifying that the admin's "
                         "reply is visible")

        self.logger.info("Deleting session cookies and signing in with an admin account")
        super().delete_cookies()

        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        expect(
            self.sumo_pages.question_page._get_posted_reply_locator(reply_id)
        ).to_be_visible()

        self.logger.info("Deleting session cookies and signing in with an admin account")
        super().delete_cookies()

        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        if status == "locked":
            self.logger.info("Unlocking the question")
            self.sumo_pages.question_page._click_on_lock_this_question_locator()
        elif status == "archived":
            self.logger.info("Clicking on the 'Archive this question' option")
            self.sumo_pages.question_page._click_on_archive_this_question_option()

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
            self.sumo_pages.question_page._get_thread_locked_locator()
        ).to_be_hidden()

        self.logger.info("Posting a question reply")
        self.logger.info("Adding text inside the textarea field")
        self.sumo_pages.question_page._add_text_to_post_a_reply_textarea(
            super().aaq_question_test_data['valid_firefox_question']['question_reply']
        )

        self.logger.info("Clicking on the 'Post a reply button'")
        reply_id_two = self.sumo_pages.question_page._click_on_post_reply_button(second_repliant)

        self.logger.info("Verifying that the posted reply is visible")

        expect(
            self.sumo_pages.question_page._get_posted_reply_locator(reply_id_two)
        ).to_be_visible()

        self.logger.info("Deleting session cookies and signing in with an admin account")
        super().delete_cookies()

        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page._click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page._click_delete_this_question_button()

        self.navigate_to_link(
            posted_question['question_details']['question_page_url']
        )

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page._click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page._click_delete_this_question_button()

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
            topic_name=self.sumo_pages.aaq_form_page._get_aaq_form_topic_options()[0],
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
            topic_name=self.sumo_pages.aaq_form_page._get_aaq_form_topic_options()[0],
            body=super().aaq_question_test_data["valid_firefox_question"]["simple_body_text"],
            attach_image=False
        )

        self.navigate_to_link(
            question_info_one['question_page_url']
        )

        self.logger.info("Clicking on the 'Subscribe to feed' option from different user posted "
                         "question")
        if self.browser == "chrome":
            self.sumo_pages.question_page._click_on_subscribe_to_feed_option()
            self.logger.info("Verifying that the url is updated to the feed endpoint")
            expect(
                self.page
            ).to_have_url(
                question_info_one['question_page_url'] + QuestionPageMessages.FEED_FILE_PATH
            )
        else:
            with self.page.expect_download() as download_info:
                self.sumo_pages.question_page._click_on_subscribe_to_feed_option()
            download = download_info.value

            self.logger.info("Verifying that the received file contains the correct name")
            check.is_in(
                QuestionPageMessages.FEED_FILE_NAME,
                download.suggested_filename,
                f"Incorrect file name. "
                f"Expected: {QuestionPageMessages.FEED_FILE_NAME} "
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
            self.sumo_pages.question_page._click_on_subscribe_to_feed_option()
            self.logger.info("Verifying that the url is updated to the feed endpoint")
            expect(
                self.page
            ).to_have_url(
                question_info_two['question_page_url'] + QuestionPageMessages.FEED_FILE_PATH
            )
            self.navigate_back()
        else:
            with self.page.expect_download() as download_info:
                self.sumo_pages.question_page._click_on_subscribe_to_feed_option()
            download = download_info.value

            self.logger.info("Verifying that the received file contains the correct name")
            check.is_in(
                QuestionPageMessages.FEED_FILE_NAME,
                download.suggested_filename,
                f"Incorrect file name. "
                f"Expected: {QuestionPageMessages.FEED_FILE_NAME} "
                f"Received: {download.suggested_filename}"
            )

            self.logger.info("Verifying that the received file is not empty")
            assert (
                os.path.getsize(download.path()) > 0
            )

        self.logger.info("Signing out")
        super().delete_cookies()

        if self.browser == "chrome":
            self.sumo_pages.question_page._click_on_subscribe_to_feed_option()
            self.logger.info("Verifying that the url is updated to the feed endpoint")
            expect(
                self.page
            ).to_have_url(
                question_info_two['question_page_url'] + QuestionPageMessages.FEED_FILE_PATH
            )
            self.navigate_back()
        else:
            with self.page.expect_download() as download_info:
                self.sumo_pages.question_page._click_on_subscribe_to_feed_option()
            download = download_info.value

            self.logger.info("Verifying that the received file contains the correct name")
            check.is_in(
                QuestionPageMessages.FEED_FILE_NAME,
                download.suggested_filename,
                f"Incorrect file name. "
                f"Expected: {QuestionPageMessages.FEED_FILE_NAME} "
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
            self.sumo_pages.question_page._click_on_subscribe_to_feed_option()
            self.logger.info("Verifying that the url is updated to the feed endpoint")
            expect(
                self.page
            ).to_have_url(
                question_info_two['question_page_url'] + QuestionPageMessages.FEED_FILE_PATH
            )
            self.navigate_back()
        else:
            with self.page.expect_download() as download_info:
                self.sumo_pages.question_page._click_on_subscribe_to_feed_option()
            download = download_info.value

            self.logger.info("Verifying that the received file contains the correct name")
            check.is_in(
                QuestionPageMessages.FEED_FILE_NAME,
                download.suggested_filename,
                f"Incorrect file name. "
                f"Expected: {QuestionPageMessages.FEED_FILE_NAME} "
                f"Received: {download.suggested_filename}"
            )

            self.logger.info("Verifying that the received file is not empty")
            assert (
                os.path.getsize(download.path()) > 0
            )

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page._click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page._click_delete_this_question_button()

        self.navigate_to_link(
            question_info_one['question_page_url']
        )

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page._click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page._click_delete_this_question_button()

    # To work on adding a check inside the moderate forum content page
    # C2191491
    @pytest.mark.postedQuestions
    def test_mark_as_spam_functionality(self):
        self.logger.info("Signing in with a non admin user account and posting a Firefox product "
                         "question")
        posted_question = self.post_firefox_product_question_flow('TEST_ACCOUNT_12')

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Verifying that the 'Mark as spam' option is not displayed")
        expect(
            self.sumo_pages.question_page._get_mark_as_spam_locator()
        ).to_be_hidden()

        self.logger.info("Signing in with a non admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        self.logger.info("Verifying that the 'Mark as spam' option is not displayed")
        expect(
            self.sumo_pages.question_page._get_mark_as_spam_locator()
        ).to_be_hidden()

        self.logger.info("Deleting user session")
        self.delete_cookies()

        username = self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Clicking on the 'Mark as spam' option")
        self.sumo_pages.question_page._click_on_mark_as_spam_option()

        self.logger.info("Verifying that the correct spam banner message is displayed")
        check.is_in(
            QuestionPageMessages.MARKED_AS_SPAM_BANNER + username,
            self.sumo_pages.question_page._get_marked_as_spam_banner_text()
        )

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Navigating to the posted question and verifying that the 404 is "
                         "returned while signed out")
        with self.page.expect_navigation() as navigation_info:
            self.navigate_to_link(
                posted_question['question_details']['question_page_url']
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
                posted_question['question_details']['question_page_url']
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
        self.sumo_pages.question_page._click_on_mark_as_spam_option()

        self.logger.info("Verifying that the 'Marked as spam' banner is not displayed")
        expect(
            self.sumo_pages.question_page._get_marked_as_spam_banner_locator()
        ).to_be_hidden()

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Verifying that the 'Marked as spam' banner is not displayed")
        expect(
            self.sumo_pages.question_page._get_marked_as_spam_banner_locator()
        ).to_be_hidden()

        self.logger.info("Signing in with a non admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        self.logger.info("Verifying that the 'Marked as spam' banner is not displayed")
        expect(
            self.sumo_pages.question_page._get_marked_as_spam_banner_locator()
        ).to_be_hidden()

        self.delete_cookies()
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page._click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page._click_delete_this_question_button()

    # C2191096, C2191098, C2191100
    @pytest.mark.postedQuestions
    @pytest.mark.parametrize("username", ['', 'TEST_ACCOUNT_13'])
    def test_question_topics(self, username):
        self.logger.info("Signing in with a non admin user account and posting a Firefox product "
                         "question")
        posted_question = self.post_firefox_product_question_flow('TEST_ACCOUNT_12')

        self.logger.info("Verifying that the 'Add a tag' input field is not displayed for OP")
        expect(
            self.sumo_pages.question_page._get_add_a_tag_input_field()
        ).to_be_hidden()

        self.logger.info("Verifying that the 'Add' topic section button is not displayed for OP")
        expect(
            self.sumo_pages.question_page._get_add_a_tag_button()
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
            self.sumo_pages.question_page._get_add_a_tag_input_field()
        ).to_be_hidden()

        self.logger.info("Verifying that the 'Add' topic section button is not displayed")
        expect(
            self.sumo_pages.question_page._get_add_a_tag_button()
        ).to_be_hidden()

        self.logger.info("Verifying that the remove tag button is not displayed")
        for tag in self.sumo_pages.question_page._get_question_tag_options():
            expect(
                self.sumo_pages.question_page._get_remove_tag_button_locator(tag)
            ).to_be_hidden()

        if username == 'TEST_ACCOUNT_13':
            super().delete_cookies()

        self.logger.info("Signing in with a admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Adding data inside the 'Add a tag' input field and selecting the "
                         "option from the dropdown menu")
        self.sumo_pages.question_page._add_text_to_add_a_tag_input_field(
            super().aaq_question_test_data['valid_firefox_question']['custom_tag']
        )

        self.logger.info("Clicking on the 'Add' button")
        self.sumo_pages.question_page._click_on_add_a_tag_button()
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
            self.sumo_pages.question_page._get_question_tag_options()
        )

        for question in self.sumo_pages.question_page._get_question_tag_options():
            self.logger.info(f"Clicking on the {question} tag")
            self.sumo_pages.question_page._click_on_a_certain_tag(question)
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
            posted_question['question_details']['question_page_url']
        )

        if username == 'TEST_ACCOUNT_13':
            super().delete_cookies()

        self.logger.info("Signing in with a admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.page.reload()
        self.logger.info("Removing the newly added tag")
        self.sumo_pages.question_page._click_on_tag_remove_button(
            super().aaq_question_test_data['valid_firefox_question']['custom_tag']
        )

        # Adding a custom wait to avoid test flakiness.
        self.wait_for_given_timeout(1000)

        self.logger.info("Verifying that the tag was removed")
        expect(
            self.sumo_pages.question_page._get_a_certain_tag(
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
            self.sumo_pages.question_page._get_a_certain_tag(
                super().aaq_question_test_data['valid_firefox_question']['custom_tag']
            )
        ).to_be_hidden()

        if username == "TEST_ACCOUNT_13":
            super().delete_cookies()

        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page._click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page._click_delete_this_question_button()

    # C2191091
    @pytest.mark.postedQuestions
    def test_email_updates_option_visibility(self):
        self.logger.info("Signing in with a non admin user account and posting a Firefox product "
                         "question")
        self.post_firefox_product_question_flow('TEST_ACCOUNT_12')

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Verifying that the 'Get email updates' option is displayed")
        expect(
            self.sumo_pages.question_page._get_email_updates_option()
        ).to_be_visible()

        self.logger.info("Signing in with another non admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        self.logger.info("Verifying that the 'Get email updates' option is displayed")
        expect(
            self.sumo_pages.question_page._get_email_updates_option()
        ).to_be_visible()

        self.logger.info("Deleting user session")
        super().delete_cookies()

        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Verifying that the 'Get email updates' option is displayed")
        expect(
            self.sumo_pages.question_page._get_email_updates_option()
        ).to_be_visible()

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page._click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page._click_delete_this_question_button()

    # C2191268
    @pytest.mark.postedQuestions
    def test_mark_reply_as_spam(self):
        self.logger.info("Signing in with a non admin user account and posting a Firefox product "
                         "question")
        posted_question = self.post_firefox_product_question_flow('TEST_ACCOUNT_12')

        self.logger.info("Posting a reply to the question")
        self.sumo_pages.question_page._add_text_to_post_a_reply_textarea(
            super().aaq_question_test_data['valid_firefox_question']['question_reply']
        )
        reply_id_one = self.sumo_pages.question_page._click_on_post_reply_button(
            posted_question['username_one']
        )

        self.logger.info("Deleting user session")
        super().delete_cookies()

        self.logger.info("Signin in with a different non admin user")
        username_two = self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_13"]
        ))

        self.logger.info("Posting a reply to the question")
        self.sumo_pages.question_page._add_text_to_post_a_reply_textarea(
            super().aaq_question_test_data['valid_firefox_question']['question_reply']
        )
        reply_id_two = self.sumo_pages.question_page._click_on_post_reply_button(username_two)

        self.logger.info("Clicking on the self reply menu and verifying that the 'mark as spam' "
                         "option is not displayed for non-admin users")

        self.sumo_pages.question_page._click_on_reply_more_options_button(reply_id_two)
        expect(
            self.sumo_pages.question_page._get_mark_as_spam_reply_locator(reply_id_two)
        ).to_be_hidden()

        self.logger.info("Closing the dropdown menu")
        self.sumo_pages.question_page._click_on_reply_more_options_button(reply_id_two)

        self.logger.info("Clicking on other user posted reply menu and verifying that the 'mark "
                         "as spam' option is not displayed for non-admin users")
        self.sumo_pages.question_page._click_on_reply_more_options_button(reply_id_one)
        expect(
            self.sumo_pages.question_page._get_mark_as_spam_reply_locator(reply_id_one)
        ).to_be_hidden()

        self.logger.info("Closing the dropdown menu")
        self.sumo_pages.question_page._click_on_reply_more_options_button(reply_id_one)

        self.logger.info("Deleting user session")
        super().delete_cookies()

        self.logger.info("Signing in with an admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Clicking on the 'Mark as Spam' option for one of the replies")
        self.sumo_pages.question_page._click_on_reply_more_options_button(reply_id_one)
        self.sumo_pages.question_page._click_on_mark_as_spam_for_a_certain_reply(reply_id_one)

        self.logger.info("Verifying that the 'Marked as spam' message is displayed for that reply")
        check.equal(
            self.sumo_pages.question_page._get_marked_as_spam_text(reply_id_one),
            QuestionPageMessages.REPLY_MARKED_AS_SPAM_MESSAGE
        )

        self.logger.info("Deleting user session")
        super().delete_cookies()

        self.logger.info("Verifying that the reply marked as spam is no longer displayed")
        expect(
            self.sumo_pages.question_page._get_reply_section_locator(reply_id_one)
        ).to_be_hidden()

        self.logger.info("Signing in with a user account and verifying that reply marked as spam "
                         "is no longer displayed")

        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_13"]
        ))
        expect(
            self.sumo_pages.question_page._get_reply_section_locator(reply_id_one)
        ).to_be_hidden()

        self.logger.info("Deleting user session")
        super().delete_cookies()
        self.logger.info("Signing in with the reply OP user account and verifying that the reply "
                         "marked as spam is no longer displayed")

        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        expect(
            self.sumo_pages.question_page._get_reply_section_locator(reply_id_one)
        ).to_be_hidden()

        self.logger.info("Deleting user session")
        super().delete_cookies()

        self.logger.info("Signing in with the admin account and unmarking the reply from spam")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        self.logger.info("Clicking on the 'Mark as Spam' option for one of the replies")
        self.sumo_pages.question_page._click_on_reply_more_options_button(reply_id_one)
        self.sumo_pages.question_page._click_on_mark_as_spam_for_a_certain_reply(reply_id_one)

        self.logger.info("Verifying that the 'Marked as spam' message is no longer displayed")
        expect(
            self.sumo_pages.question_page._get_marked_as_spam_locator(reply_id_one)
        ).to_be_hidden()

        self.logger.info("Deleting user session")
        super().delete_cookies()

        self.logger.info("Verifying that the reply is visible to the logged out users")
        expect(
            self.sumo_pages.question_page._get_reply_section_locator(reply_id_one)
        ).to_be_visible()

        self.logger.info("Verifying that the 'Marked as spam' message is no longer displayed")
        expect(
            self.sumo_pages.question_page._get_marked_as_spam_locator(reply_id_one)
        ).to_be_hidden()

        self.logger.info("Signing in with a different user and verifying that the reply is "
                         "visible again")

        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_13"]
        ))
        expect(
            self.sumo_pages.question_page._get_reply_section_locator(reply_id_one)
        ).to_be_visible()

        self.logger.info("Verifying that the 'Marked as spam' message is no longer displayed")
        expect(
            self.sumo_pages.question_page._get_marked_as_spam_locator(reply_id_one)
        ).to_be_hidden()

        self.logger.info("Deleting user session")
        super().delete_cookies()

        self.logger.info("Signing in with the reply OP and verifying that the reply is visible "
                         "again")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        expect(
            self.sumo_pages.question_page._get_reply_section_locator(reply_id_one)
        ).to_be_visible()

        self.logger.info("Verifying that the 'Marked as spam' message is no longer displayed")
        expect(
            self.sumo_pages.question_page._get_marked_as_spam_locator(reply_id_one)
        ).to_be_hidden()

        self.logger.info("Deleting user session")
        super().delete_cookies()

        self.logger.info("Signing in with the admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page._click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page._click_delete_this_question_button()

    # Need to expand this to contain additional text format.
    # C2191270, C2191259
    @pytest.mark.postedQuestions
    @pytest.mark.parametrize("username", ['TEST_ACCOUNT_13', 'TEST_ACCOUNT_MODERATOR'])
    def test_edit_reply(self, username):
        self.logger.info("Signing in with a non admin user account and posting a Firefox product "
                         "question")
        posted_question = self.post_firefox_product_question_flow('TEST_ACCOUNT_12')

        page_url = self.get_page_url()

        self.logger.info("Posting a reply to the question")
        self.sumo_pages.question_page._add_text_to_post_a_reply_textarea(
            super().aaq_question_test_data['valid_firefox_question']['question_reply']
        )
        reply_id = self.sumo_pages.question_page._click_on_post_reply_button(
            posted_question['username_one']
        )

        self.logger.info("Verifying that the reply contains the correct name and user status")
        check.equal(
            self.sumo_pages.question_page._get_display_name_of_question_reply_author(reply_id),
            posted_question['username_one']
        )

        check.equal(
            self.sumo_pages.question_page._get_displayed_user_title_of_question_reply(reply_id),
            QuestionPageMessages.QUESTION_REPLY_OWNER
        )

        self.logger.info("Deleting user session")
        super().delete_cookies()

        if username == 'TEST_ACCOUNT_13':
            self.logger.info("Signin in with a different non admin user")

            username_two = self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_13"]
            ))

            self.logger.info(
                "Clicking on the more options for the reply posted by another user and "
                "verifying that the 'edit this post' option is not displayed")
            self.sumo_pages.question_page._click_on_reply_more_options_button(reply_id)
            expect(
                self.sumo_pages.question_page._get_edit_this_post_reply_locator(reply_id)
            ).to_be_hidden()

            self.logger.info(
                "Manually navigating to edit reply endpoint and verifying that 403 is "
                "returned")
            self.logger.info(page_url + QuestionPageMessages.EDIT_REPLY_URL + str(
                super().number_extraction_from_string(
                    reply_id
                )))
            with self.page.expect_navigation() as navigation_info:
                self.navigate_to_link(
                    page_url + QuestionPageMessages.EDIT_REPLY_URL + str(
                        super().number_extraction_from_string(
                            reply_id
                        ))
                )
                response = navigation_info.value
                check.equal(
                    response.status,
                    403
                )

            self.logger.info("Navigating back")
            self.navigate_back()
            self.logger.info("Posting a reply to the question")
            self.sumo_pages.question_page._add_text_to_post_a_reply_textarea(
                super().aaq_question_test_data['valid_firefox_question']['question_reply']
            )
            reply_id = self.sumo_pages.question_page._click_on_post_reply_button(username_two)

            self.logger.info(
                "Verifying that the reply contains the correct name and no user status")
            check.equal(
                self.sumo_pages.question_page._get_display_name_of_question_reply_author(reply_id),
                username_two
            )

            expect(
                self.sumo_pages.question_page._get_displayed_user_title_of_question_reply_locator(
                    reply_id
                )
            ).to_be_hidden()
        else:
            username_two = self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        self.logger.info("Clicking on the more options for the OP reply")
        self.sumo_pages.question_page._click_on_reply_more_options_button(reply_id)

        self.logger.info("Clicking on the 'Edit this post option'")
        self.sumo_pages.question_page._click_on_edit_this_post_for_a_certain_reply(reply_id)

        self.logger.info("Verifying that the textarea contains the original reply")
        check.is_in(
            self.sumo_pages.question_page._get_post_a_reply_textarea_text().strip(),
            super().aaq_question_test_data['valid_firefox_question']['question_reply']
        )

        self.logger.info("Clearing the textarea field")
        self.sumo_pages.aaq_form_page._clear_the_question_body_textarea_field()

        self.logger.info("Adding new text inside the textarea field")
        self.sumo_pages.aaq_form_page._add_text_to_aaq_textarea_field(
            super().aaq_question_test_data['valid_firefox_question']['updated_reply']
        )

        self.logger.info("Clicking on the 'Cancel' option")
        self.sumo_pages.aaq_form_page._click_aaq_form_cancel_button()

        self.logger.info("Verifying that the question reply is the original one")
        check.equal(
            self.sumo_pages.question_page._get_posted_reply_text(reply_id).strip(),
            super().aaq_question_test_data['valid_firefox_question']['question_reply']
        )

        self.logger.info("Verifying that the 'Modified by' message is not displayed for the reply")
        expect(
            self.sumo_pages.question_page._get_posted_reply_modified_by_locator(reply_id)
        ).to_be_hidden()

        self.logger.info("Clicking on the more options for the OP reply")
        self.sumo_pages.question_page._click_on_reply_more_options_button(reply_id)

        self.logger.info("Clicking on the 'Edit this post option'")
        self.sumo_pages.question_page._click_on_edit_this_post_for_a_certain_reply(reply_id)

        self.logger.info("Verifying that the textarea contains the original reply")
        check.is_in(
            self.sumo_pages.question_page._get_post_a_reply_textarea_text(),
            super().aaq_question_test_data['valid_firefox_question']['question_reply']
        )

        self.logger.info("Clearing the textarea field")
        self.sumo_pages.aaq_form_page._clear_the_question_body_textarea_field()

        self.logger.info("Adding new text inside the textarea field")
        self.sumo_pages.aaq_form_page._add_text_to_aaq_textarea_field(
            super().aaq_question_test_data['valid_firefox_question']['updated_reply']
        )

        self.logger.info("Clicking on the 'Update Answer' button")
        self.sumo_pages.aaq_form_page._click_on_update_answer_button()

        self.logger.info("Verifying that the reply contains the updated text")
        check.equal(
            self.sumo_pages.question_page._get_posted_reply_text(reply_id).strip(),
            super().aaq_question_test_data['valid_firefox_question']['updated_reply']
        )

        self.logger.info("Verifying that the 'Modified by' message is displayed for the reply")
        check.is_in(
            username_two,
            self.sumo_pages.question_page._get_posted_reply_modified_by_text(reply_id)
        )

        if username == 'TEST_ACCOUNT_13':
            super().delete_cookies()
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page._click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page._click_delete_this_question_button()

    # C2191272
    @pytest.mark.postedQuestions
    @pytest.mark.parametrize("username", ['TEST_ACCOUNT_13', 'TEST_ACCOUNT_MODERATOR'])
    def test_delete_reply(self, username):
        self.logger.info("Signing in with a non admin user account and posting a Firefox product "
                         "question")
        posted_question = self.post_firefox_product_question_flow('TEST_ACCOUNT_12')

        page_url = self.get_page_url()

        self.logger.info("Posting a reply to the question")
        self.sumo_pages.question_page._add_text_to_post_a_reply_textarea(
            super().aaq_question_test_data['valid_firefox_question']['question_reply']
        )
        reply_id = self.sumo_pages.question_page._click_on_post_reply_button(
            posted_question['username_one']
        )

        self.logger.info("Verifying that the 'Delete this post' option is not available for self "
                         "posted reply")
        expect(
            self.sumo_pages.question_page._get_delete_this_post_reply_locator(reply_id)
        ).to_be_hidden()

        self.logger.info("Verifying that manually navigating to the delete page for the posted "
                         "reply returns 403")

        with self.page.expect_navigation() as navigation_info:
            self.navigate_to_link(
                page_url + QuestionPageMessages.DELETE_QUESTION_REPLY_URL + str(
                    super().number_extraction_from_string(
                        reply_id
                    ))
            )
            response = navigation_info.value
            check.equal(
                response.status,
                403
            )

        self.logger.info("Navigating back")
        self.navigate_back()

        self.delete_cookies()
        if username == 'TEST_ACCOUNT_13':
            username_two = self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_13"]
            ))

            self.logger.info("Posting a reply to the question")
            self.sumo_pages.question_page._add_text_to_post_a_reply_textarea(
                super().aaq_question_test_data['valid_firefox_question']['question_reply']
            )
            self.sumo_pages.question_page._click_on_post_reply_button(username_two)

            self.logger.info("Verifying that the 'Delete this post' option is not available for "
                             "replies posted by others")
            expect(
                self.sumo_pages.question_page._get_delete_this_post_reply_locator(reply_id)
            ).to_be_hidden()

            self.logger.info(
                "Verifying that manually navigating to the delete page for the posted "
                "reply returns 403")

            with self.page.expect_navigation() as navigation_info:
                self.navigate_to_link(
                    page_url + QuestionPageMessages.DELETE_QUESTION_REPLY_URL + str(
                        super().number_extraction_from_string(
                            reply_id
                        ))
                )
                response = navigation_info.value
                check.equal(
                    response.status,
                    403
                )

            self.logger.info("Navigating back")
            self.navigate_back()
            self.delete_cookies()

        self.logger.info("Signing in with an admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Clicking on the more options for the reply")
        self.sumo_pages.question_page._click_on_reply_more_options_button(reply_id)

        self.logger.info("Clicking on the 'Delete this post' option")
        self.sumo_pages.question_page._click_on_delete_this_post_for_a_certain_reply(reply_id)

        self.logger.info("Clicking on the cancel delete button")
        self.sumo_pages.question_page._click_on_cancel_delete_button()

        self.logger.info("Verifying that the reply was not deleted")
        expect(
            self.sumo_pages.question_page._get_posted_reply_locator(reply_id)
        ).to_be_visible()

        self.logger.info("Clicking on the more options for the reply")
        self.sumo_pages.question_page._click_on_reply_more_options_button(reply_id)

        self.logger.info("Clicking on the 'Delete this post' option")
        self.sumo_pages.question_page._click_on_delete_this_post_for_a_certain_reply(reply_id)

        self.logger.info("Clicking on the delete button")
        self.sumo_pages.question_page._click_delete_this_question_button()

        self.logger.info("Verifying that the reply is no longer displayed")
        expect(
            self.sumo_pages.question_page._get_posted_reply_locator(reply_id)
        ).to_be_hidden()

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page._click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page._click_delete_this_question_button()

    # C2192383, C2191224
    # Need to re-verify this for signed out case before submitting this
    @pytest.mark.postedQuestions
    def test_i_have_this_problem_too(self):
        self.logger.info("Signing in with a non admin user account and posting a Firefox product "
                         "question")
        self.post_firefox_product_question_flow('TEST_ACCOUNT_12')

        self.logger.info("Verifying that the 'I have this problem too' button is not displayed "
                         "for self posted questions")

        this_problem_counter = self.sumo_pages.question_page._get_i_have_this_problem_too_counter()

        expect(
            self.sumo_pages.question_page._get_i_have_this_problem_too_locator()
        ).to_be_hidden()

        self.logger.info("Deleting user session")
        self.delete_cookies()
        this_problem_counter += 1
        self.logger.info("Clicking on the 'I have this problem too' button while signed out")
        self.sumo_pages.question_page._click_i_have_this_problem_too_button()

        self.logger.info("Reloading the page")
        self.page.reload()

        self.logger.info("Verifying that the 'have this problem' counter has successfully "
                         "incremented")
        check.equal(
            this_problem_counter,
            self.sumo_pages.question_page._get_i_have_this_problem_too_counter()
        )

        self.logger.info("Signing in with a different non admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_13"]
        ))

        self.logger.info("Clicking on the 'I have this problem too' button")
        self.sumo_pages.question_page._click_i_have_this_problem_too_button()

        self.logger.info("Reloading the page")
        self.page.reload()
        this_problem_counter += 1

        self.logger.info("Verifying that the 'have this problem' counter has successfully "
                         "incremented")
        check.equal(
            this_problem_counter,
            self.sumo_pages.question_page._get_i_have_this_problem_too_counter()
        )

        self.logger.info("Verifying that the 'I have this problem too' button is no longer "
                         "displayed")
        expect(
            self.sumo_pages.question_page._get_i_have_this_problem_too_locator()
        ).to_be_hidden()

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Signing in with an admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        this_problem_counter += 1

        self.logger.info("Clicking on the 'I have this problem too' button")
        self.sumo_pages.question_page._click_i_have_this_problem_too_button()

        self.logger.info("Reloading the page")
        self.page.reload()

        self.logger.info("Verifying that the 'have this problem' counter has successfully "
                         "incremented")
        check.equal(
            this_problem_counter,
            self.sumo_pages.question_page._get_i_have_this_problem_too_counter()
        )

        self.logger.info("Verifying that the 'I have this problem too' button is no longer "
                         "displayed")
        expect(
            self.sumo_pages.question_page._get_i_have_this_problem_too_locator()
        ).to_be_hidden()

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page._click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page._click_delete_this_question_button()

    # C2192384
    @pytest.mark.postedQuestions
    def test_solves_this_problem(self):
        self.logger.info("Signing in with a non admin user account and posting a Firefox product "
                         "question")
        posted_question = self.post_firefox_product_question_flow('TEST_ACCOUNT_12')

        self.logger.info("Posting a reply to the question")
        self.sumo_pages.question_page._add_text_to_post_a_reply_textarea(
            super().aaq_question_test_data['valid_firefox_question']['question_reply']
        )
        reply_id = self.sumo_pages.question_page._click_on_post_reply_button(
            posted_question['username_one']
        )

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Verifying that the 'Solved the problem' button is not displayed")
        expect(
            self.sumo_pages.question_page._get_solved_the_problem_button_locator(reply_id)
        ).to_be_hidden()

        self.logger.info("Signing in with a different user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_13"]
        ))

        self.logger.info("Verifying that the 'Solved the problem' button is not displayed")
        expect(
            self.sumo_pages.question_page._get_solved_the_problem_button_locator(reply_id)
        ).to_be_hidden()

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Signing in with the first username")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        self.logger.info("Clicking on the 'Solved the problem' button")
        self.sumo_pages.question_page._click_on_solves_the_problem_button(reply_id)

        self.logger.info("Verifying that the correct banner is displayed")
        check.equal(
            self.sumo_pages.question_page._get_solved_problem_banner_text(),
            QuestionPageMessages.CHOSEN_SOLUTION_BANNER
        )

        self.logger.info("Verifying that the 'Chosen solution is displayed for the reply'")
        check.equal(
            self.sumo_pages.question_page._get_chosen_solution_reply_message(reply_id),
            QuestionPageMessages.CHOSEN_SOLUTION_REPLY_CARD
        )

        self.logger.info("Verifying that the chosen solution reply section has the correct header")
        check.equal(
            self.sumo_pages.question_page._get_problem_solved_section_header_text(),
            QuestionPageMessages.CHOSEN_SOLUTION_CARD
        )

        self.logger.info("Verifying the chosen solution text")
        check.equal(
            self.sumo_pages.question_page._get_chosen_solution_text(),
            super().aaq_question_test_data['valid_firefox_question']['question_reply']
        )

        self.logger.info("Clicking on the 'Read this answer in context' link")
        self.sumo_pages.question_page._click_read_this_answer_in_context_link()

        self.logger.info("Verifying that the page url updates to point out to the posted reply")
        expect(
            self.page
        ).to_have_url(posted_question['question_details']['question_page_url'] + "#" + reply_id)

        self.logger.info("Navigating back")
        self.navigate_back()

        self.logger.info("Clicking the Undo")
        self.sumo_pages.question_page._click_on_undo_button()

        self.logger.info("Verifying that the correct banner is displayed")
        check.equal(
            self.sumo_pages.question_page._get_solved_problem_banner_text(),
            QuestionPageMessages.UNDOING_A_SOLUTION
        )

        self.logger.info("Verifying that the 'Solved the problem' option is not displayed")
        expect(
            self.sumo_pages.question_page._get_chosen_solution_section_locator()
        ).to_be_hidden()

        self.logger.info("Verifying that the 'Chosen solution' banner is not displayed for the "
                         "previously provided solution")
        expect(
            self.sumo_pages.question_page._get_chosen_solution_reply_message_locator(reply_id)
        ).to_be_hidden()

        self.logger.info("Verifying that the 'Undo' option is not available")
        expect(
            self.sumo_pages.question_page._get_undo_button_locator()
        ).to_be_hidden()

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Signing in with an admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Clicking the solved this problem option")
        self.sumo_pages.question_page._click_on_solves_the_problem_button(reply_id)

        self.logger.info("Verifying that the chosen solution text")
        check.equal(
            self.sumo_pages.question_page._get_chosen_solution_text(),
            super().aaq_question_test_data['valid_firefox_question']['question_reply']
        )

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page._click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page._click_delete_this_question_button()

    # Need to add test for preview as well.
    # C2260447, C2260448, C2191244, C2191242
    @pytest.mark.postedQuestions
    @pytest.mark.parametrize("quote_on", ['reply', 'question'])
    def test_quote_reply_functionality(self, quote_on):
        self.logger.info("Signing in with a non admin user account and posting a Firefox product "
                         "question")

        # Using a user which doesn't have any special permissions applied & which doesn't belong to
        # any group in order to catch cases like https://github.com/mozilla/sumo/issues/1676
        posted_question = self.post_firefox_product_question_flow('TEST_ACCOUNT_MESSAGE_6')
        question_id = self.sumo_pages.question_page._get_question_id()

        if quote_on == "reply":
            self.logger.info("Posting a reply to the question")
            self.sumo_pages.question_page._add_text_to_post_a_reply_textarea(
                super().aaq_question_test_data['valid_firefox_question']['question_reply']
            )
            reply_id = self.sumo_pages.question_page._click_on_post_reply_button(
                posted_question['username_one']
            )

        self.logger.info("Deleting user session")
        self.delete_cookies()

        username_two = self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_13"]
        ))

        if quote_on == "reply":
            self.logger.info("Clicking on the more options for the reply")
            self.sumo_pages.question_page._click_on_reply_more_options_button(reply_id)

            self.logger.info("Clicking on 'Quote' option")
            self.sumo_pages.question_page._click_on_quote_for_a_certain_reply(reply_id)
        else:
            self.logger.info("Clicking on the more options for the question")
            self.sumo_pages.question_page._click_on_reply_more_options_button(question_id)

            self.logger.info("Clicking on 'Quote' option")
            self.sumo_pages.question_page._click_on_quote_for_a_certain_reply(question_id)

        self.logger.info("Adding test to the textarea field")
        self.sumo_pages.question_page._type_inside_the_post_a_reply_textarea(
            super().aaq_question_test_data['valid_firefox_question']['updated_reply']
        )

        self.logger.info("Posting the reply")
        quote_id = self.sumo_pages.question_page._click_on_post_reply_button(username_two)

        self.logger.info("Verifying that the original repliant is displayed inside the quote")
        check.is_in(
            posted_question['username_one'],
            self.sumo_pages.question_page._get_posted_quote_reply_username_text(quote_id)
        )

        if quote_on == "reply":
            self.logger.info("Verifying that the original reply is displayed inside the quote")
            check.equal(
                super().aaq_question_test_data['valid_firefox_question']['question_reply'],
                self.sumo_pages.question_page._get_blockquote_reply_text(quote_id).strip()
            )
        else:
            self.logger.info("Verifying that the question details is displayed inside the quote")
            check.equal(
                super().aaq_question_test_data['valid_firefox_question']['simple_body_text'],
                self.sumo_pages.question_page._get_blockquote_reply_text(quote_id).strip()
            )

        self.logger.info("Verifying that the new reply text is also displayed")
        check.equal(
            super().aaq_question_test_data['valid_firefox_question']['updated_reply'],
            self.sumo_pages.question_page._get_posted_reply_text(quote_id).strip()
        )

        self.logger.info("Clicking on the 'said' link")
        self.sumo_pages.question_page._click_posted_reply_said_link(quote_id)

        if quote_on == "reply":
            self.logger.info("Verifying that the correct url is displayed")
            expect(
                self.page
            ).to_have_url(
                posted_question['question_details']['question_page_url'] + "#" + reply_id
            )
        else:
            self.logger.info("Verifying that the correct url is displayed")
            expect(
                self.page
            ).to_have_url(
                posted_question['question_details']['question_page_url'] + "#" + question_id
            )

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Signing in with an admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        if quote_on == "reply":
            self.logger.info("Clicking on the more options for the reply")
            self.sumo_pages.question_page._click_on_reply_more_options_button(reply_id)

            self.logger.info("Clicking on 'Quote' option")
            self.sumo_pages.question_page._click_on_quote_for_a_certain_reply(reply_id)
        else:
            self.logger.info("Clicking on the more options for the reply")
            self.sumo_pages.question_page._click_on_reply_more_options_button(question_id)

            self.logger.info("Clicking on 'Quote' option")
            self.sumo_pages.question_page._click_on_quote_for_a_certain_reply(question_id)

        self.logger.info("Adding test to the textarea field")
        self.sumo_pages.question_page._type_inside_the_post_a_reply_textarea(
            super().aaq_question_test_data['valid_firefox_question']['updated_reply']
        )

        self.logger.info("Posting the reply")
        quote_id = self.sumo_pages.question_page._click_on_post_reply_button(username_two)

        self.logger.info("Verifying that the original repliant is displayed inside the quote")
        check.is_in(
            posted_question['username_one'],
            self.sumo_pages.question_page._get_posted_quote_reply_username_text(quote_id)
        )

        if quote_on == "reply":
            self.logger.info("Verifying that the original reply is displayed inside the quote")
            check.equal(
                super().aaq_question_test_data['valid_firefox_question']['question_reply'],
                self.sumo_pages.question_page._get_blockquote_reply_text(quote_id).strip()
            )
        else:
            self.logger.info("Verifying that the question is displayed inside the quote")
            check.equal(
                super().aaq_question_test_data['valid_firefox_question']['simple_body_text'],
                self.sumo_pages.question_page._get_blockquote_reply_text(quote_id).strip()
            )

        self.logger.info("Verifying that the new reply text is also displayed")
        check.equal(
            super().aaq_question_test_data['valid_firefox_question']['updated_reply'],
            self.sumo_pages.question_page._get_posted_reply_text(quote_id).strip()
        )

        self.logger.info("Clicking on the 'said' link")
        self.sumo_pages.question_page._click_posted_reply_said_link(quote_id)

        if quote_on == "reply":
            self.logger.info("Verifying that the correct url is displayed")
            expect(
                self.page
            ).to_have_url(
                posted_question['question_details']['question_page_url'] + "#" + reply_id
            )
        else:
            self.logger.info("Verifying that the correct url is displayed")
            expect(
                self.page
            ).to_have_url(
                posted_question['question_details']['question_page_url'] + "#" + question_id
            )

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page._click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page._click_delete_this_question_button()

    # To add tests for "I have this problem, too" option
    # C2191117, C2191223, C2191226
    @pytest.mark.postedQuestions
    def test_quote_reply_functionality_signed_out(self):
        self.logger.info("Signing in with a non admin user account and posting a Firefox product "
                         "question")
        posted_question = self.post_firefox_product_question_flow('TEST_ACCOUNT_12')
        question_id = self.sumo_pages.question_page._get_question_id()

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Clicking on the more options for the question")
        self.sumo_pages.question_page._click_on_reply_more_options_button(question_id)

        self.logger.info("Clicking on 'Quote' option for the question")
        self.sumo_pages.question_page._click_on_quote_for_a_certain_reply(question_id)

        self.logger.info("Verifying that the url has updated to contain the correct fragment "
                         "identifier")
        expect(
            self.page
        ).to_have_url(
            posted_question['question_details']['question_page_url'] + "#question-reply")

        self.logger.info("Verifying that the reply textarea field is not displayed")
        expect(
            self.sumo_pages.question_page._get_post_a_reply_textarea_locator()
        ).to_be_hidden()

        self.logger.info("Verifying that the 'Ask a question' signed out card is not displayed")
        expect(
            self.sumo_pages.question_page._ask_a_question_signed_out_card_option_locator()
        ).to_be_hidden()

        self.logger.info("Verifying that the 'I have this problem, too' option is not displayed")
        expect(
            self.sumo_pages.question_page._get_i_have_this_problem_too_signed_out_card_locator()
        ).to_be_hidden()

        self.logger.info("Clicking on the 'start a new question' signed out card link")
        self.sumo_pages.question_page._click_on_start_a_new_question_signed_out_card_link()

        self.logger.info("Verifying that we are redirected to the Contact Support page")
        expect(
            self.page
        ).to_have_url(ContactSupportMessages.PAGE_URL)

        self.logger.info("Navigating back to the question page")
        self.navigate_back()

        self.logger.info("Signing in back with the OP")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts['TEST_ACCOUNT_12']
        ))

        self.logger.info("Posting a reply to the question")
        self.sumo_pages.question_page._add_text_to_post_a_reply_textarea(
            super().aaq_question_test_data['valid_firefox_question']['question_reply']
        )
        reply_id = self.sumo_pages.question_page._click_on_post_reply_button(
            posted_question['username_one']
        )

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Clicking on the more options for the question")
        self.sumo_pages.question_page._click_on_reply_more_options_button(reply_id)

        self.logger.info("Clicking on 'Quote' option for the reply")
        self.sumo_pages.question_page._click_on_quote_for_a_certain_reply(reply_id)

        self.logger.info("Verifying that the url has updated to contain the correct fragment "
                         "identifier")
        expect(
            self.page
        ).to_have_url(
            posted_question['question_details']['question_page_url'] + "#question-reply"
        )

        self.logger.info("Verifying that the reply textarea field is not displayed")
        expect(
            self.sumo_pages.question_page._get_post_a_reply_textarea_locator()
        ).to_be_hidden()

        self.logger.info("Verifying that the 'Ask a question' signed out card is displayed")
        expect(
            self.sumo_pages.question_page._ask_a_question_signed_out_card_option_locator()
        ).to_be_visible()

        self.logger.info("Verifying that the 'I have this problem, too' option is displayed")
        expect(
            self.sumo_pages.question_page._get_i_have_this_problem_too_signed_out_card_locator()
        ).to_be_visible()

        self.logger.info("Clicking on the 'Ask a question' signed out option")
        self.sumo_pages.question_page._click_on_ask_a_question_signed_out_card_option()

        self.logger.info("Verifying that we are redirected to the Contact Support page")
        expect(
            self.page
        ).to_have_url(ContactSupportMessages.PAGE_URL)

        self.logger.info("Navigating back to the question page")
        self.navigate_back()

        self.logger.info("Clicking on the 'log in to your account' link")
        self.sumo_pages.question_page._click_on_log_in_to_your_account_signed_out_card_link()

        self.logger.info("Proceeding with the auth flow with an admin account")
        self.sumo_pages.auth_flow_page.sign_in_flow(
            username=super().user_special_chars,
            account_password=super().user_secrets_pass,
        )

        self.logger.info("Verifying that we are redirected back to the question page")
        expect(
            self.page
        ).to_have_url(posted_question['question_details']['question_page_url'])

        self.logger.info("Verifying that the textarea field is displayed")
        expect(
            self.sumo_pages.question_page._get_post_a_reply_textarea_locator()
        ).to_be_visible()

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Signing in with an admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts['TEST_ACCOUNT_MODERATOR']
        ))

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page._click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page._click_delete_this_question_button()

    # C2191227
    # Currently fails due to https://github.com/mozilla/sumo/issues/1216
    @pytest.mark.skip
    def test_question_reply_votes(self):
        number_of_thumbs_up_votes = 0
        number_of_thumbs_down_votes = 0

        self.logger.info("Signing in with a non admin user account and posting a Firefox product "
                         "question")
        posted_question = self.post_firefox_product_question_flow('TEST_ACCOUNT_12')
        self.sumo_pages.question_page._get_question_id()

        self.logger.info("Posting a reply to the question")
        self.sumo_pages.question_page._add_text_to_post_a_reply_textarea(
            super().aaq_question_test_data['valid_firefox_question']['question_reply']
        )
        reply_id = self.sumo_pages.question_page._click_on_post_reply_button(
            posted_question['username_one']
        )

        self.logger.info("Verifying the vote reply is not available for self posted questions")
        expect(
            self.sumo_pages.question_page._get_reply_votes_section_locator(reply_id)
        ).to_be_hidden()

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Signing in a different user")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts['TEST_ACCOUNT_13']
        ))

        self.logger.info("Verifying that the correct vote header is displayed")
        check.equal(
            self.sumo_pages.question_page._get_reply_vote_heading(reply_id),
            QuestionPageMessages.HELPFUL_VOTE_HEADER
        )

        self.logger.info("Clicking on the 'thumbs up' button")
        self.sumo_pages.question_page._click_reply_vote_thumbs_up_button(reply_id)
        number_of_thumbs_up_votes += 1

        self.logger.info("Verifying that the correct message is displayed")
        check.equal(
            self.sumo_pages.question_page._get_thumbs_up_vote_message(reply_id),
            QuestionPageMessages.THUMBS_UP_VOTE_MESSAGE
        )

        self.logger.info("Refreshing the page")
        self.refresh_page()

        self.logger.info("Verifying that the correct number of thumbs up votes is displayed")
        check.equal(
            int(self.sumo_pages.question_page._get_helpful_count(reply_id)),
            number_of_thumbs_up_votes
        )

        self.logger.info("Verifying that the correct number of thumbs down votes is displayed")
        check.equal(
            int(self.sumo_pages.question_page._get_not_helpful_count(reply_id)),
            number_of_thumbs_down_votes
        )

        self.logger.info("Verifying that the thumbs up button contains the disabled attribute")
        expect(
            self.sumo_pages.question_page._get_thumbs_up_button_locator(reply_id)
        ).to_have_attribute("disabled", "")

        self.logger.info("Verifying that the thumbs down button contains the disabled attribute")
        expect(
            self.sumo_pages.question_page._get_thumbs_down_button_locator(reply_id)
        ).to_have_attribute("disabled", "")

        self.logger.info("Refreshing the page")
        self.refresh_page()

        self.logger.info("Verifying that the correct number of thumbs up votes is displayed")
        check.equal(
            int(self.sumo_pages.question_page._get_helpful_count(reply_id)),
            number_of_thumbs_up_votes
        )

        self.logger.info("Verifying that the correct number of thumbs down votes is displayed")
        check.equal(
            int(self.sumo_pages.question_page._get_not_helpful_count(reply_id)),
            number_of_thumbs_down_votes
        )

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Clicking on the 'thumbs up' button")
        self.sumo_pages.question_page._click_reply_vote_thumbs_up_button(reply_id)
        number_of_thumbs_up_votes += 1

        self.logger.info("Refreshing the page")
        self.refresh_page()

        self.logger.info("Verifying that the correct number of thumbs up votes is displayed")
        check.equal(
            int(self.sumo_pages.question_page._get_helpful_count(reply_id)),
            number_of_thumbs_up_votes
        )

        self.logger.info("Verifying that the correct number of thumbs down votes is displayed")
        check.equal(
            int(self.sumo_pages.question_page._get_not_helpful_count(reply_id)),
            number_of_thumbs_down_votes
        )

        self.logger.info("Verifying that the thumbs up button contains the disabled attribute")
        expect(
            self.sumo_pages.question_page._get_thumbs_up_button_locator(reply_id)
        ).to_have_attribute("disabled", "")

        self.logger.info("Verifying that the thumbs down button contains the disabled attribute")
        expect(
            self.sumo_pages.question_page._get_thumbs_down_button_locator(reply_id)
        ).to_have_attribute("disabled", "")

        self.logger.info("Refreshing the page")
        self.refresh_page()

        self.logger.info("Verifying that the correct number of thumbs up votes is displayed")
        check.equal(
            int(self.sumo_pages.question_page._get_helpful_count(reply_id)),
            number_of_thumbs_up_votes
        )

        self.logger.info("Verifying that the correct number of thumbs down votes is displayed")
        check.equal(
            int(self.sumo_pages.question_page._get_not_helpful_count(reply_id)),
            number_of_thumbs_down_votes
        )

        self.logger.info("Signing in with an admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts['TEST_ACCOUNT_MODERATOR']
        ))

        self.logger.info("Clicking on the vote down button")
        self.sumo_pages.question_page._click_reply_vote_thumbs_down_button(reply_id)
        number_of_thumbs_down_votes += 1

        self.logger.info("Verifying that the correct message is displayed")
        check.equal(
            self.sumo_pages.question_page._get_thumbs_up_vote_message(reply_id),
            QuestionPageMessages.THUMBS_DOWN_VOTE_MESSAGE
        )

        self.logger.info("Refreshing the page")
        self.refresh_page()

        self.logger.info("Verifying that the correct number of thumbs up votes is displayed")
        check.equal(
            int(self.sumo_pages.question_page._get_helpful_count(reply_id)),
            number_of_thumbs_up_votes
        )

        self.logger.info("Verifying that the correct number of thumbs down votes is displayed")
        check.equal(
            int(self.sumo_pages.question_page._get_not_helpful_count(reply_id)),
            number_of_thumbs_down_votes
        )

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page._click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page._click_delete_this_question_button()

    # C2260449, C2260450, C2191243, C2191245
    @pytest.mark.postedQuestions
    @pytest.mark.parametrize("flagged_content, username",
                             [('question_content', 'TEST_ACCOUNT_13'),
                              ('question_content', 'TEST_ACCOUNT_MODERATOR'),
                              ('question_reply', 'TEST_ACCOUNT_13'),
                              ('question_reply', 'TEST_ACCOUNT_MODERATOR')])
    def test_report_abuse(self, flagged_content, username):
        self.logger.info("Signing in with a non admin user account and posting a Firefox product "
                         "question")
        posted_question = self.post_firefox_product_question_flow('TEST_ACCOUNT_12')

        if flagged_content == "question_reply":
            self.logger.info("Posting a reply to the question")
            self.sumo_pages.question_page._add_text_to_post_a_reply_textarea(
                super().aaq_question_test_data['valid_firefox_question']['question_reply']
            )
            reply_id = self.sumo_pages.question_page._click_on_post_reply_button(
                posted_question['username_one']
            )

        self.logger.info("Deleting user session")
        self.delete_cookies()

        if flagged_content == "question_content":
            self.logger.info("Clicking on the more options for the question and verifying that "
                             "the report abuse option is not displayed for signed out users")
            self.sumo_pages.question_page._click_on_reply_more_options_button(
                self.sumo_pages.question_page._get_question_id()
            )
            expect(
                self.sumo_pages.question_page._get_click_on_report_abuse_reply_locator(
                    self.sumo_pages.question_page._get_question_id()
                )
            ).to_be_hidden()

        else:
            self.logger.info("Clicking on the more options for the reply and verifying that the "
                             "report abuse options is not displayed for signed out users")
            self.sumo_pages.question_page._click_on_reply_more_options_button(reply_id)
            expect(
                self.sumo_pages.question_page._get_click_on_report_abuse_reply_locator(reply_id)
            ).to_be_hidden()

        if username == "TEST_ACCOUNT_MODERATOR":
            self.logger.info("Signing in with an admin account")
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_MODERATOR']
            ))
        else:
            self.logger.info("Signing in with an admin account")
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_13']
            ))

        if flagged_content == "question_content":
            self.logger.info("Clicking on the more options for the question")
            self.sumo_pages.question_page._click_on_reply_more_options_button(
                self.sumo_pages.question_page._get_question_id()
            )

            self.logger.info("Clicking on the report abuse option")
            self.sumo_pages.question_page._click_on_report_abuse_for_a_certain_reply(
                self.sumo_pages.question_page._get_question_id()
            )
        else:
            self.logger.info("Clicking on the more options for the question reply")
            self.sumo_pages.question_page._click_on_reply_more_options_button(reply_id)

            self.logger.info("Clicking on the report abuse option")
            self.sumo_pages.question_page._click_on_report_abuse_for_a_certain_reply(reply_id)

        self.logger.info("Adding text inside the report abuse textarea field")
        self.sumo_pages.question_page._add_text_to_report_abuse_textarea(
            super().aaq_question_test_data['valid_firefox_question']['report_abuse_text']
        )

        self.logger.info("Clicking on submit button")
        self.sumo_pages.question_page._click_on_report_abuse_submit_button()

        self.logger.info("Closing the report this modal button")
        self.sumo_pages.question_page._click_abuse_modal_close_button()

        if username == "TEST_ACCOUNT_13":
            self.logger.info("Deleting user cookies and signing in with a admin account")
            self.delete_cookies()
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_MODERATOR']
            ))

        self.logger.info("Navigating to 'Moderate forum content page'")
        self.sumo_pages.top_navbar._click_on_moderate_forum_content_option()

        self.logger.info("Verifying that the question exists inside the moderate forum content "
                         "page")
        expect(
            self.sumo_pages.moderate_forum_content_page._get_flagged_question_locator(
                posted_question['question_details']['aaq_subject']
            )
        ).to_be_visible()

        self.logger.info("Selecting an option from the update status and clicking on the update "
                         "button")
        self.sumo_pages.moderate_forum_content_page._select_update_status_option(
            posted_question['question_details']['aaq_subject'],
            ModerateForumContentPageMessages.UPDATE_STATUS_FIRST_VALUE
        )

        self.logger.info("Clicking on the update button")
        self.sumo_pages.moderate_forum_content_page._click_on_the_update_button(
            posted_question['question_details']['aaq_subject']
        )

        self.logger.info("Verifying that the question no longer exists inside the moderate forum "
                         "content page")
        expect(
            self.sumo_pages.moderate_forum_content_page._get_flagged_question_locator(
                posted_question['question_details']['aaq_subject']
            )
        ).to_be_hidden()

        self.logger.info("Navigating back to the posted question")
        self.navigate_to_link(posted_question['question_details']['question_page_url'])

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page._click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page._click_delete_this_question_button()

    # C2191261
    @pytest.mark.postedQuestions
    def test_common_responses(self):
        self.logger.info("Signing in with a non admin user account and posting a Firefox product "
                         "question")
        self.post_firefox_product_question_flow('TEST_ACCOUNT_12')

        self.logger.info("Deleting session cookies")
        self.delete_cookies()

        self.logger.info("Signing in with a different account")
        username = self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts['TEST_ACCOUNT_13']
        ))

        self.logger.info("Clicking on the 'Common Responses' option")
        self.sumo_pages.question_page._click_on_common_responses_option()

        self.logger.info("Waiting for Network Idle")
        self.wait_for_networkidle()

        self.logger.info("Click on a category")
        self.sumo_pages.question_page._click_on_a_particular_category_option(
            super().aaq_question_test_data["valid_firefox_question"]["common_responses_category"]
        )

        self.logger.info("Searching for a response")
        self.sumo_pages.question_page._type_into_common_responses_search_field(
            super().aaq_question_test_data["valid_firefox_question"]["common_responses_response"]
        )

        self.logger.info("Waiting for Network Idle")
        self.wait_for_networkidle()

        self.logger.info("Verifying that the only item in the category field is the search option")
        response_options = self.sumo_pages.question_page._get_list_of_responses()
        self.logger.info(response_options)
        self.logger.info(self.sumo_pages.question_page._get_list_of_responses())
        assert (
            len(response_options) == 1 and response_options[0] == super().aaq_question_test_data
            ["valid_firefox_question"]["common_responses_response"]
        )

        self.logger.info("Clicking on the response option")
        self.sumo_pages.question_page._click_on_a_particular_response_option(
            super().aaq_question_test_data["valid_firefox_question"]["common_responses_response"]
        )

        self.logger.info("Waiting for Networkidle")
        self.wait_for_networkidle()

        self.logger.info("Clicking on the 'Cancel button'")
        self.sumo_pages.question_page._click_on_common_responses_cancel_button()

        self.logger.info("Verifying that the form textarea does not contain the common response")

        check.equal(
            self.sumo_pages.question_page._get_post_a_reply_textarea_value(),
            "",
            f"Expected to be empty "
            f"Received: {self.sumo_pages.question_page._get_post_a_reply_textarea_value()}"
        )

        self.logger.info("Clicking on the 'Common Responses' option")
        self.sumo_pages.question_page._click_on_common_responses_option()

        self.logger.info("Waiting for NetworkIdle")
        self.wait_for_networkidle()

        self.logger.info("Click on a category")
        self.sumo_pages.question_page._click_on_a_particular_category_option(
            super().aaq_question_test_data["valid_firefox_question"]["common_responses_category"]
        )

        self.logger.info("Searching for a response")
        self.sumo_pages.question_page._type_into_common_responses_search_field(
            super().aaq_question_test_data["valid_firefox_question"]["common_responses_response"]
        )

        self.logger.info("Waiting for NetworkIdle")
        self.wait_for_networkidle()

        self.logger.info("Verifying that the only item in the category field is the search option")
        response_options = self.sumo_pages.question_page._get_list_of_responses()
        assert (
            len(response_options) == 1 and response_options[0] == super().aaq_question_test_data
            ["valid_firefox_question"]["common_responses_response"]
        )

        self.logger.info("Clicking on the response option")
        self.sumo_pages.question_page._click_on_a_particular_response_option(
            super().aaq_question_test_data["valid_firefox_question"]["common_responses_response"]
        )

        self.logger.info("Waiting for Networkidle")
        self.wait_for_networkidle()

        self.sumo_pages.question_page._click_on_switch_to_mode()
        self.logger.info("Waiting for Networkidle")
        self.wait_for_networkidle()

        response = self.sumo_pages.question_page._get_text_of_response_preview()

        self.logger.info("Clicking on the Insert Response button")
        self.sumo_pages.question_page._click_on_common_responses_insert_response_button()

        self.logger.info("Clicking on the post reply button")
        reply_id = self.sumo_pages.question_page._click_on_post_reply_button(username)

        self.logger.info("Verifying that the reply was successfully posted and contains the "
                         "correct data")
        check.is_in(
            self.sumo_pages.question_page._get_text_content_of_reply(reply_id),
            response,
            f"Expected: {self.sumo_pages.question_page._get_text_content_of_reply(reply_id)} "
            f"Received: {response}"
        )

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page._click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page._click_delete_this_question_button()

    def post_firefox_product_question_flow(self, username: str):
        username_one = self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts[username]
        ))

        self.logger.info("Posting a Firefox product question")
        self.navigate_to_link(super().aaq_question_test_data["products_aaq_url"]["Firefox"])

        question_details = self.sumo_pages.aaq_flow.submit_an_aaq_question_for_a_product(
            subject=super().aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=self.sumo_pages.aaq_form_page._get_aaq_form_topic_options()[0],
            body=super().aaq_question_test_data["valid_firefox_question"]["simple_body_text"],
            attach_image=False
        )

        return {"username_one": username_one, "question_details": question_details}
