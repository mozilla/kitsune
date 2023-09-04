import pytest
from selenium_tests.core.test_utilities import TestUtilities
from selenium_tests.messages.my_profile_pages_messages.my_questions_page_messages import (
    MyQuestionsPageMessages,
)


class TestMyQuestions(TestUtilities):
    #  C2094280,  C890790
    @pytest.mark.userQuestions
    def test_number_of_questions_is_incremented_when_posting_a_question(self):
        self.logger.info("Signing in wit a normal user account")

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_MODERATOR"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.logger.info("Accessing the 'My profile' page via the top-navbar menu")

        self.pages.top_navbar.click_on_view_profile_option()

        self.logger.info("Extracting original number of posted questions")

        original_number_of_questions = self.number_extraction_from_string(
            self.pages.my_profile_page.get_my_profile_questions_text()
        )

        self.logger.info("Posting a new AAQ question")

        question_info = (
            self.pages.aaq_flow.submit_valid_firefox_product_question_via_ask_now_fx_solutions()
        )

        self.logger.info("Navigating back to the My Profile page")

        self.pages.top_navbar.click_on_view_profile_option()
        new_number = self.number_extraction_from_string(
            self.pages.my_profile_page.get_my_profile_questions_text()
        )

        assert (
            self.number_extraction_from_string(
                self.pages.my_profile_page.get_my_profile_questions_text()
            )
            == original_number_of_questions + 1
        ), (
            f"The number of questions should have incremented! "
            f"The original number of question was: "
            f"{original_number_of_questions}"
            f" The new number of questions is: "
            f"{new_number}"
        )

        self.logger.info("Deleting the my posted question")

        self.pages.my_answers_page.navigate_to(question_info["question_page_url"])

        self.pages.question_page.click_delete_this_question_question_tools_option()

        self.pages.question_page.click_delete_this_question_button()

        self.logger.info("Verifying that we are on the product support forum page after deletion")

        assert (
            self.pages.product_support_page.is_product_product_title_displayed()
        ), "The product support forum page is not displayed!"

        # write tests to check my questions section as well

    # C1296000, #  C890790
    @pytest.mark.userQuestions
    def test_my_contributions_questions_reflects_my_questions_page_numbers(self):
        self.logger.info("Signing in wit a normal user account")

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.logger.info("Accessing the 'My profile' page via the top-navbar menu")

        self.pages.top_navbar.click_on_view_profile_option()

        self.logger.info("Extracting the number of questions listed inside the my profile page")

        number_of_questions = self.number_extraction_from_string(
            self.pages.my_profile_page.get_my_profile_questions_text()
        )

        self.logger.info("Clicking on the my profile questions link")

        self.pages.my_profile_page.click_on_my_profile_questions_link()

        self.logger.info(
            "Verifying that the number of questions from the"
            " my profile pages matches the ones from my questions "
            "page"
        )

        assert number_of_questions == self.pages.my_questions_page.get_number_of_questions(), (
            f"The number of questions listed inside the my profile page is:"
            f" {number_of_questions} "
            f"The number of questions listed inside the my questions page is:"
            f" {self.pages.my_questions_page.get_number_of_questions()}"
        )

    # C890821
    @pytest.mark.userQuestions
    def test_correct_messages_is_displayed_if_user_has_no_posted_questions(self):
        self.logger.info("Signing in with a user which has no posted questions")

        self.pages.top_navbar.click_on_signin_signup_button()

        original_user = super().remove_character_from_string(
            self.pages.auth_flow_page.sign_in_flow(
                username=super().user_secrets_data["TEST_ACCOUNT_SPECIAL_CHARS"],
                account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
                sign_in_with_same_account=False,
            ),
            "*",
        )

        self.logger.info("Accessing the 'My questions' page")

        self.pages.top_navbar.click_on_view_profile_option()

        self.pages.user_navbar.click_on_my_questions_option()

        self.logger.info("Verifying that the correct message is displayed")

        assert (
            self.pages.my_questions_page.get_text_of_no_question_message()
            == MyQuestionsPageMessages.NO_POSTED_QUESTIONS_MESSAGE
        ), (
            f"Incorrect message is displayed!. "
            f"Expected: {MyQuestionsPageMessages.NO_POSTED_QUESTIONS_MESSAGE} "
            f"received: {self.pages.my_questions_page.get_text_of_no_question_message()}"
        )

        self.logger.info("Verifying that a question list is not displayed")

        assert not (
            self.pages.my_questions_page.is_question_list_displayed()
        ), "Question list displayed! It shouldn't be"

        self.logger.info("Posting a new aaq question")

        question_info = (
            self.pages.aaq_flow.submit_valid_firefox_product_question_via_ask_now_fx_solutions()
        )

        self.logger.info(
            "Accessing the my questions page and verifying that the "
            "no questions message is no longer displayed"
        )

        self.pages.top_navbar.click_on_view_profile_option()
        self.pages.user_navbar.click_on_my_questions_option()

        assert not (
            self.pages.my_questions_page.is_no_question_message_displayed()
        ), "The no questions message is displayed! It shouldn't be!"

        self.logger.info("Signing in with a moderator account")

        self.pages.top_navbar.click_on_sign_out_button()
        self.pages.top_navbar.click_on_signin_signup_button()
        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_MODERATOR"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )
        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.logger.info("Deleting the my posted question")

        self.pages.my_questions_page.navigate_to(question_info["question_page_url"])

        self.pages.question_page.click_delete_this_question_question_tools_option()

        self.pages.question_page.click_delete_this_question_button()

        self.logger.info(
            "Accessing the original user and verifying that the correct message is displayed"
        )

        self.pages.homepage.navigate_to(
            MyQuestionsPageMessages.get_stage_my_questions_url(original_user)
        )

        assert (
            self.pages.my_questions_page.get_text_of_no_question_message()
            == MyQuestionsPageMessages.get_no_posted_questions_other_user_message(original_user)
        ), (
            f"Incorrect message displayed! "
            f"Expected: "
            f"{MyQuestionsPageMessages.get_no_posted_questions_other_user_message(original_user)} "
            f"received: "
            f"{self.pages.my_questions_page.get_text_of_no_question_message()}"
        )

        self.logger.info(
            "Sign in with the original user an verify that the "
            "correct message and the question list is no longer displayed"
        )

        self.pages.top_navbar.click_on_sign_out_button()
        self.pages.top_navbar.click_on_signin_signup_button()
        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_SPECIAL_CHARS"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.top_navbar.click_on_view_profile_option()
        self.pages.user_navbar.click_on_my_questions_option()

        assert (
            self.pages.my_questions_page.get_text_of_no_question_message()
            == MyQuestionsPageMessages.NO_POSTED_QUESTIONS_MESSAGE
        ), (
            f"Incorrect message displayed! "
            f"Expected: {MyQuestionsPageMessages.NO_POSTED_QUESTIONS_MESSAGE} "
            f"received: {self.pages.my_questions_page.get_text_of_no_question_message()}"
        )

    #  C890823, C890831
    @pytest.mark.userQuestions
    def test_my_question_page_reflects_posted_questions_and_redirects_to_the_correct_question(
        self,
    ):
        self.logger.info("Signing in with a moderator user account")

        self.pages.top_navbar.click_on_signin_signup_button()
        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_MODERATOR"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )
        self.pages.homepage.wait_for_searchbar_to_be_displayed_and_clickable()

        self.logger.info("Posting a new aaq question")

        question_info = (
            self.pages.aaq_flow.submit_valid_firefox_product_question_via_ask_now_fx_solutions()
        )

        self.logger.info(
            "Verifying that the first element from the "
            "My Questions page is the recently posted question"
        )

        self.pages.top_navbar.click_on_my_questions_profile_option()

        assert self.pages.my_questions_page.get_text_of_first_listed_question().replace(
            " ", ""
        ) == question_info["aaq_subject"].replace(" ", ""), (
            f" Expected: {question_info['aaq_subject']} "
            f"Received: {self.pages.my_questions_page.get_text_of_first_listed_question()}"
        )

        self.logger.info(
            "Clicking on the first listed item and verifying that "
            "the user is redirected to the correct question"
        )

        self.pages.my_questions_page.click_on_a_question_by_index(1)

        assert self.pages.question_page.current_url() == question_info["question_page_url"], (
            f"We are on the wrong page. Expected: {question_info} "
            f"received: {self.pages.question_page.current_url()}"
        )

        self.logger.info("Deleting the posted question")

        self.pages.question_page.click_delete_this_question_question_tools_option()
        self.pages.question_page.click_delete_this_question_button()
