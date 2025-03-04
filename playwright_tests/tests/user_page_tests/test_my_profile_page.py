import allure
import pytest
from pytest_check import check
from playwright.sync_api import expect, Page

from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.homepage_messages import HomepageMessages
from playwright_tests.messages.my_profile_pages_messages.my_profile_page_messages import (
    MyProfileMessages)
from playwright_tests.messages.my_profile_pages_messages.user_profile_navbar_messages import (
    UserProfileNavbarMessages)
from playwright_tests.pages.sumo_pages import SumoPages


# C891409
@pytest.mark.userProfile
def test_my_profile_page_can_be_accessed_via_top_navbar(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with a non-admin user account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts['TEST_ACCOUNT_12']
        ))
    original_username = sumo_pages.top_navbar.get_text_of_logged_in_username()

    with allure.step("Accessing the 'My profile' page and verifying that we are redirected "
                     "to the correct profile"):
        sumo_pages.top_navbar.click_on_view_profile_option()
        expect(page).to_have_url(MyProfileMessages.get_my_profile_stage_url(
            username=original_username))

    with check, allure.step("Verifying that the page header is the expected one"):
        assert sumo_pages.my_profile_page.get_my_profile_page_header(
        ) == MyProfileMessages.STAGE_MY_PROFILE_PAGE_HEADER

    with check, allure.step("Verifying that the 'My profile' navbar option is selected"):
        assert sumo_pages.my_profile_page.get_text_of_selected_navbar_option(
        ) == UserProfileNavbarMessages.NAVBAR_OPTIONS[0]


#  C891411, C891410
@pytest.mark.userProfile
def test_my_profile_sign_out_button_functionality(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with a non-admin account"):
        sumo_pages.top_navbar.click_on_signin_signup_button()

        sumo_pages.auth_flow_page.sign_in_flow(
            username=utilities.user_special_chars,
            account_password=utilities.user_secrets_pass
        )

    with allure.step("Accessing the my profile page, clicking on the sign out button and "
                     "verifying that the user is redirected to the homepage"):
        sumo_pages.top_navbar.click_on_view_profile_option()
        sumo_pages.my_profile_page.click_my_profile_page_sign_out_button(
            expected_url=HomepageMessages.STAGE_HOMEPAGE_URL_EN_US
        )
        expect(page).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL_EN_US)

    with allure.step("Verify that the 'Sign in/Up' button from the page header is displayed"):
        expect(sumo_pages.top_navbar.sign_in_up_button_displayed_element()).to_be_visible()


# C2108828, C891410
@pytest.mark.userProfile
def test_provided_solutions_number_is_successfully_displayed(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with an admin user account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))
    repliant_username = sumo_pages.top_navbar.get_text_of_logged_in_username()

    with allure.step("Navigating to the Firefox AAQ form and posting a new AAQ question for "
                     "the Firefox product"):
        utilities.navigate_to_link(utilities.aaq_question_test_data["products_aaq_url"]["Firefox"])
        question_info = (
            sumo_pages.aaq_flow.submit_an_aaq_question(
                subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
                topic_name=utilities.
                aaq_question_test_data["valid_firefox_question"]["topic_value"],
                body=utilities.
                aaq_question_test_data["valid_firefox_question"]["question_body"],
                expected_locator=sumo_pages.question_page.questions_header
            )
        )

    with allure.step("Navigating to the user profile page and extracting the original number "
                     "of posted question solutions"):
        sumo_pages.top_navbar.click_on_view_profile_option()
        if sumo_pages.my_profile_page.is_solutions_displayed():
            original_number_of_solutions = utilities.number_extraction_from_string(
                sumo_pages.my_profile_page.get_my_profile_solutions_text()
            )
        else:
            original_number_of_solutions = 0

    with allure.step("Navigating to the previously posted question and posting a reply to it"):
        utilities.navigate_to_link(question_info["question_page_url"])
        question_test_data = utilities.question_test_data
        sumo_pages.question_page.add_text_to_post_a_reply_textarea(
            question_test_data["question_reply_solution"]
        )
        answer_id = sumo_pages.question_page.click_on_post_reply_button(
            repliant_username=repliant_username
        )

    with allure.step("Marking the reply as the question solution"):
        sumo_pages.question_page.click_on_solves_the_problem_button(target_reply_id=answer_id)

    with allure.step("Accessing the 'My profile' page of the account which provided the "
                     "solution and verifying that the original number of solutions has "
                     "incremented"):
        sumo_pages.top_navbar.click_on_view_profile_option()
        utilities.number_extraction_from_string(
            sumo_pages.my_profile_page.get_my_profile_solutions_text()
        )
        assert (utilities.number_extraction_from_string(
            sumo_pages.my_profile_page.get_my_profile_solutions_text(
            )) == original_number_of_solutions + 1)

    with allure.step("Deleting the posted question and verifying that we are redirected to "
                     "the product support forum page after deletion"):
        utilities.navigate_to_link(question_info["question_page_url"])
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        sumo_pages.question_page.click_delete_this_question_question_tools_option()
        sumo_pages.question_page.click_delete_this_question_button()
        expect(sumo_pages.product_support_page.product_product_title_element()).to_be_visible()


# C890832,  C2094281, C891410, C2245210, C2245211, C2245212, C2245209
@pytest.mark.userProfile
def test_number_of_my_profile_answers_is_successfully_displayed(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with an admin user"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
    repliant_user = sumo_pages.top_navbar.get_text_of_logged_in_username()

    with allure.step("Accessing the 'My profile' page and extracting the number of posted "
                     "answers"):
        sumo_pages.top_navbar.click_on_view_profile_option()
        original_number_of_answers = utilities.number_extraction_from_string(
            sumo_pages.my_profile_page.get_my_profile_answers_text()
        )

    with allure.step("Navigating to the Firefox AAQ form and posting a new AAQ question"):
        utilities.navigate_to_link(
            utilities.aaq_question_test_data["products_aaq_url"]["Firefox"]
        )
        question_info = (
            sumo_pages.aaq_flow.submit_an_aaq_question(
                subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
                topic_name=utilities.
                aaq_question_test_data["valid_firefox_question"]["topic_value"],
                body=utilities.
                aaq_question_test_data["valid_firefox_question"]["question_body"],
                expected_locator=sumo_pages.question_page.questions_header
            )
        )

    with allure.step("Posting a reply for the question"):
        question_test_data = utilities.question_test_data
        reply_text = question_test_data["non_solution_reply"]
        sumo_pages.question_page.add_text_to_post_a_reply_textarea(reply_text)
        answer_id = sumo_pages.question_page.click_on_post_reply_button(
            repliant_username=repliant_user
        )

    with allure.step("Accessing the 'My profile' page and verifying that the number of "
                     "answers has incremented successfully"):
        sumo_pages.question_page.click_on_the_reply_author(answer_id)
        utilities.number_extraction_from_string(
            sumo_pages.my_profile_page.get_my_profile_answers_text()
        )
        assert (
            utilities.number_extraction_from_string(
                sumo_pages.my_profile_page.get_my_profile_answers_text()
            ) == original_number_of_answers + 1
        )

    with allure.step("Clicking on the my profile answers and verifying that the posted "
                     "answer is successfully displayed inside the list"):
        sumo_pages.my_profile_page.click_my_profile_answers_link()
        assert reply_text == sumo_pages.my_answers_page.get_my_answer_text(
            answer_id=answer_id
        ), "My question reply is not displayed inside the my profile answers list"
        assert question_info["aaq_subject"] == (sumo_pages.my_answers_page.
                                                get_my_answer_question_title(answer_id))

    with allure.step("Updating the question title and question reply"):
        sumo_pages.my_answers_page.click_on_specific_answer(answer_id)
        sumo_pages.question_page.click_on_edit_this_question_question_tools_option()
        updated_title_text = ("Updated Question Title " + utilities.
                              generate_random_number(1,1000))
        updated_reply_text = "Updated reply"
        sumo_pages.aaq_flow.editing_question_flow(
            subject=updated_title_text,
            submit_edit=True
        )
        sumo_pages.question_page.click_on_reply_more_options_button(answer_id)
        sumo_pages.question_page.click_on_edit_this_post_for_a_certain_reply(answer_id)
        sumo_pages.aaq_flow.editing_reply_flow(reply_body=updated_reply_text, submit_reply=True)

    with allure.step("Navigating back to the answers page from the profile section and verifying "
                     "that the updates are reflected"):
        sumo_pages.question_page.click_on_the_reply_author(answer_id)
        assert (
            utilities.number_extraction_from_string(
                sumo_pages.my_profile_page.get_my_profile_answers_text()
            ) == original_number_of_answers + 1
        )

        sumo_pages.my_profile_page.click_my_profile_answers_link()
        assert updated_reply_text == sumo_pages.my_answers_page.get_my_answer_text(
            answer_id=answer_id
        ), "My question reply is not displayed inside the my profile answers list"

        assert updated_title_text == sumo_pages.my_answers_page.get_my_answer_question_title(
            answer_id)

    with allure.step("Navigating back to the posted question and posting a reply to it"):
        sumo_pages.my_answers_page.click_on_specific_answer(answer_id)
        reply_text = "A new reply"
        sumo_pages.question_page.add_text_to_post_a_reply_textarea(reply_text)
        second_answer_id = sumo_pages.question_page.click_on_post_reply_button(
            repliant_username=repliant_user
        )

    with allure.step("Navigating back to the answers page from the profile section and verifying "
                     "that the updates are reflected"):
        sumo_pages.question_page.click_on_the_reply_author(second_answer_id)
        assert (
            utilities.number_extraction_from_string(
                sumo_pages.my_profile_page.get_my_profile_answers_text()
            ) == original_number_of_answers + 2
        )

        sumo_pages.my_profile_page.click_my_profile_answers_link()
        assert reply_text == sumo_pages.my_answers_page.get_my_answer_text(
            answer_id=second_answer_id
        ), "My question reply is not displayed inside the my profile answers list"

        assert updated_title_text == sumo_pages.my_answers_page.get_my_answer_question_title(
            second_answer_id)

    with allure.step("Deleting the posted question and verifying that the user is redirected to "
                     "the product support forum page"):
        utilities.navigate_to_link(question_info["question_page_url"])
        sumo_pages.question_page.click_delete_this_question_question_tools_option()
        sumo_pages.question_page.click_delete_this_question_button()
        expect(sumo_pages.product_support_page.product_product_title_element()).to_be_visible()


#  C2094285, C2094284, C891309, C891410, C2245213
@pytest.mark.userProfile
def test_number_of_posted_articles_is_successfully_displayed(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with an admin account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

    with allure.step("Accessing the profile page and extracting the number of documents"):
        sumo_pages.top_navbar.click_on_view_profile_option()
        original_number_of_documents = utilities.number_extraction_from_string(
            sumo_pages.my_profile_page.get_my_profile_documents_text()
        )

    with allure.step("Creating a kb article"):
        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

    with allure.step("Accessing the profile page and verifying that the number of posted "
                     "documents has incremented"):
        sumo_pages.top_navbar.click_on_view_profile_option()
        assert (
            utilities.number_extraction_from_string(
                sumo_pages.my_profile_page.get_my_profile_documents_text()
            ) == original_number_of_documents + 1
        )

    with allure.step("Clicking on my posted documents link and verifying that the posted "
                     "document is listed"):
        sumo_pages.my_profile_page.click_on_my_profile_document_link()
        assert (
            article_details['article_title'] in sumo_pages.
            my_documents_page.get_text_of_document_links()
        )

    with allure.step("Navigating to the article and changing the title"):
        new_article_title = "Updated title test v1"
        sumo_pages.my_documents_page.click_on_a_particular_document(
            article_details['article_title'])
        sumo_pages.edit_article_metadata_flow.edit_article_metadata(title=new_article_title)

    with allure.step("Accessing the profile page and verifying that the number of posted "
                     "documents is the same"):
        sumo_pages.top_navbar.click_on_view_profile_option()
        assert (
            utilities.number_extraction_from_string(
                sumo_pages.my_profile_page.get_my_profile_documents_text()
            ) == original_number_of_documents + 1
        )

    with allure.step("Clicking on my posted documents link and verifying that the new document "
                     "title is listed"):
        sumo_pages.my_profile_page.click_on_my_profile_document_link()
        assert (new_article_title in sumo_pages.my_documents_page.get_text_of_document_links())

    with allure.step("Deleting the article"):
        sumo_pages.my_documents_page.click_on_a_particular_document(
            new_article_title
        )
        sumo_pages.kb_article_deletion_flow.delete_kb_article()


# C1491023
@pytest.mark.userProfile
def test_accounts_with_symbols_are_getting_a_corresponding_valid_username(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with an account that contains SUMO-supported and "
                     "unsupported characters"):
        sumo_pages.top_navbar.click_on_signin_signup_button()

        username = utilities.username_extraction_from_email(
            utilities.remove_character_from_string(
                sumo_pages.auth_flow_page.sign_in_flow(
                    username=utilities.user_special_chars,
                    account_password=utilities.user_secrets_pass
                ),
                "*",
            ))

    with allure.step("Verifying that the username contains the supported characters and "
                     "doesn't contain the unsupported ones in top navbar"):
        assert sumo_pages.top_navbar.get_text_of_logged_in_username() == username

    with allure.step("Verifying that the username contains the supported characters and "
                     "doesn't contain the unsupported ones in My Profile page"):
        sumo_pages.top_navbar.click_on_view_profile_option()
        assert sumo_pages.my_profile_page.get_my_profile_display_name_header_text() == username

    with allure.step("Verifying that the username contains the supported characters and "
                     "doesn't contain the unsupported ones in Edit my Profile page"):
        sumo_pages.top_navbar.click_on_edit_profile_option()
        assert sumo_pages.edit_my_profile_page.get_username_input_field_value() == username
