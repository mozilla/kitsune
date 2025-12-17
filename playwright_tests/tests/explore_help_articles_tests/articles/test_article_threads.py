import allure
import pytest
from playwright.sync_api import expect, Page
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.explore_help_articles.kb_article_page_messages import (
    KBArticlePageMessages)
from playwright_tests.pages.sumo_pages import SumoPages


# C2188031
@pytest.mark.articleThreads
def test_article_thread_field_validation(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(permissions=["review_revision"])

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

        article_details = sumo_pages.submit_kb_article_flow.kb_article_creation_via_api(
            page=page, approve_revision=True)
        sumo_pages.kb_article_page.click_on_article_option()
        sumo_pages.kb_article_page.click_on_editing_tools_discussion_option()

    with allure.step("Clicking on the 'Post a new thread button' and clicking on the 'Post "
                     "Thread' button without adding any data in the form fields"):
        sumo_pages.kb_article_discussion_page.click_on_post_a_new_thread_option()
        sumo_pages.kb_article_discussion_page.click_on_submit_new_thread_button()

    with allure.step("Verifying that we are on the same page"):
        expect(page).to_have_url(
            article_details["article_url"] + KBArticlePageMessages.
            KB_ARTICLE_DISCUSSIONS_NEW_ENDPOINT)

    with allure.step("Adding one character inside the 'Title' field, clicking the 'Post "
                     "Thread' button and verifying that we are on the same page"):
        sumo_pages.kb_article_discussion_page.add_text_to_new_thread_title_field("t")
        sumo_pages.kb_article_discussion_page.click_on_submit_new_thread_button()

        expect(page).to_have_url(
            article_details["article_url"] + KBArticlePageMessages.
            KB_ARTICLE_DISCUSSIONS_NEW_ENDPOINT)

    with allure.step("Clearing the input field and adding 5 characters inside the title "
                     "input field"):
        sumo_pages.kb_article_discussion_page.clear_new_thread_title_field()
        sumo_pages.kb_article_discussion_page.add_text_to_new_thread_title_field(
            utilities.kb_new_thread_test_data['new_thread_reduced_title']
        )

    with allure.step("Clicking on the 'Post Thread' button and verifying that we are on the "
                     "same page"):
        sumo_pages.kb_article_discussion_page.click_on_submit_new_thread_button()
        expect(page).to_have_url(
            article_details["article_url"] + KBArticlePageMessages.
            KB_ARTICLE_DISCUSSIONS_NEW_ENDPOINT)

    with allure.step("Adding one character inside the content field, clicking on the 'Post "
                     "Thread' button and verifying that we are on the same page"):
        sumo_pages.kb_article_discussion_page.add_text_to_new_thread_body_input_field("a")
        sumo_pages.kb_article_discussion_page.click_on_submit_new_thread_button()
        expect(page).to_have_url(
            article_details["article_url"] + KBArticlePageMessages.
            KB_ARTICLE_DISCUSSIONS_NEW_ENDPOINT)

    with allure.step("Clearing both title and content fields and adding 5 characters inside "
                     "the thread content field"):
        sumo_pages.kb_article_discussion_page.clear_new_thread_body_field()
        sumo_pages.kb_article_discussion_page.clear_new_thread_title_field()
        sumo_pages.kb_article_discussion_page.clear_new_thread_body_field()
        sumo_pages.kb_article_discussion_page.add_text_to_new_thread_body_input_field(
            utilities.kb_new_thread_test_data['new_thread_reduced_body']
        )

    with allure.step("Clicking on the 'Post Thread' button and verifying that we are on the "
                     "same page"):
        sumo_pages.kb_article_discussion_page.click_on_submit_new_thread_button()
        expect(page).to_have_url(
            article_details["article_url"] + KBArticlePageMessages.
            KB_ARTICLE_DISCUSSIONS_NEW_ENDPOINT)

    with allure.step("Adding 5 characters inside the thread title field, clicking on the "
                     "'Cancel' button and verifying that the article is not displayed inside "
                     "the discussion thread list"):
        sumo_pages.kb_article_discussion_page.add_text_to_new_thread_title_field(
            utilities.kb_new_thread_test_data['new_thread_reduced_title']
        )
        sumo_pages.kb_article_discussion_page.click_on_cancel_new_thread_button()
        expect(sumo_pages.kb_article_discussion_page.get_thread_by_title_locator(
            utilities.kb_new_thread_test_data['new_thread_reduced_title']
        )
        ).to_be_hidden()

    with allure.step("Clicking on the 'Post a new thread' button and adding the minimum "
                     "required characters inside both title and content fields"):
        sumo_pages.kb_article_discussion_page.click_on_post_a_new_thread_option()
        sumo_pages.kb_article_discussion_page.add_text_to_new_thread_title_field(
            utilities.kb_new_thread_test_data['new_thread_reduced_title']
        )
        sumo_pages.kb_article_discussion_page.add_text_to_new_thread_body_input_field(
            utilities.kb_new_thread_test_data['new_thread_reduced_body']
        )

    with allure.step("Clicking on the 'Post Thread' button, manually navigating to the "
                     "discuss endpoint and verifying that the posted thread is successfully "
                     "displayed"):
        sumo_pages.kb_article_discussion_page.click_on_submit_new_thread_button()
        thread_url = utilities.get_page_url()
        thread_id = str(utilities.number_extraction_from_string_endpoint(
            KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT, thread_url)
        )
        utilities.navigate_to_link(
            article_details["article_url"] + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT)
        expect(sumo_pages.kb_article_discussion_page.get_posted_thread_locator(thread_id)
               ).to_be_visible()


# C2260840
@pytest.mark.articleThreads
def test_thread_replies_counter_increment(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(permissions=["review_revision"])

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

        article_details = sumo_pages.submit_kb_article_flow.kb_article_creation_via_api(
            page=page, approve_revision=True)

    with allure.step("Manually navigating to the article endpoint and clicking on the "
                     "article option"):
        utilities.navigate_to_link(article_details["article_url"])

    with allure.step("Clicking on the 'Post a new thread button', posting a new kb article "
                     "discussion thread and verifying that the thread counter is not 0"):
        thread_info = sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread()
        assert (utilities.number_extraction_from_string(
            sumo_pages.kb_article_discussion_page.get_thread_page_counter_replies_text())) == 0

    with allure.step("Manually navigating to the discuss endpoint and verifying that the reply "
                     "counter for the posted thread has incremented successfully"):
        utilities.navigate_to_link(thread_info["article_discussion_url"])
        assert (utilities.number_extraction_from_string(
            sumo_pages.kb_article_discussion_page.get_article_discussions_thread_counter(
                thread_info['thread_id']))) == 0

    with allure.step("Navigating back to the thread and posting a new reply with the same "
                     "user"):
        sumo_pages.kb_article_discussion_page.click_on_a_particular_thread(
            thread_info['thread_id'])
        sumo_pages.kb_article_thread_flow.post_reply_to_thread(
            utilities.kb_new_thread_test_data['thread_reply_body'])

    with allure.step("Verifying that the thread counter is 1"):
        assert (utilities.number_extraction_from_string(
            sumo_pages.kb_article_discussion_page.get_thread_page_counter_replies_text())) == 1

    with allure.step("Manually navigating to the discuss endpoint and verifying that the reply "
                     "counter for the posted thread has incremented successfully"):
        utilities.navigate_to_link(thread_info["article_discussion_url"])
        assert (utilities.number_extraction_from_string(
            sumo_pages.kb_article_discussion_page.get_article_discussions_thread_counter(
                thread_info['thread_id']))) == 1


# C2260840, C2260809
@pytest.mark.articleThreads
def test_thread_replies_counter_decrement(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(permissions=["review_revision"])
    test_user_two = create_user_factory(groups=["Forum Moderators"])

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)
        article_details = sumo_pages.submit_kb_article_flow.kb_article_creation_via_api(
            page=page, approve_revision=True)
        utilities.navigate_to_link(article_details["article_url"])

    with allure.step("Clicking on the 'Post a new thread button' and posting a new kb "
                     "article discussion thread"):
        thread_info = sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread()

    with allure.step("Posting a new reply with the same user"):
        thread_reply_info = sumo_pages.kb_article_thread_flow.post_reply_to_thread(
            utilities.kb_new_thread_test_data['thread_reply_body'])

    with allure.step(f"Signing in with {test_user_two['username']} user account"):
        utilities.start_existing_session(test_user_two)

    with allure.step("Posting a new reply with the same user and verifying that the reply counter"
                     " for the posted thread has incremented successfully"):
        sumo_pages.kb_article_thread_flow.post_reply_to_thread(
            utilities.kb_new_thread_test_data['thread_reply_body']
        )
        assert (utilities.number_extraction_from_string(
            sumo_pages.kb_article_discussion_page.get_thread_page_counter_replies_text()) == 2)

    with allure.step("Manually navigating to the discuss endpoint and verifying that the "
                     "reply counter for the posted thread has incremented successfully"):
        utilities.navigate_to_link(thread_info['article_discussion_url'])
        assert (utilities.number_extraction_from_string(
            sumo_pages.kb_article_discussion_page.get_article_discussions_thread_counter(
                thread_info['thread_id'])) == 2)

    with allure.step("Clicking on the 3 dotted menu for a posted thread reply"):
        sumo_pages.kb_article_discussion_page.click_on_a_particular_thread(
            thread_info['thread_id'])

    with allure.step("Clicking on the 'Delete this post' option and verifying that the reply"
                     " counter for the posted thread has incremented successfully"):
        sumo_pages.kb_article_thread_flow.delete_reply_to_thread(thread_reply_info['reply_id'])
        assert (utilities.number_extraction_from_string(
            sumo_pages.kb_article_discussion_page.get_thread_page_counter_replies_text()) == 1)

    with allure.step("Manually navigating to the discuss endpoint and verifying that the reply"
                     " counter for the posted thread has decremented successfully"):
        utilities.navigate_to_link(thread_info['article_discussion_url'])
        assert (utilities.number_extraction_from_string(
            sumo_pages.kb_article_discussion_page.get_article_discussions_thread_counter(
                thread_info['thread_id'])) == 1)


@pytest.mark.articleThreads
@pytest.mark.parametrize("user_type", ['Simple user', 'Forum Moderator', ''])
def test_article_thread_author_filter(page: Page, user_type, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["Forum Moderators"],
                                    permissions=["review_revision"])
    test_user_two = create_user_factory()

    with allure.step(f"Signing in with with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)
        article_details = sumo_pages.submit_kb_article_flow.kb_article_creation_via_api(
            page=page, approve_revision=True)
        utilities.navigate_to_link(article_details["article_url"])

    with allure.step("Posting a new kb article discussion thread"):
        thread_info = sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread()

    with allure.step("Navigating back to the article discussion page and signing in with a "
                     "non-admin account"):
        utilities.navigate_to_link(thread_info['article_discussion_url'])
        utilities.start_existing_session(cookies=test_user_two)

    with allure.step("Posting a new kb article discussion thread"):
        sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread()

    with allure.step("Navigating back to the article discussion page"):
        utilities.navigate_to_link(thread_info['article_discussion_url'])

    if user_type == 'Forum Moderator':
        with allure.step(f"Signing in with the {test_user['username']} user account"):
            utilities.start_existing_session(cookies=test_user)
    elif user_type != 'Simple user':
        with allure.step("Signing out from SUMO"):
            utilities.delete_cookies()

    with allure.step("Clicking on the 'Author' filter and verifying that the authors are in"
                     " reverse alphabetical order"):
        sumo_pages.kb_article_discussion_page.click_on_article_thread_author_replies_filter()
        assert sumo_pages.kb_article_discussion_page.get_all_article_threads_authors() != sorted(
            sumo_pages.kb_article_discussion_page.get_all_article_threads_authors())

    with allure.step("Clicking on the 'Author' filter again and verifying that the authors are"
                     " in alphabetical order"):
        sumo_pages.kb_article_discussion_page.click_on_article_thread_author_replies_filter()
        assert sumo_pages.kb_article_discussion_page.get_all_article_threads_authors() == sorted(
            sumo_pages.kb_article_discussion_page.get_all_article_threads_authors())


@pytest.mark.articleThreads
@pytest.mark.parametrize("user_type", ['Simple user', 'Forum Moderator', ''])
def test_article_thread_replies_filter(page: Page, user_type, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["Forum Moderators"],
                                    permissions=["review_revision"])
    test_user_two = create_user_factory()

    with allure.step(f"Signing in with the {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)
        article_details = sumo_pages.submit_kb_article_flow.kb_article_creation_via_api(
            page=page, approve_revision=True)
        utilities.navigate_to_link(article_details["article_url"])

    with allure.step("Clicking on the 'Post a new thread button' and posting a new kb "
                     "article discussion thread"):
        thread_info = sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread()

    with allure.step("Posting a new reply with the same user"):
        sumo_pages.kb_article_thread_flow.post_reply_to_thread(
            utilities.kb_new_thread_test_data['thread_reply_body']
        )

    with allure.step("Navigating back to the article discussion page and posting a new kb "
                     "article discussion thread"):
        sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread()

    with allure.step("Navigating back to the article discussion page"):
        utilities.navigate_to_link(thread_info['article_discussion_url'])

    if user_type == "Simple user":
        with allure.step(f"Signing in with the {test_user_two['username']} account"):
            utilities.start_existing_session(cookies=test_user_two)
    elif user_type == '':
        with allure.step("Deleting user session"):
            utilities.delete_cookies()

    with allure.step("Clicking on the 'Replies' filter and verifying that the replies is in "
                     "descending order"):
        sumo_pages.kb_article_discussion_page.click_on_article_thread_replies_filter()
        assert utilities.is_descending(
            sumo_pages.kb_article_discussion_page.get_all_article_threads_replies())

    with allure.step("Clicking on the 'Replies' filter again and verifying that the replies is in"
                     " ascending order"):
        sumo_pages.kb_article_discussion_page.click_on_article_thread_replies_filter()
        assert not utilities.is_descending(
            sumo_pages.kb_article_discussion_page.get_all_article_threads_replies())


@pytest.mark.articleThreads
def test_article_lock_thread_non_admin_users(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    test_user_two = create_user_factory(permissions=["review_revision"])

    with allure.step(f"Signing in with {test_user['username']} user account and creating a new"
                     f" article"):
        utilities.start_existing_session(cookies=test_user)
    article_details = sumo_pages.submit_kb_article_flow.kb_article_creation_via_api(page=page)

    with allure.step(f"Signing in with the {test_user_two['username']} user account and approving"
                     f" the article"):
        utilities.start_existing_session(cookies=test_user_two)
        sumo_pages.submit_kb_article_flow.approve_kb_revision(
            revision_id=article_details['first_revision_id']
        )

    with allure.step("Clicking on the 'Discussion' editing tools navbar option and posting a "
                     "new kb article discussion thread"):
        thread_info_one = sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread()

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Navigating back to the discussions page and posting a new kb article "
                     "discussion thread"):
        utilities.navigate_to_link(thread_info_one["article_discussion_url"])
        thread_info_two = sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread()

    with allure.step("Navigating back to the discussions page, clicking on the thread posted "
                     "by another user and verifying that the 'Lock thread' option is not "
                     "available"):
        utilities.navigate_to_link(thread_info_one["article_discussion_url"])
        sumo_pages.kb_article_discussion_page.click_on_a_particular_thread(
            thread_info_one['thread_id'])
        expect(sumo_pages.kb_article_discussion_page.get_lock_this_article_thread_locator()
               ).to_be_hidden()

    with allure.step("Navigating back to the article discussions page, clicking on the "
                     "thread posted by self and verifying that the 'Lock thread' option is "
                     "not available"):
        utilities.navigate_to_link(thread_info_one["article_discussion_url"])
        sumo_pages.kb_article_discussion_page.click_on_a_particular_thread(
            thread_info_two['thread_id'])
        expect(sumo_pages.kb_article_discussion_page.get_lock_this_article_thread_locator()
               ).to_be_hidden()

    with allure.step("Deleting user sessions and verifying that the 'Lock thread' options is "
                     "not available"):
        utilities.delete_cookies()
        expect(sumo_pages.kb_article_discussion_page.get_lock_this_article_thread_locator()
               ).to_be_hidden()


#  C2260810
@pytest.mark.articleThreads
@pytest.mark.parametrize("user_type", ['Forum Moderator', 'Simple user', ''])
def test_article_lock_thread_functionality(page: Page, user_type, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["Forum Moderators"],
                                    permissions=["review_revision"])
    test_user_two = create_user_factory()

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.submit_kb_article_flow.kb_article_creation_via_api(page=page,
                                                                      approve_revision=True)

    with allure.step("Posting a new kb article discussion thread"):
        thread_info_one = sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread()

    with allure.step(f"Signing in with {test_user_two['username']} user account"):
        utilities.start_existing_session(cookies=test_user_two)

    with allure.step("Navigating back to the discussions page and posting a new discussion "
                     "thread"):
        utilities.navigate_to_link(thread_info_one["article_discussion_url"])
        thread_info_two = sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread()

    with allure.step("Navigating back to the discussions page"):
        utilities.navigate_to_link(thread_info_one["article_discussion_url"])

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Clicking on the thread posted by self user and locking the thread"):
        sumo_pages.kb_article_discussion_page.click_on_a_particular_thread(
            thread_info_one['thread_id'])
        sumo_pages.kb_article_discussion_page.click_on_lock_this_article_thread_option()

    if user_type == 'Simple user':
        with allure.step("Signing in with a non-admin account and verifying that the correct"
                         " thread locked message is displayed"):
            utilities.start_existing_session(cookies=test_user_two)
            assert (sumo_pages.kb_article_discussion_page.get_text_of_locked_article_thread_text(
            ) == KBArticlePageMessages.KB_ARTICLE_LOCKED_THREAD_MESSAGE)

    elif user_type == '':
        with allure.step("Deleting user session"):
            utilities.delete_cookies()

    with allure.step("Verifying that the 'Post a reply' textarea field is not displayed"):
        expect(sumo_pages.kb_article_discussion_page.get_thread_post_a_reply_textarea_field()
               ).to_be_hidden()

    with allure.step("Verifying that the 'Locked' status is displayed under article header"):
        expect(sumo_pages.kb_article_discussion_page.get_locked_article_status()).to_be_visible()

    with allure.step("Navigating back to the discussions page"):
        utilities.navigate_to_link(thread_info_one["article_discussion_url"])

    if user_type != 'Forum Moderator':
        with allure.step("Signing in with an admin account"):
            utilities.start_existing_session(cookies=test_user)

    with allure.step("Clicking on the thread posted by the other user and clicking on the "
                     "'Lock this thread' option"):
        sumo_pages.kb_article_discussion_page.click_on_a_particular_thread(
            thread_info_two['thread_id'])
        sumo_pages.kb_article_discussion_page.click_on_lock_this_article_thread_option()

    if user_type == 'Simple user':
        with allure.step("Signing in with a non-admin account and verifying that the correct"
                         " thread locked message is displayed"):
            utilities.start_existing_session(cookies=test_user_two)
            assert (sumo_pages.kb_article_discussion_page.get_text_of_locked_article_thread_text(
            ) == KBArticlePageMessages.KB_ARTICLE_LOCKED_THREAD_MESSAGE)
    elif user_type == '':
        with allure.step("Deleting user session"):
            utilities.delete_cookies()

    with allure.step("Verifying that the 'Locked' status is displayed under article header"):
        expect(sumo_pages.kb_article_discussion_page.get_locked_article_status()).to_be_visible()

    with allure.step("Verifying that the 'Post a reply' textarea field is not displayed"):
        expect(sumo_pages.kb_article_discussion_page.get_thread_post_a_reply_textarea_field()
               ).to_be_hidden()


# C2260810
@pytest.mark.articleThreads
@pytest.mark.parametrize("user_type", ['Forum Moderator', 'Simple user', ''])
def test_article_unlock_thread_functionality(page: Page, user_type, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["Forum Moderators"],
                                    permissions=["review_revision"])
    test_user_two = create_user_factory()

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Navigating to the article endpoint"):
        sumo_pages.submit_kb_article_flow.kb_article_creation_via_api(page=page,
                                                                      approve_revision=True)

    with allure.step("Posting a new kb article discussion thread"):
        thread_info_one = sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread()

    with allure.step(f"Signing in with the {test_user_two['username']} user account"):
        utilities.start_existing_session(cookies=test_user_two)

    with allure.step("Navigating back to the discussions page"):
        utilities.navigate_to_link(thread_info_one["article_discussion_url"])

    with allure.step("Posting a new kb article discussion thread"):
        thread_info_two = sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread()

    with allure.step("Navigating back to the discussions page"):
        utilities.navigate_to_link(thread_info_one["article_discussion_url"])

    with allure.step(f"Signing in with the {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Clicking on the thread posted by self user and verifying that the correct"
                     " 'Lock this thread' option text is displayed"):
        sumo_pages.kb_article_discussion_page.click_on_a_particular_thread(
            thread_info_one['thread_id'])
        assert (sumo_pages.kb_article_discussion_page.get_lock_this_article_thread_option_text(
        ) == KBArticlePageMessages.KB_ARTICLE_LOCK_THIS_THREAD_OPTION)

    with allure.step("Clicking on 'Lock this thread' option and verifying that the correct"
                     " 'Unlock this thread' text is displayed"):
        sumo_pages.kb_article_discussion_page.click_on_lock_this_article_thread_option()
        assert (sumo_pages.kb_article_discussion_page.get_lock_this_article_thread_option_text(
        ) == KBArticlePageMessages.KB_ARTICLE_UNLOCK_THIS_THREAD_OPTION)

    if user_type == 'Simple user':
        with allure.step(f"Signing in with {test_user_two['username']} user account and verifying"
                         f" that the 'Unlock this thread' option is not displayed"):
            utilities.start_existing_session(cookies=test_user_two)
            expect(sumo_pages.kb_article_discussion_page.get_lock_this_article_thread_locator(
            )).to_be_hidden()
    if user_type == '':
        with allure.step("Deleting user session and verifying that the 'Unlock this thread' "
                         "option is no displayed"):
            utilities.delete_cookies()
            expect(sumo_pages.kb_article_discussion_page.get_lock_this_article_thread_locator(
            )).to_be_hidden()

    if user_type != 'Forum Moderator':
        with allure.step(f"Signing in with {test_user['username']} user account"):
            utilities.start_existing_session(cookies=test_user)

    with allure.step("Clicking on the 'Unlock this thread'"):
        sumo_pages.kb_article_discussion_page.click_on_lock_this_article_thread_option()

    if user_type == 'Simple user':
        with allure.step(f"Signing in with {test_user_two['username']} user account and verifying"
                         f" that the textarea field is available"):
            utilities.start_existing_session(cookies=test_user_two)
            expect(sumo_pages.kb_article_discussion_page.get_thread_post_a_reply_textarea_field(
            )).to_be_visible()
    if user_type == '':
        with allure.step("Deleting user session and verifying that the textarea field is not "
                         "available"):
            utilities.delete_cookies()
            expect(sumo_pages.kb_article_discussion_page.get_thread_post_a_reply_textarea_field(
            )).to_be_hidden()

    with allure.step("Verifying that the 'Locked' header text is not displayed"):
        expect(sumo_pages.kb_article_discussion_page.get_locked_article_status()).to_be_hidden()

    with allure.step("Verifying that the 'Thread locked' page message is not displayed"):
        expect(sumo_pages.kb_article_discussion_page.get_text_of_locked_article_thread_locator(
        )).to_be_hidden()

    if user_type != "Forum Moderator":
        with allure.step("Signing in with an admin account"):
            utilities.start_existing_session(cookies=test_user)

    with allure.step("Navigating back the article page and clicking on the thread posted by "
                     "another user"):
        utilities.navigate_to_link(thread_info_one["article_discussion_url"])
        sumo_pages.kb_article_discussion_page.click_on_a_particular_thread(
            thread_info_two['thread_id'])

    with allure.step("Verifying that the correct 'Lock this thread' option text is displayed"):
        assert (sumo_pages.kb_article_discussion_page.get_lock_this_article_thread_option_text(
        ) == KBArticlePageMessages.KB_ARTICLE_LOCK_THIS_THREAD_OPTION)

    with allure.step("Clicking on 'Lock this thread' option and verifying that the correct"
                     " 'Unlock this thread' text is displayed"):
        sumo_pages.kb_article_discussion_page.click_on_lock_this_article_thread_option()
        assert (sumo_pages.kb_article_discussion_page.get_lock_this_article_thread_option_text(
        ) == KBArticlePageMessages.KB_ARTICLE_UNLOCK_THIS_THREAD_OPTION)

    if user_type == 'Simple user':
        with allure.step(f"Signing in with {test_user_two['username']} user account and verifying"
                         f" that the 'Unlock this thread' option is displayed"):
            utilities.start_existing_session(cookies=test_user_two)
            expect(sumo_pages.kb_article_discussion_page.get_lock_this_article_thread_locator(
            )).to_be_hidden()
    if user_type == '':
        with allure.step("Deleting the user session and verifying that the 'Unlock this "
                         "thread' option is not displayed"):
            utilities.delete_cookies()
            expect(sumo_pages.kb_article_discussion_page.get_lock_this_article_thread_locator(
            )).to_be_hidden()

    if user_type != 'Forum Moderator':
        with allure.step(f"Signing in with {test_user['username']} user account and clicking on"
                         f" the 'Unlock this thread' option"):
            utilities.start_existing_session(cookies=test_user)
    sumo_pages.kb_article_discussion_page.click_on_lock_this_article_thread_option()

    if user_type == 'Simple user':
        with allure.step(f"Signing in with {test_user_two['username']} user account and verifying"
                         f" that the textarea field is available"):
            utilities.start_existing_session(cookies=test_user_two)
            expect(sumo_pages.kb_article_discussion_page.get_thread_post_a_reply_textarea_field(
            )).to_be_visible()
    if user_type == '':
        with allure.step("Deleting user session and verifying that the textarea field is not "
                         "available"):
            utilities.delete_cookies()
            expect(sumo_pages.kb_article_discussion_page.get_thread_post_a_reply_textarea_field(
            )).to_be_hidden()

    with allure.step("Verifying that the 'Locked' header text is not displayed"):
        expect(sumo_pages.kb_article_discussion_page.get_locked_article_status()).to_be_hidden()

    with allure.step("Verifying that the 'Thread locked' page message is not displayed"):
        expect(sumo_pages.kb_article_discussion_page.get_text_of_locked_article_thread_locator(
        )).to_be_hidden()


# C2260811
@pytest.mark.articleThreads
@pytest.mark.parametrize("user_type", ['Forum Moderator', 'Simple user', ''])
def test_article_thread_sticky(page: Page, user_type, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["Forum Moderators"],
                                    permissions=["review_revision"])
    test_user_two = create_user_factory()

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Posting a new kb article"):
        sumo_pages.submit_kb_article_flow.submit_simple_kb_article(approve_first_revision=True)

    with allure.step("Posting a new kb article discussion thread"):
        thread_info_one = sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread()

    with allure.step(f"Signing in with {test_user_two['username']} user account"):
        utilities.start_existing_session(cookies=test_user_two)

    with allure.step("Navigating back to the discussions page"):
        utilities.navigate_to_link(thread_info_one['article_discussion_url'])

    with allure.step("Posting a new kb article discussion thread"):
        thread_info_two = sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread(
            title='Other test thread'
        )

    with allure.step("Verifying that the 'Sticky this thread' option is not displayed"):
        expect(sumo_pages.kb_article_discussion_page.get_sticky_this_thread_locator()
               ).to_be_hidden()

    with allure.step("Navigating back to the discussions page"):
        utilities.navigate_to_link(thread_info_one['article_discussion_url'])

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Clicking on the thread posted by self and clicking on the 'sticky this "
                     "thread' option"):
        sumo_pages.kb_article_discussion_page.click_on_a_particular_thread(
            thread_info_one['thread_id'])
        sumo_pages.kb_article_discussion_page.click_on_sticky_this_thread_option()

    with allure.step("Verifying that the text changed to 'Unsticky this thread'"):
        assert (sumo_pages.kb_article_discussion_page.get_text_of_sticky_this_thread_option(
        ) == KBArticlePageMessages.KB_ARTICLE_UNSTICKY_OPTION)

    if user_type == 'Simple user':
        with allure.step(f"Signing in with {test_user_two['username']} user account and "
                         f"verifying that the unsticky this thread option is not available"):
            utilities.start_existing_session(cookies=test_user_two)
            expect(sumo_pages.kb_article_discussion_page.get_sticky_this_thread_locator()
                   ).to_be_hidden()
    if user_type == '':
        with allure.step("Deleting user session and verifying that the unsticky this thread "
                         "option is not available"):
            utilities.delete_cookies()
            expect(sumo_pages.kb_article_discussion_page.get_sticky_this_thread_locator()
                   ).to_be_hidden()

    with allure.step("Verifying that the 'Sticky' status is displayed"):
        expect(sumo_pages.kb_article_discussion_page.get_sticky_this_thread_status_locator()
               ).to_be_visible()

    with allure.step("Navigating back to the discussions page and verifying that the sticky "
                     "article is displayed in top of the list"):
        utilities.navigate_to_link(thread_info_one['article_discussion_url'])
        assert (
            sumo_pages.kb_article_discussion_page.
            get_all_article_threads_titles()[0] == thread_info_one['thread_title'])

    if user_type != 'Forum Moderator':
        with allure.step(f"Signing in with {test_user['username']} user account"):
            utilities.start_existing_session(cookies=test_user)

    with allure.step("Clicking on the unsitcky this thread and verifying that the text changed to"
                     " 'Sticky this thread'"):
        sumo_pages.kb_article_discussion_page.click_on_a_particular_thread(
            thread_info_one['thread_id'])
        sumo_pages.kb_article_discussion_page.click_on_sticky_this_thread_option()
        assert (sumo_pages.kb_article_discussion_page.get_text_of_sticky_this_thread_option(
        ) == KBArticlePageMessages.KB_ARTICLE_STICKY_THIS_THREAD_OPTION)

    if user_type == 'Simple user':
        with allure.step(f"Signing in with {test_user_two['username']} user account"):
            utilities.start_existing_session(cookies=test_user_two)
    if user_type == '':
        with allure.step("Deleting user session"):
            utilities.delete_cookies()

    with allure.step("Verifying that the 'Sticky' status is not displayed"):
        expect(sumo_pages.kb_article_discussion_page.get_sticky_this_thread_status_locator()
               ).to_be_hidden()

    with allure.step("Navigating back to the discussions page and verifying that the sticky"
                     " article is not displayed in top of the list"):
        utilities.navigate_to_link(thread_info_one['article_discussion_url'])
        assert sumo_pages.kb_article_discussion_page.get_all_article_threads_titles(
        )[0] == thread_info_two['thread_title']


#  C2260808, C2260823
@pytest.mark.articleThreads
@pytest.mark.parametrize("thread_author", ['self', 'other'])
def test_article_thread_content_edit(page: Page, thread_author, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["Forum Moderators"],
                                    permissions=["review_revision"])
    test_user_two = create_user_factory()

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Manually navigating to the article endpoint and posting a new kb "
                     "article discussion thread"):
        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            approve_first_revision=True)
        thread_info_one = sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread()

    with allure.step(f"Signing in with {test_user_two['username']} user account"):
        utilities.start_existing_session(cookies=test_user_two)

    with allure.step("Navigating back to the discussions page and posting a new kb article "
                     "discussion thread"):
        utilities.navigate_to_link(article_details["article_url"])
        thread_info_two = sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread()

    with allure.step("Adding data inside the edit this thread title field and clicking on "
                     "the cancel button"):
        sumo_pages.kb_article_thread_flow._edit_article_thread(
            thread_title=utilities.kb_new_thread_test_data['updated_thread_title'],
            submit_edit=False
        )

    with allure.step("Verifying that the thread title was not changed"):
        assert sumo_pages.kb_article_discussion_page.get_thread_title_text(
        ) == thread_info_two['thread_title']

    with allure.step("Adding data inside the edit this thread title field and clicking on "
                     "the update button"):
        sumo_pages.kb_article_thread_flow._edit_article_thread(
            thread_title=utilities.kb_new_thread_test_data['updated_thread_title']
        )

    with allure.step("Verifying that the thread title was changed"):
        assert sumo_pages.kb_article_discussion_page.get_thread_title_text(
        ) == utilities.kb_new_thread_test_data['updated_thread_title']

    with allure.step("Deleting user session and verifying that the edit this thread option "
                     "is not displayed"):
        utilities.delete_cookies()
        expect(sumo_pages.kb_article_discussion_page.get_edit_this_thread_locator()
               ).to_be_hidden()

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Navigating back to the discussions page"):
        utilities.navigate_to_link(thread_info_one["article_discussion_url"])

    if thread_author == 'self':
        with allure.step("Clicking on the self posted thread"):
            sumo_pages.kb_article_discussion_page.click_on_a_particular_thread(
                thread_info_one["thread_id"])
    else:
        with allure.step("Clicking on the other user posted thread"):
            sumo_pages.kb_article_discussion_page.click_on_a_particular_thread(
                thread_info_two["thread_id"])

    with allure.step("Clicking on the 'Edit this thread', adding data inside the title field "
                     "and clicking on the cancel button"):
        sumo_pages.kb_article_thread_flow._edit_article_thread(
            utilities.kb_new_thread_test_data['second_thread_updated_title'], False
        )

    if thread_author == 'self':
        with allure.step("Verifying that the thread title was not changed"):
            assert sumo_pages.kb_article_discussion_page.get_thread_title_text(
            ) == thread_info_one['thread_title']
    else:
        with allure.step("Verifying that the thread title was not changed"):
            assert sumo_pages.kb_article_discussion_page.get_thread_title_text(
            ) == utilities.kb_new_thread_test_data['updated_thread_title']

    with allure.step("Adding data inside the edit this thread title field and clicking on "
                     "the update button"):
        sumo_pages.kb_article_thread_flow._edit_article_thread(
            thread_title=utilities.kb_new_thread_test_data['second_thread_updated_title']
        )

    with allure.step("Verifying that the thread title was changed"):
        assert sumo_pages.kb_article_discussion_page.get_thread_title_text(
        ) == utilities.kb_new_thread_test_data['second_thread_updated_title']

    with allure.step("Navigating back to the discussions page"):
        utilities.navigate_to_link(thread_info_one["article_discussion_url"])

    with allure.step("Verifying that the updated thread title is displayed inside the threads"
                     " list"):
        assert (utilities.kb_new_thread_test_data
                ['second_thread_updated_title'] in sumo_pages.kb_article_discussion_page
                .get_all_article_threads_titles())
