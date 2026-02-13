from typing import Any
import allure
import pytest
from playwright.sync_api import Page, expect
from pytest_check import check
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.explore_help_articles.kb_article_page_messages import (
    KBArticlePageMessages,
)
from playwright_tests.pages.sumo_pages import SumoPages


# C2466509, C2483803, C2466510, C2466511, C2466512
@pytest.mark.smokeTest
@pytest.mark.kbRestrictedVisibility
@pytest.mark.parametrize("is_template", [False, True])
def test_kb_restrict_visibility(page: Page, is_template, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(groups=["Knowledge Base Reviewers", "Staff"])
    test_user_two = create_user_factory()
    test_user_three = create_user_factory(groups=["Accessibility"])
    test_user_four = create_user_factory(groups=["Contributors"])
    whitelisted_groups = utilities.kb_article_test_data['restricted_visibility_groups']

    utilities.start_existing_session(cookies=test_user)
    article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
        approve_first_revision=True, single_group=whitelisted_groups[0], is_template=is_template
    )

    with check, allure.step("Navigating to the article and verifying that 404 is not returned"):
        with page.expect_navigation() as navigation_info:
            sumo_pages.kb_article_page.click_on_article_option()
        response = navigation_info.value
        assert response.status != 404

        article_url = utilities.get_page_url()

    with check, allure.step("Verifying that the correct restricted banner is displayed"):
        assert (KBArticlePageMessages.KB_ARTICLE_RESTRICTED_BANNER in sumo_pages.kb_article_page
                .get_restricted_visibility_banner_text())

    with allure.step("Signing out from SUMO"):
        utilities.delete_cookies()

    with check, allure.step("Navigating to the article and verifying that 404 is returned"):
        with page.expect_navigation() as navigation_info:
            utilities.navigate_to_link(article_url)
        response = navigation_info.value
        assert response.status == 404

    with allure.step("Signing in with a user which is not part of the whitelisted group"):
        utilities.start_existing_session(cookies=test_user_two)

    with check, allure.step("Navigating to the article and verifying that 404 is returned"):
        with page.expect_navigation() as navigation_info:
            utilities.navigate_to_link(article_url)
        response = navigation_info.value
        assert response.status == 404

    with allure.step("Signing in with a user which is part of the whitelisted group"):
        utilities.start_existing_session(cookies=test_user_three)

    with allure.step("Navigating to the article and verifying that group and verifying that 404 is"
                     " not returned"):
        with page.expect_navigation() as navigation_info:
            utilities.navigate_to_link(article_url)
        response = navigation_info.value
        assert response.status != 404

    with allure.step("Verifying that the correct restricted banner is displayed"):
        assert (KBArticlePageMessages.KB_ARTICLE_RESTRICTED_BANNER in sumo_pages.kb_article_page
                .get_restricted_visibility_banner_text())

    with allure.step("Signing in with an admin account and whitelisting a new group"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.edit_article_metadata_flow.edit_article_metadata(
            single_group=whitelisted_groups[1]
        )

    with allure.step("Signing in with a user which is part of the whitelisted groups"):
        utilities.start_existing_session(cookies=test_user_four)


    with check, allure.step("Navigating to the article and verifying that 404 is not returned"):
        with page.expect_navigation() as navigation_info:
            utilities.navigate_to_link(article_url)
        response = navigation_info.value
        assert response.status != 404

    with check, allure.step("Verifying that the correct restricted banner is displayed"):
        assert (KBArticlePageMessages.KB_ARTICLE_RESTRICTED_BANNER in sumo_pages.kb_article_page
                .get_restricted_visibility_banner_text())

    with allure.step("Signing in with a user which is part of the whitelisted groups"):
        utilities.start_existing_session(test_user_three)

    with check, allure.step("Navigating to the article and verifying that 404 is not returned"):
        with page.expect_navigation() as navigation_info:
            utilities.navigate_to_link(article_url)
        response = navigation_info.value
        assert response.status != 404

    with check, allure.step("Verifying that the correct restricted banner is displayed"):
        assert (KBArticlePageMessages.KB_ARTICLE_RESTRICTED_BANNER in sumo_pages.kb_article_page
                .get_restricted_visibility_banner_text())

    with allure.step("Signing in with a user which is not part of the whitelisted groups"):
        utilities.start_existing_session(cookies=test_user_two)

    with allure.step("Navigating to the article and verifying that 404 is returned"):
        with page.expect_navigation() as navigation_info:
            utilities.navigate_to_link(article_url)
        response = navigation_info.value
        assert response.status == 404

    with allure.step("Signing in with an admin account and removing the first group"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.edit_article_metadata_flow.remove_a_restricted_visibility_group(
            whitelisted_groups[0]
        )

    with allure.step("Signing in with an account belonging to the removed group"):
        utilities.start_existing_session(cookies=test_user_three)

    with check, allure.step("Navigating to the article and verifying that the 404 is returned"):
        with page.expect_navigation() as navigation_info:
            utilities.navigate_to_link(article_details['article_url'])
        response = navigation_info.value
        assert response.status == 404

    with allure.step("Signing in with an account that is part of the whitelisted group"):
        utilities.start_existing_session(cookies=test_user_four)

    with check, allure.step("Navigating to the article and verifying that 404 is not returned"):
        with page.expect_navigation() as navigation_info:
            utilities.navigate_to_link(article_details['article_url'])
        response = navigation_info.value
        assert response.status != 404

    with allure.step("Signing in with an admin account and removing all restricted groups"):
        utilities.start_existing_session(cookies=test_user)

        sumo_pages.edit_article_metadata_flow.remove_a_restricted_visibility_group(
            whitelisted_groups[1])

    with allure.step("Deleting user session"):
        utilities.delete_cookies()

    with check, allure.step("Navigating to the article and verifying that 404 is not returned"):
        with page.expect_navigation() as navigation_info:
            utilities.navigate_to_link(article_details['article_url'])
        response = navigation_info.value
        assert response.status != 404

    with allure.step("Verifying that the restricted banner is no longer displayed"):
        assert not sumo_pages.kb_article_page.is_restricted_visibility_banner_text_displayed()


# C2466516
@pytest.mark.smokeTest
@pytest.mark.kbRestrictedVisibility
def test_restricted_visibility_in_search_results(page: Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(groups=["Knowledge Base Reviewers", "Staff"])
    test_user_two = create_user_factory()
    test_user_three = create_user_factory(groups=["Accessibility"])
    whitelisted_group = utilities.kb_article_test_data['restricted_visibility_groups'][0]

    with allure.step("Creating a new kb article with restricted visibility"):
        utilities.start_existing_session(cookies=test_user)

        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            approve_first_revision=True, single_group=whitelisted_group[0]
        )
        utilities.reindex_document("WikiDocument", article_details["article_id"])

    with allure.step("Clicking on the top-navbar sumo logo"):
        sumo_pages.top_navbar.click_on_sumo_nav_logo()

    with check, allure.step("Verifying that the article is not displayed inside the search "
                            "results"):
        sumo_pages.search_page.fill_into_searchbar(article_details['article_title'])
        expect(sumo_pages.search_page.get_locator_of_a_particular_article(
            article_details['article_title'])).to_be_hidden()

    with allure.step("Signing in with an account that is part of that whitelisted group"):
        utilities.start_existing_session(cookies=test_user_three)

    with check, allure.step("Verifying that the article is not inside the search results"):
        sumo_pages.search_page.fill_into_searchbar(article_details['article_title'])
        expect(sumo_pages.search_page.get_locator_of_a_particular_article(
            article_details['article_title'])).to_be_hidden()

    with allure.step("Signing in with an account that is not part of that whitelisted group"):
        utilities.start_existing_session(cookies=test_user_two)

    with check, allure.step("Verifying that the article is not displayed inside the search "
                            "results"):
        sumo_pages.search_page.fill_into_searchbar(article_details['article_title'])
        expect(sumo_pages.search_page.get_locator_of_a_particular_article(
            article_details['article_title'])).to_be_hidden()

    with allure.step("Deleting the user session"):
        utilities.delete_cookies()

    with allure.step("Verifying that the article is not displayed inside the search results"):
        sumo_pages.search_page.fill_into_searchbar(article_details['article_title'])
        expect(sumo_pages.search_page.get_locator_of_a_particular_article(
            article_details['article_title'])).to_be_hidden()


# C2466518
@pytest.mark.kbRestrictedVisibility
@pytest.mark.parametrize("is_template", [False, True])
def test_restricted_visibility_in_recent_revisions(page: Page, is_template, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(groups=["Knowledge Base Reviewers", "Staff",
                                            "forum-contributors"])
    test_user_two = create_user_factory(groups=["Accessibility"])
    test_user_three = create_user_factory(groups=["Contributors"])
    whitelisted_groups = utilities.kb_article_test_data['restricted_visibility_groups']

    with allure.step("Creating a new kb article with restricted visibility"):
        utilities.start_existing_session(cookies=test_user)

        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            approve_first_revision=True, single_group=whitelisted_groups[0],
            is_template=is_template
        )

    with check, allure.step("Navigating to the recent revisions page and verifying that the "
                            "article is displayed"):
        sumo_pages.top_navbar.click_on_recent_revisions_option()
        assert utilities.expect_locator_visibility(
            sumo_pages.recent_revisions_page.recent_revision_based_on_article(
                article_details['article_title'])
        )

    with allure.step("Signing in with an account belonging to group one"):
        utilities.start_existing_session(cookies=test_user_two)

    with check, allure.step("Verifying that the article is displayed"):
        assert utilities.expect_locator_visibility(
            sumo_pages.recent_revisions_page.recent_revision_based_on_article(
                article_details['article_title'])
        )

    with allure.step("Signing in with a user belonging to a different user group"):
        utilities.start_existing_session(cookies=test_user_three)

    with allure.step("Verifying that the article is not displayed"):
        expect(sumo_pages.recent_revisions_page.recent_revision_based_on_article(
            article_details['article_title'])).to_be_hidden()

    with allure.step("Signing in with an admin account and whitelisting a new group"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(article_details['article_url'])
        sumo_pages.edit_article_metadata_flow.edit_article_metadata(
            single_group=whitelisted_groups[1]
        )

    with allure.step("Signing in with the user belonging to group 2 and verifying that the "
                     "article is displayed inside the recent revisions page"):
        utilities.start_existing_session(cookies=test_user_three)
        sumo_pages.top_navbar.click_on_recent_revisions_option()

    with allure.step("Verifying that the article is displayed"):
        assert utilities.expect_locator_visibility(
            sumo_pages.recent_revisions_page.recent_revision_based_on_article(
                article_details['article_title'])
        )

    with allure.step("Removing restrictions"):
        utilities.navigate_to_link(article_details['article_url'])
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.edit_article_metadata_flow.remove_a_restricted_visibility_group(
            whitelisted_groups)

    with allure.step("Navigating to the recent revisions page, signing out and verifying "
                     "that the article is displayed"):
        utilities.delete_cookies()
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['recent_revisions']
        )
        assert utilities.expect_locator_visibility(
            sumo_pages.recent_revisions_page.recent_revision_based_on_article(
                article_details['article_title'])
        )


# C2466524
@pytest.mark.kbRestrictedVisibility
@pytest.mark.parametrize("is_template", [False, True])
def test_kb_restricted_visibility_media_gallery(page: Page, is_template, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["Knowledge Base Reviewers", "Staff",
                                            "forum-contributors"])
    test_user_two = create_user_factory(groups=["Accessibility"])
    test_user_three = create_user_factory(groups=["Contributors"])
    whitelisted_groups = utilities.kb_article_test_data['restricted_visibility_groups']

    with allure.step("Creating a new kb article with restricted visibility"):
        utilities.start_existing_session(cookies=test_user)

        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            approve_first_revision=True, single_group=whitelisted_groups[0],
            article_content_image=utilities.kb_article_test_data['article_image'],
            is_template=is_template
        )

    with allure.step("Navigating to the 'Media Gallery' page"):
        sumo_pages.top_navbar.click_on_media_gallery_option()

    with check, allure.step("Searching for the added image and verifying that the article is "
                            "displayed for admin users inside the 'Articles' image list"):
        sumo_pages.media_gallery.fill_search_media_gallery_searchbox_input_field(
            utilities.kb_article_test_data['article_image']
        )
        sumo_pages.media_gallery.click_on_media_gallery_searchbox_search_button()
        sumo_pages.media_gallery.select_media_file_from_list(
            utilities.kb_article_test_data['article_image']
        )
        assert article_details['article_title'] in (sumo_pages.media_gallery
                                                    .get_image_in_documents_list_items_text())

    with allure.step("Signing out from SUMO"):
        utilities.delete_cookies()

    with check, allure.step("Verifying that the article is not displayed for signed out "
                            "users inside the 'Articles image list'"):
        assert article_details['article_title'] not in (sumo_pages.media_gallery
                                                        .get_image_in_documents_list_items_text())

    with allure.step("Signing in with an account that is not part of a whitelisted group"):
        utilities.start_existing_session(cookies=test_user_three)

    with check, allure.step("Verifying that the article is not displayed for users belonging "
                            "to a non-whitelisted group inside the 'Articles image list'"):
        assert article_details['article_title'] not in (sumo_pages.media_gallery
                                                        .get_image_in_documents_list_items_text())

    with allure.step("Signing in with an account that is part of the whitelisted group"):
        utilities.start_existing_session(cookies=test_user_two)

    with allure.step("Verifying that the article is displayed for users belonging to a "
                     "whitelisted inside the 'Articles image list'"):
        assert article_details['article_title'] in (sumo_pages.media_gallery
                                                    .get_image_in_documents_list_items_text())

    with allure.step("Signing in with an admin account and whitelisting a new group"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(article_details['article_url'])
        sumo_pages.edit_article_metadata_flow.edit_article_metadata(
            single_group=whitelisted_groups[1]
        )

    with allure.step("Navigating to the 'Media Gallery' page"):
        sumo_pages.top_navbar.click_on_media_gallery_option()

    with check, allure.step("Searching for the added image and verifying that the article is "
                            "displayed for admin users inside the 'Articles' image list"):
        sumo_pages.media_gallery.fill_search_media_gallery_searchbox_input_field(
            utilities.kb_article_test_data['article_image']
        )
        sumo_pages.media_gallery.click_on_media_gallery_searchbox_search_button()
        sumo_pages.media_gallery.select_media_file_from_list(
            utilities.kb_article_test_data['article_image']
        )

    with allure.step("Verifying that the article is displayed for users belonging to the "
                     "second whitelisted group"):
        utilities.start_existing_session(cookies=test_user_three)
        assert article_details['article_title'] in (sumo_pages.media_gallery
                                                    .get_image_in_documents_list_items_text())
    with allure.step("Removing restrictions"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(article_details['article_url'])
        sumo_pages.edit_article_metadata_flow.remove_a_restricted_visibility_group(
            whitelisted_groups)

    with allure.step("Navigating to the media gallery image page and verifying that the "
                     "article is displayed for signed out users"):
        sumo_pages.top_navbar.click_on_media_gallery_option()
        utilities.delete_cookies()
        sumo_pages.media_gallery.fill_search_media_gallery_searchbox_input_field(
            utilities.kb_article_test_data['article_image']
        )
        sumo_pages.media_gallery.click_on_media_gallery_searchbox_search_button()
        sumo_pages.media_gallery.select_media_file_from_list(
            utilities.kb_article_test_data['article_image']
        )
        utilities.delete_cookies()
        assert article_details['article_title'] in (sumo_pages.media_gallery
                                                    .get_image_in_documents_list_items_text())


# C2466531
@pytest.mark.kbRestrictedVisibility
@pytest.mark.parametrize("is_template", [False, True])
def test_kb_restricted_visibility_discussion(page: Page, is_template, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["Knowledge Base Reviewers", "Staff",
                                            "forum-contributors"])
    test_user_two = create_user_factory(groups=["Accessibility"])
    test_user_three = create_user_factory(groups=["Contributors"])
    whitelisted_groups = utilities.kb_article_test_data['restricted_visibility_groups']

    with allure.step("Creating a new kb article with restricted visibility"):
        utilities.start_existing_session(cookies=test_user)

        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            approve_first_revision=True, single_group=whitelisted_groups[0],
            is_template=is_template
        )

    thread = _create_discussion_thread(page)

    with allure.step("Navigating to the Article Discussions page"):
        sumo_pages.top_navbar.click_on_article_discussions_option()

    with check, allure.step("Verifying that the the kb article is displayed for admin users"):
        assert utilities.expect_locator_visibility(
            sumo_pages.article_discussions_page.article_discussion_title(thread['thread_title'])
        )

    with check, allure.step("Verifying that the kb article is displayed for whitelisted "
                            "group users"):
        utilities.start_existing_session(cookies=test_user_two)
        assert utilities.expect_locator_visibility(
            sumo_pages.article_discussions_page.article_discussion_title(thread['thread_title'])
        )

    with check, allure.step("Verifying that the kb article is not displayed for signed out users"):
        utilities.delete_cookies()
        expect(sumo_pages.article_discussions_page
               .article_discussion_title(thread['thread_title'])).to_be_hidden()

    with allure.step("Verifying that the kb article is displayed for non-whitelisted group "
                     "users"):
        utilities.start_existing_session(cookies=test_user_three)
        expect(sumo_pages.article_discussions_page
               .article_discussion_title(thread['thread_title'])).to_be_hidden()

    with allure.step("Signing in with an admin account and whitelisting a new group"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(article_details['article_url'])
        sumo_pages.edit_article_metadata_flow.edit_article_metadata(
            single_group=whitelisted_groups[1]
        )

    with allure.step("Navigating to the article discussion page and verifying that the "
                     "article is displayed inside the article discussions list for the "
                     "second whitelisted group user"):
        utilities.start_existing_session(cookies=test_user_three)
        utilities.navigate_to_link(
            utilities.general_test_data['discussions_links']['article_discussions']
        )
        assert utilities.expect_locator_visibility(
            sumo_pages.article_discussions_page.article_discussion_title(thread['thread_title'])
        )

    with allure.step("Removing restrictions"):
        utilities.navigate_to_link(article_details['article_url'])
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.edit_article_metadata_flow.remove_a_restricted_visibility_group(
            whitelisted_groups)

    with allure.step("Navigating to the article discussion page and verifying that the "
                     "article is displayed for signed out users"):
        utilities.delete_cookies()
        utilities.navigate_to_link(
            utilities.general_test_data['discussions_links']['article_discussions']
        )
        assert utilities.expect_locator_visibility(
            sumo_pages.article_discussions_page.article_discussion_title(thread['thread_title'])
        )


# C2466533
@pytest.mark.kbRestrictedVisibility
def test_kb_restricted_visibility_in_topics_page(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["Knowledge Base Reviewers", "Staff",
                                            "forum-contributors"])
    test_user_two = create_user_factory(groups=["Accessibility"])
    test_user_three = create_user_factory(groups=["Contributors"])
    whitelisted_groups = utilities.kb_article_test_data['restricted_visibility_groups']

    with allure.step("Creating a new kb article with restricted visibility"):
        utilities.start_existing_session(cookies=test_user)

        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            approve_first_revision=True, single_group=whitelisted_groups[0]
        )

    sumo_pages.kb_article_page.click_on_article_option()
    with allure.step("Clicking on the article child topic"):
        sumo_pages.kb_article_page.click_on_a_particular_breadcrumb(
            article_details['article_topic'][0]
        )

    with check, allure.step("Verifying that the article is listed inside the article topic "
                            "page for admin users"):
        assert utilities.expect_locator_visibility(
            sumo_pages.product_topics_page.get_a_particular_article_locator(
                article_details['article_title'])
        )

    with check, allure.step("Verifying that the article is not listed for signed out users"):
        utilities.delete_cookies()
        expect(sumo_pages.product_topics_page.get_a_particular_article_locator(
            article_details['article_title'])).to_be_hidden()

    with check, allure.step("Verifying that the article is listed for users belonging to a "
                            "whitelisted group"):
        utilities.start_existing_session(cookies=test_user_two)
        assert utilities.expect_locator_visibility(
            sumo_pages.product_topics_page.get_a_particular_article_locator(
                article_details['article_title'])
        )

    with allure.step("Verifying that the article is not listed for users belonging to a "
                     "non-whitelisted group"):
        utilities.start_existing_session(cookies=test_user_three)
        expect(sumo_pages.product_topics_page.get_a_particular_article_locator(
            article_details['article_title'])).to_be_hidden()

    with allure.step("Signing in with an admin account and whitelisting a new group"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(article_details['article_url'])
        sumo_pages.edit_article_metadata_flow.edit_article_metadata(
            single_group=whitelisted_groups[1]
        )

    sumo_pages.kb_article_page.click_on_article_option()
    with allure.step("Clicking on the article child topic"):
        sumo_pages.kb_article_page.click_on_a_particular_breadcrumb(
            article_details['article_topic'][0]
        )

    with allure.step("Verifying that the article is displayed for the second whitelisted "
                     "group"):
        utilities.start_existing_session(cookies=test_user_three)
        assert utilities.expect_locator_visibility(
            sumo_pages.product_topics_page.get_a_particular_article_locator(
                article_details['article_title'])
        )


#  C2539825
@pytest.mark.kbRestrictedVisibility
@pytest.mark.parametrize("is_template", [False, True])
def test_kb_restricted_visibility_profile_level(page: Page, is_template, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["Knowledge Base Reviewers", "Staff",
                                            "forum-contributors"])
    test_user_two = create_user_factory(groups=["Accessibility"])
    test_user_three = create_user_factory(groups=["Contributors"])
    whitelisted_groups = utilities.kb_article_test_data['restricted_visibility_groups']

    with allure.step("Creating a new kb article with restricted visibility"):
        utilities.start_existing_session(cookies=test_user)

        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            approve_first_revision=True, single_group=whitelisted_groups[0],
            is_template=is_template
        )

    with allure.step("Navigating to the user profile page"):
        sumo_pages.top_navbar.click_on_view_profile_option()

    with allure.step("Clicking on the documents link"):
        sumo_pages.my_profile_page.click_on_my_profile_document_link()
        op_document_contributions_link = utilities.get_page_url()

    with check, allure.step("Verifying that the article is displayed inside the document "
                            "contribution page for admin users"):
        assert utilities.expect_locator_visibility(
            sumo_pages.my_documents_page.document_by_name(article_details['article_title'])
        )

    with check, allure.step("Verifying that the article is displayed inside the op document "
                            "contributions list for a whitelisted user"):
        utilities.start_existing_session(cookies=test_user_two)
        utilities.navigate_to_link(op_document_contributions_link)
        assert utilities.expect_locator_visibility(
            sumo_pages.my_documents_page.document_by_name(article_details['article_title'])
        )

    with allure.step("Verifying that the article is not displayed inside the op document "
                     "contributions list for a non whitelisted user"):
        utilities.start_existing_session(cookies=test_user_three)
        utilities.navigate_to_link(op_document_contributions_link)
        expect(sumo_pages.my_documents_page.document_by_name(article_details['article_title'])
               ).to_be_hidden()

    with allure.step("Signing in with an admin account and whitelisting a new group"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(article_details['article_url'])
        sumo_pages.edit_article_metadata_flow.edit_article_metadata(
            single_group=whitelisted_groups[1]
        )

    with allure.step("Navigating to the user profile page"):
        sumo_pages.top_navbar.click_on_view_profile_option()

    with allure.step("Clicking on the documents link"):
        sumo_pages.my_profile_page.click_on_my_profile_document_link()

    with allure.step("Verifying that the article is displayed inside the op document "
                     "contributions list for the newly whitelisted users group"):
        utilities.start_existing_session(cookies=test_user_three)
        assert utilities.expect_locator_visibility(
            sumo_pages.my_documents_page.document_by_name(article_details['article_title'])
        )

    with allure.step("Removing restrictions"):
        utilities.navigate_to_link(article_details['article_url'])
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.edit_article_metadata_flow.remove_a_restricted_visibility_group(
            whitelisted_groups
        )

    with allure.step("Navigating to the user profile page"):
        sumo_pages.top_navbar.click_on_view_profile_option()

    with allure.step("Clicking on the documents link"):
        sumo_pages.my_profile_page.click_on_my_profile_document_link()

    with allure.step("Verifying that the article is displayed inside the op document list "
                     "for signed out users"):
        utilities.delete_cookies()
        assert utilities.expect_locator_visibility(
            sumo_pages.my_documents_page.document_by_name(article_details['article_title'])
        )


# C2468303
@pytest.mark.kbRestrictedVisibility
@pytest.mark.parametrize("is_template", [False, True])
def test_kb_restricted_visibility_in_l10n_dashboards(page: Page, is_template, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["Knowledge Base Reviewers", "Staff",
                                            "forum-contributors"])
    test_user_two = create_user_factory(groups=["Accessibility"])
    test_user_three = create_user_factory(groups=["Contributors"])
    whitelisted_group = utilities.kb_article_test_data['restricted_visibility_groups'][0]

    with allure.step("Creating a new kb article with restricted visibility"):
        utilities.start_existing_session(cookies=test_user)

        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            approve_first_revision=True, ready_for_localization=True,
            single_group=whitelisted_group, is_template=is_template
        )

    with check, allure.step("Verifying that the article is displayed for admin users inside "
                            "the kb-overview dashboard"):
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['l10n_most_visited_translations'])
        assert utilities.expect_locator_visibility(
            sumo_pages.kb_dashboard_page.article_title(article_details['article_title'])
        )

    with check, allure.step("Verifying that the article is displayed for users belonging to "
                            "the whitelisted group"):
        utilities.start_existing_session(cookies=test_user_two)
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['l10n_most_visited_translations'])
        assert utilities.expect_locator_visibility(
            sumo_pages.kb_dashboard_page.article_title(article_details['article_title'])
        )

    with allure.step("Verifying that the article is not displayed for users belonging to "
                     "non-whitelisted groups"):
        utilities.start_existing_session(cookies=test_user_three)
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['l10n_most_visited_translations'])
        expect(sumo_pages.kb_dashboard_page.article_title(
            article_details['article_title'])).to_be_hidden()

    with allure.step("Removing restrictions"):
        utilities.navigate_to_link(article_details['article_url'])
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.edit_article_metadata_flow.remove_a_restricted_visibility_group(
            whitelisted_group
        )

    with allure.step("Signing out and verifying that the article is displayed inside the "
                     "kb-overview dashboard"):
        utilities.delete_cookies()
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['l10n_most_visited_translations'])
        assert utilities.expect_locator_visibility(
            sumo_pages.kb_dashboard_page.article_title(article_details['article_title']))


# C2466519
@pytest.mark.kbRestrictedVisibility
@pytest.mark.parametrize("is_template", [False, True])
def test_kb_restricted_visibility_in_dashboards(page: Page, is_template, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["Knowledge Base Reviewers", "Staff",
                                            "forum-contributors"])
    test_user_two = create_user_factory(groups=["Accessibility"])
    test_user_three = create_user_factory(groups=["Contributors"])
    whitelisted_group = utilities.kb_article_test_data['restricted_visibility_groups'][0]

    with allure.step("Creating a new kb article with restricted visibility"):
        utilities.start_existing_session(cookies=test_user)
        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            approve_first_revision=True, ready_for_localization=True,
            single_group=whitelisted_group, is_template=is_template
        )

    with check, allure.step("Verifying that the article is displayed for admin users inside "
                            "the kb-overview dashboard"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        assert utilities.expect_locator_visibility(
            sumo_pages.kb_dashboard_page.article_title(article_details['article_title'])
        )

    with check, allure.step("Verifying that the article is displayed for users belonging to "
                            "the whitelisted group"):
        sumo_pages.top_navbar.click_on_sumo_nav_logo()
        utilities.start_existing_session(cookies=test_user_two)
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        assert utilities.expect_locator_visibility(
            sumo_pages.kb_dashboard_page.article_title(article_details['article_title'])
        )

    with allure.step("Verifying that the article is not displayed for users belonging to "
                     "non-whitelisted groups"):
        sumo_pages.top_navbar.click_on_sumo_nav_logo()
        utilities.start_existing_session(cookies=test_user_three)
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.article_title(
            article_details['article_title'])).to_be_hidden()

    with allure.step("Removing restrictions"):
        utilities.navigate_to_link(article_details['article_url'])
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.edit_article_metadata_flow.remove_a_restricted_visibility_group(
            whitelisted_group
        )

    with allure.step("Signing out and verifying that the article is displayed inside the "
                     "kb-overview dashboard"):
        utilities.delete_cookies()
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        assert utilities.expect_locator_visibility(
            sumo_pages.kb_dashboard_page.article_title(article_details['article_title'])
        )


# C2539174 C2101640
@pytest.mark.kbRestrictedVisibility
@pytest.mark.parametrize("is_template", [False, True])
def test_kb_restricted_visibility_what_links_here_page(page: Page, is_template,
                                                       create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["Knowledge Base Reviewers", "Staff",
                                            "forum-contributors"])
    test_user_two = create_user_factory(groups=["Accessibility"])
    test_user_three = create_user_factory(groups=["Contributors"])
    whitelisted_groups = utilities.kb_article_test_data['restricted_visibility_groups']

    with allure.step("Creating a new kb article with restricted visibility"):
        utilities.start_existing_session(cookies=test_user)

        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            approve_first_revision=True, ready_for_localization=True,
            single_group=whitelisted_groups[0], is_template=is_template
        )

    with allure.step("Navigating to the test article linked to the document"):
        utilities.navigate_to_link(utilities.general_test_data['test_article_link'])

    with check, allure.step("Navigating to the 'What Links Here' page and verifying that the "
                            "restricted article is displayed for admin accounts"):
        sumo_pages.kb_article_page.click_on_what_links_here_option()
        assert utilities.expect_locator_visibility(
            sumo_pages.kb_what_links_here_page.what_links_here_for_article(
                article_details['article_title'])
        )

    with check, allure.step("Verifying that the restricted article is displayed for users "
                            "belonging to a whitelisted group"):
        utilities.start_existing_session(cookies=test_user_two)
        assert utilities.expect_locator_visibility(
            sumo_pages.kb_what_links_here_page
            .what_links_here_for_article(article_details['article_title'])
        )

    with check, allure.step("Verifying that the restricted article is not displayed for "
                            "users belonging to a non-whitelisted group"):
        utilities.start_existing_session(cookies=test_user_three)
        expect(
            sumo_pages.kb_what_links_here_page
            .what_links_here_for_article(article_details['article_title'])).to_be_hidden()

    with (allure.step("Verifying that the article is not displayed for signed out users")):
        utilities.delete_cookies()
        expect(sumo_pages.kb_what_links_here_page.
               what_links_here_for_article(article_details['article_title'])).to_be_hidden()

    with allure.step("Signing in with an admin account and whitelisting a new group"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(article_details['article_url'])
        sumo_pages.edit_article_metadata_flow.edit_article_metadata(
            single_group=whitelisted_groups[1]
        )

    utilities.start_existing_session(cookies=test_user_three)
    with allure.step("Navigating to the test article linked to the document"):
        utilities.navigate_to_link(utilities.general_test_data['test_article_link'])

    with allure.step("Navigating to the 'What Links Here' page and verifying that the linked "
                     "article is displayed to the newly added group members"):
        sumo_pages.kb_article_page.click_on_what_links_here_option()
        assert utilities.expect_locator_visibility(
            sumo_pages.kb_what_links_here_page
            .what_links_here_for_article(article_details['article_title'])
        )

    with allure.step("Removing restrictions"):
        utilities.navigate_to_link(article_details['article_url'])
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.edit_article_metadata_flow.remove_a_restricted_visibility_group(
            whitelisted_groups
        )

    with allure.step("Navigating to the test article linked to the document"):
        utilities.navigate_to_link(utilities.general_test_data['test_article_link'])

    with allure.step("Navigating to the 'What Links Here' page and verifying that the "
                     "article is displayed for signed out users"):
        sumo_pages.kb_article_page.click_on_what_links_here_option()
        utilities.delete_cookies()
        assert utilities.expect_locator_visibility(
            sumo_pages.kb_what_links_here_page
            .what_links_here_for_article(article_details['article_title'])
        )


# C2539824
@pytest.mark.kbRestrictedVisibility
@pytest.mark.parametrize("is_template", [False, True])
def test_kb_restricted_visibility_category_page(page: Page, is_template, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["Knowledge Base Reviewers", "Staff",
                                            "forum-contributors"])
    test_user_two = create_user_factory(groups=["Accessibility"])
    test_user_three = create_user_factory(groups=["Contributors"])
    whitelisted_groups = utilities.kb_article_test_data['restricted_visibility_groups']

    with allure.step("Creating a new kb article with restricted visibility"):
        utilities.start_existing_session(cookies=test_user)
        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            approve_first_revision=True, ready_for_localization=True,
            single_group=whitelisted_groups[0], is_template=is_template
        )

    with check, allure.step("Navigating to the article category field and verifying that the "
                            "restricted kb article is displayed for admin accounts"):
        utilities.navigate_to_link(article_details['article_url'])
        sumo_pages.kb_article_page.click_on_show_history_option()
        sumo_pages.kb_article_show_history_page.click_on_show_history_category()

        assert utilities.expect_locator_visibility(
            sumo_pages.kb_category_page.article_from_list(article_details['article_title'])
        )

    with check, allure.step("Verifying that the restricted kb article is displayed for users "
                            "belonging to a whitelisted group"):
        utilities.start_existing_session(cookies=test_user_two)
        assert utilities.expect_locator_visibility(
            sumo_pages.kb_category_page.article_from_list(article_details['article_title'])
        )

    with check, allure.step("Verifying that the restricted kb article is not displayed for users "
                            "belonging to a non-whitelisted group"):
        utilities.start_existing_session(cookies=test_user_three)
        expect(sumo_pages.kb_category_page.article_from_list(
            article_details['article_title'])).to_be_hidden()

    with allure.step("Verifying that the restricted kb article is not displayed for signed out "
                     "users"):
        utilities.delete_cookies()
        expect(sumo_pages.kb_category_page.article_from_list(
            article_details['article_title'])).to_be_hidden()

    with allure.step("Signing in with an admin account and whitelisting a new group"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(article_details['article_url'])
        sumo_pages.edit_article_metadata_flow.edit_article_metadata(
            single_group=whitelisted_groups[1]
        )

    with allure.step("Verifying that the restricted kb article is displayed for the second "
                     "whitelisted group users"):
        utilities.start_existing_session(cookies=test_user_three)
        utilities.navigate_to_link(article_details['article_url'])
        sumo_pages.kb_article_page.click_on_show_history_option()
        sumo_pages.kb_article_show_history_page.click_on_show_history_category()
        assert utilities.expect_locator_visibility(
            sumo_pages.kb_category_page.article_from_list(article_details['article_title'])
        )

    with allure.step("Removing restrictions"):
        utilities.navigate_to_link(article_details['article_url'])
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.edit_article_metadata_flow.remove_a_restricted_visibility_group(
            whitelisted_groups
        )

    utilities.navigate_to_link(article_details['article_url'])
    sumo_pages.kb_article_page.click_on_show_history_option()
    sumo_pages.kb_article_show_history_page.click_on_show_history_category()

    with allure.step("Navigating to the article discussion page and verifying that the "
                     "article is displayed for signed out users"):
        utilities.delete_cookies()
        assert utilities.expect_locator_visibility(
            sumo_pages.kb_category_page.article_from_list(article_details['article_title'])
        )


def _create_discussion_thread(page: Page) -> dict[str, Any]:
    sumo_pages = SumoPages(page)
    with allure.step("Posting a new kb article discussion thread"):
        thread = sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread()

    return thread
