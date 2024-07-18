import allure
import pytest
from playwright.sync_api import expect, Page
from pytest_check import check
from playwright_tests.core.testutilities import TestUtilities
from playwright_tests.messages.explore_help_articles.kb_article_page_messages import (
    KBArticlePageMessages)
from playwright_tests.pages.sumo_pages import SumoPages

with open('test_data/test_article', 'r') as file:
    article_url = file.read()


# C2188031
@pytest.mark.articleThreads
def test_article_thread_field_validation(page: Page):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with an admin account"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        test_utilities.navigate_to_link(article_url)
        sumo_pages.kb_article_page._click_on_editing_tools_discussion_option()

    with allure.step("Clicking on the 'Post a new thread button' and clicking on the 'Post "
                     "Thread' button without adding any data in the form fields"):
        sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()
        sumo_pages.kb_article_discussion_page._click_on_submit_new_thread_button()

    with allure.step("Verifying that we are on the same page"):
        expect(page).to_have_url(
            article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_NEW_ENDPOINT)

    with allure.step("Adding one character inside the 'Title' field, clicking the 'Post "
                     "Thread' button and verifying that we are on the same page"):
        sumo_pages.kb_article_discussion_page._add_text_to_new_thread_title_field("t")
        sumo_pages.kb_article_discussion_page._click_on_submit_new_thread_button()

        expect(page).to_have_url(
            article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_NEW_ENDPOINT)

    with allure.step("Clearing the input field and adding 5 characters inside the title "
                     "input field"):
        sumo_pages.kb_article_discussion_page._clear_new_thread_title_field()
        sumo_pages.kb_article_discussion_page._add_text_to_new_thread_title_field(
            test_utilities.kb_new_thread_test_data['new_thread_reduced_title']
        )

    with allure.step("Clicking on the 'Post Thread' button and verifying that we are on the "
                     "same page"):
        sumo_pages.kb_article_discussion_page._click_on_submit_new_thread_button()
        expect(page).to_have_url(
            article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_NEW_ENDPOINT)

    with allure.step("Adding one character inside the content field, clicking on the 'Post "
                     "Thread' button and verifying that we are on the same page"):
        sumo_pages.kb_article_discussion_page._add_text_to_new_thread_body_input_field("a")
        sumo_pages.kb_article_discussion_page._click_on_submit_new_thread_button()
        expect(page).to_have_url(
            article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_NEW_ENDPOINT)

    with allure.step("Clearing both title and content fields and adding 5 characters inside "
                     "the thread content field"):
        sumo_pages.kb_article_discussion_page._clear_new_thread_body_field()
        sumo_pages.kb_article_discussion_page._clear_new_thread_title_field()
        sumo_pages.kb_article_discussion_page._clear_new_thread_body_field()
        sumo_pages.kb_article_discussion_page._add_text_to_new_thread_body_input_field(
            test_utilities.kb_new_thread_test_data['new_thread_reduced_body']
        )

    with allure.step("Clicking on the 'Post Thread' button and verifying that we are on the "
                     "same page"):
        sumo_pages.kb_article_discussion_page._click_on_submit_new_thread_button()
        expect(page).to_have_url(
            article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_NEW_ENDPOINT)

    with allure.step("Adding 5 characters inside the thread title field, clicking on the "
                     "'Cancel' button and verifying that the article is not displayed inside "
                     "the discussion thread list"):
        sumo_pages.kb_article_discussion_page._add_text_to_new_thread_title_field(
            test_utilities.kb_new_thread_test_data['new_thread_reduced_title']
        )
        sumo_pages.kb_article_discussion_page._click_on_cancel_new_thread_button()
        expect(sumo_pages.kb_article_discussion_page._get_thread_by_title_locator(
            test_utilities.kb_new_thread_test_data['new_thread_reduced_title']
        )
        ).to_be_hidden()

    with allure.step("Clicking on the 'Post a new thread' button and adding the minimum "
                     "required characters inside both title and content fields"):
        sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()
        sumo_pages.kb_article_discussion_page._add_text_to_new_thread_title_field(
            test_utilities.kb_new_thread_test_data['new_thread_reduced_title']
        )
        sumo_pages.kb_article_discussion_page._add_text_to_new_thread_body_input_field(
            test_utilities.kb_new_thread_test_data['new_thread_reduced_body']
        )

    with allure.step("Clicking on the 'Post Thread' button, manually navigating to the "
                     "discuss endpoint and verifying that the posted thread is successfully "
                     "displayed"):
        sumo_pages.kb_article_discussion_page._click_on_submit_new_thread_button()
        thread_url = test_utilities.get_page_url()
        thread_id = str(test_utilities.number_extraction_from_string_endpoint(
            KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT, thread_url)
        )
        test_utilities.navigate_to_link(
            article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT)
        expect(sumo_pages.kb_article_discussion_page._get_posted_thread_locator(thread_id)
               ).to_be_visible()

    with allure.step("Clearing the newly created thread"):
        __clearing_newly_created_thread(page, thread_id)


# C2260840
@pytest.mark.articleThreads
def test_thread_replies_counter_increment(page: Page):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with an admin account"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

    with allure.step("Manually navigating to the article endpoint and clicking on the "
                     "article option"):
        test_utilities.navigate_to_link(article_url)

    with check, allure.step("Clicking on the 'Post a new thread button', posting a new kb "
                            "article discussion thread and verifying that the thread counter"
                            " is not 0"):
        thread_info = sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread()
        assert (test_utilities.number_extraction_from_string(
            sumo_pages.kb_article_discussion_page._get_thread_page_counter_replies_text())) == 0

    with check, allure.step("Manually navigating to the discuss endpoint "
                            "and verifying that the reply counter for the posted thread has "
                            "incremented successfully"):
        test_utilities.navigate_to_link(thread_info["article_discussion_url"])
        assert (test_utilities.number_extraction_from_string(
            sumo_pages.kb_article_discussion_page._get_article_discussions_thread_counter(
                thread_info['thread_id']))) == 0

    with allure.step("Navigating back to the thread and posting a new reply with the same "
                     "user"):
        sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
            thread_info['thread_id'])
        sumo_pages.kb_article_thread_flow.post_reply_to_thread(
            test_utilities.kb_new_thread_test_data['thread_reply_body'])

    with check, allure.step("Verifying that the thread counter is 1"):
        assert (test_utilities.number_extraction_from_string(
            sumo_pages.kb_article_discussion_page._get_thread_page_counter_replies_text())) == 1

    with check, allure.step("Manually navigating to the discuss endpoint and verifying that "
                            "the reply counter for the posted thread has incremented "
                            "successfully"):
        test_utilities.navigate_to_link(thread_info["article_discussion_url"])
        assert (test_utilities.number_extraction_from_string(
            sumo_pages.kb_article_discussion_page._get_article_discussions_thread_counter(
                thread_info['thread_id']))) == 1

    with allure.step("Clearing the newly created thread"):
        __clearing_newly_created_thread(page, thread_info['thread_id'])


# C2260840, C2260809
@pytest.mark.articleThreads
def test_thread_replies_counter_decrement(page: Page):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with a normal account"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts['TEST_ACCOUNT_12']
        ))
        test_utilities.navigate_to_link(article_url)

    with allure.step("Clicking on the 'Post a new thread button' and posting a new kb "
                     "article discussion thread"):
        thread_info = sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread()

    with allure.step("Posting a new reply with the same user"):
        thread_reply_info = sumo_pages.kb_article_thread_flow.post_reply_to_thread(
            test_utilities.kb_new_thread_test_data['thread_reply_body'])

    with allure.step("Signing in with an admin account"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts['TEST_ACCOUNT_MODERATOR']
        ))

    with check, allure.step("Posting a new reply with the same user and verifying that the "
                            "reply counter for the posted thread has incremented "
                            "successfully"):
        sumo_pages.kb_article_thread_flow.post_reply_to_thread(
            test_utilities.kb_new_thread_test_data['thread_reply_body']
        )
        assert (test_utilities.number_extraction_from_string(
            sumo_pages.kb_article_discussion_page._get_thread_page_counter_replies_text()) == 2)

    with allure.step("Manually navigating to the discuss endpoint and verifying that the "
                     "reply counter for the posted thread has incremented successfully"):
        test_utilities.navigate_to_link(thread_info['article_discussion_url'])
        assert (test_utilities.number_extraction_from_string(
            sumo_pages.kb_article_discussion_page._get_article_discussions_thread_counter(
                thread_info['thread_id'])) == 2)

    with allure.step("Clicking on the 3 dotted menu for a posted thread reply"):
        sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
            thread_info['thread_id'])

    with check, allure.step("Clicking on the 'Delete this post' option and verifying that "
                            "the reply counter for the posted thread has incremented "
                            "successfully"):
        sumo_pages.kb_article_thread_flow.delete_reply_to_thread(thread_reply_info['reply_id'])
        assert (test_utilities.number_extraction_from_string(
            sumo_pages.kb_article_discussion_page._get_thread_page_counter_replies_text()) == 1)

    with check, allure.step("Manually navigating to the discuss endpoint and verifying that "
                            "the reply counter for the posted thread has decremented "
                            "successfully"):
        test_utilities.navigate_to_link(thread_info['article_discussion_url'])
        assert (test_utilities.number_extraction_from_string(
            sumo_pages.kb_article_discussion_page._get_article_discussions_thread_counter(
                thread_info['thread_id'])) == 1)

    with allure.step("Clearing the newly created thread"):
        __clearing_newly_created_thread(page, thread_info['thread_id'])


@pytest.mark.articleThreads
@pytest.mark.parametrize("username", ['TEST_ACCOUNT_12', 'TEST_ACCOUNT_MODERATOR', ''])
def test_article_thread_author_filter(page: Page, username):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with an admin account"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        test_utilities.navigate_to_link(article_url)

    with allure.step("Posting a new kb article discussion thread"):
        thread_info = sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread()

    with allure.step("Navigating back to the article discussion page and signing in with a "
                     "non-admin account"):
        test_utilities.navigate_to_link(thread_info['article_discussion_url'])
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

    with allure.step("Posting a new kb article discussion thread"):
        thread_info_two = sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread()

    with allure.step("Navigating back to the article discussion page"):
        test_utilities.navigate_to_link(thread_info['article_discussion_url'])

    if username == 'TEST_ACCOUNT_MODERATOR':
        with allure.step("Signing in with an admin account"):
            test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
                test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))
    elif username != 'TEST_ACCOUNT_12':
        with allure.step("Signing out from SUMO"):
            test_utilities.delete_cookies()

    with check, allure.step("Clicking on the 'Author' filter and verifying that the authors "
                            "are in reverse alphabetical order"):
        sumo_pages.kb_article_discussion_page._click_on_article_thread_author_replies_filter()
        assert sumo_pages.kb_article_discussion_page._get_all_article_threads_authors() != sorted(
            sumo_pages.kb_article_discussion_page._get_all_article_threads_authors())

    with check, allure.step("Clicking on the 'Author' filter again and verifying that the "
                            "authors are in alphabetical order"):
        sumo_pages.kb_article_discussion_page._click_on_article_thread_author_replies_filter()
        assert sumo_pages.kb_article_discussion_page._get_all_article_threads_authors() == sorted(
            sumo_pages.kb_article_discussion_page._get_all_article_threads_authors())

    with allure.step("Clearing both created threads"):
        __clearing_newly_created_thread(page, thread_info['thread_id'])
        __clearing_newly_created_thread(page, thread_info_two['thread_id'])


@pytest.mark.articleThreads
@pytest.mark.parametrize("username", ['TEST_ACCOUNT_12', 'TEST_ACCOUNT_MODERATOR', ''])
def test_article_thread_replies_filter(page: Page, username):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with an admin account"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        test_utilities.navigate_to_link(article_url)

    with allure.step("Clicking on the 'Post a new thread button' and posting a new kb "
                     "article discussion thread"):
        thread_info = sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread()

    with allure.step("Posting a new reply with the same user"):
        sumo_pages.kb_article_thread_flow.post_reply_to_thread(
            test_utilities.kb_new_thread_test_data['thread_reply_body']
        )

    with allure.step("Navigating back to the article discussion page and posting a new kb "
                     "article discussion thread"):
        thread_info_two = sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread()

    with allure.step("Navigating back to the article discussion page"):
        test_utilities.navigate_to_link(thread_info['article_discussion_url'])

    if username == "TEST_ACCOUNT_12":
        with allure.step("Signing in with a non admin account"):
            test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
                test_utilities.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))
    elif username == '':
        with allure.step("Deleting user session"):
            test_utilities.delete_cookies()

    with allure.step("Clicking on the 'Replies' filter and verifying that the replies is in "
                     "descending order"):
        sumo_pages.kb_article_discussion_page._click_on_article_thread_replies_filter()
        assert test_utilities.is_descending(
            sumo_pages.kb_article_discussion_page._get_all_article_threads_replies())

    with check, allure.step("Clicking on the 'Replies' filter again and verifying that the "
                            "replies is in ascending order"):
        sumo_pages.kb_article_discussion_page._click_on_article_thread_replies_filter()
        assert not test_utilities.is_descending(
            sumo_pages.kb_article_discussion_page._get_all_article_threads_replies())

    with allure.step("Clearing both created threads"):
        __clearing_newly_created_thread(page, thread_info['thread_id'])
        __clearing_newly_created_thread(page, thread_info_two['thread_id'])


@pytest.mark.articleThreads
def test_article_lock_thread_non_admin_users(page: Page):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with a non-admin account and creating an article"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts['TEST_ACCOUNT_12']
        ))
    article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

    with allure.step("Signing in with an admin account and approving the article"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        sumo_pages.submit_kb_article_flow.approve_kb_revision(
            revision_id=article_details['first_revision_id']
        )

    with allure.step("Clicking on the 'Discussion' editing tools navbar option and posting a "
                     "new kb article discussion thread"):
        thread_info_one = sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread()

    with allure.step("Signing in with a non-admin user account"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts['TEST_ACCOUNT_12']
        ))

    with allure.step("Navigating back to the discussions page and posting a new kb article "
                     "discussion thread"):
        test_utilities.navigate_to_link(thread_info_one["article_discussion_url"])
        thread_info_two = sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread()

    with allure.step("Navigating back to the discussions page, clicking on the thread posted "
                     "by another user and verifying that the 'Lock thread' option is not "
                     "available"):
        test_utilities.navigate_to_link(thread_info_one["article_discussion_url"])
        sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
            thread_info_one['thread_id'])
        expect(sumo_pages.kb_article_discussion_page._get_lock_this_article_thread_locator()
               ).to_be_hidden()

    with allure.step("Navigating back to the article discussions page, clicking on the "
                     "thread posted by self and verifying that the 'Lock thread' option is "
                     "not available"):
        test_utilities.navigate_to_link(thread_info_one["article_discussion_url"])
        sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
            thread_info_two['thread_id'])
        expect(sumo_pages.kb_article_discussion_page._get_lock_this_article_thread_locator()
               ).to_be_hidden()

    with allure.step("Deleting user sessions and verifying that the 'Lock thread' options is "
                     "not available"):
        test_utilities.delete_cookies()
        expect(sumo_pages.kb_article_discussion_page._get_lock_this_article_thread_locator()
               ).to_be_hidden()

    with allure.step("Signing in with an admin account and deleting the kb article"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        test_utilities.navigate_to_link(article_details["article_url"])
        sumo_pages.kb_article_deletion_flow.delete_kb_article()


#  C2260810
@pytest.mark.articleThreads
@pytest.mark.parametrize("username", ['TEST_ACCOUNT_MODERATOR', 'TEST_ACCOUNT_12', ''])
def test_article_lock_thread_functionality(page: Page, username):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with an admin account"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        test_utilities.navigate_to_link(article_url)

    with allure.step("Posting a new kb article discussion thread"):
        thread_info_one = sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread()

    with allure.step("Signing in with a non-admin user account"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts['TEST_ACCOUNT_12']
        ))

    with allure.step("Navigating back to the discussions page and posting a new discussion "
                     "thread"):
        test_utilities.navigate_to_link(thread_info_one["article_discussion_url"])
        thread_info_two = sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread()

    with allure.step("Navigating back to the discussions page"):
        test_utilities.navigate_to_link(thread_info_one["article_discussion_url"])

    with allure.step("Signing in with an admin account"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

    with allure.step("Clicking on the thread posted by self user and locking the thread"):
        sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
            thread_info_one['thread_id'])
        sumo_pages.kb_article_discussion_page._click_on_lock_this_article_thread_option()

    if username == 'TEST_ACCOUNT_12':
        with check, allure.step("Signing in with a non-admin account and verifying that the "
                                "correct thread locked message is displayed"):
            test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
                test_utilities.user_secrets_accounts['TEST_ACCOUNT_12']
            ))
            assert (sumo_pages.kb_article_discussion_page._get_text_of_locked_article_thread_text(
            ) == KBArticlePageMessages.KB_ARTICLE_LOCKED_THREAD_MESSAGE)

    elif username == '':
        with allure.step("Deleting user session"):
            test_utilities.delete_cookies()

    with allure.step("Verifying that the 'Post a reply' textarea field is not displayed"):
        expect(sumo_pages.kb_article_discussion_page._get_thread_post_a_reply_textarea_field()
               ).to_be_hidden()

    with allure.step("Verifying that the 'Locked' status is displayed under article header"):
        expect(sumo_pages.kb_article_discussion_page._get_locked_article_status()).to_be_visible()

    with allure.step("Navigating back to the discussions page"):
        test_utilities.navigate_to_link(thread_info_one["article_discussion_url"])

    if username != 'TEST_ACCOUNT_MODERATOR':
        with allure.step("Signing in with an admin account"):
            test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
                test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

    with allure.step("Clicking on the thread posted by the other user and clicking on the "
                     "'Lock this thread' option"):
        sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
            thread_info_two['thread_id'])
        sumo_pages.kb_article_discussion_page._click_on_lock_this_article_thread_option()

    if username == 'TEST_ACCOUNT_12':
        with check, allure.step("Signing in with a non-admin account and verifying that the "
                                "correct thread locked message is displayed"):
            test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
                test_utilities.user_secrets_accounts['TEST_ACCOUNT_12']
            ))
            assert (sumo_pages.kb_article_discussion_page._get_text_of_locked_article_thread_text(
            ) == KBArticlePageMessages.KB_ARTICLE_LOCKED_THREAD_MESSAGE)
    elif username == '':
        with allure.step("Deleting user session"):
            test_utilities.delete_cookies()

    with allure.step("Verifying that the 'Locked' status is displayed under article header"):
        expect(sumo_pages.kb_article_discussion_page._get_locked_article_status()).to_be_visible()

    with allure.step("Verifying that the 'Post a reply' textarea field is not displayed"):
        expect(sumo_pages.kb_article_discussion_page._get_thread_post_a_reply_textarea_field()
               ).to_be_hidden()

    with allure.step("Clearing both created threads"):
        __clearing_newly_created_thread(page, thread_info_one['thread_id'])
        __clearing_newly_created_thread(page, thread_info_two['thread_id'])


# C2260810
@pytest.mark.articleThreads
@pytest.mark.parametrize("username", ['TEST_ACCOUNT_MODERATOR', 'TEST_ACCOUNT_12', ''])
def test_article_unlock_thread_functionality(page: Page, username):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with an admin account"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

    with allure.step("Navigating to the article endpoint"):
        test_utilities.navigate_to_link(article_url)

    with allure.step("Posting a new kb article discussion thread"):
        thread_info_one = sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread()

    with allure.step("Signing in with a normal user account"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts['TEST_ACCOUNT_12']
        ))

    with allure.step("Navigating back to the discussions page"):
        test_utilities.navigate_to_link(thread_info_one["article_discussion_url"])

    with allure.step("Posting a new kb article discussion thread"):
        thread_info_two = sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread()

    with allure.step("Navigating back to the discussions page"):
        test_utilities.navigate_to_link(thread_info_one["article_discussion_url"])

    with allure.step("Signing in with an admin account"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

    with check, allure.step("Clicking on the thread posted by self user and verifying that "
                            "the correct 'Lock this thread' option text is displayed"):
        sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
            thread_info_one['thread_id'])
        assert (sumo_pages.kb_article_discussion_page._get_lock_this_article_thread_option_text(
        ) == KBArticlePageMessages.KB_ARTICLE_LOCK_THIS_THREAD_OPTION)

    with check, allure.step("Clicking on 'Lock this thread' option and verifying that the "
                            "correct 'Unlock this thread' text is displayed"):
        sumo_pages.kb_article_discussion_page._click_on_lock_this_article_thread_option()
        assert (sumo_pages.kb_article_discussion_page._get_lock_this_article_thread_option_text(
        ) == KBArticlePageMessages.KB_ARTICLE_UNLOCK_THIS_THREAD_OPTION)

    if username == 'TEST_ACCOUNT_12':
        with allure.step("Signing in with a non-admin account and verifying that the 'Unlock "
                         "this thread' option is not displayed"):
            test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
                test_utilities.user_secrets_accounts['TEST_ACCOUNT_12']
            ))
            expect(sumo_pages.kb_article_discussion_page._get_lock_this_article_thread_locator(
            )).to_be_hidden()
    if username == '':
        with allure.step("Deleting user session and verifying that the 'Unlock this thread' "
                         "option is no displayed"):
            test_utilities.delete_cookies()
            expect(sumo_pages.kb_article_discussion_page._get_lock_this_article_thread_locator(
            )).to_be_hidden()

    if username != 'TEST_ACCOUNT_MODERATOR':
        with allure.step("Signing in with an admin account"):
            test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
                test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

    with allure.step("Clicking on the 'Unlock this thread'"):
        sumo_pages.kb_article_discussion_page._click_on_lock_this_article_thread_option()

    if username == 'TEST_ACCOUNT_12':
        with allure.step("Signing in with a non-admin account and verifying that the "
                         "textarea field is available"):
            test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
                test_utilities.user_secrets_accounts['TEST_ACCOUNT_12']
            ))
            expect(sumo_pages.kb_article_discussion_page._get_thread_post_a_reply_textarea_field(
            )).to_be_visible()
    if username == '':
        with allure.step("Deleting user session and verifying that the textarea field is not "
                         "available"):
            test_utilities.delete_cookies()
            expect(sumo_pages.kb_article_discussion_page._get_thread_post_a_reply_textarea_field(
            )).to_be_hidden()

    with allure.step("Verifying that the 'Locked' header text is not displayed"):
        expect(sumo_pages.kb_article_discussion_page._get_locked_article_status()).to_be_hidden()

    with allure.step("Verifying that the 'Thread locked' page message is not displayed"):
        expect(sumo_pages.kb_article_discussion_page._get_text_of_locked_article_thread_locator(
        )).to_be_hidden()

    if username != "TEST_ACCOUNT_MODERATOR":
        with allure.step("Signing in with an admin account"):
            test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
                test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

    with allure.step("Navigating back the article page and clicking on the thread posted by "
                     "another user"):
        test_utilities.navigate_to_link(thread_info_one["article_discussion_url"])
        sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
            thread_info_two['thread_id'])

    with check, allure.step("Verifying that the correct 'Lock this thread' option text is "
                            "displayed"):
        assert (sumo_pages.kb_article_discussion_page._get_lock_this_article_thread_option_text(
        ) == KBArticlePageMessages.KB_ARTICLE_LOCK_THIS_THREAD_OPTION)

    with check, allure.step("Clicking on 'Lock this thread' option and verifying that the "
                            "correct 'Unlock this thread' text is displayed"):
        sumo_pages.kb_article_discussion_page._click_on_lock_this_article_thread_option()
        assert (sumo_pages.kb_article_discussion_page._get_lock_this_article_thread_option_text(
        ) == KBArticlePageMessages.KB_ARTICLE_UNLOCK_THIS_THREAD_OPTION)

    if username == 'TEST_ACCOUNT_12':
        with allure.step("Signing in with a non-admin account and verifying that the 'Unlock "
                         "this thread' option is displayed"):
            test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
                test_utilities.user_secrets_accounts['TEST_ACCOUNT_12']
            ))
            expect(sumo_pages.kb_article_discussion_page._get_lock_this_article_thread_locator(
            )).to_be_hidden()
    if username == '':
        with allure.step("Deleting the user session and verifying that the 'Unlock this "
                         "thread' option is not displayed"):
            test_utilities.delete_cookies()
            expect(sumo_pages.kb_article_discussion_page._get_lock_this_article_thread_locator(
            )).to_be_hidden()

    if username != 'TEST_ACCOUNT_MODERATOR':
        with allure.step("Signing in with an admin account and clicking on the 'Unlock this "
                         "thread' option"):
            test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
                test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))
    sumo_pages.kb_article_discussion_page._click_on_lock_this_article_thread_option()

    if username == 'TEST_ACCOUNT_12':
        with allure.step("Signing in with a non-admin account and verifying that the "
                         "textarea field is available"):
            test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
                test_utilities.user_secrets_accounts['TEST_ACCOUNT_12']
            ))
            expect(sumo_pages.kb_article_discussion_page._get_thread_post_a_reply_textarea_field(
            )).to_be_visible()
    if username == '':
        with allure.step("Deleting user session and verifying that the textarea field is not "
                         "available"):
            test_utilities.delete_cookies()
            expect(sumo_pages.kb_article_discussion_page._get_thread_post_a_reply_textarea_field(
            )).to_be_hidden()

    with allure.step("Verifying that the 'Locked' header text is not displayed"):
        expect(sumo_pages.kb_article_discussion_page._get_locked_article_status()).to_be_hidden()

    with allure.step("Verifying that the 'Thread locked' page message is not displayed"):
        expect(sumo_pages.kb_article_discussion_page._get_text_of_locked_article_thread_locator(
        )).to_be_hidden()

    with allure.step("Clearing the newly created thread"):
        __clearing_newly_created_thread(page, thread_info_one['thread_id'])
        __clearing_newly_created_thread(page, thread_info_two['thread_id'])


# C2260811
@pytest.mark.articleThreads
@pytest.mark.parametrize("username", ['TEST_ACCOUNT_MODERATOR', 'TEST_ACCOUNT_12', ''])
def test_article_thread_sticky(page: Page, username):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with an admin account"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

    with allure.step("Posting a new kb article"):
        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            approve_first_revision=True
        )

    with allure.step("Posting a new kb article discussion thread"):
        thread_info_one = sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread()

    with allure.step("Signing in with a normal user account"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts['TEST_ACCOUNT_12']
        ))

    with allure.step("Navigating back to the discussions page"):
        test_utilities.navigate_to_link(thread_info_one['article_discussion_url'])

    with allure.step("Posting a new kb article discussion thread"):
        thread_info_two = sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread(
            title='Other test thread'
        )

    with allure.step("Verifying that the 'Sticky this thread' option is not displayed"):
        expect(sumo_pages.kb_article_discussion_page._get_sticky_this_thread_locator()
               ).to_be_hidden()

    with allure.step("Navigating back to the discussions page"):
        test_utilities.navigate_to_link(thread_info_one['article_discussion_url'])

    with allure.step("Signing in with an admin account"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

    with allure.step("Clicking on the thread posted by self and clicking on the 'sticky this "
                     "thread' option"):
        sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
            thread_info_one['thread_id'])
        sumo_pages.kb_article_discussion_page._click_on_sticky_this_thread_option()

    with check, allure.step("Verifying that the text changed to 'Unsticky this thread'"):
        assert (sumo_pages.kb_article_discussion_page._get_text_of_sticky_this_thread_option(
        ) == KBArticlePageMessages.KB_ARTICLE_UNSTICKY_OPTION)

    if username == 'TEST_ACCOUNT_12':
        with allure.step("Signing in with a non-admin account and verifying that the "
                         "unsticky this thread option is not available"):
            test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
                test_utilities.user_secrets_accounts['TEST_ACCOUNT_12']
            ))
            expect(sumo_pages.kb_article_discussion_page._get_sticky_this_thread_locator()
                   ).to_be_hidden()
    if username == '':
        with allure.step("Deleting user session and verifying that the unsticky this thread "
                         "option is not available"):
            test_utilities.delete_cookies()
            expect(sumo_pages.kb_article_discussion_page._get_sticky_this_thread_locator()
                   ).to_be_hidden()

    with allure.step("Verifying that the 'Sticky' status is displayed"):
        expect(sumo_pages.kb_article_discussion_page._get_sticky_this_thread_status_locator()
               ).to_be_visible()

    with check, allure.step("Navigating back to the discussions page and verifying that the "
                            "sticky article is displayed in top of the list"):
        test_utilities.navigate_to_link(thread_info_one['article_discussion_url'])
        assert sumo_pages.kb_article_discussion_page._get_all_article_threads_titles(
        )[0] == thread_info_one['thread_title']

    if username != 'TEST_ACCOUNT_MODERATOR':
        with allure.step("Signing in with an admin account"):
            test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
                test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

    with check, allure.step("Clicking on the unsitcky this thread and verifying that the "
                            "text changed to 'Sticky this thread'"):
        sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
            thread_info_one['thread_id'])
        sumo_pages.kb_article_discussion_page._click_on_sticky_this_thread_option()
        assert (sumo_pages.kb_article_discussion_page._get_text_of_sticky_this_thread_option(
        ) == KBArticlePageMessages.KB_ARTICLE_STICKY_THIS_THREAD_OPTION)

    if username == 'TEST_ACCOUNT_12':
        with allure.step("Signing in with a non-admin account"):
            test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
                test_utilities.user_secrets_accounts['TEST_ACCOUNT_12']
            ))
    if username == '':
        with allure.step("Deleting user session"):
            test_utilities.delete_cookies()

    with allure.step("Verifying that the 'Sticky' status is not displayed"):
        expect(sumo_pages.kb_article_discussion_page._get_sticky_this_thread_status_locator()
               ).to_be_hidden()

    with check, allure.step("Navigating back to the discussions page and verifying that the "
                            "sticky article is not displayed in top of the list"):
        test_utilities.navigate_to_link(thread_info_one['article_discussion_url'])
        assert sumo_pages.kb_article_discussion_page._get_all_article_threads_titles(
        )[0] == thread_info_two['thread_title']

    with allure.step("Signing in with an admin account and deleting the kb article"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        test_utilities.navigate_to_link(article_details["article_url"])
        sumo_pages.kb_article_deletion_flow.delete_kb_article()


#  C2260808, C2260823
@pytest.mark.articleThreads
@pytest.mark.parametrize("thread_author", ['self', 'other'])
def test_article_thread_content_edit(page: Page, thread_author):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with an admin account"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

    with allure.step("Manually navigating to the article endpoint and posting a new kb "
                     "article discussion thread"):
        test_utilities.navigate_to_link(article_url)
        thread_info_one = sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread()

    with allure.step("Signing in with a non-admin user account"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts['TEST_ACCOUNT_12']
        ))

    with allure.step("Navigating back to the discussions page and posting a new kb article "
                     "discussion thread"):
        test_utilities.navigate_to_link(article_url)
        thread_info_two = sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread()

    with allure.step("Adding data inside the edit this thread title field and clicking on "
                     "the cancel button"):
        sumo_pages.kb_article_thread_flow._edit_article_thread(
            thread_title=test_utilities.kb_new_thread_test_data['updated_thread_title'],
            submit_edit=False
        )

    with check, allure.step("Verifying that the thread title was not changed"):
        assert sumo_pages.kb_article_discussion_page._get_thread_title_text(
        ) == thread_info_two['thread_title']

    with allure.step("Adding data inside the edit this thread title field and clicking on "
                     "the update button"):
        sumo_pages.kb_article_thread_flow._edit_article_thread(
            thread_title=test_utilities.kb_new_thread_test_data['updated_thread_title']
        )

    with check, allure.step("Verifying that the thread title was changed"):
        assert sumo_pages.kb_article_discussion_page._get_thread_title_text(
        ) == test_utilities.kb_new_thread_test_data['updated_thread_title']

    with allure.step("Deleting user session and verifying that the edit this thread option "
                     "is not displayed"):
        test_utilities.delete_cookies()
        expect(sumo_pages.kb_article_discussion_page._get_edit_this_thread_locator()
               ).to_be_hidden()

    with allure.step("Signing in with an admin account"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

    with allure.step("Navigating back to the discussions page"):
        test_utilities.navigate_to_link(thread_info_one["article_discussion_url"])

    if thread_author == 'self':
        with allure.step("Clicking on the self posted thread"):
            sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
                thread_info_one["thread_id"])
    else:
        with allure.step("Clicking on the other user posted thread"):
            sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
                thread_info_two["thread_id"])

    with allure.step("Clicking on the 'Edit this thread', adding data inside the title field "
                     "and clicking on the cancel button"):
        sumo_pages.kb_article_thread_flow._edit_article_thread(
            test_utilities.kb_new_thread_test_data['second_thread_updated_title'], False
        )

    if thread_author == 'self':
        with check, allure.step("Verifying that the thread title was not changed"):
            assert sumo_pages.kb_article_discussion_page._get_thread_title_text(
            ) == thread_info_one['thread_title']
    else:
        with check, allure.step("Verifying that the thread title was not changed"):
            assert sumo_pages.kb_article_discussion_page._get_thread_title_text(
            ) == test_utilities.kb_new_thread_test_data['updated_thread_title']

    with allure.step("Adding data inside the edit this thread title field and clicking on "
                     "the update button"):
        sumo_pages.kb_article_thread_flow._edit_article_thread(
            thread_title=test_utilities.kb_new_thread_test_data['second_thread_updated_title']
        )

    with check, allure.step("Verifying that the thread title was changed"):
        assert sumo_pages.kb_article_discussion_page._get_thread_title_text(
        ) == test_utilities.kb_new_thread_test_data['second_thread_updated_title']

    with allure.step("Navigating back to the discussions page"):
        test_utilities.navigate_to_link(thread_info_one["article_discussion_url"])

    with check, allure.step("Verifying that the updated thread title is displayed inside the "
                            "threads list"):
        assert (test_utilities.kb_new_thread_test_data
                ['second_thread_updated_title'] in sumo_pages.kb_article_discussion_page
                ._get_all_article_threads_titles())

    with allure.step("Clearing all the created threads"):
        __clearing_newly_created_thread(page, thread_info_one['thread_id'])
        __clearing_newly_created_thread(page, thread_info_two['thread_id'])


@pytest.mark.beforeThreadTests
def test_posting_a_new_kb_test_article(page: Page):
    """
    This test function as a precondition for the articleThreads tests. It creates the test
    article upon which the majority of the test are performed.
    This needs to be placed before the articleThreads inside the yml file.
    """
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
        test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
    ))

    sumo_pages.submit_kb_article_flow.submit_simple_kb_article(approve_first_revision=True)
    sumo_pages.kb_article_page._click_on_article_option()
    with open("test_data/test_article", 'w') as file:
        file.write(test_utilities.get_page_url())


@pytest.mark.afterThreadTests
def test_delete_kb_test_article(page: Page):
    """
    This test function acts as a cleaner and deletes the article created for the article
    threads tests.
    This needs to be executed after the articleThreads tests in the yml.
    """
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
        test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
    ))
    test_utilities.navigate_to_link(article_url)
    sumo_pages.kb_article_deletion_flow.delete_kb_article()

    with open("test_data/test_article", 'w'):
        pass


def __clearing_newly_created_thread(page: Page, thread_id: str):
    """
    Test article threads helper function which deletes a thread which has the given thread_id.
    """
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
        test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
    ))

    test_utilities.navigate_to_link(
        article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
    )

    sumo_pages.kb_article_thread_flow.delete_article_thread(thread_id)
    test_utilities.navigate_to_link(
        article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT)
