import random
import allure
import pytest
from playwright.sync_api import Page, expect
from pytest_check import check
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.ask_a_question_messages.AAQ_messages.question_page_messages import (
    QuestionPageMessages,
)
from playwright_tests.messages.common_elements_messages import CommonElementsMessages
from playwright_tests.pages.sumo_pages import SumoPages
from kitsune.settings import TRUSTED_GROUPS


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

    with allure.step("Navigating to the posted question"):
        utilities.navigate_to_link(question_info_one["question_page_url"])

    with check, allure.step("Verifying that the scam banner is displayed"):
        assert sumo_pages.common_web_elements.get_scam_banner_text() == (
            CommonElementsMessages.AVOID_SCAM_BANNER_TEXT)


# C946275
@pytest.mark.smokeTest
@pytest.mark.antiSpamTests
def test_spam_content_is_auto_flagged(page: Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(groups=["Forum Moderators"])
    test_user_two = create_user_factory()
    spam_content = ['https://www.example.com', 'layout.display-list.retain.chrome',
                    '800, 888, 877, 866, 855, 844, or 833', '+1 212-555-1234']

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

    for content in spam_content:
        with allure.step("Signing in with an account that doesn't have the bypass ratelimit "
                         "permission"):
            utilities.start_existing_session(cookies=test_user_two)

        with allure.step(f"Leaving a comment with {content} spam content"):
            sumo_pages.aaq_flow.post_question_reply_flow(
                repliant_username=test_user_two["username"], reply=content, fetch_id=False
            )

        with check, allure.step("Verifying that the spam banner is successfully displayed"):
            assert (QuestionPageMessages.SPAM_FLAGGED_REPLY == sumo_pages.question_page.
                    get_text_of_spam_marked_banner())

        with check, allure.step(f"Verifying that the comment is marked as spam"):
            assert not sumo_pages.question_page.is_reply_with_content_displayed(content)

        with check, allure.step("Signing out and verifying that the reply is not displayed"):
            utilities.delete_cookies()
            assert not sumo_pages.question_page.is_reply_with_content_displayed(content)

        with check, allure.step("Signing in with an admin account and verifying that the Marked as "
                                "spam reply is visible"):
            utilities.start_existing_session(cookies=test_user)
            assert sumo_pages.question_page.is_reply_with_content_displayed(content)


# C946276
@pytest.mark.antiSpamTests
def test_valid_prefs_and_internal_links_are_not_flagged_as_spam(page: Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(groups=["Forum Moderators"])
    test_user_two = create_user_factory()
    test_content = ['https://support.mozilla.org', 'dom.ipc.processCount']

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

    for content in test_content:
        with allure.step("Signing in with an account that doesn't have the bypass ratelimit "
                         "permission"):
            utilities.start_existing_session(cookies=test_user_two)

        with allure.step(f"Leaving a comment with {content} spam content"):
            reply_id = sumo_pages.aaq_flow.post_question_reply_flow(
                repliant_username=test_user_two["username"], reply=content,
            )

        with check, allure.step("Verifying that the spam banner is not displayed"):
            expect(sumo_pages.question_page.reply_flagged_as_spam_banner).to_be_hidden()

        with check, allure.step(f"Verifying that the valid pref value comment is displayed"):
            assert sumo_pages.question_page.is_reply_displayed(reply_id)

        with check, allure.step("Signing out and verifying that the reply is displayed"):
            utilities.delete_cookies()
            assert sumo_pages.question_page.is_reply_displayed(reply_id)


# C1296001, C3395616
@pytest.mark.antiSpamTests
def test_question_owner_is_exempted_for_spam_auto_flag(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    spam_content = ['https://www.example.com', 'layout.display-list.retain.chrome',
                    '800, 888, 877, 866, 855, 844, or 833', '+1 212-555-1234']
    test_user = create_user_factory()

    with allure.step("Signing in creating an AAQ question"):
        utilities.start_existing_session(cookies=test_user)

    utilities.navigate_to_link(
        utilities.aaq_question_test_data["products_aaq_url"]["Firefox"])
    sumo_pages.aaq_flow.submit_an_aaq_question(
        subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
        topic_name=sumo_pages.aaq_form_page.get_aaq_form_topic_options()[0],
        body=utilities.
             aaq_question_test_data["valid_firefox_question"]["question_body"] + spam_content[1],
        attach_image=False,
        expected_locator=sumo_pages.question_page.questions_header
    )

    for content in spam_content:
        with allure.step(f"Leaving a comment with a spam comment"):
            reply_id = sumo_pages.aaq_flow.post_question_reply_flow(
                repliant_username=test_user["username"], reply=content
            )

        with check, allure.step("Verifying that the spam banner is not displayed"):
            expect(sumo_pages.question_page.reply_flagged_as_spam_banner).to_be_hidden()

        with check, allure.step(f"Verifying that the comment is displayed"):
            assert sumo_pages.question_page.is_reply_displayed(reply_id)


# C3395573, C3395578
@pytest.mark.antiSpamTests
@pytest.mark.parametrize("trusted_user_config", [
    {"groups": [random.choice(TRUSTED_GROUPS)]},
    {"permissions": ["can_moderate"]}
])
def test_trusted_contributors_are_exempted_from_spam_check(page: Page, create_user_factory,
                                                           trusted_user_config):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    trusted_group_user = create_user_factory(**trusted_user_config)
    spam_content = ['https://www.example.com', 'layout.display-list.retain.chrome',
                    '800, 888, 877, 866, 855, 844, or 833', '+1 212-555-1234']

    with allure.step("Signing in creating an AAQ question"):
        utilities.start_existing_session(cookies=test_user)

    utilities.navigate_to_link(
        utilities.aaq_question_test_data["products_aaq_url"]["Firefox"])
    sumo_pages.aaq_flow.submit_an_aaq_question(
        subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
        topic_name=sumo_pages.aaq_form_page.get_aaq_form_topic_options()[0],
        body=utilities.aaq_question_test_data["valid_firefox_question"]["question_body"],
        attach_image=False,
        expected_locator=sumo_pages.question_page.questions_header
    )

    for content in spam_content:
        with allure.step("Signing in with a trusted user"):
            utilities.start_existing_session(cookies=trusted_group_user)

        with allure.step(f"Leaving a comment with a spam comment"):
            reply_id = sumo_pages.aaq_flow.post_question_reply_flow(
                repliant_username=trusted_group_user["username"], reply=content
            )

        with check, allure.step("Verifying that the spam banner is not displayed"):
            expect(sumo_pages.question_page.reply_flagged_as_spam_banner).to_be_hidden()

        with check, allure.step(f"Verifying that the comment is displayed"):
            assert sumo_pages.question_page.is_reply_displayed(reply_id)
