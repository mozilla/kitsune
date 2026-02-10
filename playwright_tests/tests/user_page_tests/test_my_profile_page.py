import random
import string
import allure
import pytest
from pytest_check import check
from playwright.sync_api import expect, Page
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.contribute_messages.con_discussions.off_topic import \
    OffTopicForumMessages
from playwright_tests.messages.homepage_messages import HomepageMessages
from playwright_tests.messages.my_profile_pages_messages.edit_my_profile_page_messages import \
    EditMyProfilePageMessages
from playwright_tests.messages.my_profile_pages_messages.my_profile_page_messages import (
    MyProfileMessages)
from playwright_tests.messages.my_profile_pages_messages.user_profile_navbar_messages import (
    UserProfileNavbarMessages)
from playwright_tests.pages.sumo_pages import SumoPages


def _submit_firefox_question(utilities: Utilities, sumo_pages: SumoPages) -> dict:
    """Navigate to the Firefox AAQ form and submit a standard question."""
    firefox_data = utilities.aaq_question_test_data["valid_firefox_question"]
    utilities.navigate_to_link(utilities.aaq_question_test_data["products_aaq_url"]["Firefox"])
    return sumo_pages.aaq_flow.submit_an_aaq_question(
        subject=firefox_data["subject"],
        topic_name=firefox_data["topic_value"],
        body=firefox_data["question_body"],
        expected_locator=sumo_pages.question_page.questions_header
    )


# C891409
@pytest.mark.smokeTest
@pytest.mark.userProfile
def test_my_profile_page_can_be_accessed_via_top_navbar(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Accessing the 'My profile' page and verifying that we are redirected "
                     "to the correct profile"):
        sumo_pages.top_navbar.click_on_view_profile_option()
        expect(page).to_have_url(MyProfileMessages.get_my_profile_stage_url(test_user["username"]))

    with check, allure.step("Verifying that the page header is the expected one"):
        assert (sumo_pages.my_profile_page.get_my_profile_page_header() == MyProfileMessages.
                STAGE_MY_PROFILE_PAGE_HEADER)

    with allure.step("Verifying that the 'My profile' navbar option is selected"):
        assert sumo_pages.my_profile_page.get_text_of_selected_navbar_option(
        ) == UserProfileNavbarMessages.NAVBAR_OPTIONS[0]


#  C891411, C891410
@pytest.mark.smokeTest
@pytest.mark.userProfile
def test_my_profile_sign_out_button_functionality(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with check, allure.step("Accessing the my profile page, clicking on the sign out button and "
                            "verifying that the user is redirected to the homepage"):
        sumo_pages.top_navbar.click_on_view_profile_option()
        sumo_pages.my_profile_page.click_my_profile_page_sign_out_button(
            expected_url=HomepageMessages.STAGE_HOMEPAGE_URL_EN_US
        )
        expect(page).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL_EN_US)

    with allure.step("Verify that the 'Sign in/Up' button from the page header is displayed"):
        expect(sumo_pages.top_navbar.signin_signup_button).to_be_visible()


# C2108828, C891410
@pytest.mark.userProfile
def test_provided_solutions_number_is_successfully_displayed(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    second_user = create_user_factory(permissions=["delete_question"])

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Navigating to the Firefox AAQ form and posting a new AAQ question for "
                     "the Firefox product"):
        question_info = _submit_firefox_question(utilities, sumo_pages)

    with allure.step("Posting a reply to the question"):
        utilities.start_existing_session(cookies=second_user)
        answer_id = sumo_pages.aaq_flow.post_question_reply_flow(
            repliant_username=second_user["username"],
            reply=utilities.question_test_data["question_reply_solution"]
        )

    with allure.step("Marking the reply as the question solution"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.question_page.click_on_solves_the_problem_button(target_reply_id=answer_id)

    with check, allure.step("Accessing the 'My profile' page of the account which provided the"
                            " solution and verifying that the original number of solutions has "
                            "incremented"):
        utilities.start_existing_session(cookies=second_user)
        sumo_pages.top_navbar.click_on_view_profile_option()

        assert sumo_pages.my_profile_page.get_my_profile_solutions_text() == "1 solution"

    with allure.step("Signing in with the OP and undoing the solution"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(question_info["question_page_url"])
        sumo_pages.question_page.click_on_undo_button()

    with allure.step("Signing in back with the user that has provided the solution and verifying "
                     "that the solution counter is not displayed"):
        utilities.start_existing_session(cookies=second_user)
        sumo_pages.top_navbar.click_on_view_profile_option()
        assert not sumo_pages.my_profile_page.is_solutions_displayed()


# C1318760, C2245214
@pytest.mark.userProfile
def test_number_of_answers_and_questions_for_contributor_thread_contributions(page: Page,
                                                                              create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(groups=["forum-contributors"])

    with allure.step("Signing in with a contributor account and navigating to the Off topic"
                     "forum"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)

    with allure.step("Creating a new thread"):
        thread_title = (utilities.discussion_thread_data['thread_title'] + utilities.
                        generate_random_number(1, 1000))
        sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title=thread_title, thread_body=utilities.discussion_thread_data['thread_body']
        )

    with allure.step("Creating a new thread reply"):
        sumo_pages.contributor_thread_flow.post_thread_reply(
            reply_body=utilities.discussion_thread_data['thread_body'])

    with allure.step("Navigating to the profile page and verifying that the answer and questions "
                     "counter has not incremented"):
        sumo_pages.top_navbar.click_on_view_profile_option()
        assert not sumo_pages.my_profile_page.is_question_displayed()
        assert not sumo_pages.my_profile_page.is_my_profile_answers_link_visible()


# C890832,  C2094281, C891410, C2245210, C2245211, C2245212, C2245209
@pytest.mark.userProfile
def test_number_of_my_profile_answers_is_successfully_displayed(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Navigating to the Firefox AAQ form and posting a new AAQ question"):
        question_info = _submit_firefox_question(utilities, sumo_pages)

    with allure.step("Posting a reply for the question"):
        reply_text = utilities.question_test_data["non_solution_reply"]
        answer_id = sumo_pages.aaq_flow.post_question_reply_flow(
            repliant_username=test_user["username"], reply=reply_text
        )

    with check, allure.step("Accessing the 'My profile' page and verifying that the number of"
                            " answers has incremented successfully"):
        sumo_pages.question_page.click_on_the_reply_author(answer_id)
        assert sumo_pages.my_profile_page.get_my_profile_answers_text() == "1 answer"

    with check, allure.step("Clicking on the my profile answers and verifying that the posted"
                            " answer is successfully displayed inside the list"):
        sumo_pages.my_profile_page.click_my_profile_answers_link()
        assert reply_text == sumo_pages.my_answers_page.get_my_answer_text(answer_id=answer_id)
        assert (question_info["aaq_subject"] == sumo_pages.my_answers_page.
                get_my_answer_question_title(answer_id))

    with allure.step("Updating the question title and question reply"):
        sumo_pages.my_answers_page.click_on_specific_answer(answer_id)
        updated_title_text = (
            "Updated Question Title ".join(random.choice(string.ascii_lowercase + string.digits
                                                         ) for _ in range(10)))
        updated_reply_text = "Updated reply"
        sumo_pages.aaq_flow.editing_question_flow(subject=updated_title_text, submit_edit=True)
        sumo_pages.aaq_flow.editing_reply_flow(
            answer_id=answer_id, reply_body=updated_reply_text, submit_reply=True
        )

    with check, allure.step("Navigating back to the answers page from the profile section and"
                            " verifying that the updates are reflected"):
        sumo_pages.question_page.click_on_the_reply_author(answer_id)
        assert sumo_pages.my_profile_page.get_my_profile_answers_text() == "1 answer"

        sumo_pages.my_profile_page.click_my_profile_answers_link()
        assert (updated_reply_text == sumo_pages.my_answers_page.get_my_answer_text(
            answer_id=answer_id))
        assert (updated_title_text == sumo_pages.my_answers_page.get_my_answer_question_title(
            answer_id))

    with allure.step("Navigating back to the posted question and posting a reply to it"):
        sumo_pages.my_answers_page.click_on_specific_answer(answer_id)
        reply_text = "A new reply"
        second_answer_id = sumo_pages.aaq_flow.post_question_reply_flow(
            repliant_username=test_user["username"], reply=reply_text
        )

    with check, allure.step("Navigating back to the answers page from the profile section and"
                            " verifying that the updates are reflected"):
        sumo_pages.question_page.click_on_the_reply_author(second_answer_id)
        assert sumo_pages.my_profile_page.get_my_profile_answers_text() == "2 answers"
        sumo_pages.my_profile_page.click_my_profile_answers_link()
        assert (reply_text == sumo_pages.my_answers_page.get_my_answer_text(
            answer_id=second_answer_id))
        assert (updated_title_text == sumo_pages.my_answers_page.get_my_answer_question_title(
            second_answer_id))


#  C2094285, C2094284, C891309, C891410, C2245213
@pytest.mark.userProfile
def test_number_of_posted_articles_is_successfully_displayed(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Creating a kb article"):
        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

    with check, allure.step("Accessing the profile page and verifying that the number of posted"
                            " documents has incremented"):
        sumo_pages.top_navbar.click_on_view_profile_option()
        assert sumo_pages.my_profile_page.get_my_profile_documents_text() == "1 document"

    with check, allure.step("Clicking on my posted documents link and verifying that the posted"
                            " document is listed"):
        sumo_pages.my_profile_page.click_on_my_profile_document_link()
        assert (article_details['article_title'] in sumo_pages.my_documents_page.
                get_text_of_document_links())

    with allure.step("Navigating to the article and changing the title"):
        new_article_title = "Updated ".join(random.choice(string.ascii_lowercase + string.digits
                                                          ) for _ in range(10))
        sumo_pages.my_documents_page.click_on_a_particular_document(
            article_details['article_title'])
        sumo_pages.edit_article_metadata_flow.edit_article_metadata(title=new_article_title)

    with check, allure.step("Accessing the profile page and verifying that the number of posted"
                            " documents is the same"):
        sumo_pages.top_navbar.click_on_view_profile_option()
        assert sumo_pages.my_profile_page.get_my_profile_documents_text() == "1 document"

    with allure.step("Clicking on my posted documents link and verifying that the new document"
                     " title is listed"):
        sumo_pages.my_profile_page.click_on_my_profile_document_link()
        assert new_article_title in sumo_pages.my_documents_page.get_text_of_document_links()


# C1491023
@pytest.mark.userProfile
def test_accounts_with_symbols_are_getting_a_corresponding_valid_username(page: Page,
                                                                          create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(username="tes@tU.se-r4")

    with allure.step("Signing in with an account that contains SUMO-supported characters"):
        utilities.start_existing_session(cookies=test_user)

    with check, allure.step("Verifying that the username contains the supported characters and"
                            " doesn't contain the unsupported ones in top navbar"):
        assert sumo_pages.top_navbar.get_text_of_logged_in_username() == test_user["username"]

    with check, allure.step("Verifying that the username contains the supported characters in My"
                            " Profile page"):
        sumo_pages.top_navbar.click_on_view_profile_option()
        assert (sumo_pages.my_profile_page.
                get_my_profile_display_name_header_text() == test_user["username"])

    with check, allure.step("Verifying that the username contains the supported characters in Edit"
                            " my Profile page"):
        sumo_pages.top_navbar.click_on_edit_profile_option()
        assert (sumo_pages.edit_my_profile_page.
                get_username_input_field_value() == test_user["username"])

    with check, allure.step("Adding an unsupported character inside the username field and"
                            " verifying that the error message is displayed"):
        sumo_pages.edit_my_profile_page.send_text_to_username_field(test_user["username"] + "*")
        sumo_pages.edit_my_profile_page.click_update_my_profile_button()
        assert (sumo_pages.edit_my_profile_page.
                get_username_error_message_text() == EditMyProfilePageMessages.
                USERNAME_INPUT_ERROR_MESSAGE)

    with check, allure.step("Verifying that the username contains the supported characters in My"
                            " Profile page"):
        sumo_pages.top_navbar.click_on_view_profile_option()
        assert (sumo_pages.my_profile_page.
                get_my_profile_display_name_header_text() == test_user["username"])

    with allure.step("Verifying that the username contains the supported characters in Edit my "
                     "Profile page"):
        sumo_pages.top_navbar.click_on_edit_profile_option()
        assert (sumo_pages.edit_my_profile_page.
                get_username_input_field_value() == test_user["username"])
