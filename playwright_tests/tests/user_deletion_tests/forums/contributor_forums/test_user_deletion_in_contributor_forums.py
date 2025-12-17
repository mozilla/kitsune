import allure
import pytest
from playwright.sync_api import Page
from pytest_check import check
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.contribute_messages.con_discussions.off_topic import \
    OffTopicForumMessages
from playwright_tests.pages.sumo_pages import SumoPages


# C3132836
@pytest.mark.smokeTest
@pytest.mark.userDeletion
def test_thread_with_no_replies_is_not_assigned_to_system_user(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()

    with allure.step("Signing in and posting a new contributor forum thread"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title="Test op deletion", thread_body="Test op deletion thread body")
        thread_url = utilities.get_page_url()

    with allure.step("Deleting the user"):
        sumo_pages.edit_profile_flow.close_account()

    with allure.step("Navigating back to the thread and verifying that 404 is returned"):
        assert utilities.navigate_to_link(thread_url).status == 404


# C2955157
@pytest.mark.userDeletion
def test_locked_thread_with_no_replies_is_not_assigned_to_system_user(page: Page,
                                                                      create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(permissions=["lock_forum_thread"])

    with allure.step("Signing in to SUMO and posting a new contributor forum thread"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title="Test op deletion", thread_body="Test op deletion thread body")
        thread_url = utilities.get_page_url()

    with allure.step("Locking the forum thread"):
        sumo_pages.forum_thread_page.click_lock_this_thread_option()

    with allure.step("Deleting the account and verifying that the contributor thread is deleted"):
        sumo_pages.edit_profile_flow.close_account()
        assert utilities.navigate_to_link(thread_url).status == 404


#  C2955157
@pytest.mark.userDeletion
def test_sticky_thread_with_no_replies_is_not_assigned_to_system_user(page:Page,
                                                                      create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(permissions=["sticky_forum_thread"])

    with allure.step("Signing in to SUMO and posting a new contributor forum thread"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title="Test op deletion", thread_body="Test op deletion thread body")
        thread_url = utilities.get_page_url()

    with allure.step("Marking the thread as sticky"):
        sumo_pages.forum_thread_page.click_sticky_this_thread_option()

    with allure.step("Deleting the account and verifying that the contributor thread is deleted"):
        sumo_pages.edit_profile_flow.close_account()
        assert utilities.navigate_to_link(thread_url).status == 404


# C2960034
@pytest.mark.userDeletion
def test_edited_thread_with_no_replies_is_not_assigned_to_system_user(page: Page,
                                                                      create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["forum-contributors", "Forum Moderators"])

    with allure.step("Signing in to SUMO and posting a new contributor forum thread"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        thread_id = sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title="Test op deletion", thread_body="Test op deletion thread body")
        thread_url = utilities.get_page_url()

    with allure.step("Editing the title and first post"):
        new_thread_title = (utilities.discussion_thread_data['thread_title'] + utilities.
                            generate_random_number(1, 1000))
        sumo_pages.contributor_thread_flow.edit_thread_title(new_thread_title)
        sumo_pages.contributor_thread_flow.edit_thread_post(thread_id, "Edited thread body")

    with allure.step("Deleting the account and verifying that the contributor thread is deleted"):
        sumo_pages.edit_profile_flow.close_account()
        assert utilities.navigate_to_link(thread_url).status == 404


# C2955157
@pytest.mark.userDeletion
def test_deleting_the_user_which_locked_the_thread(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    test_user_two = create_user_factory(groups=["forum-contributors", "Forum Moderators"])
    test_user_three = create_user_factory(groups=["forum-contributors", "Forum Moderators"])

    with allure.step("Signing in to SUMO and posting a new contributor forum thread"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        thread = sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title="Test op deletion", thread_body="Test op deletion thread body")
        thread_url = utilities.get_page_url()

    with allure.step("Locking the thread using a forum moderator account"):
        utilities.start_existing_session(cookies=test_user_two)
        sumo_pages.forum_thread_page.click_lock_this_thread_option()

    with allure.step("Deleting the forum moderator account and verifying that the thread was "
                     "not affected by this deletion"):
        sumo_pages.edit_profile_flow.close_account()
        utilities.navigate_to_link(thread_url)
        assert "Locked" in sumo_pages.forum_thread_page.get_thread_meta_information()
        assert sumo_pages.forum_thread_page.get_post_author(thread) == test_user["username"]

    with allure.step("Unlocking the thread using a forum moderator account"):
        utilities.start_existing_session(cookies=test_user_three)
        sumo_pages.forum_thread_page.click_unlock_this_thread_option()

    with allure.step("Deleting the forum moderator account and verifying that the thread was not "
                     "affected by this deletion"):
        sumo_pages.edit_profile_flow.close_account()
        utilities.navigate_to_link(thread_url)
        assert not "Locked" in sumo_pages.forum_thread_page.get_thread_meta_information()
        assert sumo_pages.forum_thread_page.get_post_author(thread) == test_user["username"]


# C2955157
@pytest.mark.userDeletion
def test_deleting_the_user_which_stickied_the_thread(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    test_user_two = create_user_factory(groups=["forum-contributors", "Forum Moderators"])
    test_user_three = create_user_factory(groups=["forum-contributors", "Forum Moderators"])

    with allure.step("Signing in to SUMO and posting a new contributor forum thread"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        thread = sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title="Test op deletion", thread_body="Test op deletion thread body")
        thread_url = utilities.get_page_url()

    with allure.step("Sticking the thread using a forum moderator account"):
        utilities.start_existing_session(cookies=test_user_two)
        sumo_pages.forum_thread_page.click_sticky_this_thread_option()

    with allure.step("Deleting the forum moderator account and verifying that the thread was "
                     "not affected by this deletion"):
        sumo_pages.edit_profile_flow.close_account()
        utilities.navigate_to_link(thread_url)
        assert "Sticky" in sumo_pages.forum_thread_page.get_thread_meta_information()
        assert sumo_pages.forum_thread_page.get_post_author(thread) == test_user["username"]

    with allure.step("Unsticking the thread using a different forum moderator"):
        utilities.start_existing_session(cookies=test_user_three)
        sumo_pages.forum_thread_page.click_unsticky_this_thread_option()

    with allure.step("Deleting the forum moderator account and verifying that the thread was not "
                     "affected by this deletion"):
        sumo_pages.edit_profile_flow.close_account()
        utilities.navigate_to_link(thread_url)
        assert not "Sticky" in sumo_pages.forum_thread_page.get_thread_meta_information()
        assert sumo_pages.forum_thread_page.get_post_author(thread) == test_user["username"]


# C2952067
@pytest.mark.userDeletion
def test_edited_threads_are_assigned_successfully_to_system_account(page: Page,
                                                                    create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["forum-contributors", "Forum Moderators"])
    test_user_two = create_user_factory()

    with allure.step("Signing in to SUMO and posting a new contributor forum thread"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title="Test op deletion", thread_body="Test op deletion thread body")
        thread_url = utilities.get_page_url()


    with allure.step("Posting a new thread reply using a different account"):
        utilities.start_existing_session(cookies=test_user_two)
        thread_reply_id = sumo_pages.contributor_thread_flow.post_thread_reply("Test Reply")


    with allure.step("Signing in back with the first user and editing the second thread post"):
        utilities.start_existing_session(cookies=test_user)
        new_thread_body = "Edited thread body"
        sumo_pages.contributor_thread_flow.edit_thread_post(thread_reply_id, new_thread_body)

    with check, allure.step("Deleting the second user and verifying that: "
                            "1. The edited thread reply body is kept"
                            "2. The edited thread reply is assigned to SuMo bot "
                            "3. The editor is successfully displayed inside the 'Modified by "
                            "section'"):
        utilities.start_existing_session(cookies=test_user_two)
        sumo_pages.edit_profile_flow.close_account()
        utilities.navigate_to_link(thread_url)

        assert sumo_pages.forum_thread_page.get_post_content(thread_reply_id) == new_thread_body
        assert (sumo_pages.forum_thread_page.get_post_author(thread_reply_id) == utilities.
                general_test_data["system_account_name"])
        assert (test_user["username"] in sumo_pages.forum_thread_page.
                get_modified_by_text(thread_reply_id))


# C2952066
@pytest.mark.userDeletion
def test_deleting_the_user_which_edited_a_thread(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    test_user_two = create_user_factory(groups=["forum-contributors", "Forum Moderators"])

    with allure.step("Signing in to SUMO and posting a new contributor forum thread"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        thread_id = sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title="Test op deletion", thread_body="Test op deletion thread body")
        thread_url = utilities.get_page_url()

    with allure.step("Signing in with a forum moderator and editing the title and the body of the"
                     " forum post"):
        utilities.start_existing_session(cookies=test_user_two)
        new_thread_title = (utilities.discussion_thread_data['thread_title'] + utilities.
                            generate_random_number(1, 1000))
        new_thread_body = "Edited thread body"
        sumo_pages.contributor_thread_flow.edit_thread_title(new_thread_title)
        sumo_pages.contributor_thread_flow.edit_thread_post(
            thread_id, new_thread_body)

    with check, allure.step("Deleting the forum moderator and verifying that: "
                            "1. The thread title edit is kept. "
                            "2. The thread body edit is kept. "
                            "3. The modified by section is removed."):
        utilities.start_existing_session(cookies=test_user_two)
        sumo_pages.edit_profile_flow.close_account()
        utilities.navigate_to_link(thread_url)

        assert sumo_pages.forum_thread_page.get_forum_thread_title() == new_thread_title
        assert sumo_pages.forum_thread_page.get_post_content(thread_id) == new_thread_body
        assert not sumo_pages.forum_thread_page.is_modified_by_section_displayed(thread_id)


# C2939461
@pytest.mark.smokeTest
@pytest.mark.userDeletion
def test_threads_are_assigned_to_system_account_if_contains_additional_posts(page: Page,
                                                                             create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    test_user_two = create_user_factory()
    staff_user = utilities.username_extraction_from_email(utilities.staff_user)

    with allure.step("Signing in to SUMO and posting a new contributor forum thread"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        thread = sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title="Test op deletion", thread_body="Test op deletion thread body")
        thread_url = utilities.get_page_url()

    with allure.step("Posting a new thread reply using a different account"):
        utilities.start_existing_session(cookies=test_user_two)
        thread_reply_id = sumo_pages.contributor_thread_flow.post_thread_reply("Test Reply")

    with check, allure.step("Deleting the OP of the forum post and verifying that: "
                            "1. The first forum post is assigned to Sumo Bot "
                            "2. The second forum post remains assigned to the second user"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.edit_profile_flow.close_account()
        utilities.navigate_to_link(thread_url)

        assert (sumo_pages.forum_thread_page.get_post_author(thread) == utilities.
                general_test_data["system_account_name"])
        assert (sumo_pages.forum_thread_page.
                get_post_author(thread_reply_id) == test_user_two["username"])

        with allure.step("Deleting the thread"):
            utilities.start_existing_session(session_file_name=staff_user)
            sumo_pages.contributor_thread_flow.delete_thread()


# C2939461
@pytest.mark.smokeTest
@pytest.mark.userDeletion
def test_thread_replies_are_assigned_to_system_account(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    test_user_two = create_user_factory()
    staff_user = utilities.username_extraction_from_email(utilities.staff_user)
    thread_title = "Test thread " + utilities.generate_random_number(1, 1000)

    with allure.step("Signing in to SUMO and posting a new contributor forum thread"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        thread = sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title=thread_title, thread_body="Test op deletion thread body")
        thread_url = utilities.get_page_url()

    with allure.step("Posting a new thread reply using a different account"):
        utilities.start_existing_session(cookies=test_user_two)
        thread_reply_id = sumo_pages.contributor_thread_flow.post_thread_reply("Test Reply")

    with check, allure.step("Deleting the second user and verifying that: "
                            "1. The first forum post remains assigned to the first user, "
                            "2. The second forum post is assigned to SumoBot."
                            "3. Verifying that the 'Last Post' from the targeted forum/thread "
                            "shows SumoBot."):
        sumo_pages.edit_profile_flow.close_account()
        utilities.navigate_to_link(thread_url)

        assert (sumo_pages.forum_thread_page.
                get_post_author(thread) == test_user["username"])
        assert (sumo_pages.forum_thread_page.get_post_author(thread_reply_id) == utilities.
                general_test_data["system_account_name"])

        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        assert (sumo_pages.forum_discussions_page.get_last_post_by_text(thread_title) == utilities.
                general_test_data["system_account_name"])

        with allure.step("Deleting the thread"):
            utilities.start_existing_session(session_file_name=staff_user)
            utilities.navigate_to_link(thread_url)
            sumo_pages.contributor_thread_flow.delete_thread()


# C2947499
@pytest.mark.userDeletion
def test_quoted_first_post_is_moved_to_system_account(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    test_user_two = create_user_factory()
    thread_title = "Test thread " + utilities.generate_random_number(1, 1000)
    staff_user = utilities.username_extraction_from_email(utilities.staff_user)

    with allure.step("Signing in to SUMO and posting a new contributor forum thread"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        thread = sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title=thread_title, thread_body="Test op deletion thread body")
        thread_url = utilities.get_page_url()

    with allure.step("Posting a new thread reply with a different user by quoting the original "
                     "post."):
        utilities.start_existing_session(cookies=test_user_two)
        thread_reply_id = sumo_pages.contributor_thread_flow.quote_thread_post(thread)

    with check, allure.step("Deleting the second user and verifying that: "
                            "1. The first forum post remains assigned to the first user, "
                            "2. The second forum post is assigned to SumoBot."
                            "3. The user one is displayed inside the quoted field"):
        sumo_pages.edit_profile_flow.close_account()
        utilities.navigate_to_link(thread_url)

        assert (sumo_pages.forum_thread_page.
                get_post_author(thread) == test_user["username"])
        assert (sumo_pages.forum_thread_page.get_post_author(thread_reply_id) == utilities.
                general_test_data["system_account_name"])
        assert (test_user["username"] in sumo_pages.forum_thread_page.
                get_thread_post_mention_text(thread_reply_id))

    with allure.step("Deleting the thread"):
        utilities.start_existing_session(session_file_name=staff_user)
        sumo_pages.contributor_thread_flow.delete_thread()


# C2952021
@pytest.mark.userDeletion
def test_quoted_replies_are_moved_to_system_account(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    test_user_two = create_user_factory()
    staff_user = utilities.username_extraction_from_email(utilities.staff_user)
    thread_title = "Test thread " + utilities.generate_random_number(1, 1000)

    with allure.step("Signing in to SUMO and posting a new contributor forum thread"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        thread = sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title=thread_title, thread_body="Test op deletion thread body")
        thread_url = utilities.get_page_url()

    with allure.step("Posting a new thread reply with a different user"):
        utilities.start_existing_session(cookies=test_user_two)
        second_thread_reply = sumo_pages.contributor_thread_flow.post_thread_reply("Just a reply")

    with allure.step("Signing back with the first user and leaving a new thread reply by quoting "
                     "the thread reply posted by the second user"):
        utilities.start_existing_session(cookies=test_user)
        third_thread_reply = sumo_pages.contributor_thread_flow.quote_thread_post(
            second_thread_reply)

    with check, allure.step("Deleting the second user and verifying that: "
                            "1. The first forum post remains assigned to the first user, "
                            "2. The second forum post is assigned to SumoBot."
                            "3. The reply which quotes the second reply belongs to the first user "
                            "4. The reply which quotes the second reply contains the username of  "
                            "the deleted user inside the mention section"):
        utilities.start_existing_session(cookies=test_user_two)
        sumo_pages.edit_profile_flow.close_account()
        utilities.navigate_to_link(thread_url)

        assert (sumo_pages.forum_thread_page.
                get_post_author(thread) == test_user["username"])
        assert (sumo_pages.forum_thread_page.get_post_author(second_thread_reply) == utilities.
                general_test_data["system_account_name"])
        assert (sumo_pages.forum_thread_page.
                get_post_author(third_thread_reply) == test_user["username"])

        # Currently we are showing the username of the deleted user. This might change in the
        # future.
        assert (test_user_two["username"] in sumo_pages.forum_thread_page.
                get_thread_post_mention_text(third_thread_reply))

    with allure.step("Deleting the thread"):
        utilities.start_existing_session(session_file_name=staff_user)
        sumo_pages.contributor_thread_flow.delete_thread()
