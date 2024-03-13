import allure
import pytest

from playwright.sync_api import expect
from playwright_tests.core.testutilities import TestUtilities
from playwright_tests.messages.my_profile_pages_messages.my_questions_page_messages import (
    MyQuestionsPageMessages)


class TestMyQuestions(TestUtilities):
    #  C2094280,  C890790
    @pytest.mark.userQuestions
    def test_number_of_questions_is_incremented_when_posting_a_question(self):
        with allure.step("Signing in with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Accessing the 'My profile' page and extracting the original number of "
                         "posted questions"):
            self.sumo_pages.top_navbar._click_on_view_profile_option()
            original_number_of_questions = self.number_extraction_from_string(
                self.sumo_pages.my_profile_page._get_my_profile_questions_text()
            )

        with allure.step("Navigating to the AAQ form and posting a new AAQ question"):
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

        with allure.step("Navigating back to the profile page and verifying that the number of "
                         "questions has incremented"):
            self.sumo_pages.top_navbar._click_on_view_profile_option()
            new_number = self.number_extraction_from_string(
                self.sumo_pages.my_profile_page._get_my_profile_questions_text()
            )
            assert new_number == original_number_of_questions + 1

        with allure.step("Deleting the posted question"):
            self.navigate_to_link(question_info["question_page_url"])
            self.sumo_pages.question_page._click_delete_this_question_question_tools_option()
            self.sumo_pages.question_page._click_delete_this_question_button()

        with allure.step("Verifying that we are on the product support forum page after deletion"):
            expect(
                self.sumo_pages.product_support_page._product_product_title_element()
            ).to_be_visible()

        # write tests to check my questions section as well

    # C1296000, #  C890790
    @pytest.mark.userQuestions
    def test_my_contributions_questions_reflects_my_questions_page_numbers(self):
        with allure.step("Signing in with a non-admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))

        with allure.step("Accessing the 'My profile' and extracting the number of questions "
                         "listed inside the my profile page"):
            self.sumo_pages.top_navbar._click_on_view_profile_option()
            number_of_questions = self.number_extraction_from_string(
                self.sumo_pages.my_profile_page._get_my_profile_questions_text()
            )

        with allure.step("Clicking on the my profile questions link and verifying that the "
                         "number of questions from the my profile page matches the one from the "
                         "ones from my questions page"):
            self.sumo_pages.my_profile_page._click_on_my_profile_questions_link()
            assert (number_of_questions
                    == self.sumo_pages.my_questions_page._get_number_of_questions())

    # C890821
    @pytest.mark.userQuestions
    def test_correct_messages_is_displayed_if_user_has_no_posted_questions(self):
        with allure.step("Signing in with a user which has no posted questions"):
            self.sumo_pages.top_navbar._click_on_signin_signup_button()
            self.sumo_pages.auth_flow_page.sign_in_flow(
                username=super().user_special_chars,
                account_password=super().user_secrets_pass
            )

        original_user = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        with allure.step("Accessing the 'My questions' page and verifying that the correct "
                         "message is displayed"):
            self.sumo_pages.top_navbar._click_on_view_profile_option()
            self.sumo_pages.user_navbar._click_on_my_questions_option()
            assert (
                self.sumo_pages.my_questions_page._get_text_of_no_question_message()
                == MyQuestionsPageMessages.NO_POSTED_QUESTIONS_MESSAGE
            )

        with allure.step("Verifying that the question list is not displayed"):
            expect(
                self.sumo_pages.my_questions_page._is_question_list_displayed()
            ).to_be_hidden()

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

        with allure.step("Accessing the my questions page and verifying that the no question "
                         "message is no longer displayed"):
            self.sumo_pages.top_navbar._click_on_view_profile_option()
            self.sumo_pages.user_navbar._click_on_my_questions_option()
            expect(
                self.sumo_pages.my_questions_page._is_no_question_message_displayed()
            ).to_be_hidden()

        with allure.step("Signing in with an admin account and deleting the posted question"):
            self.sumo_pages.top_navbar._click_on_sign_out_button()
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))
            self.navigate_to_link(question_info["question_page_url"])
            self.sumo_pages.question_page._click_delete_this_question_question_tools_option()
            self.sumo_pages.question_page._click_delete_this_question_button()

        with allure.step("Accessing the original user and verifying that the correct message is "
                         "displayed"):
            self.navigate_to_link(
                MyQuestionsPageMessages.get_stage_my_questions_url(original_user)
            )
            assert (
                self.sumo_pages.my_questions_page._get_text_of_no_question_message()
                == MyQuestionsPageMessages.get_no_posted_questions_other_user_message(
                    original_user)
            )

        with allure.step("Signing in with the original user and verifying that the correct "
                         "message and the question list is no longer displayed"):
            self.delete_cookies()
            self.sumo_pages.top_navbar._click_on_signin_signup_button()
            self.sumo_pages.auth_flow_page.sign_in_flow(
                username=super().user_special_chars,
                account_password=super().user_secrets_pass
            )
            self.sumo_pages.top_navbar._click_on_view_profile_option()
            self.sumo_pages.user_navbar._click_on_my_questions_option()
            assert (
                self.sumo_pages.my_questions_page._get_text_of_no_question_message()
                == MyQuestionsPageMessages.NO_POSTED_QUESTIONS_MESSAGE
            )

    #  C890823, C890831
    @pytest.mark.userQuestions
    def test_my_question_page_reflects_posted_questions_and_redirects_to_the_correct_question(
            self,
    ):
        with allure.step("Signing in with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

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

        with allure.step("Navigating to my questions profile page and verifying that the first "
                         "element from the My Questions page is the recently posted question"):
            self.sumo_pages.top_navbar._click_on_my_questions_profile_option()
            assert self.sumo_pages.my_questions_page._get_text_of_first_listed_question().replace(
                " ", ""
            ) == question_info["aaq_subject"].replace(" ", "")

        with allure.step("Clicking on the first list item and verifying that the user is "
                         "redirected to the correct question"):
            self.sumo_pages.my_questions_page._click_on_a_question_by_index(1)
            expect(
                self.page
            ).to_have_url(question_info["question_page_url"])

        # assert self.sumo_pages.question_page.current_url() == question_info[
        # "question_page_url"], ( f"We are on the wrong page. Expected: {question_info} "
        # f"received: {self.sumo_pages.question_page.current_url()}" )

        with allure.step("Deleting the posted question"):
            self.sumo_pages.aaq_flow.deleting_question_flow()
