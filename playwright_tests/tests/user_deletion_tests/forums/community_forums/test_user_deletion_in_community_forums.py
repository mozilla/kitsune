import allure
import pytest
from playwright.sync_api import Page
from pytest_check import check
from playwright_tests.core.utilities import Utilities
from playwright_tests.pages.sumo_pages import SumoPages


# C2979511, C2979512
@pytest.mark.userDeletion
@pytest.mark.parametrize("question_type", ['archived', 'locked', 'archived-locked'])
def test_user_deletion_on_archived_locked_no_replies_and_votes_question(page: Page,
                                                                        create_user_factory,
                                                                        question_type):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    staff = utilities.username_extraction_from_email(utilities.staff_user)

    with allure.step("Signing in with the test user and posting a question to a freemium product"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(utilities.aaq_question_test_data["products_aaq_url"]["Firefox"])
        question_details = sumo_pages.aaq_flow.submit_an_aaq_question(
            subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=utilities.aaq_question_test_data["valid_firefox_question"]["topic_value"],
            body=utilities.aaq_question_test_data["valid_firefox_question"]["question_body"],
            expected_locator=sumo_pages.question_page.questions_header
        )

    with allure.step(f"Signing in with the staff user and marking the question as "
                     f"{question_type}"):
        utilities.start_existing_session(session_file_name=staff)
        if question_type == "archived":
            sumo_pages.question_page.click_on_archive_this_question_option()
        elif question_type == "locked":
            sumo_pages.question_page.click_on_lock_this_question_option()
        elif question_type == "archived-locked":
            sumo_pages.question_page.click_on_archive_this_question_option()
            sumo_pages.question_page.click_on_lock_this_question_option()

    with allure.step("Signing in with the test user and initiating the user deletion flow"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.edit_profile_flow.close_account()

    with check, allure.step("Navigating back to the posted question and verifying that 404 is "
                            "returned"):
        assert utilities.navigate_to_link(question_details["question_page_url"]).status == 404


# C2807313, C2979513, C2981636
@pytest.mark.userDeletion
@pytest.mark.parametrize("question_type", ["spam", "archived-locked"])
def test_user_deletion_on_spam_no_replies_and_votes_question(page: Page, question_type,
                                                             create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    staff = utilities.username_extraction_from_email(utilities.staff_user)

    with allure.step("Signing in with the test user and posting a question to a freemium product"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(utilities.aaq_question_test_data["products_aaq_url"]["Firefox"])
        question_details = sumo_pages.aaq_flow.submit_an_aaq_question(
            subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=utilities.aaq_question_test_data["valid_firefox_question"]["topic_value"],
            body=utilities.aaq_question_test_data["valid_firefox_question"]["question_body"],
            expected_locator=sumo_pages.question_page.questions_header
        )

    with allure.step("Signing in with the staff user"):
        utilities.start_existing_session(session_file_name=staff)
        if question_type == "spam":
            with allure.step("Marking the question as spam"):
                sumo_pages.question_page.click_on_mark_as_spam_option()
        if question_type == "archived-locked":
            with allure.step("Marking the question as archived, locked and spam"):
                sumo_pages.question_page.click_on_lock_this_question_option()
                sumo_pages.question_page.click_on_archive_this_question_option()
                sumo_pages.question_page.click_on_mark_as_spam_option()

    with allure.step("Signing in with the test user and initiating the user deletion flow"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.edit_profile_flow.close_account()

    with check, allure.step("Navigating back to the posted question and verifying that 404 is "
                            "returned"):
        utilities.start_existing_session(session_file_name=staff)
        assert utilities.navigate_to_link(question_details["question_page_url"]).status == 404


# C2979514, C2979647
@pytest.mark.userDeletion
@pytest.mark.parametrize("question_type", ["archived", "locked", "archived-locked"])
def test_user_deletion_on_archived_locked_with_replies_question(page: Page, question_type,
                                                                create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    staff = utilities.username_extraction_from_email(utilities.staff_user)

    with allure.step("Signing in with the test user and posting a question to a freemium product"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(utilities.aaq_question_test_data["products_aaq_url"]["Firefox"])
        question_details = sumo_pages.aaq_flow.submit_an_aaq_question(
            subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=utilities.aaq_question_test_data["valid_firefox_question"]["topic_value"],
            body=utilities.aaq_question_test_data["valid_firefox_question"]["question_body"],
            expected_locator=sumo_pages.question_page.questions_header
        )

    with allure.step("Signing in with the staff user replying and marking the question as "
                     f"{question_type}"):
        utilities.start_existing_session(session_file_name=staff)
        reply_id = sumo_pages.aaq_flow.post_question_reply_flow(repliant_username=staff,
                                                                reply="Test Reply")
        if question_type == "archived":
            sumo_pages.question_page.click_on_archive_this_question_option()
        elif question_type == "locked":
            sumo_pages.question_page.click_on_lock_this_question_option()
        elif question_type == "archived-locked":
            sumo_pages.question_page.click_on_archive_this_question_option()
            sumo_pages.question_page.click_on_lock_this_question_option()

    with allure.step("Signing in with the test user and initiating the user deletion flow"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.edit_profile_flow.close_account()

    with check, allure.step("Navigating back to the posted question and verifying that the"
                            " question ownership is assigned to the system account"):
        utilities.start_existing_session(session_file_name=staff)
        utilities.navigate_to_link(question_details["question_page_url"])
        assert (sumo_pages.question_page.get_question_author_name() == utilities.
                general_test_data["system_account_name"])
        assert (sumo_pages.question_page
                .get_display_name_of_question_reply_author(reply_id) == staff)

    with allure.step("Deleting the question"):
        sumo_pages.aaq_flow.deleting_question_flow()


# C2979648, C2807894
@pytest.mark.userDeletion
@pytest.mark.parametrize("question_type", ["spam", "archived-locked"])
def test_user_deletion_on_spam_with_replies_question(page: Page, question_type,
                                                     create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    staff = utilities.username_extraction_from_email(utilities.staff_user)

    with allure.step("Signing in with the test user and posting a question to a freemium product"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(utilities.aaq_question_test_data["products_aaq_url"]["Firefox"])
        question_details = sumo_pages.aaq_flow.submit_an_aaq_question(
            subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=utilities.aaq_question_test_data["valid_firefox_question"]["topic_value"],
            body=utilities.aaq_question_test_data["valid_firefox_question"]["question_body"],
            expected_locator=sumo_pages.question_page.questions_header
        )

    with allure.step("Signing in with the staff user and leaving a reply to the question"):
        utilities.start_existing_session(session_file_name=staff)
        sumo_pages.aaq_flow.post_question_reply_flow(repliant_username=staff, reply="Test Reply")
        if question_type == "spam":
            with allure.step("Marking the question as spam"):
                sumo_pages.question_page.click_on_mark_as_spam_option()
        if question_type == "archived-locked":
            with allure.step("Marking the question as archived, locked and spam"):
                sumo_pages.question_page.click_on_lock_this_question_option()
                sumo_pages.question_page.click_on_archive_this_question_option()
                sumo_pages.question_page.click_on_mark_as_spam_option()

    with allure.step("Signing in with the test user and initiating the user deletion flow"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.edit_profile_flow.close_account()

    with check, allure.step("Navigating back to the posted question and verifying that 404 is "
                            "returned"):
        utilities.start_existing_session(session_file_name=staff)
        assert utilities.navigate_to_link(question_details["question_page_url"]).status == 404


# C2979649
@pytest.mark.userDeletion
def test_user_deletion_on_question_with_spam_replies(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    staff = utilities.username_extraction_from_email(utilities.staff_user)

    with allure.step("Signing in with the test user and posting a question to a freemium product"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(utilities.aaq_question_test_data["products_aaq_url"]["Firefox"])
        question_details = sumo_pages.aaq_flow.submit_an_aaq_question(
            subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=utilities.aaq_question_test_data["valid_firefox_question"]["topic_value"],
            body=utilities.aaq_question_test_data["valid_firefox_question"]["question_body"],
            expected_locator=sumo_pages.question_page.questions_header
        )

    with allure.step("Signing in with the staff user leaving a reply and marking the reply as "
                     "spam"):
        utilities.start_existing_session(session_file_name=staff)
        reply_id = sumo_pages.aaq_flow.post_question_reply_flow(repliant_username=staff,
                                                                reply="Test Reply")
        sumo_pages.aaq_flow.spam_marking_a_reply(reply_id=reply_id)

    with allure.step("Signing in with the test user and initiating the user deletion flow"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.edit_profile_flow.close_account()

    with check, allure.step("Navigating back to the posted question and verifying that 404 is "
                            "returned"):
        utilities.start_existing_session(session_file_name=staff)
        assert utilities.navigate_to_link(question_details["question_page_url"]).status == 404


# C2807314
@pytest.mark.smokeTest
@pytest.mark.userDeletion
@pytest.mark.parametrize("question_type", ["archived", "non-archived"])
def test_user_deletion_on_question_with_replies_from_other_user(page: Page, question_type,
                                                                create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    staff = utilities.username_extraction_from_email(utilities.staff_user)

    with allure.step("Signing in with the test user and posting a question to a freemium product"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(utilities.aaq_question_test_data["products_aaq_url"]["Firefox"])
        question_details = sumo_pages.aaq_flow.submit_an_aaq_question(
            subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=utilities.aaq_question_test_data["valid_firefox_question"]["topic_value"],
            body=utilities.aaq_question_test_data["valid_firefox_question"]["question_body"],
            expected_locator=sumo_pages.question_page.questions_header
        )

    with allure.step("Signing in with the staff user replying to the question"):
        utilities.start_existing_session(session_file_name=staff)
        reply_id = sumo_pages.aaq_flow.post_question_reply_flow(repliant_username=staff,
                                                                reply="Test Reply")
        if question_type == "archived":
            with allure.step("Archiving the question"):
                sumo_pages.question_page.click_on_archive_this_question_option()

    with allure.step("Signing in with the test user and initiating the user deletion flow"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.edit_profile_flow.close_account()

    with check, allure.step("Navigating back to the posted question and verifying that the "
                            "question ownership is assigned to the system account"):
        utilities.start_existing_session(session_file_name=staff)
        utilities.navigate_to_link(question_details["question_page_url"])
        assert (sumo_pages.question_page.get_question_author_name() == utilities.
                general_test_data["system_account_name"])
        assert (sumo_pages.question_page
                .get_display_name_of_question_reply_author(reply_id) == staff)

    with allure.step("Deleting the question"):
        sumo_pages.aaq_flow.deleting_question_flow()


# C2807314
@pytest.mark.userDeletion
@pytest.mark.parametrize("question_type", ["archived", "non-archived"])
def test_user_deletion_on_question_with_replies_from_same_user(page: Page, question_type,
                                                               create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    staff = utilities.username_extraction_from_email(utilities.staff_user)

    with allure.step("Signing in with the test user and posting a question to a freemium product"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(utilities.aaq_question_test_data["products_aaq_url"]["Firefox"])
        question_details = sumo_pages.aaq_flow.submit_an_aaq_question(
            subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=utilities.aaq_question_test_data["valid_firefox_question"]["topic_value"],
            body=utilities.aaq_question_test_data["valid_firefox_question"]["question_body"],
            expected_locator=sumo_pages.question_page.questions_header
        )

    with allure.step("Leaving a reply to the question with the same user"):
        reply_id = sumo_pages.aaq_flow.post_question_reply_flow(
            repliant_username=test_user["username"], reply="Test Reply")

        if question_type == "archived":
            utilities.start_existing_session(session_file_name=staff)
            sumo_pages.question_page.click_on_archive_this_question_option()
            utilities.start_existing_session(cookies=test_user)

    with allure.step("Initiating the user deletion flow"):
        sumo_pages.edit_profile_flow.close_account()

    with check, allure.step("Navigating back to the posted question and verifying that the"
                            " question and reply ownership is assigned to the system account"):
        utilities.start_existing_session(session_file_name=staff)
        utilities.navigate_to_link(question_details["question_page_url"])
        assert (sumo_pages.question_page.get_question_author_name() == utilities.
                general_test_data["system_account_name"])
        assert (sumo_pages.question_page
                .get_display_name_of_question_reply_author(reply_id) == utilities.
                general_test_data["system_account_name"])

    with allure.step("Deleting the question"):
        sumo_pages.aaq_flow.deleting_question_flow()


# C2807314
@pytest.mark.smokeTest
@pytest.mark.userDeletion
@pytest.mark.parametrize("question_type", ["archived", "non-archived"])
def test_user_deletion_on_question_with_solution(page: Page, question_type, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    staff = utilities.username_extraction_from_email(utilities.staff_user)

    with allure.step("Signing in with the test user and posting a question to a freemium product"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(utilities.aaq_question_test_data["products_aaq_url"]["Firefox"])
        question_details = sumo_pages.aaq_flow.submit_an_aaq_question(
            subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=utilities.aaq_question_test_data["valid_firefox_question"]["topic_value"],
            body=utilities.aaq_question_test_data["valid_firefox_question"]["question_body"],
            expected_locator=sumo_pages.question_page.questions_header
        )

    with allure.step("Leaving a reply to the question with a different user"):
        utilities.start_existing_session(session_file_name=staff)
        reply_id = sumo_pages.aaq_flow.post_question_reply_flow(
            repliant_username=staff, reply="Test Reply")

    with allure.step("Signing in back with the test user and marking the reply as the solution"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.question_page.click_on_solves_the_problem_button(target_reply_id=reply_id)

    if question_type == "archived":
        with allure.step("Signing back with the staff user and archiving the question"):
            utilities.start_existing_session(session_file_name=staff)
            sumo_pages.question_page.click_on_archive_this_question_option()
            utilities.start_existing_session(cookies=test_user)

    with allure.step("Initiating the user deletion flow"):
        sumo_pages.edit_profile_flow.close_account()

    with check, allure.step("Navigating back to the posted question and verifying that the"
                            " question is assigned to the system account"):
        utilities.start_existing_session(session_file_name=staff)
        utilities.navigate_to_link(question_details["question_page_url"])
        assert (sumo_pages.question_page.get_question_author_name() == utilities.
                general_test_data["system_account_name"])
        assert (sumo_pages.question_page
                .get_display_name_of_question_reply_author(reply_id) == staff)

    with allure.step("Deleting the question"):
        sumo_pages.aaq_flow.deleting_question_flow()


# C2807314
@pytest.mark.userDeletion
@pytest.mark.parametrize("question_type", ["archived", "non-archived"])
def test_user_deletion_on_voted_question(page: Page, question_type, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    staff = utilities.username_extraction_from_email(utilities.staff_user)

    with allure.step("Signing in with the test user and posting a question to a freemium product"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(utilities.aaq_question_test_data["products_aaq_url"]["Firefox"])
        question_details = sumo_pages.aaq_flow.submit_an_aaq_question(
            subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=utilities.aaq_question_test_data["valid_firefox_question"]["topic_value"],
            body=utilities.aaq_question_test_data["valid_firefox_question"]["question_body"],
            expected_locator=sumo_pages.question_page.questions_header
        )

    with allure.step("Signing in with a staff user and voting the question"):
        utilities.start_existing_session(session_file_name=staff)
        sumo_pages.question_page.click_i_have_this_problem_too_button()

    if question_type == "archived":
        with allure.step("Archiving the question"):
            sumo_pages.question_page.click_on_archive_this_question_option()

    with allure.step("Initiating the user deletion flow"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.edit_profile_flow.close_account()

    utilities.start_existing_session(session_file_name=staff)
    response = utilities.navigate_to_link(question_details["question_page_url"])

    with check, allure.step("Verifying that the question was deleted"):
        assert response.status == 404


# C2807938, C2807940, C2926133, C2807890, C2807892, C2807893
@pytest.mark.smokeTest
@pytest.mark.userDeletion
@pytest.mark.parametrize("answer_type", ["simple", "solution", "voted"])
@pytest.mark.parametrize("question_type", ["archived", "non-archived"])
def test_user_deletion_on_question_reply_for_archived_questions(page: Page, answer_type,
                                                                question_type,
                                                                create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    staff = utilities.username_extraction_from_email(utilities.staff_user)

    with allure.step("Signing in with the staff user and posting a question to a freemium "
                     "product"):
        utilities.start_existing_session(session_file_name=staff)
        utilities.navigate_to_link(utilities.aaq_question_test_data["products_aaq_url"]["Firefox"])
        question_details = sumo_pages.aaq_flow.submit_an_aaq_question(
            subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=utilities.aaq_question_test_data["valid_firefox_question"]["topic_value"],
            body=utilities.aaq_question_test_data["valid_firefox_question"]["question_body"],
            expected_locator=sumo_pages.question_page.questions_header
        )

    with allure.step("Leaving a reply to the question with a different user"):
        utilities.start_existing_session(cookies=test_user)
        reply_id = sumo_pages.aaq_flow.post_question_reply_flow(
            repliant_username=test_user["username"], reply="Test Reply")

    if answer_type == "solution":
        utilities.start_existing_session(session_file_name=staff)
        sumo_pages.question_page.click_on_solves_the_problem_button(target_reply_id=reply_id)
        utilities.start_existing_session(cookies=test_user)
    if answer_type == "voted":
        utilities.start_existing_session(session_file_name=staff)
        sumo_pages.question_page.click_reply_vote_thumbs_down_button(reply_id=reply_id)
        utilities.start_existing_session(cookies=test_user)

    if question_type == "archived":
        utilities.start_existing_session(session_file_name=staff)
        sumo_pages.question_page.click_on_archive_this_question_option()
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Initiating the user deletion flow"):
        sumo_pages.edit_profile_flow.close_account()

    with check, allure.step("Navigating back to the posted question and verifying that the"
                            " question reply was assigned to the system account"):
        utilities.start_existing_session(session_file_name=staff)
        utilities.navigate_to_link(question_details["question_page_url"])
        assert sumo_pages.question_page.get_question_author_name() == staff
        assert (sumo_pages.question_page
                .get_display_name_of_question_reply_author(reply_id) == utilities.
                general_test_data["system_account_name"])

    with allure.step("Deleting the question"):
        sumo_pages.aaq_flow.deleting_question_flow()
