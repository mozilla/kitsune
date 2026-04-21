import re

import allure
import pytest
from playwright.sync_api import Page, expect
from pytest_check import check

from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.contribute_messages.con_discussions.con_discussions_messages import (
    ConDiscussionsMessages,
)
from playwright_tests.messages.contribute_messages.con_discussions.forum_moderators import (
    ForumModerators,
)
from playwright_tests.messages.contribute_messages.con_discussions.localization_discussions import (
    LocalizationDiscussionsMessages,
)
from playwright_tests.messages.contribute_messages.con_discussions.off_topic import (
    OffTopicForumMessages,
)
from playwright_tests.messages.contribute_messages.con_discussions.support_forum_discussions import (
    SupportForumDiscussionsMessages,
)
from playwright_tests.messages.homepage_messages import HomepageMessages
from playwright_tests.pages.sumo_pages import SumoPages


@pytest.mark.contributorDiscussions
def test_contributor_discussions_forums_description(page: Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(groups=["forum-contributors"])

    with allure.step("Signing in with a contributor account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Navigate to the Contributor Discussions page"):
        sumo_pages.top_navbar.click_on_contributor_discussions_top_navbar_option()

    with check, allure.step("Verifying that the correct description is displayed for each "
                            "available forum"):
        for forum in (sumo_pages.contributor_discussions_page.
                      get_contributor_discussions_forums_titles()):
            expect(sumo_pages.contributor_discussions_page.forum_description(forum)
                   ).to_contain_text([ConDiscussionsMessages.FORUM_DESCRIPTIONS[forum]])


# C890970
@pytest.mark.contributorDiscussions
def test_contributor_discussions_side_nav_redirect(page: Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(groups=["forum-contributors"])

    with allure.step("Signing in with a contributor account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Navigate to the Contributor Discussions page"):
        sumo_pages.top_navbar.click_on_contributor_discussions_top_navbar_option()

    for option in (sumo_pages.contributor_discussions_page.
                   get_contributor_discussions_side_navbar_items()):
        with check, allure.step(f"Clicking on the '{option}' side navbar option and "
                                "verifying that the correct side navbar option is highlighted and "
                                "the correct forum page is opened"):
            (sumo_pages.contributor_discussions_page.
             click_on_contributor_discussions_side_navbar_item(option))
            expect(sumo_pages.forum_discussions_page.forum_side_nav_selected_option).to_have_text(
                option, ignore_case=True)

            if option == "Forum moderator discussions":
                option = "Forum Moderators"
            elif option == "Article discussions":
                option = "English Knowledge Base Discussions"
            elif option == "Off topic discussions":
                option = "Off Topic"
            elif option == "Lost thread discussions":
                option = "Lost Threads"

            expect(sumo_pages.forum_discussions_page.forum_page_title).to_have_text(
                option,ignore_case=True)


# C3002113
@pytest.mark.contributorDiscussions
def test_contributor_discussions_forums_title_redirect(page: Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(groups=["forum-contributors"])

    with allure.step("Signing in with a contributor account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Navigate to the Contributor Discussions page"):
        sumo_pages.top_navbar.click_on_contributor_discussions_top_navbar_option()

    with check, allure.step("Clicking on each Contributor Discussions forum title, verifying "
                            "that the correct discussion page is opened and the correct side "
                            "navbar option is selected"):
        for forum in (sumo_pages.contributor_discussions_page.
                      get_contributor_discussions_forums_titles()):
            sumo_pages.contributor_discussions_page.click_on_an_available_contributor_forum(forum)

            expect(sumo_pages.forum_discussions_page.forum_page_title).to_have_text(
                forum, ignore_case=True)

            if forum == "Forum Moderators":
                forum = "forum moderator discussions"
            elif forum == "Off Topic":
                forum = forum + " discussions"
            elif forum == "Lost Threads":
                forum = "Lost thread discussions"

            expect(sumo_pages.forum_discussions_page.forum_side_nav_selected_option).to_have_text(
                forum, ignore_case=True)

            utilities.navigate_back()


@pytest.mark.smokeTest
@pytest.mark.contributorDiscussions
@pytest.mark.parametrize("user", [None, 'Simple User', 'Forum Moderator'])
def test_forum_moderators_availability(page: Page, user, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory()
    test_user_two = create_user_factory(groups=["forum-contributors", "Forum Moderators"])
    user_map = {'Simple User': test_user, 'Forum Moderator': test_user_two}

    utilities.start_existing_session(cookies=user_map.get(user))

    with allure.step("Navigating to the Contributor Discussions forum"):
        utilities.navigate_to_link(ConDiscussionsMessages.PAGE_URL)

    if user == 'Simple User' or user is None:
        with check, allure.step("Verifying that the 'Forum Moderators' forum is not available"):
            expect(sumo_pages.contributor_discussions_page.contributor_discussions_forum_names
                   ).not_to_contain_text([ForumModerators.PAGE_TITLE])
            expect(sumo_pages.contributor_discussions_page.
                   contributor_discussions_side_navbar_items).not_to_contain_text(
                ["Forum moderator discussions"])

        with check, allure.step("Navigating to the 'Forum Moderators' forum directly and "
                                "verifying that a 404 is returned"):
            with page.expect_navigation() as navigation_info:
                utilities.navigate_to_link(ForumModerators.PAGE_URL)
            response = navigation_info.value
            assert response.status == 404
    else:
        with check, allure.step("Verifying that the 'Forum Moderators' forum is available"):
            expect(sumo_pages.contributor_discussions_page.contributor_discussions_forum_names
                   ).to_contain_text([ForumModerators.PAGE_TITLE])
            expect(sumo_pages.contributor_discussions_page.
                   contributor_discussions_side_navbar_items).to_contain_text(
                ["Forum moderator discussions"])

        with check, allure.step("Navigating to the 'Forum Moderators' forum directly and "
                                "verifying that a 404 is not returned"):
            with page.expect_navigation() as navigation_info:
                utilities.navigate_to_link(ForumModerators.PAGE_URL)
            response = navigation_info.value
            assert response.status != 404


# C2254016
@pytest.mark.contributorDiscussions
def test_threads_number_and_last_post_details(page: Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    target_topic = OffTopicForumMessages.PAGE_TITLE
    test_user = create_user_factory(groups=["forum-contributors"],
                                    permissions=["delete_forum_thread"])

    with allure.step("Signing in with a moderator account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Navigating to the 'Contributor Discussions' page and fetching the number of "
                     "threads posted for the 'Off Topic' forum"):
        utilities.navigate_to_link(ConDiscussionsMessages.PAGE_URL)
        thread_count = int(sumo_pages.contributor_discussions_page.
                           get_forum_thread_count(target_topic))

    with allure.step("Navigating to the 'Off Topic' forum"):
        sumo_pages.contributor_discussions_page.click_on_an_available_contributor_forum(
            OffTopicForumMessages.PAGE_TITLE)

    thread_title = (utilities.discussion_thread_data['thread_title'] + utilities.
                    generate_random_number(1, 1000))

    with allure.step("Creating a new thread to the 'Off topic' forum"):
        post_id = sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title=thread_title, thread_body=utilities.discussion_thread_data['thread_body']
        )

    thread_link = utilities.get_page_url()

    with allure.step("Fetching the thread post date/time"):
        post_time = sumo_pages.forum_thread_page.get_post_time(post_id, "US/Central")

    with check, allure.step("Verifying that the number of threads has incremented successfully "
                            "inside the contributor threads"):
        utilities.navigate_to_link(ConDiscussionsMessages.PAGE_URL)
        thread_count += 1

        expect(sumo_pages.contributor_discussions_page.contributor_discussions_forum_thread_count(
            target_topic)).to_contain_text(str(thread_count))

    with check, allure.step("Verifying that the last post time reflects the newly created "
                            "thread"):
        expect(sumo_pages.contributor_discussions_page.contributor_discussions_forum_last_post_date
               (target_topic)).to_have_text(
            "Today at " + post_time.strftime("%#I:%M %p").lstrip("0").replace("\u202f", " "))

    with check, allure.step("Verifying that the correct username is displayed inside the last post "
                            "section"):
        expect(sumo_pages.contributor_discussions_page.contributor_discussions_forum_last_post_by(
            OffTopicForumMessages.PAGE_TITLE)).to_have_text(test_user["username"])

    with allure.step("Deleting the newly posted thread"):
        utilities.navigate_to_link(thread_link)
        sumo_pages.forum_thread_page.click_on_delete_thread_option()
        sumo_pages.forum_thread_page.click_on_delete_button_from_confirmation_page()

    thread_count -= 1
    with check, allure.step("Navigating back to the contributor discussions page and verifying "
                            "that the thread count has decremented successfully"):
        utilities.navigate_to_link(ConDiscussionsMessages.PAGE_URL)
        expect(sumo_pages.contributor_discussions_page.contributor_discussions_forum_thread_count(
            target_topic)).to_have_text(str(thread_count))

    with check, allure.step("Verifying that the previous post time is no longer displayed inside "
                            "the last post section"):
        expect(sumo_pages.contributor_discussions_page.
               contributor_discussions_forum_last_post_date(target_topic)).not_to_have_text(
            "Today at " + post_time.strftime("%#I:%M %p"))

    with check, allure.step("Verifying that username is no longer displayed inside the last post "
                            "section"):
        expect(sumo_pages.contributor_discussions_page.contributor_discussions_forum_last_post_by(
            OffTopicForumMessages.PAGE_TITLE)).not_to_have_text(test_user["username"])


# C2254016
@pytest.mark.contributorDiscussions
def test_number_of_threads_and_last_post_details_updates_when_moving_a_thread(page: Page,
                                                                              create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    original_forum = LocalizationDiscussionsMessages.PAGE_TITLE
    target_forum = SupportForumDiscussionsMessages.PAGE_TITLE
    test_user = create_user_factory(groups=["forum-contributors"],
                                    permissions=["move_forum_thread"])

    with allure.step("Signing in with a moderator account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Navigating to the 'Contributor Discussions' page and fetching the number of "
                     "threads posted for the 'Localization Discussions' and for the Support "
                     "forum"):
        utilities.navigate_to_link(ConDiscussionsMessages.PAGE_URL)
        original_forum_count = int(sumo_pages.contributor_discussions_page.
                                   get_forum_thread_count(original_forum))
        target_forum_count = int(sumo_pages.contributor_discussions_page.
                                 get_forum_thread_count(target_forum))

    with allure.step("Navigating to the 'Localization Discussions' forum"):
        sumo_pages.contributor_discussions_page.click_on_an_available_contributor_forum(
            original_forum)

    thread_title = (utilities.discussion_thread_data['thread_title'] + utilities.
                    generate_random_number(1, 1000))

    with allure.step("Creating a new thread to the 'Localization Discussions' forum"):
        post_id = sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title=thread_title, thread_body=utilities.discussion_thread_data['thread_body']
        )

    thread_link = utilities.get_page_url()

    with allure.step("Fetching the thread post date/time"):
        post_time = sumo_pages.forum_thread_page.get_post_time(post_id, "US/Central")

    with check, allure.step("Verifying that the number of threads has incremented successfully "
                            "inside the contributor threads"):
        utilities.navigate_to_link(ConDiscussionsMessages.PAGE_URL)
        original_forum_count += 1
        expect(sumo_pages.contributor_discussions_page.contributor_discussions_forum_thread_count(
            original_forum)).to_have_text(str(original_forum_count))

    with check, allure.step("Verifying that the last post time reflects the newly created "
                            "thread"):
        expect(sumo_pages.contributor_discussions_page.
               contributor_discussions_forum_last_post_date(original_forum)).to_have_text(
            "Today at " + post_time.strftime("%#I:%M %p").lstrip("0").replace("\u202f", " "))

    with check, allure.step("Verifying that the correct username is displayed inside the last post "
                            "section"):
        expect(sumo_pages.contributor_discussions_page.contributor_discussions_forum_last_post_by(
            original_forum)).to_have_text(test_user["username"])

    with allure.step("Moving the thread to the 'Support forum'"):
        utilities.navigate_to_link(thread_link)
        sumo_pages.contributor_thread_flow.move_thread_to_a_different_forum(target_forum)

    with allure.step("Verifying that the number of threads has decremented successfully inside "
                     "the original topic and incremented inside the target topic"):
        utilities.navigate_to_link(ConDiscussionsMessages.PAGE_URL)
        original_forum_count -= 1
        expect(sumo_pages.contributor_discussions_page.contributor_discussions_forum_thread_count(
            original_forum)).to_have_text(str(original_forum_count))

        target_forum_count += 1
        expect(sumo_pages.contributor_discussions_page.contributor_discussions_forum_thread_count(
            target_forum)).to_have_text(str(target_forum_count))

    with check, allure.step("Verifying that the last post time reflects the newly moved thread"):
        expect(sumo_pages.contributor_discussions_page.
               contributor_discussions_forum_last_post_date(target_forum)).to_have_text(
            "Today at " + post_time.strftime("%#I:%M %p").lstrip("0").replace("\u202f", " "))

    with check, allure.step("Verifying that the correct username is displayed inside the last "
                            "post"):
        expect(sumo_pages.contributor_discussions_page.contributor_discussions_forum_last_post_by(
            target_forum)).to_have_text(test_user["username"])

    with check, allure.step("Verifying that the last post time is no longer displayed inside "
                            "the original forum"):
        expect(sumo_pages.contributor_discussions_page.
               contributor_discussions_forum_last_post_date(original_forum)).not_to_have_text(
            "Today at " + post_time.strftime("%#I:%M %p").lstrip("0").replace("\u202f", " "))

    with check, allure.step("Verifying that the username is no longer displayed inside the "
                            "original forum section"):
        expect(sumo_pages.contributor_discussions_page.contributor_discussions_forum_last_post_by(
            original_forum)).not_to_have_text(test_user["username"])


# C890958
@pytest.mark.contributorDiscussions
def test_contributor_discussions_breadcrumb_redirect(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)

    with allure.step("Navigating to the Contributor Discussions page"):
        utilities.navigate_to_link(ConDiscussionsMessages.PAGE_URL)

    with check, allure.step("Verifying that the 'Contributor Discussions' breadcrumb is as the "
                            "current one"):
        expect(sumo_pages.contributor_discussions_page.contributor_discussions_page_breadcrumbs.
               last).to_have_text(ConDiscussionsMessages.PAGE_TITLE)

    with check, allure.step("Clicking on the 'Home' breadcrumb and verifying that the user is "
                            "redirected to the homepage successfully"):
        sumo_pages.contributor_discussions_page.click_on_first_breadcrumb()
        expect(page).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL_EN_US)


# C890959,  C2254024
@pytest.mark.contributorDiscussions
def test_contributor_discussions_last_post_redirects(page: Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(groups=["forum-contributors"])
    test_user_two = create_user_factory()

    with allure.step("Signing in with a contributor account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Navigating to the 'Support Forum' forum and posting a new thread"):
        utilities.navigate_to_link(SupportForumDiscussionsMessages.PAGE_URL)
        thread_title = (utilities.discussion_thread_data['thread_title'] + utilities.
                        generate_random_number(1, 1000))
        post_id = sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title=thread_title, thread_body=utilities.discussion_thread_data['thread_body']
        )
    thread_link = utilities.get_page_url()

    with allure.step("Signing out from SUMO"):
        utilities.delete_cookies()

    with allure.step("Navigating back to the Contributor Discussions page"):
        utilities.navigate_to_link(ConDiscussionsMessages.PAGE_URL)

    with check, allure.step("Clicking on the last post date link and verifying that the user is"
                            " redirected to the correct link"):
        sumo_pages.contributor_discussions_page.click_on_last_post_date(
            SupportForumDiscussionsMessages.PAGE_TITLE
        )
        expect(sumo_pages.forum_thread_page.thread_post(post_id)).to_be_visible()

    with check, allure.step("Navigating back to the Contributor Discussions page and clicking on "
                            "the last post by link and verifying that the user is redirected to "
                            "the correct user profile page"):
        utilities.navigate_back()
        sumo_pages.contributor_discussions_page.click_on_last_post_by(
            SupportForumDiscussionsMessages.PAGE_TITLE
        )
        expect(page).to_have_url(re.compile(f".*{test_user['username']}*"))

    with allure.step("Signing in with a different user and leaving a reply to the posted thread"):
        utilities.start_existing_session(cookies=test_user_two)
        utilities.navigate_to_link(thread_link)

        reply_id = sumo_pages.contributor_thread_flow.post_thread_reply(
            reply_body=utilities.discussion_thread_data['thread_reply_body']
        )

    with allure.step("Signing out from SUMO"):
        utilities.delete_cookies()

    with allure.step("Navigating back to the Contributor Discussions page"):
        utilities.navigate_to_link(ConDiscussionsMessages.PAGE_URL)

    with check, allure.step("Clicking on the last post date link and verifying that the user is "
                            "redirected to the correct link"):
        sumo_pages.contributor_discussions_page.click_on_last_post_date(
            SupportForumDiscussionsMessages.PAGE_TITLE
        )
        expect(sumo_pages.forum_thread_page.thread_post(reply_id)).to_be_visible()

    utilities.navigate_back()

    with check, allure.step("Clicking on the last post by link and verifying that the user is "
                            "redirected to the correct user profile page"):
        sumo_pages.contributor_discussions_page.click_on_last_post_by(
            SupportForumDiscussionsMessages.PAGE_TITLE
        )
        expect(page).to_have_url(re.compile(f".*{test_user_two['username']}*"))
