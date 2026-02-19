import allure
import pytest
from playwright.sync_api import Page
from pytest_check import check
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.ask_a_question_messages.community_forums_messages import \
    SupportForumsPageMessages
from playwright_tests.messages.ask_a_question_messages.contact_support_messages import \
    ContactSupportMessages
from playwright_tests.pages.sumo_pages import SumoPages


# C3040845
@pytest.mark.communityForums
def test_product_community_cards_are_redirecting_to_the_correct_forum(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)

    with allure.step("Navigating to the all products community forums page"):
        sumo_pages.top_navbar.click_on_view_all_forums_option()

    with check, allure.step("Clicking on each product community forum card and verifying that the "
                            "user is redirected to the correct community forum"):
        for card in sumo_pages.all_community_forums_page.get_product_card_titles_list():
            sumo_pages.all_community_forums_page.click_on_a_particular_product_card(card)
            assert (sumo_pages.product_support_forum.
                    get_text_of_product_community_forum_header() == card)

            with allure.step("Navigating back to the all products community forum page"):
                utilities.navigate_back()

    with allure.step("Clicking on the 'All Products Community Forums' button"):
        sumo_pages.all_community_forums_page.click_on_all_products_support_forum_button()

    with check, allure.step("Verifying that the user is redirected to the correct forum page"):
        assert (sumo_pages.product_support_forum.
                get_text_of_product_community_forum_header() == "All Products Community Forum")


# C2663508
@pytest.mark.communityForums
def test_ask_the_community_button_redirect(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)

    with allure.step("Navigating to the all products community forums page"):
        sumo_pages.top_navbar.click_on_view_all_forums_option()

    with check, allure.step("Clicking on the 'Ask the Community' button for each community forum "
                            "and verifying that the user is redirected to the correct product "
                            "solutions page"):
        for card in sumo_pages.all_community_forums_page.get_product_card_titles_list():
            sumo_pages.all_community_forums_page.click_on_a_particular_product_card(card)
            sumo_pages.product_support_forum.click_on_the_ask_the_community_button()
            assert (sumo_pages.product_solutions_page.get_product_solutions_heading() == card.
                    replace("Community Forum", "Solutions"))
            utilities.navigate_to_link(SupportForumsPageMessages.PAGE_URL)

    with allure.step("Clicking on the 'All Products Community Forums' button and clicking on "
                     "'Ask the Community'"):
        sumo_pages.all_community_forums_page.click_on_all_products_support_forum_button()
        with page.expect_navigation() as navigation_info:
            sumo_pages.product_support_forum.click_on_the_ask_the_community_button()

    with check, allure.step("Verifying that the 'Ask the Community' button redirects to the "
                            "'Contact Support' page"):
        assert navigation_info.value.url == ContactSupportMessages.PAGE_URL


# C3170429
@pytest.mark.communityForums
def test_question_transitions_from_attention_needed_to_responded(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    test_user_two = create_user_factory(groups=["Forum Moderators"])

    with allure.step("Submitting an AAQ question to the Firefox product"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(utilities.aaq_question_test_data["products_aaq_url"]["Firefox"])
        question_details = sumo_pages.aaq_flow.submit_an_aaq_question(
            subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=sumo_pages.aaq_form_page.get_aaq_form_topic_options()[0],
            body=utilities.aaq_question_test_data["valid_firefox_question"]["question_body"],
            attach_image=False,
            expected_locator=sumo_pages.question_page.questions_header
        )

    with check, allure.step("Navigating to the 'Firefox Community Forum' and verifying that the "
                            "question is listed inside the 'Attention needed' tab filter"):
        utilities.navigate_to_link(utilities.general_test_data["product_forums"]["Firefox"])
        assert (sumo_pages.product_support_forum.
                get_text_of_selected_tab_filter() == "Attention needed")
        assert (question_details["question_id"] in sumo_pages.product_support_forum.
                get_ids_of_all_listed_questions())

    with check, allure.step("Leaving a reply to the question with the question owner and verifying"
                            " that the question is still listed inside the 'Attention needed' tab "
                            "filter"):
        utilities.navigate_to_link(question_details["question_page_url"])
        sumo_pages.aaq_flow.post_question_reply_flow(repliant_username=test_user["username"],
                                                     reply="Test Reply")
        utilities.navigate_to_link(utilities.general_test_data["product_forums"]["Firefox"])
        assert (question_details["question_id"] in sumo_pages.product_support_forum.
                get_ids_of_all_listed_questions())

    with check, allure.step("Navigating to the 'Responded' filter and verifying that the question "
                            "is not displayed"):
        sumo_pages.product_support_forum.click_on_a_certain_tab_filter("Responded")
        assert (question_details["question_id"] not in sumo_pages.product_support_forum.
                get_ids_of_all_listed_questions())

    with allure.step("Signing in with a different user and leaving a reply to the question"):
        utilities.start_existing_session(cookies=test_user_two)
        utilities.navigate_to_link(question_details["question_page_url"])
        sumo_pages.aaq_flow.post_question_reply_flow(repliant_username=test_user_two["username"],
                                                     reply="Test Reply")

    with check, allure.step("Navigating back to the 'Attention needed' tab filter and verifying "
                            "that the question is not displayed"):
        utilities.navigate_to_link(utilities.general_test_data["product_forums"]["Firefox"])
        assert (question_details["question_id"] not in sumo_pages.product_support_forum.
                get_ids_of_all_listed_questions())

    with check, allure.step("Navigating to the 'Responded' tab filter and verifying that the "
                            "question is displayed"):
        sumo_pages.product_support_forum.click_on_a_certain_tab_filter("Responded")
        assert (question_details["question_id"] in sumo_pages.product_support_forum.
                get_ids_of_all_listed_questions())

    with allure.step("Signing in back with the question owner and leaving a new question reply"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(question_details["question_page_url"])
        sumo_pages.aaq_flow.post_question_reply_flow(repliant_username=test_user["username"],
                                                     reply="Test Reply")

    with check, allure.step("Navigating back to the 'Attention needed' tab filter and verifying "
                            "that the question is displayed"):
        utilities.navigate_to_link(utilities.general_test_data["product_forums"]["Firefox"])
        assert (question_details["question_id"] in sumo_pages.product_support_forum.
                get_ids_of_all_listed_questions())

    with check, allure.step("Navigating to the 'Responded' tab filter and verifying that the "
                            "question is not displayed"):
        sumo_pages.product_support_forum.click_on_a_certain_tab_filter("Responded")
        assert (question_details["question_id"] not in sumo_pages.product_support_forum.
                get_ids_of_all_listed_questions())


# C3171297, C3170431
@pytest.mark.communityForums
def test_spam_tab_filter_visibility(page: Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory()
    test_user_two = create_user_factory(groups=["Forum Moderators"])

    with allure.step("Creating a question and marking it as spam"):
        utilities.start_existing_session(cookies=test_user_two)
        utilities.navigate_to_link(utilities.aaq_question_test_data["products_aaq_url"]["Firefox"])
        question_details = sumo_pages.aaq_flow.submit_an_aaq_question(
            subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=sumo_pages.aaq_form_page.get_aaq_form_topic_options()[0],
            body=utilities.aaq_question_test_data["valid_firefox_question"]["question_body"],
            attach_image=False,
            expected_locator=sumo_pages.question_page.questions_header
        )
        sumo_pages.question_page.click_on_mark_as_spam_option()

    with check, allure.step("Navigating to the 'All Products Community Forum', clicking on the"
                            " 'All' tab filter and verifying that no spam questions are"
                            " displayed"):
        utilities.navigate_to_link(utilities.general_test_data['product_forums']
                                   ['All Products Forum'])
        sumo_pages.product_support_forum.click_on_a_certain_tab_filter("All")
        assert len(sumo_pages.product_support_forum.is_spam_locator.all()) == 0

    with check, allure.step("Clicking on the 'Spam' filter and verifying that the spam-marked"
                            " question is displayed with the correct spam tag"):
        sumo_pages.product_support_forum.click_on_a_certain_tab_filter("Spam")
        assert (sumo_pages.product_support_forum.
                is_spam_flag_for_question(question_details["question_id"]))

    with check, allure.step("Signing out from SUMO and verifying that spam questions and the Spam"
                            " tab filter is not displayed"):
        utilities.delete_cookies()
        assert len(sumo_pages.product_support_forum.is_spam_locator.all()) == 0
        assert not sumo_pages.product_support_forum.is_tab_filter_displayed("Spam")

    with check, allure.step("Signing in with a normal user and verifying that the spam questions"
                            " and the spam tab filter is not displayed"):
        utilities.start_existing_session(cookies=test_user)
        assert len(sumo_pages.product_support_forum.is_spam_locator.all()) == 0


# C3171622
@pytest.mark.communityForums
def test_question_transitions_to_spam_tab_filter(page: Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory()
    test_user_two = create_user_factory(groups=["Forum Moderators"])

    with allure.step("Submitting an AAQ question to the Firefox product"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(utilities.aaq_question_test_data["products_aaq_url"]["Firefox"])
        question_details = sumo_pages.aaq_flow.submit_an_aaq_question(
            subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=sumo_pages.aaq_form_page.get_aaq_form_topic_options()[0],
            body=utilities.aaq_question_test_data["valid_firefox_question"]["question_body"],
            attach_image=False,
            expected_locator=sumo_pages.question_page.questions_header
        )

    with check, allure.step("Navigating to the 'Firefox Community Forum' and verifying that the "
                            "question is listed inside the 'Attention needed' tab filter"):
        utilities.navigate_to_link(utilities.general_test_data["product_forums"]["Firefox"])
        assert (sumo_pages.product_support_forum.
                get_text_of_selected_tab_filter() == "Attention needed")
        assert (question_details["question_id"] in sumo_pages.product_support_forum.
                get_ids_of_all_listed_questions())

    with allure.step("Signing in with a Forum Moderator and marking the question as spam"):
        utilities.navigate_to_link(question_details['question_page_url'])
        utilities.start_existing_session(cookies=test_user_two)
        sumo_pages.question_page.click_on_mark_as_spam_option()

    with check, allure.step("Refreshing the page and verifying that the question is no longer "
                            "listed inside the 'Attention needed' filter tab"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(utilities.general_test_data["product_forums"]["Firefox"])
        utilities.refresh_page()
        assert (question_details["question_id"] not in sumo_pages.product_support_forum.
                get_ids_of_all_listed_questions())

    with check, allure.step("Signing in with a Forum Moderator account and verifying that the"
                            " question is successfully listed inside the 'Spam' tab filter"):
        utilities.start_existing_session(cookies=test_user_two)
        sumo_pages.product_support_forum.click_on_a_certain_tab_filter("Spam")
        assert (question_details["question_id"] in sumo_pages.product_support_forum.
                get_ids_of_all_listed_questions())

    with allure.step("Navigating to the question and unmarking it from spam"):
        utilities.navigate_to_link(question_details['question_page_url'])
        sumo_pages.question_page.click_on_mark_as_spam_option()

    with check, allure.step("Navigating to the 'Firefox Community Forum' and verifying that the "
                            "question is listed inside the 'Attention needed' filter"):
        utilities.navigate_to_link(utilities.general_test_data["product_forums"]["Firefox"])
        assert (sumo_pages.product_support_forum.
                get_text_of_selected_tab_filter() == "Attention needed")
        assert (question_details["question_id"] in sumo_pages.product_support_forum.
                get_ids_of_all_listed_questions())

    with allure.step("Clicking on the 'Spam' filter and verifying that the question is not "
                     "displayed"):
        sumo_pages.product_support_forum.click_on_a_certain_tab_filter("Spam")
        assert (question_details["question_id"] not in sumo_pages.product_support_forum.
                get_ids_of_all_listed_questions())


# C3171686, C3171694
@pytest.mark.communityForums
@pytest.mark.parametrize("question_status", ["has_solution", "is_archived", "is_locked"])
def test_spam_marked_question_does_not_transition_from_spam_tab_filter(page: Page,
                                                                       create_user_factory,
                                                                       question_status):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory()
    test_user_two = utilities.username_extraction_from_email(utilities.staff_user)

    with allure.step("Submitting an AAQ question to the Firefox product"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(utilities.aaq_question_test_data["products_aaq_url"]["Firefox"])
        question_details = sumo_pages.aaq_flow.submit_an_aaq_question(
            subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=sumo_pages.aaq_form_page.get_aaq_form_topic_options()[0],
            body=utilities.aaq_question_test_data["valid_firefox_question"]["question_body"],
            attach_image=False,
            expected_locator=sumo_pages.question_page.questions_header
        )

    with allure.step("Signing in with a Forum Moderator"):
        utilities.start_existing_session(session_file_name=test_user_two)

    with allure.step(f"Marking the question with the {question_status} status and as spam"):
        if question_status == "has_solution":
            reply_id = sumo_pages.aaq_flow.post_question_reply_flow(
                repliant_username=test_user_two, reply="Test Reply")
            sumo_pages.question_page.click_on_solves_the_problem_button(reply_id)
            sumo_pages.question_page.click_on_mark_as_spam_option()
        elif question_status == "is_archived":
            sumo_pages.question_page.click_on_archive_this_question_option()
            sumo_pages.question_page.click_on_mark_as_spam_option()
        elif question_status == "is_locked":
            sumo_pages.question_page.click_on_mark_as_spam_option()
            sumo_pages.question_page.click_on_lock_this_question_option()

    with check, allure.step("Verifying that the question is not displayed inside the 'Attention "
                            "needed' filter"):
        utilities.navigate_to_link(utilities.general_test_data["product_forums"]["Firefox"])
        assert (sumo_pages.product_support_forum.
                get_text_of_selected_tab_filter() == "Attention needed")
        assert (question_details["question_id"] not in sumo_pages.product_support_forum.
                get_ids_of_all_listed_questions())

    with check, allure.step("Clicking on the 'All' filter and verifying that the question is not "
                            "displayed"):
        sumo_pages.product_support_forum.click_on_a_certain_tab_filter("All")
        assert (question_details["question_id"] not in sumo_pages.product_support_forum.
                get_ids_of_all_listed_questions())

    with check, allure.step("Navigating to the 'Spam' filter and verifying that the question is "
                            "displayed"):
        sumo_pages.product_support_forum.click_on_a_certain_tab_filter("Spam")
        assert (question_details["question_id"] in sumo_pages.product_support_forum.
                get_ids_of_all_listed_questions())
        if question_status == "has_solution":
            assert sumo_pages.product_support_forum.is_question_solved_indicator_displayed(
                question_details["question_id"]
            )
        elif question_status == "is_archived":
            assert sumo_pages.product_support_forum.is_question_archived_indicator_displayed(
                question_details["question_id"]
            )
        elif question_status == "is_locked":
            assert sumo_pages.product_support_forum.is_question_locked_indicator_displayed(
                question_details["question_id"]
            )


#  C3170429
@pytest.mark.communityForums
@pytest.mark.parametrize("question_status", ["has_solution", "is_archived", "is_locked"])
def test_questions_transitions_on_status_change(page: Page, create_user_factory, question_status):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory()
    staff_user = utilities.username_extraction_from_email(utilities.staff_user)

    with allure.step("Submitting an AAQ question to the Firefox product"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(utilities.aaq_question_test_data["products_aaq_url"]["Firefox"])
        question_details = sumo_pages.aaq_flow.submit_an_aaq_question(
            subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=sumo_pages.aaq_form_page.get_aaq_form_topic_options()[0],
            body=utilities.aaq_question_test_data["valid_firefox_question"]["question_body"],
            attach_image=False,
            expected_locator=sumo_pages.question_page.questions_header
            )

    with allure.step("Signing in with the second user and leaving a question reply"):
        utilities.start_existing_session(session_file_name=staff_user)
        reply = sumo_pages.aaq_flow.post_question_reply_flow(staff_user, "Solution to question")

    if question_status == "has_solution":
        with allure.step("Marking the question reply as the solution"):
            sumo_pages.question_page.click_on_solves_the_problem_button(reply)
    elif question_status == "is_archived":
        with allure.step("Marking the question as archived"):
            sumo_pages.question_page.click_on_archive_this_question_option()
    elif question_status == "is_locked":
        with allure.step("Marking the question as locked"):
            sumo_pages.question_page.click_on_lock_this_question_option()

    with check, allure.step("Navigating back to the Firefox community forum and verifying that the"
                            " question is not displayed inside the 'Attention needed' tab filter"):
        utilities.navigate_to_link(utilities.general_test_data["product_forums"]["Firefox"])
        assert (sumo_pages.product_support_forum.
                get_text_of_selected_tab_filter() == "Attention needed")
        assert (question_details["question_id"] not in sumo_pages.product_support_forum.
                get_ids_of_all_listed_questions())

    with check, allure.step("Clicking on the 'Responded' tab filter and verifying that the"
                            " question is not displayed"):
        sumo_pages.product_support_forum.click_on_a_certain_tab_filter("Responded")
        assert (question_details["question_id"] not in sumo_pages.product_support_forum.
                get_ids_of_all_listed_questions())

    if question_status == "is_archived":
        with check, allure.step("Clicking on the 'Done' tab filter and verifying that the "
                                "question is not displayed"):
            sumo_pages.product_support_forum.click_on_a_certain_tab_filter("Done")
            assert (question_details["question_id"] not in sumo_pages.product_support_forum.
                    get_ids_of_all_listed_questions())

        with check, allure.step("Clicking on the 'All' tab filter and verifying that the "
                                "1. Question is successfully displayed."
                                "2. Has the correct status icon displayed."):
            sumo_pages.product_support_forum.click_on_a_certain_tab_filter("All")
            assert (question_details["question_id"] in sumo_pages.product_support_forum.
                    get_ids_of_all_listed_questions())
            assert sumo_pages.product_support_forum.is_question_archived_indicator_displayed(
                question_details["question_id"])
    else:
        with check, allure.step("Clicking on the 'Done' tab filter and verifying that:"
                                " 1. The question is successfully displayed."
                                " 2. Has the correct status icon displayed."):
            sumo_pages.product_support_forum.click_on_a_certain_tab_filter("Done")
            assert (question_details["question_id"] in sumo_pages.product_support_forum.
                    get_ids_of_all_listed_questions())

            assert sumo_pages.product_support_forum.is_question_contributed_indicator_displayed(
                question_details["question_id"])

            if question_status == "has_solution":
                assert sumo_pages.product_support_forum.is_question_solved_indicator_displayed(
                    question_details["question_id"])
            elif question_status == "is_locked":
                assert sumo_pages.product_support_forum.is_question_locked_indicator_displayed(
                    question_details["question_id"])

    with allure.step("Navigating back to the question and undoing the question status change."):
        utilities.navigate_to_link(question_details['question_page_url'])
        if question_status == "has_solution":
            with allure.step("Unmarking the question reply from being the solution."):
                sumo_pages.question_page.click_on_undo_button()
        elif question_status == "is_archived":
            with allure.step("Unmarking the question from being archived."):
                sumo_pages.question_page.click_on_archive_this_question_option()
        elif question_status == "is_locked":
            with allure.step("Unmarking the question from being locked"):
                sumo_pages.question_page.click_on_lock_this_question_option()

    with check, allure.step("Navigating back to the Firefox community forum and verifying that"
                            " the question is not displayed inside the 'Attention needed' tab "
                            "filter"):
        utilities.navigate_to_link(utilities.general_test_data["product_forums"]["Firefox"])
        assert (sumo_pages.product_support_forum.
                get_text_of_selected_tab_filter() == "Attention needed")
        assert (question_details["question_id"] not in sumo_pages.product_support_forum.
                get_ids_of_all_listed_questions())

    with check, allure.step("Clicking on the 'Responded' tab filter and verifying that the "
                            "1. Question is successfully displayed. "
                            "2. The correct question status icon is displayed."):
        sumo_pages.product_support_forum.click_on_a_certain_tab_filter("Responded")
        assert (question_details["question_id"] in sumo_pages.product_support_forum.
                get_ids_of_all_listed_questions())
        assert sumo_pages.product_support_forum.is_question_contributed_indicator_displayed(
            question_details["question_id"])
        assert not sumo_pages.product_support_forum.is_question_solved_indicator_displayed(
            question_details["question_id"])
        assert not sumo_pages.product_support_forum.is_question_archived_indicator_displayed(
            question_details["question_id"])
        assert not sumo_pages.product_support_forum.is_question_locked_indicator_displayed(
            question_details["question_id"])

    with check, allure.step("Clicking on the 'Done' tab filter and verifying that the question "
                            "is not displayed"):
        sumo_pages.product_support_forum.click_on_a_certain_tab_filter("Done")
        assert (question_details["question_id"] not in sumo_pages.product_support_forum.
                get_ids_of_all_listed_questions())
