import pytest

from playwright.sync_api import expect
from playwright_tests.core.testutilities import TestUtilities
from playwright_tests.messages.my_profile_pages_messages.my_questions_page_messages import (
    MyQuestionsPageMessages)


class TestMyQuestions(TestUtilities):
    #  C2094280,  C890790
    @pytest.mark.userQuestions
    def test_number_of_questions_is_incremented_when_posting_a_question(self):
        self.logger.info("Signing in wit a normal user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Accessing the 'My profile' page via the top-navbar menu")
        self.sumo_pages.top_navbar.click_on_view_profile_option()

        self.logger.info("Extracting original number of posted questions")
        original_number_of_questions = self.number_extraction_from_string(
            self.sumo_pages.my_profile_page.get_my_profile_questions_text()
        )

        self.logger.info("Navigating to the Firefox AAQ form")
        self.navigate_to_link(
            super().aaq_question_test_data["products_aaq_url"]["Firefox"]
        )

        self.logger.info("Posting a new AAQ question for Firefox product")
        question_info = (
            self.sumo_pages.aaq_flow.submit_an_aaq_question_for_a_product(
                subject=super().aaq_question_test_data["valid_firefox_question"]["subject"],
                topic_name=super().aaq_question_test_data["valid_firefox_question"]["topic_value"],
                body=super().aaq_question_test_data["valid_firefox_question"]["question_body"]
            )
        )

        self.logger.info("Navigating back to the My Profile page")
        self.sumo_pages.top_navbar.click_on_view_profile_option()
        new_number = self.number_extraction_from_string(
            self.sumo_pages.my_profile_page.get_my_profile_questions_text()
        )

        assert (
            new_number
            == original_number_of_questions + 1
        ), (
            f"The number of questions should have incremented! "
            f"The original number of question was: "
            f"{original_number_of_questions}"
            f" The new number of questions is: "
            f"{new_number}"
        )

        self.logger.info("Deleting the my posted question")
        self.navigate_to_link(question_info["question_page_url"])
        self.sumo_pages.question_page.click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page.click_delete_this_question_button()

        self.logger.info("Verifying that we are on the product support forum page after deletion")

        expect(
            self.sumo_pages.product_support_page._product_product_title_element()
        ).to_be_visible()

        # write tests to check my questions section as well

    # C1296000, #  C890790
    @pytest.mark.userQuestions
    def test_my_contributions_questions_reflects_my_questions_page_numbers(self):
        self.logger.info("Signing in with a normal user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        self.logger.info("Accessing the 'My profile' page via the top-navbar menu")
        self.sumo_pages.top_navbar.click_on_view_profile_option()

        self.logger.info("Extracting the number of questions listed inside the my profile page")

        number_of_questions = self.number_extraction_from_string(
            self.sumo_pages.my_profile_page.get_my_profile_questions_text()
        )

        self.logger.info("Clicking on the my profile questions link")
        self.sumo_pages.my_profile_page.click_on_my_profile_questions_link()

        self.logger.info(
            "Verifying that the number of questions from the"
            " my profile pages matches the ones from my questions "
            "page"
        )

        assert (number_of_questions
                == self.sumo_pages.my_questions_page.get_number_of_questions()), (
            f"The number of questions listed inside the my profile page is:"
            f" {number_of_questions} "
            f"The number of questions listed inside the my questions page is:"
            f" {self.sumo_pages.my_questions_page.get_number_of_questions()}"
        )

    # C890821
    @pytest.mark.userQuestions
    def test_correct_messages_is_displayed_if_user_has_no_posted_questions(self):
        self.logger.info("Signing in with a user which has no posted questions")
        self.sumo_pages.top_navbar.click_on_signin_signup_button()

        self.sumo_pages.auth_flow_page.sign_in_flow(
            username=super().user_special_chars,
            account_password=super().user_secrets_pass
        )

        original_user = self.sumo_pages.top_navbar.get_text_of_logged_in_username()

        self.logger.info("Accessing the 'My questions' page")
        self.sumo_pages.top_navbar.click_on_view_profile_option()
        self.sumo_pages.user_navbar.click_on_my_questions_option()

        self.logger.info("Verifying that the correct message is displayed")

        assert (
            self.sumo_pages.my_questions_page.get_text_of_no_question_message()
            == MyQuestionsPageMessages.NO_POSTED_QUESTIONS_MESSAGE
        ), (
            f"Incorrect message is displayed!. "
            f"Expected: {MyQuestionsPageMessages.NO_POSTED_QUESTIONS_MESSAGE} "
            f"received: {self.sumo_pages.my_questions_page.get_text_of_no_question_message()}"
        )

        self.logger.info("Verifying that a question list is not displayed")

        expect(
            self.sumo_pages.my_questions_page.is_question_list_displayed()
        ).to_be_hidden()

        self.logger.info("Navigating to the Firefox AAQ form")
        self.navigate_to_link(
            super().aaq_question_test_data["products_aaq_url"]["Firefox"]
        )

        self.logger.info("Posting a new AAQ question for Firefox product")
        question_info = (
            self.sumo_pages.aaq_flow.submit_an_aaq_question_for_a_product(
                subject=super().aaq_question_test_data["valid_firefox_question"]["subject"],
                topic_name=super().aaq_question_test_data["valid_firefox_question"]["topic_value"],
                body=super().aaq_question_test_data["valid_firefox_question"]["question_body"]
            )
        )

        self.logger.info(
            "Accessing the my questions page and verifying that the "
            "no questions message is no longer displayed"
        )

        self.sumo_pages.top_navbar.click_on_view_profile_option()
        self.sumo_pages.user_navbar.click_on_my_questions_option()

        expect(
            self.sumo_pages.my_questions_page.is_no_question_message_displayed()
        ).to_be_hidden()

        self.logger.info("Signing in with a moderator account")
        self.sumo_pages.top_navbar.click_on_sign_out_button()

        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Deleting the my posted question")
        self.navigate_to_link(question_info["question_page_url"])
        self.sumo_pages.question_page.click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page.click_delete_this_question_button()

        self.logger.info(
            "Accessing the original user and verifying that the correct message is displayed"
        )
        self.navigate_to_link(
            MyQuestionsPageMessages.get_stage_my_questions_url(original_user)
        )

        assert (
            self.sumo_pages.my_questions_page.get_text_of_no_question_message()
            == MyQuestionsPageMessages.get_no_posted_questions_other_user_message(original_user)
        ), (
            f"Incorrect message displayed! "
            f"Expected: "
            f"{MyQuestionsPageMessages.get_no_posted_questions_other_user_message(original_user)} "
            f"received: "
            f"{self.sumo_pages.my_questions_page.get_text_of_no_question_message()}"
        )

        self.logger.info(
            "Sign in with the original user an verify that the "
            "correct message and the question list is no longer displayed"
        )
        self.delete_cookies()
        self.sumo_pages.top_navbar.click_on_signin_signup_button()
        self.sumo_pages.auth_flow_page.sign_in_flow(
            username=super().user_special_chars,
            account_password=super().user_secrets_pass
        )

        self.sumo_pages.top_navbar.click_on_view_profile_option()
        self.sumo_pages.user_navbar.click_on_my_questions_option()

        assert (
            self.sumo_pages.my_questions_page.get_text_of_no_question_message()
            == MyQuestionsPageMessages.NO_POSTED_QUESTIONS_MESSAGE
        ), (
            f"Incorrect message displayed! "
            f"Expected: {MyQuestionsPageMessages.NO_POSTED_QUESTIONS_MESSAGE} "
            f"received: {self.sumo_pages.my_questions_page.get_text_of_no_question_message()}"
        )

    #  C890823, C890831
    @pytest.mark.userQuestions
    def test_my_question_page_reflects_posted_questions_and_redirects_to_the_correct_question(
            self,
    ):
        self.logger.info("Signing in with a moderator user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Navigating to the Firefox AAQ form")
        self.navigate_to_link(
            super().aaq_question_test_data["products_aaq_url"]["Firefox"]
        )

        self.logger.info("Posting a new AAQ question for Firefox product")
        question_info = (
            self.sumo_pages.aaq_flow.submit_an_aaq_question_for_a_product(
                subject=super().aaq_question_test_data["valid_firefox_question"]["subject"],
                topic_name=super().aaq_question_test_data["valid_firefox_question"]["topic_value"],
                body=super().aaq_question_test_data["valid_firefox_question"]["question_body"]
            )
        )

        self.logger.info(
            "Verifying that the first element from the "
            "My Questions page is the recently posted question"
        )
        self.sumo_pages.top_navbar.click_on_my_questions_profile_option()

        assert self.sumo_pages.my_questions_page.get_text_of_first_listed_question().replace(
            " ", ""
        ) == question_info["aaq_subject"].replace(" ", ""), (
            f" Expected: {question_info['aaq_subject']} "
            f"Received: {self.sumo_pages.my_questions_page.get_text_of_first_listed_question()}"
        )

        self.logger.info(
            "Clicking on the first listed item and verifying that "
            "the user is redirected to the correct question"
        )

        self.sumo_pages.my_questions_page.click_on_a_question_by_index(1)

        expect(
            self.page
        ).to_have_url(question_info["question_page_url"])

        # assert self.sumo_pages.question_page.current_url() == question_info[
        # "question_page_url"], ( f"We are on the wrong page. Expected: {question_info} "
        # f"received: {self.sumo_pages.question_page.current_url()}" )

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page.click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page.click_delete_this_question_button()
