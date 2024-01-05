import pytest
import pytest_check as check
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
        self.logger.info("Signing in with a normal user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts['TEST_ACCOUNT_12']
        ))

        original_username = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        self.logger.info("Accessing the 'My profile' page via the top-navbar menu")
        self.sumo_pages.top_navbar._click_on_view_profile_option()

        self.logger.info(
            "Verifying that we are on the correct URL and viewing the correct profile"
        )
        expect(
            self.page
        ).to_have_url(MyProfileMessages.get_my_profile_stage_url(username=original_username))

        self.logger.info("Verifying that the page header is the expected one")
        check.equal(
            self.sumo_pages.my_profile_page._get_my_profile_page_header(),
            MyProfileMessages.STAGE_MY_PROFILE_PAGE_HEADER,
            f"Page header is {self.sumo_pages.my_profile_page._get_my_profile_page_header()}"
            f"Expected to be {MyProfileMessages.STAGE_MY_PROFILE_PAGE_HEADER}",
        )

        self.logger.info("Verifying that the 'My profile' navbar option is selected")
        check.equal(
            self.sumo_pages.my_profile_page._get_text_of_selected_navbar_option(),
            UserProfileNavbarMessages.NAVBAR_OPTIONS[0],
            f"Selected navbar option is: "
            f"{self.sumo_pages.my_profile_page._get_text_of_selected_navbar_option}"
            f"Expected to be: {UserProfileNavbarMessages.NAVBAR_OPTIONS[0]}",
        )

    #  C891411
    @pytest.mark.userProfile
    def test_my_profile_sign_out_button_functionality(self):
        self.logger.info("Signing in with a normal user account")
        self.sumo_pages.top_navbar._click_on_signin_signup_button()

        self.sumo_pages.auth_flow_page.sign_in_flow(
            username=super().user_special_chars,
            account_password=super().user_secrets_pass
        )

        self.logger.info("Accessing the 'My profile' page via the top-navbar menu")
        self.sumo_pages.top_navbar._click_on_view_profile_option()

        self.logger.info("Clicking on the 'Sign Out' button from the 'My Profile' page")
        self.sumo_pages.my_profile_page._click_my_profile_page_sign_out_button()

        self.logger.info("Verifying that the user is redirected to the homepage")

        expect(
            self.page
        ).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL_EN_US)

        self.logger.info("Verify that the 'Sign in/Up' button from the page header is displayed")

        expect(
            self.sumo_pages.top_navbar._sign_in_up_button_displayed_element()
        ).to_be_visible()

    # C2108828
    @pytest.mark.userProfile
    def test_provided_solutions_number_is_successfully_displayed(self):
        self.logger.info("Signing in with a normal user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        repliant_username = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

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

        self.sumo_pages.top_navbar._click_on_view_profile_option()

        self.logger.info("Extracting original number of posted solutions")
        original_number_of_solutions = self.number_extraction_from_string(
            self.sumo_pages.my_profile_page._get_my_profile_solutions_text()
        )

        self.logger.info("Navigating to the previously posted question")
        self.navigate_to_link(question_info["question_page_url"])

        self.logger.info("Posting a reply for the question")
        question_test_data = super().question_test_data

        self.sumo_pages.question_page._add_text_to_post_a_reply_textarea(
            question_test_data["question_reply_solution"]
        )

        self.logger.info("Clicking on the 'Post Reply' button and extracting answer id from url")
        answer_id = self.sumo_pages.question_page._click_on_post_reply_button(
            repliant_username=repliant_username
        )

        self.logger.info("Marking the reply as the solution")
        self.sumo_pages.question_page._click_on_solves_the_problem_button(
            target_reply_id=answer_id)

        self.logger.info(
            "Accessing the 'My profile' page of the account which provided a solution"
        )
        self.sumo_pages.top_navbar._click_on_view_profile_option()

        new_number = self.number_extraction_from_string(
            self.sumo_pages.my_profile_page._get_my_profile_solutions_text()
        )

        assert (
            self.number_extraction_from_string(
                self.sumo_pages.my_profile_page._get_my_profile_solutions_text()
            )
            == original_number_of_solutions + 1
        ), (
            f"The number of questions should have incremented! "
            f"The original number of question was: {original_number_of_solutions}"
            f" The new number of questions is: "
            f"{new_number}"
        )

        self.logger.info("Deleting the my posted question")
        self.navigate_to_link(question_info["question_page_url"])

        self.sumo_pages.question_page._click_delete_this_question_question_tools_option()

        self.sumo_pages.question_page._click_delete_this_question_button()

        self.logger.info("Verifying that we are on the product support forum page after deletion")

        expect(
            self.sumo_pages.product_support_page._product_product_title_element()
        ).to_be_visible()

    # C890832,  C2094281
    @pytest.mark.userProfile
    def test_number_of_my_profile_answers_is_successfully_displayed(self):
        reply_text = None

        self.logger.info("Signing in with a user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        repliant_user = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        self.logger.info("Accessing the 'My profile' page via the top-navbar menu")
        self.sumo_pages.top_navbar._click_on_view_profile_option()

        self.logger.info("Extracting original number of posted answers")
        original_number_of_answers = self.number_extraction_from_string(
            self.sumo_pages.my_profile_page._get_my_profile_answers_text()
        )

        self.logger.info("Navigating to the Firefox AAQ form")
        self.navigate_to_link(
            super().aaq_question_test_data["products_aaq_url"]["Firefox"]
        )

        self.logger.info("Posting a new AAQ question")
        question_info = (
            self.sumo_pages.aaq_flow.submit_an_aaq_question_for_a_product(
                subject=super().aaq_question_test_data["valid_firefox_question"]["subject"],
                topic_name=super().aaq_question_test_data["valid_firefox_question"]["topic_value"],
                body=super().aaq_question_test_data["valid_firefox_question"]["question_body"]
            )
        )

        self.logger.info("Posting a reply for the question")
        question_test_data = super().question_test_data

        reply_text = question_test_data["non_solution_reply"]

        self.sumo_pages.question_page._add_text_to_post_a_reply_textarea(reply_text)

        self.logger.info("Clicking on the 'Post Reply' button and extracting answer id from url")
        answer_id = self.sumo_pages.question_page._click_on_post_reply_button(
            repliant_username=repliant_user
        )

        self.logger.info("Accessing the 'My profile' page by clicking on the replient username")
        self.sumo_pages.question_page._click_on_the_reply_author(answer_id)

        self.logger.info("Verify that my number of profile answers has incremented successfully")
        new_number = self.number_extraction_from_string(
            self.sumo_pages.my_profile_page._get_my_profile_answers_text()
        )

        assert (
            self.number_extraction_from_string(
                self.sumo_pages.my_profile_page._get_my_profile_answers_text()
            )
            == original_number_of_answers + 1
        ), (
            f"The number of questions should have incremented! "
            f"The original number of question was: {original_number_of_answers}"
            f" The new number of questions is: "
            f"{new_number}"
        )

        self.sumo_pages.my_profile_page._click_my_profile_answers_link()
        self.logger.info(
            "Verify that my answer is successfully displayed inside the profile answers list"
        )

        assert reply_text == self.sumo_pages.my_answers_page._get_my_answer_text(
            answer_id=answer_id
        ), "My question reply is not displayed inside the my profile answers list"

        self.logger.info("Deleting the my posted question")
        self.navigate_to_link(question_info["question_page_url"])

        self.sumo_pages.question_page._click_delete_this_question_question_tools_option()

        self.sumo_pages.question_page._click_delete_this_question_button()

        self.logger.info("Verifying that we are on the product support forum page after deletion")
        expect(
            self.sumo_pages.product_support_page._product_product_title_element()
        ).to_be_visible()

    #  C2094285, C2094284
    @pytest.mark.userProfile
    def test_number_of_posted_articles_is_successfully_displayed(self):
        self.logger.info("Logging in with an moderator account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Accessing the View Profile page")
        self.sumo_pages.top_navbar._click_on_view_profile_option()

        self.logger.info("Extracting the number of posted documents")
        original_number_of_documents = self.number_extraction_from_string(
            self.sumo_pages.my_profile_page._get_my_profile_documents_text()
        )

        self.logger.info("Create a new simple article")
        article_title = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        self.logger.info("Accessing the View Profile page")

        self.sumo_pages.top_navbar._click_on_view_profile_option()

        self.logger.info("Verifying that the number of posted documents has incremented")
        new_number = self.number_extraction_from_string(
            self.sumo_pages.my_profile_page._get_my_profile_documents_text()
        )

        assert (
            self.number_extraction_from_string(
                self.sumo_pages.my_profile_page._get_my_profile_documents_text()
            )
            == original_number_of_documents + 1
        ), (
            f"The number of documents should have incremented! "
            f"The original number of documents was: {original_number_of_documents}"
            f" The new number of documents is: "
            f"{new_number}"
        )

        self.logger.info("Click on the my posted documents link")
        self.sumo_pages.my_profile_page._click_on_my_profile_document_link()

        self.logger.info(
            "Verifying that the posted document is listed inside the my profile documents list"
        )
        assert (
            article_title in self.sumo_pages.my_documents_page._get_text_of_document_links()
        ), f"The {article_title} is not listed inside the my posted documents list"

        self.logger.info(
            "Verifying that clicking on the posted article title redirects the "
            "user to that article"
        )
        self.sumo_pages.my_documents_page._click_on_a_particular_document(article_title)

        self.logger.info("Deleting the created article")
        self.sumo_pages.kb_article_page._click_on_show_history_option()

        self.sumo_pages.kb_article_show_history_page._click_on_delete_this_document_button()

        self.sumo_pages.kb_article_show_history_page._click_on_confirmation_delete_button()

    # C1491023
    @pytest.mark.userProfile
    def test_accounts_with_symbols_are_getting_a_corresponding_valid_username(self):
        self.logger.info(
            "Signing in with an account that contains SUMO-supported and unsupported characters"
        )

        self.sumo_pages.top_navbar._click_on_signin_signup_button()

        username = self.username_extraction_from_email(
            self.remove_character_from_string(
                self.sumo_pages.auth_flow_page.sign_in_flow(
                    username=super().user_special_chars,
                    account_password=super().user_secrets_pass
                ),
                "*",
            ))

        self.logger.info(
            "Verifying that the username contains the supported characters "
            "and doesn't contain the unsupported ones in top navbar"
        )
        assert self.sumo_pages.top_navbar._get_text_of_logged_in_username() == username, (
            f" The displayed username inside the top-navbar is incorrect. "
            f"The displayed username should be: {username} "
            f"but instead is : {self.sumo_pages.top_navbar._get_text_of_logged_in_username()}"
        )

        self.logger.info(
            "Verifying that the username contains the supported characters "
            "and doesn't contain the unsupported ones in My Profile page"
        )
        self.sumo_pages.top_navbar._click_on_view_profile_option()

        assert (self.sumo_pages.my_profile_page._get_my_profile_display_name_header_text()
                == username), (
            f"The displayed username inside the my profile page is incorrect. "
            f"The displayed username should be: {username}"
            f"but instead is: "
            f"{self.sumo_pages.my_profile_page._get_my_profile_display_name_header_text()}"
        )

        self.logger.info(
            "Verifying that the username contains the supported characters and "
            "doesn't contain the unsupported ones in Edit my Profile page"
        )
        self.sumo_pages.top_navbar._click_on_edit_profile_option()

        assert (
            self.sumo_pages.edit_my_profile_page._get_username_input_field_value() == username), (
            f"The displayed username inside the Edit my Profile page is incorrect. "
            f"The displayed field value should be: {username}"
            f"but instead is: "
            f"{self.sumo_pages.edit_my_profile_page._get_username_input_field_value()}"
        )
