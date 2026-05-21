import allure
import pytest
from pytest_check import check
from playwright.sync_api import expect, Page
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.my_profile_pages_messages.my_questions_page_messages import (
    MyQuestionsPageMessages)
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


#  C2094280,  C890790
@pytest.mark.userQuestions
def test_number_of_questions_is_incremented_when_posting_a_question(page: Page,
                                                                    create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Navigating to the AAQ form and posting a new AAQ question"):
        _submit_firefox_question(utilities, sumo_pages)

    with allure.step("Navigating back to the profile page and verifying that the number of "
                     "questions has incremented"):
        sumo_pages.top_navbar.click_on_view_profile_option()
        expect(sumo_pages.my_profile_page.questions_link).to_contain_text("1")



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
        for _ in range(2):
            _submit_firefox_question(utilities, sumo_pages)

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
        expect(sumo_pages.my_questions_page.questions_list).to_have_count(number_of_questions)


# T5697863, C3961769
@pytest.mark.userQuestions
def test_correct_messages_is_displayed_if_user_has_no_posted_questions(page: Page,
                                                                       create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(permissions=["delete_question"])

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with check, allure.step("Accessing the 'My questions' page and verifying that the correct"
                            " message inside all tab filters"):
        sumo_pages.top_navbar.click_on_view_profile_option()
        sumo_pages.user_navbar.click_on_my_questions_option()
        expect(sumo_pages.my_questions_page.questions_no_question_message).to_have_text(
            MyQuestionsPageMessages.NO_POSTED_QUESTIONS_MESSAGE)
        sumo_pages.my_questions_page.click_on_forum_tab_filter()
        expect(sumo_pages.my_questions_page.questions_no_question_message).to_have_text(
            MyQuestionsPageMessages.NO_POSTED_QUESTIONS_MESSAGE)
        sumo_pages.my_questions_page.click_on_direct_support_tab_filter()
        expect(sumo_pages.my_questions_page.questions_no_question_message).to_have_text(
            MyQuestionsPageMessages.NO_POSTED_QUESTIONS_MESSAGE)

    with check, allure.step("Verifying that the question list is not displayed"):
        expect(sumo_pages.my_questions_page.questions_list).to_be_hidden()

    with allure.step("Navigating to the Firefox AAQ form and posting a new AAQ question for "
                     "the Firefox product"):
        question_info = _submit_firefox_question(utilities, sumo_pages)

    with check, allure.step("Accessing the my questions page and verifying that the no question"
                            " message is no longer displayed"):
        sumo_pages.top_navbar.click_on_view_profile_option()
        expect(sumo_pages.my_profile_page.questions_link).to_contain_text("1")
        sumo_pages.user_navbar.click_on_my_questions_option()
        expect(sumo_pages.my_questions_page.questions_no_question_message).to_be_hidden()

    with allure.step("Deleting the question"):
        utilities.navigate_to_link(question_info["question_page_url"])
        sumo_pages.question_page.click_delete_this_question_question_tools_option()
        sumo_pages.question_page.click_delete_this_question_button()

    with allure.step("Verifying that the questions counter is no longer displayed at the profile "
                     "level"):
        sumo_pages.top_navbar.click_on_view_profile_option()
        expect(sumo_pages.my_profile_page.questions_link).to_be_hidden()

    with allure.step("Verifying that the question list is no longer displayed"):
        sumo_pages.top_navbar.click_on_my_questions_profile_option()
        expect(sumo_pages.my_questions_page.questions_no_question_message).to_have_text(
            MyQuestionsPageMessages.NO_POSTED_QUESTIONS_MESSAGE)


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
        first_question = _submit_firefox_question(utilities, sumo_pages)
        second_question = _submit_firefox_question(utilities, sumo_pages)

    with check, allure.step("Navigating to my questions profile page and verifying that the first "
                            "element from the My Questions page is the recently posted question"):
        sumo_pages.top_navbar.click_on_my_questions_profile_option()
        expect(sumo_pages.my_questions_page.questions_titles.nth(0)).to_have_text(
            second_question["aaq_subject"])
        expect(sumo_pages.my_questions_page.questions_titles.nth(1)).to_have_text(
            first_question["aaq_subject"])

    with allure.step("Clicking on the first list item and verifying that the user is "
                     "redirected to the correct question"):
        sumo_pages.my_questions_page.click_on_a_question_by_index(0)
        expect(page).to_have_url(second_question["question_page_url"])

    with allure.step("Navigating back, clicking on the second listed item and verifying that the "
                     "user is redirected to the correct question"):
        utilities.navigate_back()
        sumo_pages.my_questions_page.click_on_a_question_by_index(1)
        expect(page).to_have_url(first_question["question_page_url"])


# C3911832
@pytest.mark.userQuestions
def test_aaq_questions_are_placed_under_the_correct_channel(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Submitting a question against the AAQ forum"):
        question_info = _submit_firefox_question(utilities, sumo_pages)

    with allure.step("Navigating to the My Questions page and verifying that the question is "
                     "visible under the 'All' filter tab."):
        sumo_pages.top_navbar.click_on_my_questions_profile_option()

    with allure.step("Verifying that the question is successfully displayed inside the 'All' "
                     "tab filter"):
        expect(sumo_pages.my_questions_page.questions_list).to_contain_text(
            [question_info["aaq_subject"]])

    with allure.step("Verifying that the question is displayed inside the 'Forum' tab filter"):
        sumo_pages.my_questions_page.click_on_forum_tab_filter()
        expect(sumo_pages.my_questions_page.questions_list).to_contain_text(
            [question_info["aaq_subject"]])

    with allure.step("Verifying that the question is displayed inside the 'Direct Support' tab "
                     "filter"):
        sumo_pages.my_questions_page.click_on_direct_support_tab_filter()
        expect(sumo_pages.my_questions_page.questions_list).not_to_contain_text(
            [question_info["aaq_subject"]])


# C3911833, C4039420
@pytest.mark.userQuestions
def test_correct_meta_info_is_displayed_inside_the_my_questions_page(page: Page,
                                                                     create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    staff_user = utilities.username_extraction_from_email(utilities.staff_user)

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Submitting a question against the AAQ forum"):
        question_info = _submit_firefox_question(utilities, sumo_pages)

    with allure.step("Navigating to the My Questions page and verifying that the correct product "
                     "and topic is displayed inside the metadata information"):
        sumo_pages.top_navbar.click_on_my_questions_profile_option()
        expect(sumo_pages.my_questions_page.question_meta(question_info["aaq_subject"])
               ).to_contain_text(["Firefox"])
        expect(sumo_pages.my_questions_page.question_meta(question_info["aaq_subject"])
               ).to_contain_text(["App crash"])

    with allure.step("Moving the question under a different product & topic"):
        sumo_pages.my_questions_page.click_on_a_question_by_name(question_info["aaq_subject"])
        utilities.start_existing_session(session_file_name=staff_user)
        sumo_pages.aaq_flow.change_question_details(product="Thunderbird", topic="Settings")

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Navigating to the My Questions page and verifying that the product and "
                     "topic updates successfully displayed inside the metadata information"):
        sumo_pages.top_navbar.click_on_my_questions_profile_option()
        expect(sumo_pages.my_questions_page.question_meta(question_info["aaq_subject"])
               ).to_contain_text(["Thunderbird"])
        expect(sumo_pages.my_questions_page.question_meta(question_info["aaq_subject"])
               ).to_contain_text(["Settings"])


# C3911835
@pytest.mark.userQuestions
def test_correct_question_status_is_displayed(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    staff_user = utilities.username_extraction_from_email(utilities.staff_user)

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Submitting a question against the AAQ forum"):
        question_info = _submit_firefox_question(utilities, sumo_pages)

    with allure.step("Navigating to the My Questions page and verifying that the correct question "
                     "status is displayed"):
        sumo_pages.top_navbar.click_on_my_questions_profile_option()
        my_questions_page = utilities.get_page_url()
        expect(sumo_pages.my_questions_page.question_extras(question_info["aaq_subject"])
               ).to_contain_text(["Open"])

    with allure.step("Signing in with a staff account and archiving the question"):
        utilities.start_existing_session(session_file_name=staff_user)
        sumo_pages.my_questions_page.click_on_a_question_by_name(question_info["aaq_subject"])
        question_page = utilities.get_page_url()
        sumo_pages.question_page.click_on_archive_this_question_option()

    with allure.step("Navigating back to the my questions page and verifying that the correct"
                     "question status is displayed"):
        utilities.navigate_to_link(my_questions_page)
        expect(sumo_pages.my_questions_page.question_extras(question_info["aaq_subject"])
               ).to_contain_text(["Archived"])
        expect(sumo_pages.my_questions_page.question_extras(question_info["aaq_subject"])
               ).not_to_contain_text(["Open"])

    with allure.step("Navigating back and locking the question"):
        utilities.navigate_to_link(question_page)
        sumo_pages.question_page.click_on_lock_this_question_option()

    with allure.step("Navigating back to the my questions page and verifying that the question "
                     "status updates to contain both the 'Archived' and 'Locked' labels"):
        utilities.navigate_to_link(my_questions_page)
        expect(sumo_pages.my_questions_page.question_extras(question_info["aaq_subject"])
               ).to_contain_text(["Locked", "Archived"])
        expect(sumo_pages.my_questions_page.question_extras(question_info["aaq_subject"])
               ).not_to_contain_text(["Open"])

    with allure.step("Navigating back to the question, un-archiving, unlocking and leaving "
                     "a solution"):
        utilities.navigate_to_link(question_page)
        sumo_pages.question_page.click_on_lock_this_question_option()
        sumo_pages.question_page.click_on_archive_this_question_option()
        reply_id = sumo_pages.aaq_flow.post_question_reply_flow(
            repliant_username=staff_user,
            reply=utilities.aaq_question_test_data['valid_firefox_question']['question_reply']
        )
        sumo_pages.question_page.click_on_solves_the_problem_button(reply_id)

    with allure.step("Navigating back to the my questions page and verifying that the question "
                     "status updates to contain the 'Solved' status"):
        utilities.navigate_to_link(my_questions_page)
        expect(sumo_pages.my_questions_page.question_extras(question_info["aaq_subject"])
               ).to_contain_text(["Solved"])
        expect(sumo_pages.my_questions_page.question_extras(question_info["aaq_subject"])
               ).not_to_contain_text(["Locked", "Archived"])

    with allure.step("Navigating back to the question and marking it as both 'Locked' and "
                     "'Archived'"):
        utilities.navigate_to_link(question_page)
        sumo_pages.question_page.click_on_lock_this_question_option()
        sumo_pages.question_page.click_on_archive_this_question_option()

    with allure.step("Navigating back to the my questions page and verifying that the question "
                     "status updates to contain the 'Solved', 'Locked' and 'Archived' status"):
        utilities.navigate_to_link(my_questions_page)
        expect(sumo_pages.my_questions_page.question_extras(question_info["aaq_subject"])
               ).to_contain_text(["Solved", "Locked", "Archived"])

    with allure.step("Navigating back to the question and undoing the solution and unmarking the "
                     "question as being archived and locked"):
        utilities.navigate_to_link(question_page)
        sumo_pages.question_page.click_on_lock_this_question_option()
        sumo_pages.question_page.click_on_archive_this_question_option()
        sumo_pages.question_page.click_on_undo_solution_button_from_reply()

    with allure.step("Navigating back to the my questions page and verifying that the question "
                     "status updates to contain only the 'Open' status"):
        utilities.navigate_to_link(my_questions_page)
        expect(sumo_pages.my_questions_page.question_extras(question_info["aaq_subject"])
               ).to_contain_text(["Open"])
        expect(sumo_pages.my_questions_page.question_extras(question_info["aaq_subject"])
               ).not_to_contain_text(["Solved", "Locked", "Archived"])


#  C3911837, C4039430
@pytest.mark.userQuestions
def test_spam_marked_questions_visibility(page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    test_user_two = create_user_factory()
    staff_user = utilities.username_extraction_from_email(utilities.staff_user)

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Submitting a question against the AAQ forum"):
        question_info = _submit_firefox_question(utilities, sumo_pages)

    with allure.step("Signing in with a forum moderator and marking the question as spam"):
        utilities.start_existing_session(session_file_name=staff_user)
        sumo_pages.question_page.click_on_mark_as_spam_option()

    with allure.step(f"Signing in with {test_user['username']} user account and navigating to "
                     f"the My Questions page"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.top_navbar.click_on_my_questions_profile_option()

    with allure.step("Verifying that the spam filter is not displayed"):
        expect(sumo_pages.my_questions_page.questions_page_spam_filter).to_be_hidden()

    with allure.step("Verifying that the spam marked question is not displayed"):
        expect(sumo_pages.my_questions_page.questions_titles).not_to_contain_text(
            [question_info["aaq_subject"]])

    with allure.step(f"Signing in with a different non forum moderator account"):
        utilities.start_existing_session(cookies=test_user_two)

    with allure.step("Verifying that the spam filter is not displayed"):
        expect(sumo_pages.my_questions_page.questions_page_spam_filter).to_be_hidden()

    with allure.step("Verifying that the spam marked question is not displayed"):
        expect(sumo_pages.my_questions_page.questions_titles).not_to_contain_text(
            [question_info["aaq_subject"]])

    with allure.step(f"Signing out from SUMO"):
        utilities.delete_cookies()

    with allure.step("Verifying that the spam filter is not displayed"):
        expect(sumo_pages.my_questions_page.questions_page_spam_filter).to_be_hidden()

    with allure.step("Verifying that the spam marked question is not displayed"):
        expect(sumo_pages.my_questions_page.questions_titles).not_to_contain_text(
            [question_info["aaq_subject"]])

    with allure.step("Signing in with a forum moderator"):
        utilities.start_existing_session(session_file_name=staff_user)

    with allure.step("Verifying that the spam filter is displayed"):
        expect(sumo_pages.my_questions_page.questions_page_spam_filter).to_be_visible()

    with allure.step("Verifying that the spam marked question is displayed inside both the 'All'"
                     "and 'Spam' tab filters and that it contains the correct Spam status"):
        expect(sumo_pages.my_questions_page.question_extras(question_info["aaq_subject"])
               ).to_contain_text(["Spam"])
        sumo_pages.my_questions_page.click_on_spam_tab_filter()
        expect(sumo_pages.my_questions_page.question_extras(question_info["aaq_subject"])
               ).to_contain_text(["Spam"])
