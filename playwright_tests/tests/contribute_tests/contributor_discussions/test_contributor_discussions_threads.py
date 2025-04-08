from urllib.parse import urlsplit

import allure
import pytest
from playwright.sync_api import Page
from pytest_check import check
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.auth_pages_messages.fxa_page_messages import FxAPageMessages
from playwright_tests.messages.contribute_messages.con_discussions.off_topic import \
    OffTopicForumMessages
from playwright_tests.pages.sumo_pages import SumoPages


# C954250
@pytest.mark.contributorDiscussionsThreads
def test_new_thread_field_validations(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    valid_thread_title = "testt"

    with allure.step("Signing in with an moderator account and navigating to the Off Topic forum"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)

    with allure.step("Clicking on the 'Post a new thread' button"):
        sumo_pages.forum_discussions_page.click_on_new_thread_button()
        new_thread_page_url = utilities.get_page_url()

    with check, allure.step("Clicking on the 'Post Thread' button without filling the title and "
                            "body and verifying that we are still on the same page"):
        sumo_pages.new_thread_page.click_on_post_thread_button()
        check.equal(
            utilities.get_page_url(),
            new_thread_page_url
        )

    with check, allure.step("Adding text inside the title input field only, clicking on the "
                            "'Post Thread' button and verifying that we are still on the same "
                            "page"):
        sumo_pages.new_thread_page.fill_title_input_field(
            utilities.discussion_thread_data['thread_title'])

    with allure.step("Deleting the text inside the title input field"):
        sumo_pages.new_thread_page.clear_title_input_field()

    with check, allure.step("Adding text inside the body textarea only, clicking on the "
                            "'Post Thread' button and verifying that we are still on the same "
                            "page"):
        sumo_pages.new_thread_page.fill_content_textarea_field(
            utilities.discussion_thread_data['thread_body'])
        sumo_pages.new_thread_page.click_on_post_thread_button()
        check.equal(
            utilities.get_page_url(),
            new_thread_page_url
        )

    with allure.step("Deleting the text inside the body textarea"):
        sumo_pages.new_thread_page.clear_content_textarea_field()

    with check, allure.step("Adding < 5 characters inside both the title & body fields, "
                            "clicking on the 'Post Thread' button and verifying that we are still "
                            "on the same page"):
        sumo_pages.new_thread_page.fill_title_input_field("test")
        sumo_pages.new_thread_page.fill_content_textarea_field("test")
        sumo_pages.new_thread_page.click_on_post_thread_button()
        check.equal(
            utilities.get_page_url(),
            new_thread_page_url
        )

    sumo_pages.new_thread_page.clear_title_input_field()
    sumo_pages.new_thread_page.clear_content_textarea_field()

    with check, allure.step("Adding 5 characters inside the title field, < 5 inside the body,"
                            "clicking on the 'Post Thread' button and verifying that we are still"
                            " on the same page"):
        sumo_pages.new_thread_page.fill_title_input_field(valid_thread_title)
        sumo_pages.new_thread_page.fill_content_textarea_field("test")
        sumo_pages.new_thread_page.click_on_post_thread_button()

        check.equal(
            utilities.get_page_url(),
            new_thread_page_url
        )

    sumo_pages.new_thread_page.clear_content_textarea_field()

    with check, allure.step("Adding 5 characters in both the body & title fields, clicking on the "
                            "'Post Thread' button and verifying that we thread was submitted "
                            "successfully"):
        sumo_pages.new_thread_page.fill_title_input_field(valid_thread_title)
        sumo_pages.new_thread_page.fill_content_textarea_field("testt")
        sumo_pages.new_thread_page.click_on_post_thread_button()

        check.equal(
            valid_thread_title,
            sumo_pages.forum_thread_page.get_forum_thread_title()
        )

    with allure.step("Deleting the article"):
        sumo_pages.contributor_thread_flow.delete_thread()


# C954249
@pytest.mark.contributorDiscussionsThreads
def test_new_thread_creation_cancel_button(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    thread_title = (utilities.discussion_thread_data['thread_title'] + utilities.
                    generate_random_number(1, 1000))

    with allure.step("Signing in with a contributor account and navigating to the Off topic "
                     "forum"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)

    with allure.step("Adding valid data to both title and body fields and clicking on the 'Cancel'"
                     " button"):
        sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title=thread_title,
            thread_body=utilities.discussion_thread_data['thread_body'],
            cancel=True
        )

    with check, allure.step("Verifying that we are redirected to the Off topic forum page"):
        check.equal(
            utilities.get_page_url(),
            OffTopicForumMessages.PAGE_URL
        )

    with check, allure.step("Verifying that the thread title is not visible in the forum page"):
        check.is_false(sumo_pages.forum_discussions_page.is_thread_displayed(thread_title))


# C890980
@pytest.mark.contributorDiscussionsThreads
def test_thread_title_edit(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)

    with allure.step("Signing in with a contributor account and navigating to the Off topic"
                     "forum"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)

    with allure.step("Creating a new thread"):
        thread_title = (utilities.discussion_thread_data['thread_title'] + utilities.
                        generate_random_number(1, 1000))
        sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title=thread_title,
            thread_body=utilities.discussion_thread_data['thread_body']
        )

    thread_url = urlsplit(utilities.get_page_url())._replace(query="").geturl()

    with check, allure.step("Signing in with a different user and verifying that the 'Edit "
                            "Thread Title' option is not visible"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_13"]
        ))
        check.is_false(sumo_pages.forum_thread_page.is_edit_thread_title_option_visible())

    with check, allure.step("Navigating to the /edit page directly and verifying that a 403 is "
                            "returned"):
        with page.expect_navigation() as navigation_info:
            utilities.navigate_to_link(thread_url + "/edit")
        response = navigation_info.value
        assert response.status == 403

    with check, allure.step("Deleting the user session and verifying that the 'Edit Thread Title' "
                            "option is not visible"):
        utilities.delete_cookies()
        check.is_false(sumo_pages.forum_thread_page.is_edit_thread_title_option_visible())

    with check, allure.step("Navigating to the /edit page directly and verifying that the user is "
                            "redirected to the auth page"):
        utilities.navigate_to_link(thread_url + "/edit")
        check.is_in(
            FxAPageMessages.AUTH_PAGE_URL,
            utilities.get_page_url()
        )

    utilities.navigate_to_link(thread_url)
    new_thread_title = (utilities.discussion_thread_data['thread_title'] + utilities.
                        generate_random_number(1, 1000))
    with allure.step("Signing in with the original user and editing the title of the thread"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))
        sumo_pages.contributor_thread_flow.edit_thread_title(new_thread_title)

    with check, allure.step("Verifying that the new thread title is visible inside the thread "
                            "page"):
        check.equal(
            sumo_pages.forum_thread_page.get_forum_thread_title(),
            new_thread_title
        )

    with check, allure.step("Verifying that the new thread title is visible inside the forum "
                            "page for signed out users"):
        utilities.delete_cookies()
        check.equal(
            sumo_pages.forum_thread_page.get_forum_thread_title(),
            new_thread_title
        )

    with check, allure.step("Navigating to the forum thread listing page and verifying that the "
                            "newly updated thread title is displayed"):
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        check.is_true(sumo_pages.forum_discussions_page.is_thread_displayed(new_thread_title))

    with check, allure.step("Navigating back to the thread and editing the thread title using an "
                            "admin account and verifying that the changes are applied"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        utilities.navigate_to_link(thread_url)
        sumo_pages.contributor_thread_flow.edit_thread_title(thread_title)
        check.equal(
            sumo_pages.forum_thread_page.get_forum_thread_title(),
            thread_title
        )

    with check, allure.step("Signing out and verifying that the thread title is displayed "
                            "correctly in the thread page and the forum page"):
        utilities.delete_cookies()
        check.equal(
            sumo_pages.forum_thread_page.get_forum_thread_title(),
            thread_title
        )
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        check.is_true(sumo_pages.forum_discussions_page.is_thread_displayed(thread_title))

    utilities.navigate_to_link(thread_url)
    with allure.step("Deleting the article"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        sumo_pages.contributor_thread_flow.delete_thread()


# C890981
@pytest.mark.contributorDiscussionsThreads
def test_thread_deletion(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)

    with allure.step("Signing in with a contributor account and navigating to the Off topic"
                     "forum"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)

    with allure.step("Creating a new thread"):
        thread_title = (utilities.discussion_thread_data['thread_title'] + utilities.
                        generate_random_number(1, 1000))
        sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title=thread_title,
            thread_body=utilities.discussion_thread_data['thread_body']
        )

    thread_url = urlsplit(utilities.get_page_url())._replace(query="").geturl()

    with check, allure.step("Verifying that the delete thread option is not displayed"):
        check.is_false(sumo_pages.forum_thread_page.is_delete_thread_option_visible())

    with check, allure.step("Navigating to the /delete page and verifying that 403 is returned"):
        with page.expect_navigation() as navigation_info:
            utilities.navigate_to_link(thread_url + "/delete")
        response = navigation_info.value
        assert response.status == 403

    utilities.navigate_to_link(thread_url)

    with check, allure.step("Signing in with a different user and verifying that the delete "
                            "thread option is not visible"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_13"]
        ))
        check.is_false(sumo_pages.forum_thread_page.is_delete_thread_option_visible())

    with check, allure.step("Navigating to the /delete page and verifying that 403 is returned"):
        with page.expect_navigation() as navigation_info:
            utilities.navigate_to_link(thread_url + "/delete")
        response = navigation_info.value
        assert response.status == 403

    with allure.step("Signing in with an admin account and deleting the thread"):
        utilities.delete_cookies()
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        utilities.navigate_to_link(thread_url)
        sumo_pages.contributor_thread_flow.delete_thread()

    with allure.step("Navigating to the forum page and verifying that the thread is no longer "
                     "displayed"):
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        check.is_false(sumo_pages.forum_discussions_page.is_thread_displayed(thread_title))


# C890982
@pytest.mark.contributorDiscussionsThreads
def test_thread_locking(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)

    with allure.step("Signing in with a contributor and posting a new thread"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        thread_title = (utilities.discussion_thread_data['thread_title'] + utilities.
                        generate_random_number(1, 1000))
        sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title=thread_title,
            thread_body=utilities.discussion_thread_data['thread_body']
        )

    thread_url = utilities.get_page_url()

    with check, allure.step("Verifying that the 'Lock this thread' option is not displayed"):
        check.is_false(sumo_pages.forum_thread_page.is_lock_this_thread_option_visible())

    with check, allure.step("Signing in with a different user and verifying that the "
                            "'Lock this thread' option is not displayed"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_13"]
        ))
        check.is_false(sumo_pages.forum_thread_page.is_lock_this_thread_option_visible())

    with check, allure.step("Verifying that the 'Lock this thread' option is not displayed for "
                            "signed out users"):
        utilities.delete_cookies()
        check.is_false(sumo_pages.forum_thread_page.is_lock_this_thread_option_visible())

    with allure.step("Signing in with an admin account and locking the thread"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        sumo_pages.forum_thread_page.click_lock_this_thread_option()

    with check, allure.step("Verifying that the 'Lock this thread' option is no longer available "
                            "and the 'Unlock this thread' option is displayed"):
        check.is_false(sumo_pages.forum_thread_page.is_lock_this_thread_option_visible())
        check.is_true(sumo_pages.forum_thread_page.is_unlock_this_thread_option_visible())

    with check, allure.step("Verifying that the reply textarea is not displayed"):
        check.is_false(sumo_pages.forum_thread_page.is_reply_textarea_visible())

    with check, allure.step("Verifying that the 'Locked' information is displayed inside the "
                            "thread meta"):
        check.is_in(
            "Locked",
            sumo_pages.forum_thread_page.get_thread_meta_information()
        )

    with check, allure.step("Navigating to the forum page and verifying that the lock image is "
                            "displayed inside the threads table"):
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        check.is_true(sumo_pages.forum_discussions_page.is_thread_type_image_displayed(
            thread_title, "Locked"
        ))

    with allure.step("Navigating back to the thread, signing in with the op and verifying that "
                     "the 'Unlock this thread' option is not displayed"):
        utilities.navigate_to_link(thread_url)
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))
        check.is_false(sumo_pages.forum_thread_page.is_unlock_this_thread_option_visible())

    with allure.step("Signing in with an admin account and unlocking the thread"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        sumo_pages.forum_thread_page.click_unlock_this_thread_option()

    with check, allure.step("Verifying that the: "
                            "1. 'Unlock this thread' option is no longer available "
                            "2. 'Lock this thread' option is displayed "
                            "3. Reply textarea is displayed "
                            "4. 'Locked' information is not displayed inside the thread meta "
                            "5. Locked message is not displayed near the reply textarea"):
        check.is_false(sumo_pages.forum_thread_page.is_unlock_this_thread_option_visible())
        check.is_true(sumo_pages.forum_thread_page.is_lock_this_thread_option_visible())
        check.is_true(sumo_pages.forum_thread_page.is_reply_textarea_visible())
        check.is_false(sumo_pages.forum_thread_page.is_thread_locked_message_displayed())
        check.is_not_in(
            "Locked",
            sumo_pages.forum_thread_page.get_thread_meta_information()
        )
    with allure.step("Verifying that the lock image is not displayed inside the threads table"):
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        check.is_false(sumo_pages.forum_discussions_page.is_thread_type_image_displayed(
            thread_title, "Locked"
        ))

    with check, allure.step("Verifying that a reply can be posted after unlocking the thread"):
        utilities.navigate_to_link(thread_url)
        reply_id = sumo_pages.contributor_thread_flow.post_thread_reply(
            reply_body=utilities.discussion_thread_data['thread_reply_body']
        )
        check.is_true(sumo_pages.forum_thread_page.is_thread_post_visible(reply_id))

    with allure.step("Deleting the article"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        sumo_pages.contributor_thread_flow.delete_thread()


# C890983
@pytest.mark.contributorDiscussionsThreads
def test_sticky_this_thread(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)

    with allure.step("Signing in with a contributor and posting a new thread"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        thread_title = (utilities.discussion_thread_data['thread_title'] + utilities.
                        generate_random_number(1, 1000))
        sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title=thread_title,
            thread_body=utilities.discussion_thread_data['thread_body']
        )

    thread_link = utilities.get_page_url()

    with check, allure.step("Verifying that the 'Sticky this thread' option is not displayed"):
        check.is_false(sumo_pages.forum_thread_page.is_sticky_this_thread_option_visible())

    with check, allure.step("Signing in with a different user and verifying that the "
                            "'Sticky this thread' option is not displayed"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_13"]
        ))
        check.is_false(sumo_pages.forum_thread_page.is_sticky_this_thread_option_visible())

    with check, allure.step("Signing out and verifying that the 'Sticky this thread' option is "
                            "not displayed"):
        utilities.delete_cookies()
        check.is_false(sumo_pages.forum_thread_page.is_sticky_this_thread_option_visible())

    with allure.step("Signing in with the admin account and sticky the thread"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        sumo_pages.forum_thread_page.click_sticky_this_thread_option()

    with check, allure.step("Verifying that the 'Sticky this thread' option is no longer "
                            "available and the 'Unsticky this thread' option is displayed"):
        check.is_false(sumo_pages.forum_thread_page.is_sticky_this_thread_option_visible())
        check.is_true(sumo_pages.forum_thread_page.is_unsticky_this_thread_option_visible())

    with check, allure.step("Verifying that the 'Sticky' information is displayed inside the "
                            "thread meta"):
        check.is_in(
            "Sticky",
            sumo_pages.forum_thread_page.get_thread_meta_information()
        )

    with check, allure.step("Verifying that the sticky image is displayed inside the threads "
                            "table"):
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        check.is_true(sumo_pages.forum_discussions_page.is_thread_type_image_displayed(
            thread_title, "Sticky"
        ))

    with check, allure.step("Signing out and verifying that the sticky image is displayed inside "
                            "the threads table"):
        utilities.delete_cookies()
        check.is_true(sumo_pages.forum_discussions_page.is_thread_type_image_displayed(
            thread_title, "Sticky"
        ))

    with check, allure.step("Navigating to the thread and verifying that the Sticky text is "
                            "displayed inside the thread meta and the unsticky this thread option "
                            "is not displayed"):
        utilities.navigate_to_link(thread_link)
        check.is_in(
            "Sticky",
            sumo_pages.forum_thread_page.get_thread_meta_information()
        )
        check.is_false(sumo_pages.forum_thread_page.is_unsticky_this_thread_option_visible())

    with check, allure.step("Signing in with the op and verifying that the "
                            "'Unsticky this thread' option is not displayed"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))
        check.is_false(sumo_pages.forum_thread_page.is_unsticky_this_thread_option_visible())

    with check, allure.step("Signing in with the admin account, unsticking the thread and "
                            "verifying that the:"
                            "1. Unsticky this thread option is no longer available "
                            "2. Sticky this thread option is displayed "
                            "3. Sticky information is not displayed inside the thread meta "):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        sumo_pages.forum_thread_page.click_unsticky_this_thread_option()
        check.is_false(sumo_pages.forum_thread_page.is_unsticky_this_thread_option_visible())
        check.is_true(sumo_pages.forum_thread_page.is_sticky_this_thread_option_visible())
        check.is_false(sumo_pages.forum_discussions_page.is_thread_type_image_displayed(
            thread_title, "Sticky"
        ))

    with check, allure.step("Verifying that the sticky image is not displayed inside the threads "
                            "table"):
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        check.is_false(sumo_pages.forum_discussions_page.is_thread_type_image_displayed(
            thread_title, "Sticky"
        ))

    with allure.step("Deleting the thread"):
        utilities.navigate_to_link(thread_link)
        sumo_pages.contributor_thread_flow.delete_thread()
