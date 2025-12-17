import allure
import pytest
from pytest_check import check
from playwright.sync_api import expect, Page
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.my_profile_pages_messages.my_questions_page_messages import (
    MyQuestionsPageMessages)
from playwright_tests.pages.sumo_pages import SumoPages


#  C2094280,  C890790
@pytest.mark.userQuestions
def test_number_of_questions_is_incremented_when_posting_a_question(page: Page,
                                                                    create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()

    with allure.step(f"Signing in with {test_user['username']} a user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Navigating to the AAQ form and posting a new AAQ question"):
        utilities.navigate_to_link(
            utilities.aaq_question_test_data["products_aaq_url"]["Firefox"]
        )

        sumo_pages.aaq_flow.submit_an_aaq_question(
            subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=utilities.aaq_question_test_data["valid_firefox_question"]["topic_value"],
            body=utilities.aaq_question_test_data["valid_firefox_question"]["question_body"],
            expected_locator=sumo_pages.question_page.questions_header
        )

    with allure.step("Navigating back to the profile page and verifying that the number of "
                     "questions has incremented"):
        sumo_pages.top_navbar.click_on_view_profile_option()
        assert (utilities.number_extraction_from_string(
            sumo_pages.my_profile_page.get_my_profile_questions_text()) == 1)


# C1296000, #  C890790
@pytest.mark.userQuestions
def test_my_contributions_questions_reflects_my_questions_page_numbers(page: Page,
                                                                       create_user_factory):

    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Submitting two new questions"):
        counter = 0
        while counter < 2:
            utilities.navigate_to_link(
                utilities.aaq_question_test_data["products_aaq_url"]["Firefox"]
            )
            sumo_pages.aaq_flow.submit_an_aaq_question(
                subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
                topic_name=utilities.aaq_question_test_data[
                    "valid_firefox_question"]["topic_value"],
                body=utilities.aaq_question_test_data["valid_firefox_question"]["question_body"],
                expected_locator=sumo_pages.question_page.questions_header
            )
            counter += 1

    with allure.step("Accessing the 'My profile' and extracting the number of questions "
                     "listed inside the my profile page"):
        sumo_pages.top_navbar.click_on_view_profile_option()
        number_of_questions = utilities.number_extraction_from_string(
            sumo_pages.my_profile_page.get_my_profile_questions_text()
        )

    with allure.step("Clicking on the my profile questions link and verifying that the "
                     "number of questions from the my profile page matches the one from the "
                     "ones from my questions page"):
        sumo_pages.my_profile_page.click_on_my_profile_questions_link()
        assert number_of_questions == sumo_pages.my_questions_page.get_number_of_questions()


# T5697863
@pytest.mark.userQuestions
def test_correct_messages_is_displayed_if_user_has_no_posted_questions(page: Page,
                                                                       create_user_factory):

    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(permissions=["delete_question"])

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with check, allure.step("Accessing the 'My questions' page and verifying that the correct"
                            " message is displayed"):
        sumo_pages.top_navbar.click_on_view_profile_option()
        sumo_pages.user_navbar.click_on_my_questions_option()
        assert (sumo_pages.my_questions_page.
                get_text_of_no_question_message() == MyQuestionsPageMessages.
                NO_POSTED_QUESTIONS_MESSAGE)

    with check, allure.step("Verifying that the question list is not displayed"):
        expect(sumo_pages.my_questions_page.get_list_of_profile_questions_locators()
               ).to_be_hidden()

    with allure.step("Navigating to the Firefox AAQ form and posting a new AAQ question for "
                     "the Firefox product"):
        utilities.navigate_to_link(utilities.aaq_question_test_data["products_aaq_url"]["Firefox"])
        question_info = (
            sumo_pages.aaq_flow.submit_an_aaq_question(
                subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
                topic_name=utilities
                .aaq_question_test_data["valid_firefox_question"]["topic_value"],
                body=utilities.
                aaq_question_test_data["valid_firefox_question"]["question_body"],
                expected_locator=sumo_pages.question_page.questions_header

            )
        )

    with check, allure.step("Accessing the my questions page and verifying that the no question"
                            " message is no longer displayed"):
        sumo_pages.top_navbar.click_on_view_profile_option()
        sumo_pages.user_navbar.click_on_my_questions_option()
        expect(sumo_pages.my_questions_page.get_list_of_profile_no_question_message_locator()
               ).to_be_hidden()

    with allure.step("Deleting the question"):
        utilities.navigate_to_link(question_info["question_page_url"])
        sumo_pages.question_page.click_delete_this_question_question_tools_option()
        sumo_pages.question_page.click_delete_this_question_button()

    with allure.step("Verifying that the question list is no longer displayed"):
        sumo_pages.top_navbar.click_on_my_questions_profile_option()
        assert (
            sumo_pages.my_questions_page.get_text_of_no_question_message()
            == MyQuestionsPageMessages.NO_POSTED_QUESTIONS_MESSAGE
        )


# T5697862, T5697864, T5697865
@pytest.mark.userQuestions
def test_question_page_reflects_posted_questions_and_redirects_to_question(page: Page,
                                                                           create_user_factory):

    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Navigating to the Firefox AAQ form and posting a new AAQ question"):
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

    with check, allure.step("Navigating to my questions profile page and verifying that the first "
                            "element from the My Questions page is the recently posted question"):
        sumo_pages.top_navbar.click_on_my_questions_profile_option()
        assert (sumo_pages.my_questions_page.get_text_of_first_listed_question().
                strip() == question_info["aaq_subject"].strip())

    with allure.step("Clicking on the first list item and verifying that the user is "
                     "redirected to the correct question"):
        sumo_pages.my_questions_page.click_on_a_question_by_index(1)
        expect(page).to_have_url(question_info["question_page_url"])
