import os
import time

import allure
import pytest
from pytest_check import check
from playwright_tests.core.utilities import Utilities
from playwright.sync_api import expect, TimeoutError, Page

from playwright_tests.messages.contribute_messages.con_tools.moderate_forum_messages import (
    ModerateForumContentPageMessages)
from playwright_tests.messages.ask_a_question_messages.AAQ_messages.question_page_messages import (
    QuestionPageMessages)
from playwright_tests.messages.auth_pages_messages.fxa_page_messages import (
    FxAPageMessages)
from playwright_tests.messages.ask_a_question_messages.contact_support_messages import (
    ContactSupportMessages)
from playwright_tests.pages.sumo_pages import SumoPages


# C2191086, C2191094, C2191263,  C2191263, C2191087, C2191088
# T5696747, T5696755, T5696748, T5696751, T5696749
@pytest.mark.postedQuestions
@pytest.mark.parametrize("username", ['TEST_ACCOUNT_MESSAGE_5', ''])
def test_posted_question_details(page: Page, username):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with a non-admin user account and posting a Firefox product "
                     "question"):
        post_firefox_product_question_flow(page, 'TEST_ACCOUNT_MESSAGE_5')

    with allure.step("Deleting user session"):
        utilities.delete_cookies()

    if username == 'TEST_ACCOUNT_MESSAGE_5':
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_5"]
        ))
        page.reload()

    with allure.step("Verifying that the scam banner is displayed"):
        expect(sumo_pages.product_solutions_page._get_scam_banner_locator()).to_be_visible()

    with allure.step("Verifying that the still need help banner is displayed"):
        expect(sumo_pages.product_solutions_page._get_still_need_help_locator()).to_be_visible()

    with check, allure.step("Verifying that the Learn More button contains the correct link"):
        assert sumo_pages.product_solutions_page._get_scam_alert_banner_link(
        ) == QuestionPageMessages.AVOID_SCAM_SUPPORT_LEARN_MORE_LINK

    with allure.step("Signing in with an admin account and verifying that the scam banner is "
                     "displayed and the still need help banner is displayed"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        expect(sumo_pages.product_solutions_page._get_scam_banner_locator()).to_be_visible()
        expect(sumo_pages.product_solutions_page._get_still_need_help_locator()).to_be_visible()

    with check, allure.step("Verifying that the Learn More button contains the correct link"):
        assert sumo_pages.product_solutions_page._get_scam_alert_banner_link(
        ) == QuestionPageMessages.AVOID_SCAM_SUPPORT_LEARN_MORE_LINK

    with allure.step("Deleting the posted question"):
        sumo_pages.aaq_flow.deleting_question_flow()


# T5696750, T5696753
@pytest.mark.postedQuestions
def test_edit_this_question_functionality_not_signed_in(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with an admin account and posting a Firefox question"):
        post_firefox_product_question_flow(page, 'TEST_ACCOUNT_MODERATOR')

    with allure.step("Deleting user session and verifying that the 'edit this question' nav "
                     "option is not available"):
        utilities.delete_cookies()
        expect(sumo_pages.question_page.get_edit_this_question_option_locator()).to_be_hidden()

    with allure.step("Navigating to the edit endpoint and verifying that the user is "
                     "redirected to the auth page"):
        utilities.navigate_to_link(
            utilities.get_page_url() + QuestionPageMessages.EDIT_QUESTION_URL_ENDPOINT
        )
        assert (
            FxAPageMessages.AUTH_PAGE_URL in utilities.get_page_url()
        )

    with allure.step("Deleting the posted question"):
        utilities.navigate_back()
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        sumo_pages.aaq_flow.deleting_question_flow()


# C2191262, C2436105,  C2191263
# To add image tests
@pytest.mark.postedQuestions
@pytest.mark.parametrize("username", ['TEST_ACCOUNT_MESSAGE_6', 'TEST_ACCOUNT_MODERATOR'])
def test_cancel_edit_this_question_functionality(page: Page, username):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with a non admin user account and posting a Firefox product "
                     "question"):
        posted_question = post_firefox_product_question_flow(page,
                                                             'TEST_ACCOUNT_MESSAGE_6')

    if username == 'TEST_ACCOUNT_MODERATOR':
        with allure.step("Signing in with an admin account"):
            utilities.start_existing_session(utilities.username_extraction_from_email(
                utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

    with check, allure.step("Navigating to the posted question, clicking on the 'Edit this "
                            "question' option and verifying that the subject field contains "
                            "the correct value"):
        utilities.navigate_to_link(posted_question['question_details']['question_page_url'])
        sumo_pages.question_page.click_on_edit_this_question_question_tools_option()
        assert sumo_pages.aaq_form_page.get_value_of_subject_input_field(
        ) == posted_question['question_details']['aaq_subject']

    with check, allure.step("Verifying that the question body contains the correct value"):
        assert sumo_pages.aaq_form_page.get_value_of_question_body_textarea_field(
        ) == posted_question['question_details']['question_body']

    with allure.step("Editing the question with new data"):
        sumo_pages.aaq_flow.editing_question_flow(
            subject=utilities.aaq_question_test_data['valid_firefox_question']
            ['subject_updated'],
            body=utilities.aaq_question_test_data['valid_firefox_question']['body_updated'],
            troubleshoot=utilities.aaq_question_test_data['troubleshooting_information'],
            submit_edit=False
        )

    with check, allure.step("Clicking on the 'Cancel' button and verifying that the modified "
                            "text is not displayed"):
        sumo_pages.aaq_form_page.click_aaq_form_cancel_button()
        expect(sumo_pages.question_page.get_modified_question_locator()).to_be_hidden()
        assert sumo_pages.question_page.get_question_header(
        ) == posted_question['question_details']['aaq_subject']
        assert sumo_pages.question_page.get_question_body(
        ) == posted_question['question_details']['question_body'] + '\n'

    if username == 'TEST_ACCOUNT_12':
        with allure.step("Verifying that the additional question details option is hidden"):
            expect(sumo_pages.question_page.get_question_details_button_locator()).to_be_hidden()
    elif username == "TEST_ACCOUNT_MODERATOR":
        with allure.step("Verifying that the more information section from the 'More System "
                         "Details' is not displayed"):
            sumo_pages.question_page.click_on_question_details_button()
            sumo_pages.question_page.click_on_more_system_details_option()
            expect(sumo_pages.question_page.get_more_information_locator()).to_be_hidden()

        with allure.step("Closing the more information panel and deleting the question"):
            sumo_pages.question_page.click_on_the_additional_system_panel_close()

            if username != 'TEST_ACCOUNT_MODERATOR':
                utilities.start_existing_session(
                    utilities.username_extraction_from_email(
                        utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
                    ))

            sumo_pages.aaq_flow.deleting_question_flow()


# C2191263
@pytest.mark.postedQuestions
def test_edit_other_user_question_non_admin(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with a non admin user account and posting a Firefox product "
                     "question"):
        posted_question = post_firefox_product_question_flow(page, 'TEST_ACCOUNT_13')

    with allure.step("Signing in with a non admin user account and verifying that the 'Edit "
                     "this question' option is not available"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))
        expect(sumo_pages.question_page.get_edit_this_question_option_locator()).to_be_hidden()

    with check, allure.step("Manually navigating to the '/edit' endpoint and verifying that "
                            "403 is returned"):
        with page.expect_navigation() as navigation_info:
            utilities.navigate_to_link(
                posted_question['question_details']
                ['question_page_url'] + QuestionPageMessages.
                EDIT_QUESTION_URL_ENDPOINT)
        response = navigation_info.value
        assert response.status == 403

    with allure.step("Signing in with an admin account and deleting the posted question"):
        utilities.navigate_to_link(posted_question['question_details']['question_page_url'])
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        sumo_pages.aaq_flow.deleting_question_flow()


# T5696778, T5696752, T5696797
# To add image tests
@pytest.mark.postedQuestions
@pytest.mark.parametrize("username", ['TEST_ACCOUNT_MESSAGE_6', 'TEST_ACCOUNT_MODERATOR'])
def test_edit_this_question_functionality(page: Page, username):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with a non admin user account and posting a Firefox product "
                     "question"):
        posted_question = post_firefox_product_question_flow(page,
                                                             'TEST_ACCOUNT_MESSAGE_6')
        user = utilities.username_extraction_from_email(utilities.user_secrets_accounts[username])

    if username == 'TEST_ACCOUNT_MODERATOR':
        with allure.step("Signing in with an admin account"):
            utilities.start_existing_session(utilities.username_extraction_from_email(
                utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

    with check, allure.step("Clicking on the 'Edit this question' option and verifying that "
                            "the subject and body fields contain the correct value"):
        utilities.navigate_to_link(posted_question['question_details']['question_page_url'])
        sumo_pages.question_page.click_on_edit_this_question_question_tools_option()
        assert sumo_pages.aaq_form_page.get_value_of_subject_input_field(
        ) == posted_question['question_details']['aaq_subject']
        assert sumo_pages.aaq_form_page.get_value_of_question_body_textarea_field(
        ) == posted_question['question_details']['question_body']

    with check, allure.step("Editing the question with new data and verifying that the "
                            "modified text is displayed and the username is displayed inside"
                            " the modified text"):
        sumo_pages.aaq_flow.editing_question_flow(
            subject=utilities.aaq_question_test_data['valid_firefox_question']
            ['subject_updated'],
            body=utilities.aaq_question_test_data['valid_firefox_question']['body_updated'],
            troubleshoot=utilities.aaq_question_test_data['troubleshooting_information']
        )
        expect(sumo_pages.question_page.get_modified_question_locator()).to_be_visible()

        assert user in sumo_pages.question_page.get_modified_by_text()
        assert sumo_pages.question_page.get_question_header(
        ) == utilities.aaq_question_test_data['valid_firefox_question']['subject_updated']
        assert sumo_pages.question_page.get_question_body(
        ) == utilities.aaq_question_test_data['valid_firefox_question']['body_updated'] + '\n'

    if username == 'TEST_ACCOUNT_12':
        with allure.step("Verifying that the additional question details option is hidden"):
            expect(sumo_pages.question_page.get_question_details_button_locator()).to_be_hidden()
    elif username == "TEST_ACCOUNT_MODERATOR":
        with allure.step("Verifying that the more information section displays the updated "
                         "information"):
            sumo_pages.question_page.click_on_question_details_button()
            sumo_pages.question_page.click_on_more_system_details_option()
            expect(sumo_pages.question_page.get_more_information_with_text_locator(
                utilities.aaq_question_test_data['troubleshooting_information']
            )
            ).to_be_visible()

        sumo_pages.question_page.click_on_the_additional_system_panel_close()

    with allure.step("Deleting the posted question"):
        if username != 'TEST_ACCOUNT_MODERATOR':
            utilities.start_existing_session(utilities.username_extraction_from_email(
                utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        sumo_pages.aaq_flow.deleting_question_flow()


# T5696750, T5696779, T5696752
@pytest.mark.postedQuestions
def test_delete_question_cancel_button(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with a non admin user account and posting a Firefox product "
                     "question"):
        posted_question_one = post_firefox_product_question_flow(page, 'TEST_ACCOUNT_13')

    with allure.step("Signing in with a different non-admin user account and posting a "
                     "Firefox product question"):
        posted_question_two = post_firefox_product_question_flow(page, 'TEST_ACCOUNT_12')

    with allure.step("Navigating to the posted question by a different user an verifying "
                     "that the 'Delete this question' option is not available"):
        utilities.navigate_to_link(posted_question_one['question_details']['question_page_url'])
        expect(sumo_pages.question_page.get_delete_this_question_locator()).to_be_hidden()

    with check, allure.step("Manually navigating to the delete endpoint and verifying that "
                            "403 is returned"):
        with page.expect_navigation() as navigation_info:
            utilities.navigate_to_link(
                posted_question_one['question_details']
                ['question_page_url'] + QuestionPageMessages.DELETE_QUESTION_URL_ENDPOINT)
        response = navigation_info.value
        assert response.status == 403

    with allure.step("Navigating to the posted question by self and verifying that the "
                     "'Delete this question' option is not available"):
        utilities.navigate_to_link(posted_question_two['question_details']['question_page_url'])
        expect(sumo_pages.question_page.get_delete_this_question_locator()).to_be_hidden()

    with check, allure.step("Manually navigating to the delete endpoint and verifying that "
                            "403 is returned"):
        with page.expect_navigation() as navigation_info:
            utilities.navigate_to_link(
                posted_question_one['question_details']
                ['question_page_url'] + QuestionPageMessages.DELETE_QUESTION_URL_ENDPOINT)
        response = navigation_info.value
        assert response.status == 403

    with allure.step("Signing in with an admin account, clicking on the delete question for "
                     "second question and clicking on the 'Cancel' confirmation button"):
        utilities.navigate_to_link(posted_question_two['question_details']['question_page_url'])
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        sumo_pages.question_page.click_delete_this_question_question_tools_option()
        sumo_pages.aaq_form_page.click_aaq_form_cancel_button()

    with allure.step("Verifying that the question is not deleted"):
        expect(page).to_have_url(posted_question_two['question_details']['question_page_url'])

    with allure.step("Deleting both questions"):
        sumo_pages.aaq_flow.deleting_question_flow()
        utilities.navigate_to_link(posted_question_one['question_details']['question_page_url'])
        sumo_pages.aaq_flow.deleting_question_flow()


# T5696750, T5696780, T5696781, T5696752
# To add coverage for images as well
@pytest.mark.postedQuestions
@pytest.mark.parametrize("status", ['locked', 'archived'])
def test_lock_and_archive_this_question(page: Page, status):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with a non-admin user account and posting a Firefox product "
                     "question"):
        posted_question = post_firefox_product_question_flow(page, 'TEST_ACCOUNT_13')

    with allure.step("Signing in with a different non-admin user account and posting a "
                     "different question"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))
        utilities.navigate_to_link(utilities.aaq_question_test_data["products_aaq_url"]["Firefox"])

        question_info_two = sumo_pages.aaq_flow.submit_an_aaq_question(
            subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=sumo_pages.aaq_form_page.get_aaq_form_topic_options()[0],
            body=utilities.aaq_question_test_data["valid_firefox_question"]
            ["simple_body_text"],
            attach_image=False
        )

    with allure.step("Navigating to the first posted question"):
        utilities.navigate_to_link(posted_question['question_details']['question_page_url'])

    if status == "locked":
        with allure.step("Verifying that the 'Lock this question' option is not available for "
                         "other posted questions"):
            expect(sumo_pages.question_page.get_lock_this_question_locator()).to_be_hidden()
    elif status == "archived":
        with allure.step("Verifying that the 'Archive this question' option is not available "
                         "for other posted questions"):
            expect(sumo_pages.question_page.get_archive_this_question_locator()).to_be_hidden()

    with allure.step("Navigating to the question posted by self"):
        utilities.navigate_to_link(question_info_two['question_page_url'])

    if status == "locked":
        with allure.step("Verifying that the 'Lock this question is not available for self "
                         "posted questions"):
            expect(sumo_pages.question_page.get_lock_this_question_locator()).to_be_hidden()
    elif status == "archived":
        with allure.step("Verifying that the 'Archive this question' is not available for "
                         "self posted questions"):
            expect(sumo_pages.question_page.get_archive_this_question_locator()).to_be_hidden()

    with allure.step("Signing in with an admin account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

    if status == "locked":
        with allure.step("Clicking on the 'Lock this question' option"):
            sumo_pages.question_page.click_on_lock_this_question_locator()
    elif status == "archived":
        with allure.step("Clicking on the 'Archive this question' option"):
            sumo_pages.question_page.click_on_archive_this_question_option()

    with allure.step("Signing in with a different non admin user account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

    if status == "locked":
        with check, allure.step("Verifying that correct locked thread banner text is "
                                "displayed"):
            assert sumo_pages.question_page.get_thread_locked_text(
            ) == QuestionPageMessages.LOCKED_THREAD_BANNER
    elif status == "archived":
        with check, allure.step("Verifying that correct archived thread banner text is "
                                "displayed"):
            assert sumo_pages.question_page.get_thread_locked_text(
            ) == QuestionPageMessages.ARCHIVED_THREAD_BANNER

    with allure.step("Clicking on the locked thread link and verifying that we are "
                     "redirected to the correct page"):
        sumo_pages.question_page.click_on_thread_locked_link()
        expect(page).to_have_url(ContactSupportMessages.PAGE_URL)

    with allure.step("Navigating back to the question page"):
        utilities.navigate_back()

    if status == "locked":
        with allure.step("Verifying that the 'Unlock this question option' is not available'"):
            expect(sumo_pages.question_page.get_lock_this_question_locator()).to_be_hidden()
    elif status == "archived":
        with allure.step("Verifying that the 'Archive this question' options is not "
                         "available"):
            expect(sumo_pages.question_page.get_archive_this_question_locator()).to_be_hidden()

    with allure.step("Verifying that the post a reply textarea field is not displayed"):
        expect(sumo_pages.question_page.get_post_a_reply_textarea_locator()).to_be_hidden()

    with allure.step("Verifying that the 'needs more information from the user' checkbox is "
                     "not displayed"):
        expect(sumo_pages.question_page.get_needs_more_information_checkbox_locator()
               ).to_be_hidden()

    with allure.step("Verifying that the 'Add images section is not displayed'"):
        expect(sumo_pages.question_page.get_add_image_section_locator()).to_be_hidden()

    with allure.step("Signing in with an admin account and verifying that the 'needs more "
                     "information from the user' checkbox is available"):
        repliant_username = utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        )
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        expect(sumo_pages.question_page.get_needs_more_information_checkbox_locator()
               ).to_be_visible()

    with allure.step("Verifying that the 'Add images' section is available"):
        expect(sumo_pages.question_page.get_add_image_section_locator()).to_be_visible()

    with allure.step("Submitting a reply to the question and verifying that the posted reply "
                     "is visible"):
        reply_id = sumo_pages.aaq_flow.post_question_reply_flow(
            repliant_username=repliant_username,
            reply=utilities.aaq_question_test_data['valid_firefox_question']['question_reply']
        )
        expect(sumo_pages.question_page.get_posted_reply_locator(reply_id)).to_be_visible()

    with allure.step("Signing in with a normal user account and verifying that the admin's "
                     "reply is visible"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))
        expect(sumo_pages.question_page.get_posted_reply_locator(reply_id)).to_be_visible()

    with allure.step("Signing in with an admin account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

    if status == "locked":
        with allure.step("Unlocking the question"):
            sumo_pages.question_page.click_on_lock_this_question_locator()
    elif status == "archived":
        with allure.step("Clicking on the 'Archive this question' option"):
            sumo_pages.question_page.click_on_archive_this_question_option()

    with allure.step("Signing in with a non-admin account and verifying that the 'Thread "
                     "locked' banner is not displayed"):
        second_repliant = utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_12"]
        )
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))
        expect(sumo_pages.question_page.get_thread_locked_locator()).to_be_hidden()

    with allure.step("Submitting a reply to the question and verifying that the posted reply "
                     "is visible"):
        reply_id_two = sumo_pages.aaq_flow.post_question_reply_flow(
            repliant_username=second_repliant,
            reply=utilities.aaq_question_test_data['valid_firefox_question']['question_reply']
        )
        expect(sumo_pages.question_page.get_posted_reply_locator(reply_id_two)).to_be_visible()

    with allure.step("Signing in with an admin account and deleting both questions"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        sumo_pages.aaq_flow.deleting_question_flow()
        utilities.navigate_to_link(
            posted_question['question_details']['question_page_url']
        )
        sumo_pages.aaq_flow.deleting_question_flow()


# T5696750, T5696783, T5696752, T5696764
@pytest.mark.postedQuestions
def test_subscribe_to_feed_option(page: Page, is_firefox):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with a non admin user account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_13"]
        ))

    with allure.step("Posting a Firefox product question"):
        utilities.navigate_to_link(utilities.aaq_question_test_data["products_aaq_url"]["Firefox"])

        question_info_one = sumo_pages.aaq_flow.submit_an_aaq_question(
            subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=sumo_pages.aaq_form_page.get_aaq_form_topic_options()[0],
            body=utilities.aaq_question_test_data["valid_firefox_question"]
            ["simple_body_text"],
            attach_image=False
        )

    with allure.step("Signing in with a different non admin user account and posting a "
                     "Firefox product question"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))
        utilities.navigate_to_link(utilities.aaq_question_test_data["products_aaq_url"]["Firefox"])

        question_info_two = sumo_pages.aaq_flow.submit_an_aaq_question(
            subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=sumo_pages.aaq_form_page.get_aaq_form_topic_options()[0],
            body=utilities.aaq_question_test_data["valid_firefox_question"]
            ["simple_body_text"],
            attach_image=False
        )

    with allure.step("Navigating to the first question, clicking on the 'Subscribe to feed' "
                     "option and verifying that the url is updated to the feed endpoint ("
                     "Chrome) or has the correct download info (Firefox)"):
        utilities.navigate_to_link(question_info_one['question_page_url'])

        if not is_firefox:
            sumo_pages.question_page.click_on_subscribe_to_feed_option()
            expect(page).to_have_url(
                question_info_one['question_page_url'] + QuestionPageMessages.FEED_FILE_PATH
            )
        else:
            with page.expect_download() as download_info:
                sumo_pages.question_page.click_on_subscribe_to_feed_option()
            download = download_info.value

            with allure.step("Verifying that the received file contains the correct name"):
                assert QuestionPageMessages.FEED_FILE_NAME in download.suggested_filename

            with allure.step("Verifying that the received file is not empty"):
                assert (
                    os.path.getsize(download.path()) > 0
                )

    with allure.step("Navigating to the first question, clicking on the 'Subscribe to feed' "
                     "option and verifying that the url is updated to the feed endpoint ("
                     "Chrome) or has the correct download info (Firefox)"):
        utilities.navigate_to_link(question_info_two['question_page_url'])
        if not is_firefox:
            sumo_pages.question_page.click_on_subscribe_to_feed_option()
            expect(page).to_have_url(
                question_info_two['question_page_url'] + QuestionPageMessages.FEED_FILE_PATH
            )
            utilities.navigate_back()
        else:
            with page.expect_download() as download_info:
                sumo_pages.question_page.click_on_subscribe_to_feed_option()
            download = download_info.value

            with check, allure.step("Verifying that the received file contains the correct "
                                    "name"):
                assert QuestionPageMessages.FEED_FILE_NAME in download.suggested_filename

            with allure.step("Verifying that the received file is not empty"):
                assert (
                    os.path.getsize(download.path()) > 0
                )

    with allure.step("Signing out and Navigating to the first question,clicking on the "
                     "'Subscribe to feed' option and verifying that the url is updated to "
                     "the feed endpoint (Chrome) or has the correct download info (Firefox)"):
        utilities.delete_cookies()

        if not is_firefox:
            sumo_pages.question_page.click_on_subscribe_to_feed_option()
            expect(page).to_have_url(
                question_info_two['question_page_url'] + QuestionPageMessages.FEED_FILE_PATH
            )
            utilities.navigate_back()
        else:
            with page.expect_download() as download_info:
                sumo_pages.question_page.click_on_subscribe_to_feed_option()
            download = download_info.value

            with check, allure.step("Verifying that the received file contains the correct "
                                    "name"):
                assert QuestionPageMessages.FEED_FILE_NAME in download.suggested_filename

            with allure.step("Verifying that the received file is not empty"):
                assert (
                    os.path.getsize(download.path()) > 0
                )

    with allure.step("Signing in with an admin account and Navigating to the first question,"
                     "clicking on the 'Subscribe to feed' option and verifying that the url "
                     "is updated to the feed endpoint (Chrome) or has the correct download "
                     "info (Firefox)"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        if not is_firefox:
            sumo_pages.question_page.click_on_subscribe_to_feed_option()
            expect(page).to_have_url(
                question_info_two['question_page_url'] + QuestionPageMessages.FEED_FILE_PATH
            )
            utilities.navigate_back()
        else:
            with page.expect_download() as download_info:
                sumo_pages.question_page.click_on_subscribe_to_feed_option()
            download = download_info.value

            with check, allure.step("Verifying that the received file contains the correct "
                                    "name"):
                assert QuestionPageMessages.FEED_FILE_NAME in download.suggested_filename

            with allure.step("Verifying that the received file is not empty"):
                assert (
                    os.path.getsize(download.path()) > 0
                )

    with allure.step("Deleting the posted question"):
        sumo_pages.aaq_flow.deleting_question_flow()
        utilities.navigate_to_link(question_info_one['question_page_url'])
        sumo_pages.aaq_flow.deleting_question_flow()


# To work on adding a check inside the moderate forum content page
# T5696784, T5696750, T5696787,  T5696752
@pytest.mark.postedQuestions
def test_mark_as_spam_functionality(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with a non admin user account and posting a Firefox product "
                     "question"):
        posted_question = post_firefox_product_question_flow(page, 'TEST_ACCOUNT_12')

    with allure.step("Deleting user session and verifying that the 'Mark as spam' option is "
                     "not displayed"):
        utilities.delete_cookies()
        expect(sumo_pages.question_page.get_mark_as_spam_locator()).to_be_hidden()

    with allure.step("Signing in with a non admin user account and verifying that the 'Mark "
                     "as spam' option is not displayed"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))
        expect(sumo_pages.question_page.get_mark_as_spam_locator()).to_be_hidden()

    with check, allure.step("Signing in with an admin account, clicking on the 'mark as "
                            "spam' option and verifying that the correct spam banner message"
                            " is displayed"):
        username = utilities.start_existing_session(
            utilities.username_extraction_from_email(
                utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))
        sumo_pages.question_page.click_on_mark_as_spam_option()
        assert (QuestionPageMessages.MARKED_AS_SPAM_BANNER + username in sumo_pages.question_page.
                get_marked_as_spam_banner_text())

    with check, allure.step("Deleting the user session, navigating to the posted question "
                            "and verifying that the 404 is returned"):
        utilities.delete_cookies()
        with page.expect_navigation() as navigation_info:
            utilities.navigate_to_link(posted_question['question_details']['question_page_url'])
        response = navigation_info.value
        assert response.status == 404

    with check, allure.step("Signing in with a non admin user account, navigating to the "
                            "posted question and verifying that 404 is returned"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))
        with page.expect_navigation() as navigation_info:
            utilities.navigate_to_link(posted_question['question_details']['question_page_url'])
        response = navigation_info.value
        assert response.status == 404

    with allure.step("Signing in with an admin account, clicking on the 'Mark as spam' "
                     "option and verifying that the 'Mark as spam' banner is not displayed"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        sumo_pages.question_page.click_on_mark_as_spam_option()
        expect(sumo_pages.question_page.get_marked_as_spam_banner_locator()).to_be_hidden()

    with allure.step("Deleting the user session and verifying that the 'Marked as spam' "
                     "banner is not displayed"):
        utilities.delete_cookies()
        expect(sumo_pages.question_page.get_marked_as_spam_banner_locator()).to_be_hidden()

    with allure.step("Signing in with a non admin user account and verifying that the "
                     "'Marked as spam' banner is not displayed"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))
        expect(sumo_pages.question_page.get_marked_as_spam_banner_locator()).to_be_hidden()

    with allure.step("Signing in with an admin account and deleting the question"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        sumo_pages.aaq_flow.deleting_question_flow()


# T5696756, T5696758, T5696760
@pytest.mark.postedQuestions
@pytest.mark.parametrize("username", ['', 'TEST_ACCOUNT_13'])
def test_question_topics(page: Page, username):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with a non admin user account and posting a Firefox product "
                     "question"):
        posted_question = post_firefox_product_question_flow(page, 'TEST_ACCOUNT_12')

    with allure.step("Verifying that the 'Add a tag' input field is not displayed for OP"):
        expect(sumo_pages.question_page.get_add_a_tag_input_field()).to_be_hidden()

    with allure.step("Verifying that the 'Add' topic section button is not displayed for OP"):
        expect(sumo_pages.question_page.get_add_a_tag_button()).to_be_hidden()

    with allure.step("Deleting user session"):
        utilities.delete_cookies()

    if username == 'TEST_ACCOUNT_13':
        with allure.step("Signing in with a non admin user account"):
            utilities.start_existing_session(utilities.username_extraction_from_email(
                utilities.user_secrets_accounts["TEST_ACCOUNT_13"]
            ))

    with allure.step("Verifying that the 'Add a tag' input field is not displayed"):
        expect(sumo_pages.question_page.get_add_a_tag_input_field()).to_be_hidden()

    with allure.step("Verifying that the 'Add' topic section button is not displayed"):
        expect(sumo_pages.question_page.get_add_a_tag_button()).to_be_hidden()

    with allure.step("Verifying that the remove tag button is not displayed"):
        for tag in sumo_pages.question_page.get_question_tag_options():
            expect(sumo_pages.question_page.get_remove_tag_button_locator(tag)).to_be_hidden()

    with allure.step("Signing in with a admin user account, adding data inside the 'Add a "
                     "tag' input field"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        sumo_pages.question_page.add_text_to_add_a_tag_input_field(
            utilities.aaq_question_test_data['valid_firefox_question']['custom_tag']
        )
        sumo_pages.question_page.click_on_add_a_tag_button()

    with allure.step("Deleting user session"):
        utilities.delete_cookies()

    if username == 'TEST_ACCOUNT_13':
        with allure.step("Signing in with a non admin user account"):
            utilities.start_existing_session(utilities.username_extraction_from_email(
                utilities.user_secrets_accounts["TEST_ACCOUNT_13"]
            ))

    with check, allure.step("Verifying that the tag is available for all users"):
        page.reload()
        assert (utilities.aaq_question_test_data['valid_firefox_question']
                ['custom_tag'] in sumo_pages.question_page.get_question_tag_options())

    with allure.step("Verifying that the question tags are acting as filters"):
        for question in sumo_pages.question_page.get_question_tag_options():
            with check, allure.step(f"Clicking on the {question} tag and verifying tha the "
                                    f"filter is applied to the clicked tag"):
                time.sleep(1)
                sumo_pages.question_page.click_on_a_certain_tag(question)
                assert (question == sumo_pages.product_support_forum.
                        _get_text_of_selected_tag_filter_option())

            with check, allure.step("Verifying that each listed question inside the product "
                                    "forum contains the filtered tab"):
                for article_id in sumo_pages.product_support_forum._extract_question_ids(
                ):
                    assert (question in sumo_pages.product_support_forum.
                            _get_all_question_list_tags(article_id))
                utilities.navigate_back()

    with allure.step("Navigate back to the posted question, signing in with an admin account "
                     "and removing the newly added tag"):
        utilities.navigate_to_link(posted_question['question_details']['question_page_url'])
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        page.reload()
        sumo_pages.question_page.click_on_tag_remove_button(
            utilities.aaq_question_test_data['valid_firefox_question']['custom_tag']
        )
        # Adding a custom wait to avoid test flakiness.
        utilities.wait_for_given_timeout(1000)

    with allure.step("Verifying that the tag was removed"):
        expect(sumo_pages.question_page.get_a_certain_tag(
            utilities.aaq_question_test_data['valid_firefox_question']['custom_tag']
        )
        ).to_be_hidden()

    with allure.step("Deleting the user session"):
        utilities.delete_cookies()

    if username == "TEST_ACCOUNT_13":
        with allure.step("Signing in with a non admin user account"):
            utilities.start_existing_session(utilities.username_extraction_from_email(
                utilities.user_secrets_accounts["TEST_ACCOUNT_13"]
            ))

    with allure.step("Verifying that the tag was removed"):
        expect(sumo_pages.question_page.get_a_certain_tag(
            utilities.aaq_question_test_data['valid_firefox_question']['custom_tag']
        )
        ).to_be_hidden()

    with allure.step("Deleting the posted question"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        sumo_pages.aaq_flow.deleting_question_flow()


# T5696750, T5696752
@pytest.mark.postedQuestions
def test_email_updates_option_visibility(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with a non admin user account and posting a Firefox product "
                     "question"):
        post_firefox_product_question_flow(page, 'TEST_ACCOUNT_12')

    with allure.step("Deleting user session and verifying that the 'Get  email updates' "
                     "option is displayed"):
        utilities.delete_cookies()
        expect(sumo_pages.question_page.get_email_updates_option()).to_be_visible()

    with allure.step("Signing in with another non admin user account and verifying that the "
                     "'Get email updates' option is displayed"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))
        expect(sumo_pages.question_page.get_email_updates_option()).to_be_visible()

    with allure.step("Signing in with an admin account and verifying that the 'Get email "
                     "updated' options is displayed"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        expect(sumo_pages.question_page.get_email_updates_option()).to_be_visible()

    with allure.step("Deleting the posted question"):
        sumo_pages.aaq_flow.deleting_question_flow()


# T5696771
@pytest.mark.postedQuestions
def test_mark_reply_as_spam(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with a non admin user account and posting a Firefox product "
                     "question"):
        posted_question = post_firefox_product_question_flow(page, 'TEST_ACCOUNT_12')

    with allure.step("Submitting a reply to the question"):
        reply_id_one = sumo_pages.aaq_flow.post_question_reply_flow(
            repliant_username=posted_question['username_one'],
            reply=utilities.aaq_question_test_data['valid_firefox_question']['question_reply']
        )

    with allure.step("Signin in with a different non admin user and submitting a reply to "
                     "the question"):
        username_two = utilities.start_existing_session(
            utilities.username_extraction_from_email(
                utilities.user_secrets_accounts["TEST_ACCOUNT_13"]
            ))
        reply_id_two = sumo_pages.aaq_flow.post_question_reply_flow(
            repliant_username=username_two,
            reply=utilities.aaq_question_test_data['valid_firefox_question']['question_reply']
        )

    with allure.step("Clicking on the self reply menu and verifying that the 'mark as spam' "
                     "option is not displayed for non-admin users"):
        sumo_pages.question_page.click_on_reply_more_options_button(reply_id_two)
        expect(sumo_pages.question_page.get_mark_as_spam_reply_locator(reply_id_two)
               ).to_be_hidden()
        sumo_pages.question_page.click_on_reply_more_options_button(reply_id_two)

    with allure.step("Clicking on other user posted reply menu and verifying that the 'mark "
                     "as spam' option is not displayed for non-admin users"):
        sumo_pages.question_page.click_on_reply_more_options_button(reply_id_one)
        expect(sumo_pages.question_page.get_mark_as_spam_reply_locator(reply_id_one)
               ).to_be_hidden()
        sumo_pages.question_page.click_on_reply_more_options_button(reply_id_one)

    with check, allure.step("Signing in with an admin account, clicking on the 'Marks as "
                            "Spam' option for one of the replies and verifying that the "
                            "'Marked as spam' message is displayed"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        sumo_pages.aaq_flow.spam_marking_a_reply(reply_id_one)
        assert sumo_pages.question_page.get_marked_as_spam_text(
            reply_id_one) == QuestionPageMessages.REPLY_MARKED_AS_SPAM_MESSAGE

    with allure.step("Deleting user session and verifying that the reply marked as spam is "
                     "no longer displayed"):
        utilities.delete_cookies()
        expect(sumo_pages.question_page.get_reply_section_locator(reply_id_one)).to_be_hidden()

    with allure.step("Signing in with a user account and verifying that reply marked as spam "
                     "is no longer displayed"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_13"]
        ))
        expect(sumo_pages.question_page.get_reply_section_locator(reply_id_one)).to_be_hidden()

    with allure.step("Signing in with the reply OP user account and verifying that the reply "
                     "marked as spam is no longer displayed"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))
        expect(sumo_pages.question_page.get_reply_section_locator(reply_id_one)).to_be_hidden()

    with allure.step("Signing in with the admin account, unmarking the reply from spam and "
                     "verifying that the 'Marked as spam' message is no longer displayed"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        sumo_pages.aaq_flow.spam_marking_a_reply(reply_id_one)
        expect(sumo_pages.question_page.get_marked_as_spam_locator(reply_id_one)).to_be_hidden()

    with allure.step("Deleting the user session and verifying that the reply is visible to "
                     "the logged out users"):
        utilities.delete_cookies()
        expect(sumo_pages.question_page.get_reply_section_locator(reply_id_one)).to_be_visible()

    with allure.step("Verifying that the 'Marked as spam' message is no longer displayed"):
        expect(sumo_pages.question_page.get_marked_as_spam_locator(reply_id_one)).to_be_hidden()

    with allure.step("Signing in with a different user and verifying that the reply is "
                     "visible again"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_13"]
        ))
        expect(sumo_pages.question_page.get_reply_section_locator(reply_id_one)).to_be_visible()

    with allure.step("Verifying that the 'Marked as spam' message is no longer displayed"):
        expect(sumo_pages.question_page.get_marked_as_spam_locator(reply_id_one)).to_be_hidden()

    with allure.step("Signing in with the reply OP and verifying that the reply is visible "
                     "again"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))
        expect(sumo_pages.question_page.get_reply_section_locator(reply_id_one)).to_be_visible()

    with allure.step("Verifying that the 'Marked as spam' message is no longer displayed"):
        expect(sumo_pages.question_page.get_marked_as_spam_locator(reply_id_one)).to_be_hidden()

    with allure.step("Signing in with an admin account and deleting the posted question"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        sumo_pages.aaq_flow.deleting_question_flow()


# Need to expand this to contain additional text format.
# C2191270, C2191259
# T5696785
@pytest.mark.postedQuestions
@pytest.mark.parametrize("username", ['TEST_ACCOUNT_13', 'TEST_ACCOUNT_MODERATOR'])
def test_edit_reply(page: Page, username):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with a non admin user account and posting a Firefox product "
                     "question"):
        posted_question = post_firefox_product_question_flow(page, 'TEST_ACCOUNT_12')

    page_url = utilities.get_page_url()

    with allure.step("Submitting a reply to the question"):
        reply_id = sumo_pages.aaq_flow.post_question_reply_flow(
            repliant_username=posted_question['username_one'],
            reply=utilities.aaq_question_test_data['valid_firefox_question']['question_reply']
        )

    with check, allure.step("Verifying that the reply contains the correct name and user "
                            "status"):
        assert sumo_pages.question_page.get_display_name_of_question_reply_author(
            reply_id) == posted_question['username_one']
        assert sumo_pages.question_page.get_displayed_user_title_of_question_reply(
            reply_id) == QuestionPageMessages.QUESTION_REPLY_OWNER

    if username == 'TEST_ACCOUNT_13':
        with allure.step("Signin in with a different non admin user"):
            username_two = utilities.start_existing_session(
                utilities.username_extraction_from_email(
                    utilities.user_secrets_accounts["TEST_ACCOUNT_13"]
                ))

        with allure.step("Clicking on the more options for the reply posted by another user "
                         "and verifying that the 'edit this post' option is not displayed"):
            sumo_pages.question_page.click_on_reply_more_options_button(reply_id)
            expect(sumo_pages.question_page.get_edit_this_post_reply_locator(reply_id)
                   ).to_be_hidden()

        with check, allure.step("Manually navigating to edit reply endpoint and verifying "
                                "that 403 is returned"):
            with page.expect_navigation() as navigation_info:
                utilities.navigate_to_link(
                    page_url + QuestionPageMessages.EDIT_REPLY_URL + str(
                        utilities.number_extraction_from_string(reply_id))
                )
                response = navigation_info.value
                assert response.status == 403

        with check, allure.step("Navigating back and verifying that the reply contains the "
                                "correct name and no user status"):
            utilities.navigate_to_link(page_url)
            reply_id = sumo_pages.aaq_flow.post_question_reply_flow(
                repliant_username=username_two,
                reply=utilities.aaq_question_test_data['valid_firefox_question']
                ['question_reply']
            )
            assert sumo_pages.question_page.get_display_name_of_question_reply_author(
                reply_id
            ) == username_two
            expect(
                sumo_pages.question_page.get_displayed_user_title_of_question_reply_locator(
                    reply_id
                )
            ).to_be_hidden()
    else:
        username_two = utilities.start_existing_session(
            utilities.username_extraction_from_email(
                utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

    with check, allure.step("Clicking on the 'Edit this post option' and verifying that the "
                            "textarea contains the original reply"):
        sumo_pages.question_page.click_on_reply_more_options_button(reply_id)
        sumo_pages.question_page.click_on_edit_this_post_for_a_certain_reply(reply_id)
        assert sumo_pages.question_page.get_post_a_reply_textarea_text().strip(
        ) in utilities.aaq_question_test_data['valid_firefox_question']['question_reply']

    with allure.step("Editing the question reply"):
        sumo_pages.aaq_flow.editing_reply_flow(
            reply_body=utilities.aaq_question_test_data['valid_firefox_question']
            ['updated_reply'],
            submit_reply=False
        )

    with check, allure.step("Verifying that the question reply is the original one"):
        assert sumo_pages.question_page.get_posted_reply_text(reply_id).strip(
        ) == utilities.aaq_question_test_data['valid_firefox_question']['question_reply']

    with allure.step("Verifying that the 'Modified by' message is not displayed for the "
                     "reply"):
        expect(sumo_pages.question_page.get_posted_reply_modified_by_locator(reply_id)
               ).to_be_hidden()

    with check, allure.step("Clicking on the 'Edit this post option' and verifying that the "
                            "textarea contains the original reply"):
        sumo_pages.question_page.click_on_reply_more_options_button(reply_id)
        sumo_pages.question_page.click_on_edit_this_post_for_a_certain_reply(reply_id)
        assert sumo_pages.question_page.get_post_a_reply_textarea_text(
        ) in utilities.aaq_question_test_data['valid_firefox_question']['question_reply']

    with check, allure.step("Editing the reply and verifying that the reply contains the "
                            "updated text"):
        sumo_pages.aaq_flow.editing_reply_flow(
            reply_body=utilities.aaq_question_test_data['valid_firefox_question']
            ['updated_reply']
        )
        assert sumo_pages.question_page.get_posted_reply_text(reply_id).strip(
        ) == utilities.aaq_question_test_data['valid_firefox_question']['updated_reply']

    with check, allure.step("Verifying that the 'Modified by' message is displayed for the "
                            "reply"):
        assert username_two in sumo_pages.question_page.get_posted_reply_modified_by_text(
            reply_id)

    with allure.step("Deleting the posted question"):
        if username == 'TEST_ACCOUNT_13':
            utilities.start_existing_session(utilities.username_extraction_from_email(
                utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))
        sumo_pages.aaq_flow.deleting_question_flow()


# T5696786
@pytest.mark.postedQuestions
@pytest.mark.parametrize("username", ['TEST_ACCOUNT_13', 'TEST_ACCOUNT_MODERATOR'])
def test_delete_reply(page: Page, username):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with a non admin user account and posting a Firefox product "
                     "question"):
        posted_question = post_firefox_product_question_flow(page, 'TEST_ACCOUNT_12')

    page_url = utilities.get_page_url()

    with allure.step("Posting a reply to the question and verifying that the 'Delete this "
                     "post' option is not available for self posted reply"):
        reply_id = sumo_pages.aaq_flow.post_question_reply_flow(
            repliant_username=posted_question['username_one'],
            reply=utilities.aaq_question_test_data['valid_firefox_question']['question_reply']
        )
        expect(sumo_pages.question_page.get_delete_this_post_reply_locator(reply_id)
               ).to_be_hidden()

    with check, allure.step("Verifying that manually navigating to the delete page for the "
                            "posted reply returns 403"):
        with page.expect_navigation() as navigation_info:
            utilities.navigate_to_link(
                page_url + QuestionPageMessages.DELETE_QUESTION_REPLY_URL + str(
                    utilities.number_extraction_from_string(reply_id))
            )
            response = navigation_info.value
            assert response.status == 403

    with allure.step("Navigating back to the question and posting a reply to it"):
        utilities.navigate_to_link(posted_question['question_details']['question_page_url'])

        if username == 'TEST_ACCOUNT_13':
            username_two = utilities.start_existing_session(
                utilities.username_extraction_from_email(
                    utilities.user_secrets_accounts["TEST_ACCOUNT_13"]
                ))
            sumo_pages.aaq_flow.post_question_reply_flow(
                repliant_username=username_two,
                reply=utilities.aaq_question_test_data['valid_firefox_question']
                ['question_reply']
            )

            with allure.step("Verifying that the 'Delete this post' option is not available "
                             "for replies posted by others"):
                sumo_pages.question_page.click_on_reply_more_options_button(reply_id)
                expect(sumo_pages.question_page.get_delete_this_post_reply_locator(reply_id)
                       ).to_be_hidden()

            with check, allure.step("Verifying that manually navigating to the delete page "
                                    "for the posted reply returns 403"):
                with page.expect_navigation() as navigation_info:
                    utilities.navigate_to_link(
                        page_url + QuestionPageMessages.DELETE_QUESTION_REPLY_URL + str(
                            utilities.number_extraction_from_string(reply_id))
                    )
                    response = navigation_info.value
                    assert response.status == 403

            utilities.navigate_to_link(posted_question['question_details']['question_page_url'])

    with allure.step("Signing in with an admin account and, clicking on the 'Cancel' delete "
                     "reply confirmation box and verifying that the reply was not deleted"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        sumo_pages.aaq_flow.delete_question_reply(reply_id, delete_reply=False)
        expect(sumo_pages.question_page.get_posted_reply_locator(reply_id)).to_be_visible()

    with allure.step("Deleting the reply and verifying that the reply is no longer displayed"):
        sumo_pages.aaq_flow.delete_question_reply(reply_id, delete_reply=True)
        expect(sumo_pages.question_page.get_posted_reply_locator(reply_id)).to_be_hidden()

    with allure.step("Deleting the posted question"):
        sumo_pages.aaq_flow.deleting_question_flow()


# T5696788, T5696767
# Need to re-verify this for signed out case before submitting this
@pytest.mark.postedQuestions
def test_i_have_this_problem_too(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with a non admin user account and posting a Firefox product "
                     "question"):
        post_firefox_product_question_flow(page, 'TEST_ACCOUNT_12')

    with allure.step("Verifying that the 'I have this problem too' button is not displayed "
                     "for self posted questions"):
        problem_counter = sumo_pages.question_page.get_i_have_this_problem_too_counter()
        expect(sumo_pages.question_page.get_i_have_this_problem_too_locator()).to_be_hidden()

    with check, allure.step("Deleting the user session, clicking on the 'I have this problem "
                            "too' button and verifying tha the 'have this problem' counter "
                            "was successfully incremented"):
        utilities.delete_cookies()
        problem_counter += 1
        sumo_pages.question_page.click_i_have_this_problem_too_button()
        page.reload()
        assert problem_counter == sumo_pages.question_page.get_i_have_this_problem_too_counter()

    with check, allure.step("Signing in with a different non-admin user account, clicking on "
                            "the 'I have this problem too' and verifying that the 'have this "
                            "problem' counter has incremented"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_13"]
        ))
        sumo_pages.question_page.click_i_have_this_problem_too_button()
        page.reload()
        problem_counter += 1
        assert problem_counter == sumo_pages.question_page.get_i_have_this_problem_too_counter()

    with allure.step("Verifying that the 'I have this problem too' button is no longer "
                     "displayed"):
        expect(sumo_pages.question_page.get_i_have_this_problem_too_locator()).to_be_hidden()

    with check, allure.step("Signing in with an admin account, clicking on the 'I have this "
                            "problem too' and verifying that the 'have this problem' counter "
                            "incremented successfully"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        problem_counter += 1
        sumo_pages.question_page.click_i_have_this_problem_too_button()
        page.reload()
        assert problem_counter == sumo_pages.question_page.get_i_have_this_problem_too_counter()

    with allure.step("Verifying that the 'I have this problem too' button is no longer "
                     "displayed"):
        expect(sumo_pages.question_page.get_i_have_this_problem_too_locator()).to_be_hidden()

    with allure.step("Deleting the posted question"):
        sumo_pages.aaq_flow.deleting_question_flow()


# T5696789
@pytest.mark.postedQuestions
def test_solves_this_problem(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with a non admin user account and posting a Firefox product "
                     "question"):
        posted_question = post_firefox_product_question_flow(page, 'TEST_ACCOUNT_12')

    with allure.step("Posting a reply to the question"):
        reply_id = sumo_pages.aaq_flow.post_question_reply_flow(
            repliant_username=posted_question['username_one'],
            reply=utilities.aaq_question_test_data['valid_firefox_question']['question_reply']
        )

    with allure.step("Deleting user session and verifying that the 'Solved the problem' "
                     "button is not displayed"):
        utilities.delete_cookies()
        expect(sumo_pages.question_page.get_solved_the_problem_button_locator(reply_id)
               ).to_be_hidden()

    with allure.step("Signing in with a different user account and verifying that the "
                     "'Solved the problem' button is not displayed"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_13"]
        ))
        expect(sumo_pages.question_page.get_solved_the_problem_button_locator(reply_id)
               ).to_be_hidden()

    with check, allure.step("Signing in with the first username, clicking on the 'Solved the "
                            "problem' button and verifying that the correct banner is "
                            "displayed"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))
        sumo_pages.question_page.click_on_solves_the_problem_button(reply_id)
        assert sumo_pages.question_page.get_solved_problem_banner_text(
        ) == QuestionPageMessages.CHOSEN_SOLUTION_BANNER

    with check, allure.step("Verifying that the 'Chosen solution is displayed for the reply'"):
        assert sumo_pages.question_page.get_chosen_solution_reply_message(
            reply_id) == QuestionPageMessages.CHOSEN_SOLUTION_REPLY_CARD

    with check, allure.step("Verifying that the chosen solution reply section has the "
                            "correct header"):
        assert sumo_pages.question_page.get_problem_solved_section_header_text(
        ) == QuestionPageMessages.CHOSEN_SOLUTION_CARD

    with check, allure.step("Verifying the chosen solution text"):
        assert sumo_pages.question_page.get_chosen_solution_text(
        ) == utilities.aaq_question_test_data['valid_firefox_question']['question_reply']

    with allure.step("Clicking on the 'Read this answer in context' link and verifying that "
                     "the page url updates to point out to the posted reply"):
        sumo_pages.question_page.click_read_this_answer_in_context_link()
        expect(page).to_have_url(
            posted_question['question_details']['question_page_url'] + "#" + reply_id
        )

    with check, allure.step("Navigating back, clicking on the undo button and verifying that "
                            "the correct banner is displayed"):
        utilities.navigate_back()
        sumo_pages.question_page.click_on_undo_button()
        assert sumo_pages.question_page.get_solved_problem_banner_text(
        ) == QuestionPageMessages.UNDOING_A_SOLUTION

    with allure.step("Verifying that the 'Solved the problem' option is not displayed"):
        expect(sumo_pages.question_page.get_chosen_solution_section_locator()).to_be_hidden()

    with allure.step("Verifying that the 'Chosen solution' banner is not displayed for the "
                     "previously provided solution"):
        expect(sumo_pages.question_page.get_chosen_solution_reply_message_locator(reply_id)
               ).to_be_hidden()

    with allure.step("Verifying that the 'Undo' option is not available"):
        expect(sumo_pages.question_page.get_undo_button_locator()).to_be_hidden()

    with check, allure.step("Signing in with an admin account, clicking on the 'solved this "
                            "problem option' and verifying the chosen solution text"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        sumo_pages.question_page.click_on_solves_the_problem_button(reply_id)
        assert sumo_pages.question_page.get_chosen_solution_text(
        ) == utilities.aaq_question_test_data['valid_firefox_question']['question_reply']

    with allure.step("Deleting the posted question"):
        sumo_pages.aaq_flow.deleting_question_flow()


# Need to add test for preview as well.
# T5696791, T5696772, T5696774, T5696776, T5696792
@pytest.mark.postedQuestions
@pytest.mark.parametrize("quote_on", ['reply', 'question'])
def test_quote_reply_functionality(page: Page, quote_on):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    # Using a user which doesn't have any special permissions applied & which doesn't belong to
    # any group in order to catch cases like https://github.com/mozilla/sumo/issues/1676
    with allure.step("Signing in with a non admin user account and posting a Firefox product "
                     "question"):
        posted_question = post_firefox_product_question_flow(page,
                                                             "TEST_ACCOUNT_MESSAGE_3")
    question_id = sumo_pages.question_page.get_question_id()

    if quote_on == "reply":
        with allure.step("Posting a reply to the question"):
            reply_id = sumo_pages.aaq_flow.post_question_reply_flow(
                repliant_username=posted_question['username_one'],
                reply=utilities.aaq_question_test_data['valid_firefox_question']
                ['question_reply']
            )
    with allure.step("Signing in with a different non-admin user"):
        username_two = utilities.start_existing_session(
            utilities.username_extraction_from_email(
                utilities.user_secrets_accounts["TEST_ACCOUNT_13"]
            ))

    if quote_on == "reply":
        with allure.step("Posting a quoted reply for question reply"):
            quote_id = sumo_pages.aaq_flow.post_question_reply_flow(
                repliant_username=username_two,
                reply=utilities.aaq_question_test_data['valid_firefox_question']
                ['updated_reply'],
                quoted_reply=True,
                reply_for_id=reply_id
            )
    else:
        with allure.step("Posting a quoted reply for question"):
            quote_id = sumo_pages.aaq_flow.post_question_reply_flow(
                repliant_username=username_two,
                reply=utilities.aaq_question_test_data['valid_firefox_question']
                ['updated_reply'],
                quoted_reply=True,
                reply_for_id=question_id
            )

    with check, allure.step("Verifying that the original repliant is displayed inside the "
                            "quote"):
        assert (posted_question['username_one'] in sumo_pages.question_page
                .get_posted_quote_reply_username_text(quote_id))

    if quote_on == "reply":
        with check, allure.step("Verifying that the original reply is displayed inside the "
                                "quote"):
            assert (utilities.aaq_question_test_data['valid_firefox_question']
                    ['question_reply'] == sumo_pages.question_page
                    .get_blockquote_reply_text(quote_id).strip())
    else:
        with check, allure.step("Verifying that the question details is displayed inside the "
                                "quote"):
            assert (utilities.aaq_question_test_data['valid_firefox_question']
                    ['simple_body_text'] == sumo_pages.question_page
                    .get_blockquote_reply_text(quote_id).strip())

    with check, allure.step("Verifying that the new reply text is also displayed"):
        assert (utilities
                .aaq_question_test_data['valid_firefox_question']['updated_reply'] in sumo_pages.
                question_page.get_posted_reply_text(quote_id).strip())

    with allure.step("Clicking on the 'said' link"):
        sumo_pages.question_page.click_posted_reply_said_link(quote_id)

    if quote_on == "reply":
        with check, allure.step("Verifying that the correct url is displayed"):
            expect(page).to_have_url(
                posted_question['question_details']['question_page_url'] + "#" + reply_id
            )
    else:
        with check, allure.step("Verifying that the correct url is displayed"):
            expect(page).to_have_url(
                posted_question['question_details']['question_page_url'] + "#" + question_id
            )

    with allure.step("Signing in with an admin account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

    if quote_on == "reply":
        with allure.step("Posting a quoted reply for question reply"):
            quote_id = sumo_pages.aaq_flow.post_question_reply_flow(
                repliant_username=username_two,
                reply=utilities.aaq_question_test_data['valid_firefox_question']
                ['updated_reply'],
                quoted_reply=True,
                reply_for_id=reply_id
            )
    else:
        with allure.step("Posting a quoted reply for question reply"):
            quote_id = sumo_pages.aaq_flow.post_question_reply_flow(
                repliant_username=username_two,
                reply=utilities.aaq_question_test_data['valid_firefox_question']
                ['updated_reply'],
                quoted_reply=True,
                reply_for_id=question_id
            )

    with check, allure.step("Verifying that the original repliant is displayed inside the "
                            "quote"):
        assert (posted_question['username_one'] in sumo_pages.question_page
                .get_posted_quote_reply_username_text(quote_id))

    if quote_on == "reply":
        with check, allure.step("Verifying that the original reply is displayed inside the "
                                "quote"):
            assert (utilities.aaq_question_test_data['valid_firefox_question']
                    ['question_reply'] == sumo_pages.question_page
                    .get_blockquote_reply_text(quote_id).strip())
    else:
        with check, allure.step("Verifying that the question is displayed inside the quote"):
            assert (utilities.aaq_question_test_data['valid_firefox_question']
                    ['simple_body_text'] == sumo_pages.question_page
                    .get_blockquote_reply_text(quote_id).strip())

    with check, allure.step("Verifying that the new reply text is also displayed"):
        assert (utilities.aaq_question_test_data['valid_firefox_question']
                ['updated_reply'] == sumo_pages.question_page
                .get_posted_reply_text(quote_id).strip())

    with allure.step("Clicking on the 'said' link"):
        sumo_pages.question_page.click_posted_reply_said_link(quote_id)

    if quote_on == "reply":
        with allure.step("Verifying that the correct url is displayed"):
            expect(page).to_have_url(
                posted_question['question_details']['question_page_url'] + "#" + reply_id
            )
    else:
        with allure.step("Verifying that the correct url is displayed"):
            expect(page).to_have_url(
                posted_question['question_details']['question_page_url'] + "#" + question_id
            )

    with allure.step("Deleting the posted question"):
        sumo_pages.aaq_flow.deleting_question_flow()


# To add tests for "I have this problem, too" option
# T5696766, T5696765, T5696769
@pytest.mark.postedQuestions
def test_quote_reply_functionality_signed_out(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with a non admin user account and posting a Firefox product "
                     "question"):
        posted_question = post_firefox_product_question_flow(page, 'TEST_ACCOUNT_12')
    question_id = sumo_pages.question_page.get_question_id()

    with allure.step("Deleting user session, clicking on the 'Quote' option for the question "
                     "and verifying that the url has updated to contain the correct fragment"
                     " identifier"):
        utilities.delete_cookies()
        sumo_pages.question_page.click_on_reply_more_options_button(question_id)
        sumo_pages.question_page.click_on_quote_for_a_certain_reply(question_id)
        expect(page).to_have_url(
            posted_question['question_details']['question_page_url'] + "#question-reply")

    with allure.step("Verifying that the reply textarea field is not displayed"):
        expect(sumo_pages.question_page.get_post_a_reply_textarea_locator()).to_be_hidden()

    with allure.step("Verifying that the 'Ask a question' signed out card is not displayed"):
        expect(sumo_pages.question_page.ask_a_question_signed_out_card_option_locator()
               ).to_be_hidden()

    with allure.step("Verifying that the 'I have this problem, too' option is not displayed"):
        expect(sumo_pages.question_page.get_i_have_this_problem_too_signed_out_card_locator()
               ).to_be_hidden()

    with allure.step("Clicking on the 'start a new question' signed out card link and "
                     "verifying that we are redirected to the Contact Support page"):
        sumo_pages.question_page.click_on_start_a_new_question_signed_out_card_link()
        expect(page).to_have_url(ContactSupportMessages.PAGE_URL)

    with allure.step("Navigating back to the question page,signing in back with the op and "
                     "leaving a question reply"):
        utilities.navigate_back()
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts['TEST_ACCOUNT_12']
        ))
        reply_id = sumo_pages.aaq_flow.post_question_reply_flow(
            repliant_username=posted_question['username_one'],
            reply=utilities.aaq_question_test_data['valid_firefox_question']['question_reply']
        )

    with allure.step("Deleting user session, clicking on the quote option fro the reply and "
                     "verifying that the url has updated to contain the correct fragment "
                     "identifier"):
        utilities.delete_cookies()
        sumo_pages.question_page.click_on_reply_more_options_button(reply_id)
        sumo_pages.question_page.click_on_quote_for_a_certain_reply(reply_id)
        expect(page).to_have_url(
            posted_question['question_details']['question_page_url'] + "#question-reply"
        )

    with allure.step("Verifying that the reply textarea field is not displayed"):
        expect(sumo_pages.question_page.get_post_a_reply_textarea_locator()).to_be_hidden()

    with allure.step("Verifying that the 'Ask a question' signed out card is displayed"):
        expect(sumo_pages.question_page.ask_a_question_signed_out_card_option_locator()
               ).to_be_visible()

    with allure.step("Verifying that the 'I have this problem, too' option is displayed"):
        expect(sumo_pages.question_page.get_i_have_this_problem_too_signed_out_card_locator()
               ).to_be_visible()

    with allure.step("Clicking on the 'Ask a question' and verifying that we are redirected "
                     "to the contact support page"):
        sumo_pages.question_page.click_on_ask_a_question_signed_out_card_option()
        expect(page).to_have_url(ContactSupportMessages.PAGE_URL)

    with allure.step("Navigating back to the question page, clicking on the 'log in to your "
                     "account' link and proceeding with the auth flow with an admin account"):
        utilities.navigate_back()
        sumo_pages.question_page.click_on_log_in_to_your_account_signed_out_card_link()
        sumo_pages.auth_flow_page.sign_in_flow(
            username=utilities.user_special_chars,
            account_password=utilities.user_secrets_pass,
        )

    with allure.step("Verifying that we are redirected back to the question page"):
        expect(page).to_have_url(posted_question['question_details']['question_page_url'])

    with allure.step("Verifying that the textarea field is displayed"):
        expect(sumo_pages.question_page.get_post_a_reply_textarea_locator()).to_be_visible()

    with allure.step("Signing in with an admin account and deleting the posted question"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts['TEST_ACCOUNT_MODERATOR']
        ))
        sumo_pages.aaq_flow.deleting_question_flow()


# T5696770
# Currently fails due to https://github.com/mozilla/sumo/issues/1216
@pytest.mark.skip
def test_question_reply_votes(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    number_of_thumbs_up_votes = 0
    number_of_thumbs_down_votes = 0

    with allure.step("Signing in with a non admin user account and posting a Firefox product "
                     "question"):
        posted_question = post_firefox_product_question_flow(page, 'TEST_ACCOUNT_12')
    sumo_pages.question_page.get_question_id()

    with allure.step("Posting a reply to the question"):
        sumo_pages.question_page.add_text_to_post_a_reply_textarea(
            utilities.aaq_question_test_data['valid_firefox_question']['question_reply']
        )
        reply_id = sumo_pages.question_page.click_on_post_reply_button(
            posted_question['username_one']
        )

    with allure.step("Verifying the vote reply is not available for self posted questions"):
        expect(sumo_pages.question_page.get_reply_votes_section_locator(reply_id)).to_be_hidden()

    with check, allure.step("Signing in a different user and verifying that the correct vote "
                            "header is displayed"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts['TEST_ACCOUNT_13']
        ))
        assert sumo_pages.question_page.get_reply_vote_heading(
            reply_id) == QuestionPageMessages.HELPFUL_VOTE_HEADER

    with allure.step("Clicking on the 'thumbs up' button and verifying that the correct "
                     "message is displayed"):
        sumo_pages.question_page.click_reply_vote_thumbs_up_button(reply_id)
        number_of_thumbs_up_votes += 1
        assert sumo_pages.question_page.get_thumbs_up_vote_message(
            reply_id) == QuestionPageMessages.THUMBS_UP_VOTE_MESSAGE

    with check, allure.step("Refreshing the page and verifying that the correct number of "
                            "thumbs up votes is displayed"):
        utilities.refresh_page()
        assert int(sumo_pages.question_page.get_helpful_count(reply_id
                                                              )) == number_of_thumbs_up_votes

    with check, allure.step("Verifying that the correct number of thumbs down votes is "
                            "displayed"):
        assert int(sumo_pages.question_page.get_not_helpful_count(reply_id)
                   ) == number_of_thumbs_down_votes

    with allure.step("Verifying that the thumbs up button contains the disabled attribute"):
        expect(sumo_pages.question_page.get_thumbs_up_button_locator(reply_id)
               ).to_have_attribute("disabled", "")

    with allure.step("Verifying that the thumbs down button contains the disabled attribute"):
        expect(sumo_pages.question_page.get_thumbs_down_button_locator(reply_id)
               ).to_have_attribute("disabled", "")

    with check, allure.step("Refreshing the page and verifying that the correct number of "
                            "thumbs up votes is displayed"):
        utilities.refresh_page()
        assert int(sumo_pages.question_page.get_helpful_count(reply_id)
                   ) == number_of_thumbs_up_votes

    with check, allure.step("Verifying that the correct number of thumbs down votes is "
                            "displayed"):
        assert int(sumo_pages.question_page.get_not_helpful_count(reply_id)
                   ) == number_of_thumbs_down_votes

    with allure.step("Deleting the user session and clicking on the 'thumbs up' button"):
        utilities.delete_cookies()
        sumo_pages.question_page.click_reply_vote_thumbs_up_button(reply_id)
        number_of_thumbs_up_votes += 1

    with check, allure.step("Refreshing the page and verifying that the correct number of "
                            "thumbs up votes is displayed"):
        utilities.refresh_page()
        assert int(sumo_pages.question_page.get_helpful_count(reply_id)
                   ) == number_of_thumbs_up_votes

    with check, allure.step("Verifying that the correct number of thumbs down votes is "
                            "displayed"):
        assert int(sumo_pages.question_page.get_not_helpful_count(reply_id)
                   ) == number_of_thumbs_down_votes

    with allure.step("Verifying that the thumbs up button contains the disabled attribute"):
        expect(sumo_pages.question_page.get_thumbs_up_button_locator(reply_id)
               ).to_have_attribute("disabled", "")

    with allure.step("Verifying that the thumbs down button contains the disabled attribute"):
        expect(sumo_pages.question_page.get_thumbs_down_button_locator(reply_id)
               ).to_have_attribute("disabled", "")

    with check, allure.step("Refreshing the page and verifying that the correct number of "
                            "thumbs up votes is displayed"):
        utilities.refresh_page()
        assert int(sumo_pages.question_page.get_helpful_count(reply_id
                                                              )) == number_of_thumbs_up_votes

    check.equal(
        int(sumo_pages.question_page.get_not_helpful_count(reply_id)), number_of_thumbs_down_votes
    )

    with allure.step("Signing in with an admin account and clicking on the vote down button"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts['TEST_ACCOUNT_MODERATOR']
        ))
        sumo_pages.question_page.click_reply_vote_thumbs_down_button(reply_id)
        number_of_thumbs_down_votes += 1

    with check, allure.step("Verifying that the correct message is displayed"):
        assert sumo_pages.question_page.get_thumbs_up_vote_message(
            reply_id) == QuestionPageMessages.THUMBS_DOWN_VOTE_MESSAGE

    with check, allure.step("Refreshing the page and verifying that the correct number of "
                            "thumbs up votes is displayed"):
        utilities.refresh_page()
        assert int(sumo_pages.question_page.get_helpful_count(reply_id
                                                              )) == number_of_thumbs_up_votes

    with check, allure.step("Verifying that the correct number of thumbs down votes is "
                            "displayed"):
        assert int(sumo_pages.question_page.get_not_helpful_count(reply_id)
                   ) == number_of_thumbs_down_votes

    with allure.step("Deleting the posted question"):
        sumo_pages.aaq_flow.deleting_question_flow()


# C2260449, C2260450, C2191243, C2191245
# T5696793, T5696773, T5696775
@pytest.mark.postedQuestions
@pytest.mark.parametrize("flagged_content, username",
                         [('question_content', 'TEST_ACCOUNT_13'),
                          ('question_content', 'TEST_ACCOUNT_MODERATOR'),
                          ('question_reply', 'TEST_ACCOUNT_13'),
                          ('question_reply', 'TEST_ACCOUNT_MODERATOR')])
def test_report_abuse(page: Page, flagged_content, username):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with a non admin user account and posting a Firefox product "
                     "question"):
        posted_question = post_firefox_product_question_flow(page, 'TEST_ACCOUNT_12')

    if flagged_content == "question_reply":
        with allure.step("Posting a reply to the question"):
            reply_id = sumo_pages.aaq_flow.post_question_reply_flow(
                repliant_username=posted_question['username_one'],
                reply=utilities.aaq_question_test_data['valid_firefox_question']
                ['question_reply']
            )

    with allure.step("Deleting user session"):
        utilities.delete_cookies()

    if flagged_content == "question_content":
        with allure.step("Clicking on the more options for the question and verifying that "
                         "the report abuse option is not displayed for signed out users"):
            sumo_pages.question_page.click_on_reply_more_options_button(
                sumo_pages.question_page.get_question_id()
            )
            expect(
                sumo_pages.question_page.get_click_on_report_abuse_reply_locator(
                    sumo_pages.question_page.get_question_id()
                )
            ).to_be_hidden()

    else:
        with allure.step("Clicking on the more options for the reply and verifying that the "
                         "report abuse options is not displayed for signed out users"):
            sumo_pages.question_page.click_on_reply_more_options_button(reply_id)
            expect(sumo_pages.question_page.get_click_on_report_abuse_reply_locator(
                reply_id)).to_be_hidden()

    if username == "TEST_ACCOUNT_MODERATOR":
        with allure.step("Signing in with an admin account"):
            utilities.start_existing_session(utilities.username_extraction_from_email(
                utilities.user_secrets_accounts['TEST_ACCOUNT_MODERATOR']
            ))
    else:
        with allure.step("Signing in with an admin account"):
            utilities.start_existing_session(utilities.username_extraction_from_email(
                utilities.user_secrets_accounts['TEST_ACCOUNT_13']
            ))

    if flagged_content == "question_content":
        with allure.step("Reporting the question as abusive"):
            sumo_pages.aaq_flow.report_question_abuse(
                answer_id=sumo_pages.question_page.get_question_id(),
                text=utilities.aaq_question_test_data['valid_firefox_question']
                ['report_abuse_text']
            )
    else:
        with allure.step("Reporting the question reply as abusive"):
            sumo_pages.aaq_flow.report_question_abuse(
                answer_id=reply_id,
                text=utilities.aaq_question_test_data['valid_firefox_question']
                ['report_abuse_text']
            )

    if username == "TEST_ACCOUNT_13":
        with allure.step("Signing in with a admin account"):
            utilities.start_existing_session(utilities.username_extraction_from_email(
                utilities.user_secrets_accounts['TEST_ACCOUNT_MODERATOR']
            ))

    with allure.step("Navigating to 'Moderate forum content page' and verifying that the "
                     "question exists inside the moderate forum content page"):
        sumo_pages.top_navbar.click_on_moderate_forum_content_option()
        expect(
            sumo_pages.moderate_forum_content_page._get_flagged_question_locator(
                posted_question['question_details']['aaq_subject']
            )
        ).to_be_visible()

    with allure.step("Selecting an option from the update status and clicking on the update "
                     "button"):
        sumo_pages.moderate_forum_content_page._select_update_status_option(
            posted_question['question_details']['aaq_subject'],
            ModerateForumContentPageMessages.UPDATE_STATUS_FIRST_VALUE
        )
        sumo_pages.moderate_forum_content_page._click_on_the_update_button(
            posted_question['question_details']['aaq_subject']
        )

    with allure.step("Verifying that the question no longer exists inside the moderate forum "
                     "content page"):
        expect(
            sumo_pages.moderate_forum_content_page._get_flagged_question_locator(
                posted_question['question_details']['aaq_subject']
            )
        ).to_be_hidden()

    with allure.step("Navigating back to the posted question and deleting it"):
        utilities.navigate_to_link(posted_question['question_details']['question_page_url'])
        sumo_pages.aaq_flow.deleting_question_flow()


# T5696777
@pytest.mark.postedQuestions
def test_common_responses(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with a non admin user account and posting a Firefox product "
                     "question"):
        post_firefox_product_question_flow(page, 'TEST_ACCOUNT_12')

    with allure.step("Signing in with a different account, clicking on the 'Common "
                     "Responses' option and selecting one from the list"):
        username = utilities.start_existing_session(
            utilities.username_extraction_from_email(
                utilities.user_secrets_accounts['TEST_ACCOUNT_13']
            ))
        sumo_pages.question_page.click_on_common_responses_option()
        sumo_pages.question_page.click_on_a_particular_category_option(
            utilities.aaq_question_test_data["valid_firefox_question"]["common_responses_category"]
        )
        sumo_pages.question_page.type_into_common_responses_search_field(
            utilities.aaq_question_test_data["valid_firefox_question"]["common_responses_response"]
        )
        utilities.wait_for_given_timeout(3000)

    with allure.step("Verifying that the only item in the category field is the searched "
                     "option"):
        response_options = sumo_pages.question_page.get_list_of_responses()
        assert (
            len(response_options) == 1 and response_options[0] == utilities.
            aaq_question_test_data["valid_firefox_question"]["common_responses_response"]
        )

    with allure.step("Clicking on the response option and on the 'Cancel' panel button"):
        sumo_pages.question_page.click_on_a_particular_response_option(
            utilities.aaq_question_test_data["valid_firefox_question"]
            ["common_responses_response"]
        )
        sumo_pages.question_page.click_on_common_responses_cancel_button()

    with check, allure.step("Verifying that the form textarea does not contain the common "
                            "response"):
        assert sumo_pages.question_page.get_post_a_reply_textarea_value() == ""

    with allure.step("Clicking on the 'Common Responses' option and selecting a response "
                     "from the list"):
        sumo_pages.question_page.click_on_common_responses_option()
        sumo_pages.question_page.click_on_a_particular_category_option(
            utilities.aaq_question_test_data["valid_firefox_question"]["common_responses_category"]
        )
        sumo_pages.question_page.type_into_common_responses_search_field(
            utilities.aaq_question_test_data["valid_firefox_question"]["common_responses_response"]
        )
        utilities.wait_for_given_timeout(3000)

    with allure.step("Verifying that the only item in the category field is the searched "
                     "option"):
        response_options = sumo_pages.question_page.get_list_of_responses()
        assert (
            len(response_options) == 1 and response_options[0] == utilities
            .aaq_question_test_data["valid_firefox_question"]["common_responses_response"]
        )

    with allure.step("Clicking on the response option"):
        sumo_pages.question_page.click_on_a_particular_response_option(
            utilities.aaq_question_test_data["valid_firefox_question"]["common_responses_response"]
        )
        sumo_pages.question_page.click_on_switch_to_mode()
        response = sumo_pages.question_page.get_text_of_response_preview()

    with check, allure.step("Clicking on the Insert Response, post reply and verifying that "
                            "the reply was successfully posted and contains the correct data"):
        sumo_pages.question_page.click_on_common_responses_insert_response_button()
        try:
            reply_id = sumo_pages.question_page.click_on_post_reply_button(username)
        except TimeoutError:
            reply_id = sumo_pages.question_page.click_on_post_reply_button(username)
        assert sumo_pages.question_page.get_text_content_of_reply(
            reply_id).strip() in response.strip()

    with allure.step("Signing in  with an admin account and deleting the posted question"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        sumo_pages.aaq_flow.deleting_question_flow()


def post_firefox_product_question_flow(page: Page, username: str):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    username_one = utilities.start_existing_session(
        utilities.username_extraction_from_email(
            utilities.user_secrets_accounts[username]
        ))

    with allure.step("Posting a Firefox product question"):
        utilities.navigate_to_link(utilities.aaq_question_test_data["products_aaq_url"]["Firefox"])

        question_details = sumo_pages.aaq_flow.submit_an_aaq_question(
            subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=sumo_pages.aaq_form_page.get_aaq_form_topic_options()[0],
            body=utilities.aaq_question_test_data["valid_firefox_question"]
            ["simple_body_text"],
            attach_image=False
        )

        return {"username_one": username_one, "question_details": question_details}
