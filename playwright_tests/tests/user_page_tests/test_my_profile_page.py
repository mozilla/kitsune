import allure
import pytest
from pytest_check import check
from playwright.sync_api import expect

from playwright_tests.core.testutilities import TestUtilities
from playwright_tests.messages.homepage_messages import HomepageMessages
from playwright_tests.messages.my_profile_pages_messages.my_profile_page_messages import (
    MyProfileMessages)
from playwright_tests.messages.my_profile_pages_messages.user_profile_navbar_messages import (
    UserProfileNavbarMessages)


class TestMyProfilePage(TestUtilities):
    # C891409
    @pytest.mark.userProfile
    def test_my_profile_page_can_be_accessed_via_top_navbar(self):
        with allure.step("Signing in with a non-admin user account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_12']
            ))

        original_username = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        with allure.step("Accessing the 'My profile' page and verifying that we are redirected "
                         "to the correct profile"):
            self.sumo_pages.top_navbar._click_on_view_profile_option()
            expect(
                self.page
            ).to_have_url(MyProfileMessages.get_my_profile_stage_url(username=original_username))

        with check, allure.step("Verifying that the page header is the expected one"):
            assert self.sumo_pages.my_profile_page._get_my_profile_page_header(
            ) == MyProfileMessages.STAGE_MY_PROFILE_PAGE_HEADER

        with check, allure.step("Verifying that the 'My profile' navbar option is selected"):
            assert self.sumo_pages.my_profile_page._get_text_of_selected_navbar_option(
            ) == UserProfileNavbarMessages.NAVBAR_OPTIONS[0]

    #  C891411
    @pytest.mark.userProfile
    def test_my_profile_sign_out_button_functionality(self):
        with allure.step("Signing in with a non-admin account"):
            self.sumo_pages.top_navbar._click_on_signin_signup_button()

            self.sumo_pages.auth_flow_page.sign_in_flow(
                username=super().user_special_chars,
                account_password=super().user_secrets_pass
            )

        with allure.step("Accessing the my profile page, clicking on the sign out button and "
                         "verifying that the user is redirected to the homepage"):
            self.sumo_pages.top_navbar._click_on_view_profile_option()
            self.sumo_pages.my_profile_page._click_my_profile_page_sign_out_button()
            expect(
                self.page
            ).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL_EN_US)

        with allure.step("Verify that the 'Sign in/Up' button from the page header is displayed"):
            expect(
                self.sumo_pages.top_navbar._sign_in_up_button_displayed_element()
            ).to_be_visible()

    # C2108828
    @pytest.mark.userProfile
    def test_provided_solutions_number_is_successfully_displayed(self):
        with allure.step("Signing in with an admin user account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        repliant_username = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        with allure.step("Navigating to the Firefox AAQ form and posting a new AAQ question for "
                         "the Firefox product"):
            self.navigate_to_link(
                super().aaq_question_test_data["products_aaq_url"]["Firefox"]
            )
            question_info = (
                self.sumo_pages.aaq_flow.submit_an_aaq_question(
                    subject=super().aaq_question_test_data["valid_firefox_question"]["subject"],
                    topic_name=super(
                    ).aaq_question_test_data["valid_firefox_question"]["topic_value"],
                    body=super().aaq_question_test_data["valid_firefox_question"]["question_body"]
                )
            )

        with allure.step("Navigating to the user profile page and extracting the original number "
                         "of posted question solutions"):
            self.sumo_pages.top_navbar._click_on_view_profile_option()
            original_number_of_solutions = self.number_extraction_from_string(
                self.sumo_pages.my_profile_page._get_my_profile_solutions_text()
            )

        with allure.step("Navigating to the previously posted question and posting a reply to it"):
            self.navigate_to_link(question_info["question_page_url"])
            question_test_data = super().question_test_data
            self.sumo_pages.question_page._add_text_to_post_a_reply_textarea(
                question_test_data["question_reply_solution"]
            )
            answer_id = self.sumo_pages.question_page._click_on_post_reply_button(
                repliant_username=repliant_username
            )

        with allure.step("Marking the reply as the question solution"):
            self.sumo_pages.question_page._click_on_solves_the_problem_button(
                target_reply_id=answer_id)

        with allure.step("Accessing the 'My profile' page of the account which provided the "
                         "solution and verifying that the original number of solutions has "
                         "incremented"):
            self.sumo_pages.top_navbar._click_on_view_profile_option()
            self.number_extraction_from_string(
                self.sumo_pages.my_profile_page._get_my_profile_solutions_text()
            )
            assert (self.number_extraction_from_string(
                self.sumo_pages.my_profile_page._get_my_profile_solutions_text(
                )) == original_number_of_solutions + 1
            )

        with allure.step("Deleting the posted question and verifying that we are redirected to "
                         "the product support forum page after deletion"):
            self.navigate_to_link(question_info["question_page_url"])
            self.sumo_pages.question_page._click_delete_this_question_question_tools_option()
            self.sumo_pages.question_page._click_delete_this_question_button()
            expect(
                self.sumo_pages.product_support_page._product_product_title_element()
            ).to_be_visible()

    # C890832,  C2094281
    @pytest.mark.userProfile
    def test_number_of_my_profile_answers_is_successfully_displayed(self):
        with allure.step("Signing in with an admin user"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        repliant_user = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        with allure.step("Accessing the 'My profile' page and extracting the number of posted "
                         "answers"):
            self.sumo_pages.top_navbar._click_on_view_profile_option()
            original_number_of_answers = self.number_extraction_from_string(
                self.sumo_pages.my_profile_page._get_my_profile_answers_text()
            )

        with allure.step("Navigating to the Firefox AAQ form and posting a new AAQ question"):
            self.navigate_to_link(
                super().aaq_question_test_data["products_aaq_url"]["Firefox"]
            )
            question_info = (
                self.sumo_pages.aaq_flow.submit_an_aaq_question(
                    subject=super().aaq_question_test_data["valid_firefox_question"]["subject"],
                    topic_name=super(
                    ).aaq_question_test_data["valid_firefox_question"]["topic_value"],
                    body=super().aaq_question_test_data["valid_firefox_question"]["question_body"]
                )
            )

        with allure.step("Posting a reply for the question"):
            question_test_data = super().question_test_data
            reply_text = question_test_data["non_solution_reply"]
            self.sumo_pages.question_page._add_text_to_post_a_reply_textarea(reply_text)
            answer_id = self.sumo_pages.question_page._click_on_post_reply_button(
                repliant_username=repliant_user
            )

        with allure.step("Accessing the 'My profile' page and verifying that the number of "
                         "answers has incremented successfully"):
            self.sumo_pages.question_page._click_on_the_reply_author(answer_id)
            self.number_extraction_from_string(
                self.sumo_pages.my_profile_page._get_my_profile_answers_text()
            )
            assert (
                self.number_extraction_from_string(
                    self.sumo_pages.my_profile_page._get_my_profile_answers_text()
                ) == original_number_of_answers + 1
            )

        with allure.step("Clicking on the my profile answers and verifying that the posted "
                         "answer is successfully displayed inside the list"):
            self.sumo_pages.my_profile_page._click_my_profile_answers_link()
            assert reply_text == self.sumo_pages.my_answers_page._get_my_answer_text(
                answer_id=answer_id
            ), "My question reply is not displayed inside the my profile answers list"

        with allure.step("Deleting the posted question and verifying that the user is redirected "
                         "to the product support forum page"):
            self.navigate_to_link(question_info["question_page_url"])
            self.sumo_pages.question_page._click_delete_this_question_question_tools_option()
            self.sumo_pages.question_page._click_delete_this_question_button()
            expect(
                self.sumo_pages.product_support_page._product_product_title_element()
            ).to_be_visible()

    #  C2094285, C2094284, C891309
    @pytest.mark.userProfile
    def test_number_of_posted_articles_is_successfully_displayed(self):
        with allure.step("Signing in with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Accessing the profile page and extracting the number of documents"):
            self.sumo_pages.top_navbar._click_on_view_profile_option()
            original_number_of_documents = self.number_extraction_from_string(
                self.sumo_pages.my_profile_page._get_my_profile_documents_text()
            )

        with allure.step("Creating a kb article"):
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        with allure.step("Accessing the profile page and verifying that the number of posted "
                         "documents has incremented"):
            self.sumo_pages.top_navbar._click_on_view_profile_option()
            assert (
                self.number_extraction_from_string(
                    self.sumo_pages.my_profile_page._get_my_profile_documents_text()
                ) == original_number_of_documents + 1
            )

        with allure.step("Clicking on my posted documents link and verifying that the posted "
                         "document is listed"):
            self.sumo_pages.my_profile_page._click_on_my_profile_document_link()
            assert (
                article_details['article_title'] in self.sumo_pages.my_documents_page.
                _get_text_of_document_links()
            )

        with allure.step("Deleting the article"):
            self.sumo_pages.my_documents_page._click_on_a_particular_document(
                article_details['article_title']
            )
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C1491023
    @pytest.mark.userProfile
    def test_accounts_with_symbols_are_getting_a_corresponding_valid_username(self):
        with allure.step("Signing in with an account that contains SUMO-supported and "
                         "unsupported characters"):
            self.sumo_pages.top_navbar._click_on_signin_signup_button()

            username = self.username_extraction_from_email(
                self.remove_character_from_string(
                    self.sumo_pages.auth_flow_page.sign_in_flow(
                        username=super().user_special_chars,
                        account_password=super().user_secrets_pass
                    ),
                    "*",
                ))

        with allure.step("Verifying that the username contains the supported characters and "
                         "doesn't contain the unsupported ones in top navbar"):
            assert self.sumo_pages.top_navbar._get_text_of_logged_in_username() == username

        with allure.step("Verifying that the username contains the supported characters and "
                         "doesn't contain the unsupported ones in My Profile page"):
            self.sumo_pages.top_navbar._click_on_view_profile_option()
            assert (self.sumo_pages.my_profile_page._get_my_profile_display_name_header_text()
                    == username)

        with allure.step("Verifying that the username contains the supported characters and "
                         "doesn't contain the unsupported ones in Edit my Profile page"):
            self.sumo_pages.top_navbar._click_on_edit_profile_option()
            assert (self.sumo_pages.edit_my_profile_page._get_username_input_field_value(
            ) == username)
