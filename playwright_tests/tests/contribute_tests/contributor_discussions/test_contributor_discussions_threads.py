from urllib.parse import urlsplit
import allure
import pytest
from playwright.sync_api import Page, expect
from pytest_check import check
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.auth_pages_messages.fxa_page_messages import FxAPageMessages
from playwright_tests.messages.contribute_messages.con_discussions.off_topic import \
    OffTopicForumMessages
from playwright_tests.messages.homepage_messages import HomepageMessages
from playwright_tests.messages.mess_system_pages_messages.sent_messages_page_messages import \
    SentMessagesPageMessages
from playwright_tests.pages.sumo_pages import SumoPages


# C954250
@pytest.mark.smokeTest
@pytest.mark.contributorDiscussionsThreads
def test_new_thread_field_validations(page: Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    valid_thread_title = "testt"
    test_user = create_user_factory(groups=["forum-contributors"])

    with allure.step("Signing in with an moderator account and navigating to the Off Topic forum"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)

    with allure.step("Clicking on the 'Post a new thread' button"):
        sumo_pages.forum_discussions_page.click_on_new_thread_button()
        new_thread_page_url = utilities.get_page_url()

    with check, allure.step("Clicking on the 'Post Thread' button without filling the title and "
                            "body and verifying that we are still on the same page"):
        sumo_pages.new_thread_page.click_on_post_thread_button()
        assert utilities.get_page_url() == new_thread_page_url

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
        assert utilities.get_page_url() == new_thread_page_url

    with allure.step("Deleting the text inside the body textarea"):
        sumo_pages.new_thread_page.clear_content_textarea_field()

    with check, allure.step("Adding < 5 characters inside both the title & body fields, "
                            "clicking on the 'Post Thread' button and verifying that we are still "
                            "on the same page"):
        sumo_pages.new_thread_page.fill_title_input_field("test")
        sumo_pages.new_thread_page.fill_content_textarea_field("test")
        sumo_pages.new_thread_page.click_on_post_thread_button()
        assert utilities.get_page_url() == new_thread_page_url

    sumo_pages.new_thread_page.clear_title_input_field()
    sumo_pages.new_thread_page.clear_content_textarea_field()

    with check, allure.step("Adding 5 characters inside the title field, < 5 inside the body,"
                            "clicking on the 'Post Thread' button and verifying that we are still"
                            " on the same page"):
        sumo_pages.new_thread_page.fill_title_input_field(valid_thread_title)
        sumo_pages.new_thread_page.fill_content_textarea_field("test")
        sumo_pages.new_thread_page.click_on_post_thread_button()

        assert utilities.get_page_url() == new_thread_page_url

    sumo_pages.new_thread_page.clear_content_textarea_field()

    with check, allure.step("Adding 5 characters in both the body & title fields, clicking on the "
                            "'Post Thread' button and verifying that we thread was submitted "
                            "successfully"):
        sumo_pages.new_thread_page.fill_title_input_field(valid_thread_title)
        sumo_pages.new_thread_page.fill_content_textarea_field("testt")
        sumo_pages.new_thread_page.click_on_post_thread_button()

        assert valid_thread_title == sumo_pages.forum_thread_page.get_forum_thread_title()


# C954249
@pytest.mark.contributorDiscussionsThreads
def test_new_thread_creation_cancel_button(page: Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    thread_title = (utilities.discussion_thread_data['thread_title'] + utilities.
                    generate_random_number(1, 1000))
    test_user = create_user_factory(groups=["forum-contributors"])

    with allure.step("Signing in with a contributor account and navigating to the Off topic "
                     "forum"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)

    with allure.step("Adding valid data to both title and body fields and clicking on the 'Cancel'"
                     " button"):
        sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title=thread_title,
            thread_body=utilities.discussion_thread_data['thread_body'],
            cancel=True
        )

    with check, allure.step("Verifying that we are redirected to the Off topic forum page"):
        assert utilities.get_page_url() == OffTopicForumMessages.PAGE_URL

    with check, allure.step("Verifying that the thread title is not visible in the forum page"):
        assert not sumo_pages.forum_discussions_page.is_thread_displayed(thread_title)


# C890980
@pytest.mark.contributorDiscussionsThreads
def test_thread_title_edit(page: Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(groups=["forum-contributors"])
    test_user_two = create_user_factory(groups=["forum-contributors"])
    test_user_three = create_user_factory(permissions=["edit_forum_thread"])

    with allure.step("Signing in with a contributor account and navigating to the Off topic"
                     "forum"):
        utilities.start_existing_session(cookies=test_user)
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
        utilities.start_existing_session(cookies=test_user_two)
        assert not sumo_pages.forum_thread_page.is_edit_thread_title_option_visible()

    with check, allure.step("Navigating to the /edit page directly and verifying that a 403 is "
                            "returned"):
        with page.expect_navigation() as navigation_info:
            utilities.navigate_to_link(thread_url + "/edit")
        response = navigation_info.value
        assert response.status == 403

    with check, allure.step("Deleting the user session and verifying that the 'Edit Thread Title' "
                            "option is not visible"):
        utilities.delete_cookies()
        assert not sumo_pages.forum_thread_page.is_edit_thread_title_option_visible()

    with check, allure.step("Navigating to the /edit page directly and verifying that the user is "
                            "redirected to the auth page"):
        utilities.navigate_to_link(thread_url + "/edit")
        assert FxAPageMessages.AUTH_PAGE_URL in utilities.get_page_url()

    utilities.navigate_to_link(thread_url)
    new_thread_title = (utilities.discussion_thread_data['thread_title'] + utilities.
                        generate_random_number(1, 1000))
    with allure.step("Signing in with the original user and editing the title of the thread"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.contributor_thread_flow.edit_thread_title(new_thread_title)

    with check, allure.step("Verifying that the new thread title is visible inside the thread "
                            "page"):
        assert sumo_pages.forum_thread_page.get_forum_thread_title() == new_thread_title

    with check, allure.step("Verifying that the new thread title is visible inside the forum "
                            "page for signed out users"):
        utilities.delete_cookies()
        assert sumo_pages.forum_thread_page.get_forum_thread_title() == new_thread_title

    with check, allure.step("Navigating to the forum thread listing page and verifying that the "
                            "newly updated thread title is displayed"):
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        assert sumo_pages.forum_discussions_page.is_thread_displayed(new_thread_title)

    with check, allure.step("Navigating back to the thread and editing the thread title using an "
                            "admin account and verifying that the changes are applied"):
        utilities.start_existing_session(cookies=test_user_three)
        utilities.navigate_to_link(thread_url)
        sumo_pages.contributor_thread_flow.edit_thread_title(thread_title)
        assert sumo_pages.forum_thread_page.get_forum_thread_title() == thread_title

    with check, allure.step("Signing out and verifying that the thread title is displayed "
                            "correctly in the thread page and the forum page"):
        utilities.delete_cookies()
        assert sumo_pages.forum_thread_page.get_forum_thread_title() == thread_title

        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        assert sumo_pages.forum_discussions_page.is_thread_displayed(thread_title)


# C890981
@pytest.mark.contributorDiscussionsThreads
def test_thread_deletion(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    test_user_two = create_user_factory(groups=["forum-contributors"])
    test_user_three = create_user_factory(groups=["forum-contributors"],
                                          permissions=["delete_forum_thread"])

    with allure.step("Signing in with a contributor account and navigating to the Off topic"
                     "forum"):
        utilities.start_existing_session(cookies=test_user)
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
        assert not sumo_pages.forum_thread_page.is_delete_thread_option_visible()

    with check, allure.step("Navigating to the /delete page and verifying that 403 is returned"):
        with page.expect_navigation() as navigation_info:
            utilities.navigate_to_link(thread_url + "/delete")
        response = navigation_info.value
        assert response.status == 403

    utilities.navigate_to_link(thread_url)

    with check, allure.step("Signing in with a different user and verifying that the delete "
                            "thread option is not visible"):
        utilities.start_existing_session(cookies=test_user_two)
        assert not sumo_pages.forum_thread_page.is_delete_thread_option_visible()

    with check, allure.step("Navigating to the /delete page and verifying that 403 is returned"):
        with page.expect_navigation() as navigation_info:
            utilities.navigate_to_link(thread_url + "/delete")
        response = navigation_info.value
        assert response.status == 403

    with allure.step("Signing in with a user that has the permissions of deleting the thread"):
        utilities.delete_cookies()
        utilities.start_existing_session(cookies=test_user_three)
        utilities.navigate_to_link(thread_url)
        sumo_pages.contributor_thread_flow.delete_thread()

    with allure.step("Navigating to the forum page and verifying that the thread is no longer "
                     "displayed"):
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        assert not sumo_pages.forum_discussions_page.is_thread_displayed(thread_title)


# C890982
@pytest.mark.contributorDiscussionsThreads
def test_thread_locking(page: Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(groups=["forum-contributors"])
    test_user_two = create_user_factory(groups=["forum-contributors"])
    test_user_three = create_user_factory(groups=["forum-contributors"],
                                          permissions=["lock_forum_thread"])

    with allure.step("Signing in with a contributor and posting a new thread"):
        utilities.start_existing_session(cookies=test_user)

        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        thread_title = (utilities.discussion_thread_data['thread_title'] + utilities.
                        generate_random_number(1, 1000))
        sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title=thread_title,
            thread_body=utilities.discussion_thread_data['thread_body']
        )

    thread_url = utilities.get_page_url()

    with check, allure.step("Verifying that the 'Lock this thread' option is not displayed"):
        assert not sumo_pages.forum_thread_page.is_lock_this_thread_option_visible()

    with check, allure.step("Signing in with a different user and verifying that the "
                            "'Lock this thread' option is not displayed"):
        utilities.start_existing_session(cookies=test_user_two)
        assert not sumo_pages.forum_thread_page.is_lock_this_thread_option_visible()

    with check, allure.step("Verifying that the 'Lock this thread' option is not displayed for "
                            "signed out users"):
        utilities.delete_cookies()
        assert not sumo_pages.forum_thread_page.is_lock_this_thread_option_visible()

    with allure.step("Signing in with a user that has the necessary permissions to lock a thread"):
        utilities.start_existing_session(cookies=test_user_three)
        sumo_pages.forum_thread_page.click_lock_this_thread_option()

    with check, allure.step("Verifying that the 'Lock this thread' option is no longer available "
                            "and the 'Unlock this thread' option is displayed"):
        assert not sumo_pages.forum_thread_page.is_lock_this_thread_option_visible()
        assert sumo_pages.forum_thread_page.is_unlock_this_thread_option_visible()

    with check, allure.step("Verifying that the reply textarea is not displayed"):
        assert not sumo_pages.forum_thread_page.is_reply_textarea_visible()

    with check, allure.step("Verifying that the 'Locked' information is displayed inside the "
                            "thread meta"):
        assert "Locked" in sumo_pages.forum_thread_page.get_thread_meta_information()

    with check, allure.step("Navigating to the forum page and verifying that the lock image is "
                            "displayed inside the threads table"):
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        assert (sumo_pages.forum_discussions_page.
                is_thread_type_image_displayed(thread_title, "Locked"))

    with allure.step("Navigating back to the thread, signing in with the op and verifying that "
                     "the 'Unlock this thread' option is not displayed"):
        utilities.navigate_to_link(thread_url)
        utilities.start_existing_session(cookies=test_user)
        assert not sumo_pages.forum_thread_page.is_unlock_this_thread_option_visible()

    with allure.step("Signing in with a user that has the permissions of unlocking the thread"):
        utilities.start_existing_session(cookies=test_user_three)
        sumo_pages.forum_thread_page.click_unlock_this_thread_option()

    with check, allure.step("Verifying that the: "
                            "1. 'Unlock this thread' option is no longer available "
                            "2. 'Lock this thread' option is displayed "
                            "3. Reply textarea is displayed "
                            "4. 'Locked' information is not displayed inside the thread meta "
                            "5. Locked message is not displayed near the reply textarea"):
        assert not sumo_pages.forum_thread_page.is_unlock_this_thread_option_visible()
        assert sumo_pages.forum_thread_page.is_lock_this_thread_option_visible()
        assert sumo_pages.forum_thread_page.is_reply_textarea_visible()
        assert not sumo_pages.forum_thread_page.is_thread_locked_message_displayed()
        assert "Locked" not in sumo_pages.forum_thread_page.get_thread_meta_information()

    with allure.step("Verifying that the lock image is not displayed inside the threads table"):
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        assert not (sumo_pages.forum_discussions_page.
                    is_thread_type_image_displayed(thread_title, "Locked"))

    with check, allure.step("Verifying that a reply can be posted after unlocking the thread"):
        utilities.navigate_to_link(thread_url)
        reply_id = sumo_pages.contributor_thread_flow.post_thread_reply(
            reply_body=utilities.discussion_thread_data['thread_reply_body']
        )
        assert sumo_pages.forum_thread_page.is_thread_post_visible(reply_id)


# C890983
@pytest.mark.contributorDiscussionsThreads
def test_sticky_this_thread(page: Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(groups=["forum-contributors"])
    test_user_two = create_user_factory(groups=["forum-contributors"])
    test_user_three = create_user_factory(groups=["forum-contributors"],
                                          permissions=["sticky_forum_thread"])

    with allure.step("Signing in with a contributor and posting a new thread"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        thread_title = (utilities.discussion_thread_data['thread_title'] + utilities.
                        generate_random_number(1, 1000))
        sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title=thread_title,
            thread_body=utilities.discussion_thread_data['thread_body']
        )

    thread_link = utilities.get_page_url()

    with check, allure.step("Verifying that the 'Sticky this thread' option is not displayed"):
        assert not sumo_pages.forum_thread_page.is_sticky_this_thread_option_visible()

    with check, allure.step("Signing in with a different user and verifying that the "
                            "'Sticky this thread' option is not displayed"):
        utilities.start_existing_session(cookies=test_user_two)
        assert not sumo_pages.forum_thread_page.is_sticky_this_thread_option_visible()

    with check, allure.step("Signing out and verifying that the 'Sticky this thread' option is "
                            "not displayed"):
        utilities.delete_cookies()
        assert not sumo_pages.forum_thread_page.is_sticky_this_thread_option_visible()

    with allure.step("Signing in with an account that has the permissions to sticky the thread"):
        utilities.start_existing_session(cookies=test_user_three)
        sumo_pages.forum_thread_page.click_sticky_this_thread_option()

    with check, allure.step("Verifying that the 'Sticky this thread' option is no longer "
                            "available and the 'Unsticky this thread' option is displayed"):
        assert not sumo_pages.forum_thread_page.is_sticky_this_thread_option_visible()
        assert sumo_pages.forum_thread_page.is_unsticky_this_thread_option_visible()

    with check, allure.step("Verifying that the 'Sticky' information is displayed inside the "
                            "thread meta"):
        assert "Sticky" in sumo_pages.forum_thread_page.get_thread_meta_information()

    with check, allure.step("Verifying that the sticky image is displayed inside the threads "
                            "table"):
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        assert (sumo_pages.forum_discussions_page.
                is_thread_type_image_displayed(thread_title, "Sticky"))

    with check, allure.step("Signing out and verifying that the sticky image is displayed inside "
                            "the threads table"):
        utilities.delete_cookies()
        assert (sumo_pages.forum_discussions_page.
                is_thread_type_image_displayed(thread_title, "Sticky"))

    with check, allure.step("Navigating to the thread and verifying that the Sticky text is "
                            "displayed inside the thread meta and the unsticky this thread option "
                            "is not displayed"):
        utilities.navigate_to_link(thread_link)
        assert "Sticky" in sumo_pages.forum_thread_page.get_thread_meta_information()
        assert not sumo_pages.forum_thread_page.is_unsticky_this_thread_option_visible()

    with check, allure.step("Signing in with the op and verifying that the "
                            "'Unsticky this thread' option is not displayed"):
        utilities.start_existing_session(cookies=test_user)
        assert not sumo_pages.forum_thread_page.is_unsticky_this_thread_option_visible()

    with check, allure.step("Signing in with the user account that has the permissions of"
                            " unsticking the thread and verifying that the:"
                            "1. Unsticky this thread option is no longer available "
                            "2. Sticky this thread option is displayed "
                            "3. Sticky information is not displayed inside the thread meta "):
        utilities.start_existing_session(cookies=test_user_three)
        sumo_pages.forum_thread_page.click_unsticky_this_thread_option()
        assert not sumo_pages.forum_thread_page.is_unsticky_this_thread_option_visible()
        assert sumo_pages.forum_thread_page.is_sticky_this_thread_option_visible()
        assert not (sumo_pages.forum_discussions_page.
                    is_thread_type_image_displayed(thread_title, "Sticky"))

    with check, allure.step("Verifying that the sticky image is not displayed inside the threads "
                            "table"):
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        assert not (sumo_pages.forum_discussions_page.
                    is_thread_type_image_displayed(thread_title, "Sticky"))


# C890978
@pytest.mark.contributorDiscussionsThreads
def test_thread_breadcrumbs(page: Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(groups=["forum-contributors"])

    with allure.step("Signing in with a contributor and posting a new thread"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        thread_title = (utilities.discussion_thread_data['thread_title'] + utilities.
                        generate_random_number(1, 1000))
        sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title=thread_title,
            thread_body=utilities.discussion_thread_data['thread_body']
        )

    with check, allure.step("Verifying that the thread title is displayed inside the list of "
                            "breadcrumbs"):
        assert thread_title in sumo_pages.forum_thread_page.get_breadcrumb_options()

    with check, allure.step("Clicking on all breadcrumb links and verifying that they redirect to "
                            "the correct page"):
        for breadcrumb in sumo_pages.forum_thread_page.get_all_breadcrumb_link_names():
            sumo_pages.forum_thread_page.click_on_a_breadcrumb_link(breadcrumb)
            if breadcrumb == "Home":
                assert utilities.get_page_url() == HomepageMessages.STAGE_HOMEPAGE_URL_EN_US
            elif breadcrumb == OffTopicForumMessages.PAGE_TITLE:
                assert (breadcrumb == sumo_pages.forum_discussions_page.
                        get_forum_discussions_page_title())
            else :
                assert (breadcrumb == sumo_pages.contributor_discussions_page.
                        get_contributor_discussions_page_title())

            utilities.navigate_back()


# C3010845
@pytest.mark.contributorDiscussionsThreads
def test_forum_post_side_navbar_redirects(page: Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(groups=["forum-contributors"])

    with allure.step("Signing in with a contributor account and navigating to the Off Topic forum "
                     "page"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)

    with allure.step("Creating a new forum thread"):
        thread_title = utilities.discussion_thread_data['thread_title'] + (
            utilities.generate_random_number(1, 1000))
        sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title=thread_title,
            thread_body=utilities.discussion_thread_data['thread_body']
        )

    navbar_items = sumo_pages.forum_thread_page.get_contributor_discussions_side_navbar_items()
    for option in navbar_items:
        with check, allure.step(f"Verifying navigation for side navbar option: {option}"):
            sumo_pages.forum_thread_page.click_on_contributor_discussions_side_navbar_item(option)
            assert (sumo_pages.forum_discussions_page.
                    get_forum_discussions_side_nav_selected_option().lower() == option.lower())
            expected_title = {
                "Forum moderator discussions": "Forum Moderators",
                "Article discussions": "English Knowledge Base Discussions",
                "Off topic discussions": "Off Topic",
                "Lost thread discussions": "Lost Threads"
            }.get(option, option)
            assert (sumo_pages.forum_discussions_page.get_forum_discussions_page_title().
                    lower() == expected_title.lower())
            utilities.navigate_back()


# C3010846
@pytest.mark.contributorDiscussionsThreads
@pytest.mark.parametrize("user_type", [None, 'simple_user', 'moderator'])
def test_forum_moderators_availability_inside_the_forum_post_page(page: Page, user_type,
                                                                  create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(groups=["forum-contributors"])
    test_user_two = create_user_factory(groups=["forum-contributors", "Forum Moderators"])

    with allure.step("Signing in with the Forum Moderator user"):
        utilities.start_existing_session(cookies=test_user_two)

    with allure.step("Navigating to the Contributor Discussions forum"):
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)

    with allure.step("Creating a new forum thread"):
        thread_title = utilities.discussion_thread_data['thread_title'] + (
            utilities.generate_random_number(1, 1000))
        sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title=thread_title,
            thread_body=utilities.discussion_thread_data['thread_body']
        )

    utilities.delete_cookies()

    if user_type in ['simple_user', None]:
        account = test_user if user_type == 'simple_user' else None
        if account:
            utilities.start_existing_session(cookies=account)
        with check, allure.step("Verifying that the 'Forum Moderators' forum is not available "
                                "inside the navbar"):
            assert ("Forum moderator discussions" not in sumo_pages.forum_thread_page.
                    get_contributor_discussions_side_navbar_items())
    else:
        utilities.start_existing_session(cookies=test_user_two)
        with check, allure.step("Verifying that the 'Forum Moderators' forum is available inside "
                                "the navbar"):
            assert ("Forum moderator discussions" in sumo_pages.forum_thread_page.
                    get_contributor_discussions_side_navbar_items())


# C3016247
@pytest.mark.contributorDiscussionsThreads
@pytest.mark.parametrize("user_type", ['simple_user', 'moderator'])
def test_edit_own_forum_post(page: Page, user_type, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(groups=["forum-contributors"])
    test_user_two = create_user_factory(groups=["forum-contributors", "Forum Moderators"])

    with allure.step("Signing in to SUMO"):
        account = test_user if user_type == 'simple_user' else test_user_two
        utilities.start_existing_session(cookies=account)

    with allure.step("Creating a new forum thread"):
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        thread_title = utilities.discussion_thread_data['thread_title'] + (
            utilities.generate_random_number(1, 1000))
        thread_id = sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title=thread_title,
            thread_body=utilities.discussion_thread_data['thread_body']
        )

    with allure.step("Editing the own forum thread post"):
        sumo_pages.contributor_thread_flow.edit_thread_post(
            thread_id,
            "Edited thread body"
        )

    with check, allure.step("Verifying that the edited post is displayed"):
        assert sumo_pages.forum_thread_page.is_thread_post_by_name_visible("Edited thread body")

    with check, allure.step("Verifying that the 'Modified by' information is displayed"):
        assert (f"Modified by {account['username']}" in sumo_pages.forum_thread_page.
                get_modified_by_text(thread_id))


# C3016248
@pytest.mark.contributorDiscussionsThreads
def test_edit_forum_posts(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["forum-contributors"])
    test_user_two = create_user_factory(groups=["forum-contributors"])
    test_user_three = create_user_factory(groups=["forum-contributors"],
                                          permissions=["edit_forum_thread_post"])

    with allure.step("Signing in to SUMO and creating a new forum thread"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        thread_title = utilities.discussion_thread_data['thread_title'] + (
            utilities.generate_random_number(1, 1000))
        thread_id = sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title=thread_title,
            thread_body=utilities.discussion_thread_data['thread_body']
        )
        thread_url = utilities.get_page_url()

    with allure.step("Verifying that the 'Edit this post' option is displayed and accessible"):
        sumo_pages.forum_thread_page.click_on_edit_this_post_option(thread_id)
        edit_url = utilities.get_page_url()

    with check, allure.step("Signing in with a user that doesn't have the necessary permissions "
                            "to edit the post and verifying that the 'Edit this post' option is "
                            "not displayed"):
        utilities.navigate_to_link(thread_url)
        utilities.start_existing_session(cookies=test_user_two)
        assert not sumo_pages.forum_thread_page.is_edit_this_post_option_displayed(thread_id)

    with check, allure.step("Navigating to the edit page directly and verifying that a 403 is "
                            "returned"):
        with page.expect_navigation() as navigation_info:
            utilities.navigate_to_link(edit_url)
        response = navigation_info.value
        assert response.status == 403

    with check, allure.step("Signing out from SUMO and verifying that the 'Edit this post' option"
                            " is not displayed"):
        utilities.navigate_to_link(thread_url)
        utilities.delete_cookies()
        assert not sumo_pages.forum_thread_page.is_edit_this_post_option_displayed(thread_id)

    with check, allure.step("Navigate to the edit page directly and verifying that the user is "
                            "redirected to the auth page"):
        utilities.navigate_to_link(edit_url)
        assert FxAPageMessages.AUTH_PAGE_URL in utilities.get_page_url()

    with check, allure.step("Singing in with a user that has the necesarry permissions to edit a"
                            " thread and verifying that the 'Edit this post' option is displayed"):
        utilities.navigate_to_link(thread_url)
        utilities.start_existing_session(cookies=test_user_three)
        assert sumo_pages.forum_thread_page.is_edit_this_post_option_displayed(thread_id)


# C3020040
@pytest.mark.contributorDiscussionsThreads
def test_delete_this_post(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["forum-contributors"],
                                    permissions=["delete_forum_thread_post"])
    test_user_two = create_user_factory(groups=["forum-contributors"])

    with allure.step("Signing in to SUMO and creating a new forum thread"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        thread_title = utilities.discussion_thread_data['thread_title'] + (
            utilities.generate_random_number(1, 1000))
        sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title=thread_title,
            thread_body=utilities.discussion_thread_data['thread_body']
        )
        thread_url = utilities.get_page_url()

    with allure.step("Creating a new thread post"):
        thread_id = sumo_pages.contributor_thread_flow.post_thread_reply(
            reply_body=utilities.discussion_thread_data['thread_body']
        )

    with check, allure.step("Deleting the thread post and verifying that the thread post is no "
                            "longer displayed"):
        sumo_pages.forum_thread_page.click_on_delete_this_post_option(thread_id)
        sumo_pages.delete_thread_post_page.click_on_delete_button()
        assert not sumo_pages.forum_thread_page.is_thread_post_visible(thread_id)

    with allure.step("Signing in with a different user and posting a new thread post"):
        utilities.start_existing_session(cookies=test_user_two)
        thread_id = sumo_pages.contributor_thread_flow.post_thread_reply(
            reply_body=utilities.discussion_thread_data['thread_body']
        )

    with allure.step("Signing in with an admin account and verifying that the delete this post is "
                     "accessible"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.forum_thread_page.click_on_delete_this_post_option(thread_id)
        delete_post_url = utilities.get_page_url()

    with check, allure.step("Signing in with the thread reply author and verifying that the"
                            " delete this post option is not displayed"):
        utilities.navigate_to_link(thread_url)
        utilities.start_existing_session(cookies=test_user_two)
        assert not sumo_pages.forum_thread_page.is_delete_this_post_option_displayed(thread_id)

    with check, allure.step("Navigating to the delete page directly and verifying that a 403 is "
                            "returned"):
        with page.expect_navigation() as navigation_info:
            utilities.navigate_to_link(delete_post_url)
        response = navigation_info.value
        assert response.status == 403

    with check, allure.step("Signing out from SUMO and verifying that the delete this post option "
                            "is not displayed"):
        utilities.navigate_to_link(thread_url)
        utilities.delete_cookies()
        assert not sumo_pages.forum_thread_page.is_delete_this_post_option_displayed(thread_id)

    with check, allure.step("Navigate to the delete page directly and verifying that the user is "
                            "redirected to the auth page"):
        utilities.navigate_to_link(delete_post_url)
        assert FxAPageMessages.AUTH_PAGE_URL in utilities.get_page_url()


# C3020041
@pytest.mark.contributorDiscussionsThreads
def test_delete_this_post_option_availability(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["forum-contributors"],
                                    permissions=["delete_forum_thread_post"])
    test_user_two = create_user_factory(groups=["forum-contributors"])

    with allure.step("Signing in to SUMO and creating a new forum thread"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        thread_title = utilities.discussion_thread_data['thread_title'] + (
            utilities.generate_random_number(1, 1000))
        first_thread_id = sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title=thread_title,
            thread_body=utilities.discussion_thread_data['thread_body']
        )

    with allure.step("Creating a new thread post"):
        utilities.start_existing_session(cookies=test_user_two)
        second_thread_id = sumo_pages.contributor_thread_flow.post_thread_reply(
            reply_body=utilities.discussion_thread_data['thread_body']
        )

    with allure.step("Signing in with a user that has the permissions of deleting thread posts"
                     " and deleting the first thread post"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.contributor_thread_flow.delete_thread_post(first_thread_id)

    with check, allure.step("Verifying that the first thread post is no longer displayed"):
        assert not sumo_pages.forum_thread_page.is_thread_post_visible(first_thread_id)
        assert sumo_pages.forum_thread_page.is_thread_post_visible(second_thread_id)

    with check, allure.step("Deleting the second thread and verifying that the thread is no "
                            "longer displayed"):
        sumo_pages.contributor_thread_flow.delete_thread_post(second_thread_id)
        assert not sumo_pages.forum_discussions_page.is_thread_displayed(thread_title)


# C3020042
@pytest.mark.contributorDiscussionsThreads
def test_quote_this_post(page: Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(groups=["forum-contributors"])
    test_user_two = create_user_factory(groups=["forum-contributors"])

    with allure.step("Signing in to SUMO and creating a new forum thread"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        thread_title = utilities.discussion_thread_data['thread_title'] + (
            utilities.generate_random_number(1, 1000))
        thread_body = utilities.discussion_thread_data['thread_body']
        thread_id = sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title=thread_title,
            thread_body=thread_body
        )

    with check, allure.step("Signing in with a different account and quoting the first post"):
        utilities.start_existing_session(cookies=test_user_two)
        second_quote = sumo_pages.contributor_thread_flow.quote_thread_post(thread_id)

    with check, allure.step("Verifying that the correct information is displayed inside the "
                            "reply section"):
        assert (sumo_pages.forum_thread_page.
                get_thread_post_mention_text(second_quote) == f"{test_user['username']} said")
        assert (sumo_pages.forum_thread_page.
                get_thread_post_quote_text(second_quote).strip() == thread_body.strip())

    with check, allure.step("Clicking on the 'said' link and verifying that the user is redirected"
                            "to the correct section of the page"):
        sumo_pages.forum_thread_page.click_on_post_mention_link(second_quote)
        assert f"#post-{thread_id}" in utilities.get_page_url()

    with check, allure.step("Signing out from SUMO and verifying that the 'Quote' option is not "
                            "displayed"):
        utilities.delete_cookies()
        assert not sumo_pages.forum_thread_page.is_quote_option_displayed(thread_id)


# C3020047
@pytest.mark.contributorDiscussionsThreads
def test_link_to_this_post_option(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["forum-contributors"])
    test_user_two = create_user_factory(groups=["forum-contributors"])

    with allure.step("Signing in to SUMO and creating a new forum thread"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        thread_title = utilities.discussion_thread_data['thread_title'] + (
            utilities.generate_random_number(1, 1000))
        thread_id = sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title=thread_title,
            thread_body=utilities.discussion_thread_data['thread_body']
        )

    with check, allure.step("Signing in with a different user and clicking on the 'Link to this "
                            "post' option and verifying that the correct URL is displayed"):
        utilities.start_existing_session(cookies=test_user_two)
        sumo_pages.forum_thread_page.click_on_link_to_this_post_option(thread_id)
        assert f"#post-{thread_id}" in utilities.get_page_url()

    with check, allure.step("Signing out from SUMO and clicking on the 'Link to this post' option "
                            "and verifying that the correct URL is displayed"):
        utilities.delete_cookies()
        sumo_pages.forum_thread_page.click_on_link_to_this_post_option(thread_id)
        assert f"#post-{thread_id}" in utilities.get_page_url()


# C3020048
@pytest.mark.contributorDiscussionsThreads
def test_private_message_option(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    message = "This is a test message " + utilities.generate_random_number(1, 1000)
    test_user = create_user_factory(groups=["forum-contributors"])
    test_user_two = create_user_factory(groups=["forum-contributors"])

    with allure.step("Signing in to SUMO and creating a new forum thread"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(OffTopicForumMessages.PAGE_URL)
        thread_title = utilities.discussion_thread_data['thread_title'] + (
            utilities.generate_random_number(1, 1000))
        thread_id = sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title=thread_title,
            thread_body=utilities.discussion_thread_data['thread_body']
        )
        thread_url = utilities.get_page_url()

    with allure.step("Signing in with a different user, clicking on the 'Private message' option "
                     "and sending out a message"):
        utilities.start_existing_session(cookies=test_user_two)

        sumo_pages.forum_thread_page.click_on_private_message_option(thread_id)
        sumo_pages.messaging_system_flow.complete_send_message_form_with_data(
            message_body=message,
            expected_url=SentMessagesPageMessages.SENT_MESSAGES_PAGE_URL
        )

    with check, allure.step("Verifying that the sent message is displayed inside the sent "
                            "messages page"):
        sumo_pages.mess_system_user_navbar.click_on_messaging_system_nav_sent_messages()
        expect(sumo_pages.sent_message_page.sent_messages_by_excerpt_locator(message)
               ).to_be_visible()

    with check, allure.step("Signing in with the receiver account and verifying that the message "
                            "is displayed inside the inbox section"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.top_navbar.click_on_inbox_option()
        expect(sumo_pages.inbox_page.get_inbox_message_locator_based_on_excerpt(message)).to_be_visible()

    with check, allure.step("Navigating back to the thread, signing out and verifying that the "
                            "'Private message' option redirects the user to the auth page"):
        utilities.navigate_to_link(thread_url)
        utilities.delete_cookies()
        sumo_pages.forum_thread_page.click_on_private_message_option(thread_id)
        assert FxAPageMessages.AUTH_PAGE_URL in utilities.get_page_url()
