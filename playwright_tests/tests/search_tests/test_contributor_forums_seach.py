import random
import allure
import pytest
from playwright.sync_api import Page
from pytest_check import check
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.contribute_messages.con_discussions.con_discussions_messages import \
    ConDiscussionsMessages
from playwright_tests.pages.sumo_pages import SumoPages


# C1359175
@pytest.mark.contributorForumSearch
def test_by_thread_title(page: Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(groups=["forum-contributors"])
    thread_title = "contribution"

    with allure.step(f"Signing in with {test_user['username']} and navigating to the contributor"
                     f"forums"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.top_navbar.click_on_contributor_discussions_top_navbar_option()

    with allure.step("Navigating to the 'SUMO community discussions' forum"):
        sumo_pages.contributor_discussions_page.click_on_an_available_contributor_forum(
            "SUMO community discussions")

    with check, allure.step("Searching for the test string and verifying that all search results"
                            "include the searched term"):
        sumo_pages.forum_discussions_page.search_in_community_discussion(
            f"field:thread_title:{thread_title}")
        assert all(thread_title in thread_title for thread_title in sumo_pages.
                   forum_discussions_page.get_all_thread_titles_from_search_results())


# C1350866, C1350867, C1350868
@pytest.mark.contributorForumSearch
def test_and_or_not_operators_in_community_hub(page: Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(groups=["forum-contributors"])
    target_user_first_name = "Ryan"
    target_user_last_name = "Johnson"

    with allure.step(f"Navigating to the 'Community hub' page and searching "
                     f"for {target_user_first_name} + {target_user_last_name}"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.top_navbar.click_on_community_hub_option()
        sumo_pages.community_hub_page.search_for_contributor(
            target_user_first_name + ' ' + target_user_last_name)
        cards = sumo_pages.community_hub_page.get_all_users_from_user_cards()

    with check, allure.step(f"Verifying that the {target_user_first_name} + ' ' +"
                            f" {target_user_last_name} is in all returned user cards"):
        assert all(
            target_user_first_name.lower() in card.lower() and target_user_last_name
            .lower() in card.lower() for card in cards)

    with check, allure.step("Using AND operator to search for full name and verifying that the "
                            "same list is returned"):
        sumo_pages.community_hub_page.clear_search()
        sumo_pages.community_hub_page.search_for_contributor(
            target_user_first_name + " AND " + target_user_last_name)
        assert cards == sumo_pages.community_hub_page.get_all_users_from_user_cards()

    with check, allure.step("Using the OR operator to search for full name and verifying that "
                            "cards containing the first name or the last name are returned"):
        sumo_pages.community_hub_page.clear_search()
        sumo_pages.community_hub_page.search_for_contributor(
            target_user_first_name + " OR " + target_user_last_name)
        cards = sumo_pages.community_hub_page.get_all_users_from_user_cards()
        assert all(
            target_user_first_name.lower() in card.lower() or target_user_last_name.
            lower() in card.lower() for card in cards)

    with check, allure.step("Using the NOT operator to search for full name and verifying that "
                            "only the first name is returned"):
        sumo_pages.community_hub_page.clear_search()
        sumo_pages.community_hub_page.search_for_contributor(
            target_user_first_name + " NOT " + target_user_last_name)
        cards = sumo_pages.community_hub_page.get_all_users_from_user_cards()
        assert all(target_user_first_name.lower() in card.lower() for card in cards)
        assert all(target_user_last_name.lower() not in card.lower() for card in cards)


# C1350863, C1350992, C1350865, C1350864
@pytest.mark.contributorForumSearch
def test_and_or_not_operators_in_contributor_forums(page: Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(groups=["forum-contributors"])
    search_term_one = "test"
    search_term_two = "thread"

    with allure.step(f"Signing in with {test_user['username']} and navigating to the contributor"
                     f"forums"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.top_navbar.click_on_contributor_discussions_top_navbar_option()

    with allure.step("Navigating to the 'SUMO community discussions' forum"):
        sumo_pages.contributor_discussions_page.click_on_an_available_contributor_forum(
            "SUMO community discussions")

    with check, allure.step("Searching for the test string and verifying that all search results"
                            "include the searched term"):
        sumo_pages.forum_discussions_page.search_in_community_discussion(
            search_term_one + ' ' + search_term_two)
        assert any(
            all(term in item.lower() for term in [search_term_one, search_term_two]
                ) for item in sumo_pages.forum_discussions_page.
            get_all_thread_titles_from_search_results() or any(
                all(term in item.lower() for term in [search_term_one, search_term_two]
                    ) for item in sumo_pages.forum_discussions_page.
                get_all_thread_content_from_search_results()))

    with check, allure.step("Navigating back, searching for the search term by using the AND"
                            " operator and verifying that all search results include the search "
                            "term"):
        utilities.navigate_back()
        sumo_pages.forum_discussions_page.search_in_community_discussion(
            search_term_one + ' AND ' + search_term_two)
        assert (
            any(search_term_one in item.lower() and search_term_two in item
                .lower() for item in sumo_pages.forum_discussions_page.
                get_all_thread_titles_from_search_results()
                ) or any(search_term_one in item.lower() and search_term_two in item.
                         lower() for item in sumo_pages.forum_discussions_page.
                         get_all_thread_content_from_search_results())
        )

    with check, allure.step("Navigating back, searching for the search term by using the 'OR' "
                            "operator and verifying that the search results include the first or "
                            "second search term"):
        utilities.navigate_back()
        sumo_pages.forum_discussions_page.search_in_community_discussion(
            search_term_one + ' OR ' + search_term_two)
        assert(
            any(search_term_one in item.lower() or search_term_two in item.
                lower() for item in sumo_pages.forum_discussions_page.
                get_all_thread_titles_from_search_results()
                ) or any(search_term_one in item.lower() or search_term_two in item.
                         lower() for item in sumo_pages.forum_discussions_page.
                         get_all_thread_content_from_search_results())
        )

    with check, allure.step("Navigating back, searching for the search term by using the 'NOT'"
                            "operator and verifying that the search results include the first "
                            "but not the second search term"):
        utilities.navigate_back()
        sumo_pages.forum_discussions_page.search_in_community_discussion(
            search_term_one + ' NOT ' + search_term_two)
        assert(
            any(search_term_one in item.lower() for item in sumo_pages.forum_discussions_page.
                get_all_thread_titles_from_search_results()
                ) or any(search_term_one in item.lower() for item in sumo_pages.
                         forum_discussions_page.get_all_thread_content_from_search_results())
        ) and not (
            any(search_term_two in item.lower().split() for item in sumo_pages.
                forum_discussions_page.get_all_thread_titles_from_search_results()
                ) or any(search_term_two in item.lower().split() for item in sumo_pages.
                         forum_discussions_page.get_all_thread_content_from_search_results())
        )

    with check, allure.step("Navigating back, searching for the search term by matching the exact "
                            "search string and verifying that the search results contain the "
                            "search strings"):
        utilities.navigate_back()
        sumo_pages.forum_discussions_page.search_in_community_discussion(
            f'"{search_term_one} '+ f'{search_term_two}"')
        assert(
            any(search_term_one + " " + search_term_two in item.lower() for item in sumo_pages.
                forum_discussions_page.get_all_thread_titles_from_search_results()
                ) or any(search_term_one + " " + search_term_two in item.
                         lower() for item in sumo_pages.forum_discussions_page.
                         get_all_thread_content_from_search_results())
        )

# C1329242
@pytest.mark.contributorForumSearch
def test_searching_in_contributor_forums_return_results_only_to_that_forum(page,
                                                                           create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    thread_title = "Test Contributor Thread " + utilities.generate_random_number(1, 1000)
    test_user = create_user_factory(groups=["forum-contributors"])

    utilities.start_existing_session(cookies=test_user)
    with allure.step("Navigating to Contributor Discussions"):
        utilities.navigate_to_link(ConDiscussionsMessages.PAGE_URL)

    with allure.step("Clicking on the SUMO community discussions forum"):
        sumo_pages.contributor_discussions_page.click_on_an_available_contributor_forum(
            "SUMO community discussions")

    with allure.step("Creating a new forum thread"):
        post_id = sumo_pages.contributor_thread_flow.post_a_new_thread(
            thread_title=thread_title,
            thread_body="Contributor Thread body test"
        )
        utilities.reindex_document("ForumDocument", post_id)

    with allure.step("Navigating back to the SUMO community discussions page"):
        sumo_pages.forum_thread_page.click_on_a_breadcrumb_link("SUMO community discussions")

    with check, allure.step("Searching this forum for the posted thread and verifying that the "
                            "thread is returned"):
        sumo_pages.forum_discussions_page.search_in_community_discussion(thread_title)
        assert (thread_title in sumo_pages.forum_discussions_page.
                get_all_thread_titles_from_search_results())

    with allure.step("Navigating back to the Contributor Discussions page"):
        utilities.navigate_to_link(ConDiscussionsMessages.PAGE_URL)

    with allure.step("Clicking on the Support Forum discussions thread"):
        sumo_pages.contributor_discussions_page.click_on_an_available_contributor_forum(
            "Support Forum discussions")

    with check, allure.step("Searching this forum for the posted thread and verifying that the "
                            "thread is not returned"):
        sumo_pages.forum_discussions_page.search_in_community_discussion(thread_title)
        assert (thread_title not in sumo_pages.forum_discussions_page.
                get_all_thread_titles_from_search_results())


# C1359176
@pytest.mark.contributorForumSearch
def test_by_thread_locked_status(page: Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(groups=["forum-contributors"],
                                    permissions=["lock_forum_thread"])

    with allure.step(f"Signing in with {test_user['username']} and navigating to the contributor"
                     f"forums"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.top_navbar.click_on_contributor_discussions_top_navbar_option()

    with allure.step("Navigating to the 'SUMO community discussions' forum"):
        sumo_pages.contributor_discussions_page.click_on_an_available_contributor_forum(
            "SUMO community discussions")
        forum_url = utilities.get_page_url()

    with check, allure.step("Searching for locked threads and verifying that the returned search"
                            "results are locked."):
        sumo_pages.forum_discussions_page.search_in_community_discussion(
            "field:thread_is_locked:true")
        results = (sumo_pages.forum_discussions_page.
                   get_all_thread_titles_from_search_results_handles())
        random.choice(results).click()

        assert sumo_pages.forum_thread_page.is_unlock_this_thread_option_visible()
        assert "Locked" in sumo_pages.forum_thread_page.get_thread_meta_information()

    with check, allure.step("Navigating back to the forum page, searching for unlocked threads "
                            "and verifying that the returned search results are unlocked."):
        utilities.navigate_to_link(forum_url)
        sumo_pages.forum_discussions_page.search_in_community_discussion(
            "field:thread_is_locked:false")
        results = (sumo_pages.forum_discussions_page.
                   get_all_thread_titles_from_search_results_handles())
        random.choice(results).click()

        assert sumo_pages.forum_thread_page.is_lock_this_thread_option_visible()
        assert "Locked" not in sumo_pages.forum_thread_page.get_thread_meta_information()


# C1359177
@pytest.mark.contributorForumSearch
def test_by_sticky_status(page: Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(groups=["forum-contributors"],
                                    permissions=["sticky_forum_thread"])

    with allure.step(f"Signing in with {test_user['username']} and navigating to the contributor"
                     f"forums"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.top_navbar.click_on_contributor_discussions_top_navbar_option()

    with allure.step("Navigating to the 'SUMO community discussions' forum"):
        sumo_pages.contributor_discussions_page.click_on_an_available_contributor_forum(
            "SUMO community discussions")
        forum_url = utilities.get_page_url()

    with check, allure.step("Searching for sticky threads and verifying that the returned search"
                            "results are sticky."):
        sumo_pages.forum_discussions_page.search_in_community_discussion(
            "field:thread_is_sticky:true")
        results = (sumo_pages.forum_discussions_page.
                   get_all_thread_titles_from_search_results_handles())
        random.choice(results).click()

        assert sumo_pages.forum_thread_page.is_unsticky_this_thread_option_visible()
        assert "Sticky" in sumo_pages.forum_thread_page.get_thread_meta_information()

    with check, allure.step("Navigating back to the forum page, searching for non sticky threads "
                            "and verifying that the returned search results are not sticky."):
        utilities.navigate_to_link(forum_url)
        sumo_pages.forum_discussions_page.search_in_community_discussion(
            "field:thread_is_sticky:false")
        results = (sumo_pages.forum_discussions_page.
                   get_all_thread_titles_from_search_results_handles())
        random.choice(results).click()

        assert sumo_pages.forum_thread_page.is_sticky_this_thread_option_visible()
        assert "Sticky" not in sumo_pages.forum_thread_page.get_thread_meta_information()


