import allure
import pytest
from playwright.sync_api import Page
from pytest_check import check
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.ask_a_question_messages.AAQ_messages.question_page_messages import (
    QuestionPageMessages,
)
from playwright_tests.messages.common_elements_messages import CommonElementsMessages
from playwright_tests.pages.sumo_pages import SumoPages


# C946237
@pytest.mark.antiSpamTests
@pytest.mark.parametrize("user_type", ['', 'Simple User'])
def test_anti_spam_banner(page: Page, user_type, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(groups=["Forum Moderators"])
    test_user_two = create_user_factory()

    with allure.step("Signing in with a Forum Moderator account and creating an AAQ question"):
        utilities.start_existing_session(cookies=test_user)

        utilities.navigate_to_link(utilities.aaq_question_test_data["products_aaq_url"]["Firefox"])
        question_info_one = sumo_pages.aaq_flow.submit_an_aaq_question(
            subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=sumo_pages.aaq_form_page.get_aaq_form_topic_options()[0],
            body=utilities.aaq_question_test_data["valid_firefox_question"]["question_body"],
            attach_image=False,
            expected_locator=sumo_pages.question_page.questions_header
        )

    if user_type != '':
        utilities.start_existing_session(cookies=test_user_two)
    else:
        utilities.delete_cookies()

    with check, allure.step("Navigating to each available product support forum and verifying that"
                            " the scam banner is displayed"):
        for product, url in utilities.general_test_data["product_forums"].items():
            utilities.navigate_to_link(url)
            assert sumo_pages.common_web_elements.get_scam_banner_text() == (
                CommonElementsMessages.AVOID_SCAM_BANNER_TEXT)

    with allure.step("Navigating to the posted question and verifying that the scam banner is "
                     "displayed"):
        utilities.navigate_to_link(question_info_one["question_page_url"])
        assert sumo_pages.common_web_elements.get_scam_banner_text() == (CommonElementsMessages.
                                                                         AVOID_SCAM_BANNER_TEXT)


# C946274
@pytest.mark.smokeTest
@pytest.mark.antiSpamTests
def test_valid_tld_in_question_comment(page: Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    invalid_tld = "dom.ipc.processCount"
    valid_tld = "layout.display-list.retain.chrome"
    test_user = create_user_factory(groups=["Forum Moderators"])
    test_user_two = create_user_factory()

    with allure.step("Signing in with a Forum Moderator account and creating an AAQ question"):
        utilities.start_existing_session(cookies=test_user)

        utilities.navigate_to_link(utilities.aaq_question_test_data["products_aaq_url"]["Firefox"])
        sumo_pages.aaq_flow.submit_an_aaq_question(
            subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=sumo_pages.aaq_form_page.get_aaq_form_topic_options()[0],
            body=utilities.aaq_question_test_data["valid_firefox_question"]["question_body"],
            attach_image=False,
            expected_locator=sumo_pages.question_page.questions_header
        )

    with allure.step("Signing in with an account that doesn't have the bypass ratelimit "
                     "permission"):
        utilities.start_existing_session(cookies=test_user_two)

    with allure.step("Leaving a comment with an invalid TLD"):
        reply_one = sumo_pages.aaq_flow.post_question_reply_flow(
            repliant_username=test_user_two["username"], reply=invalid_tld
        )

    with check, allure.step("Verifying that the invalid TLD comment is not marked as spam "
                            "and the spam banner is not displayed"):
        assert not sumo_pages.question_page.is_spam_marked_banner_displayed()
        assert sumo_pages.question_page.is_reply_displayed(reply_one)

    with allure.step("Leaving a comment with a valid TLD"):
        sumo_pages.aaq_flow.post_question_reply_flow(
            repliant_username=test_user_two["username"], reply=valid_tld
        )

    with check, allure.step("Verifying that the valid TLD comment is marked as spam and the "
                            "banner is successfully displayed"):
        assert (QuestionPageMessages.SPAM_FLAGGED_REPLY == sumo_pages.question_page.
                get_text_of_spam_marked_banner())
        assert not sumo_pages.question_page.is_reply_with_content_displayed(valid_tld)

    with check, allure.step("Signing out and verifying that the reply is not displayed"):
        utilities.delete_cookies()
        assert not sumo_pages.question_page.is_reply_with_content_displayed(valid_tld)

    with check, allure.step("Signing in with an admin account and verifying that the Marked as"
                            "spam reply is visible"):
        utilities.start_existing_session(cookies=test_user)
        assert sumo_pages.question_page.is_reply_with_content_displayed(valid_tld)
