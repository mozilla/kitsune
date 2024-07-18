import json
from typing import Any

import allure
from pytest_check import check
import pytest
from playwright.sync_api import expect, Page
from playwright_tests.core.testutilities import TestUtilities
from playwright_tests.messages.explore_help_articles.kb_article_page_messages import (
    KBArticlePageMessages)
from playwright_tests.pages.sumo_pages import SumoPages

with open("test_data/restricted_visibility_articles.json", "r") as restricted_kb_articles_file:
    restricted_kb_articles = json.load(restricted_kb_articles_file)
restricted_kb_articles_file.close()


# C2466509, C2483803
@pytest.mark.kbRestrictedVisibilitySingleGroup
@pytest.mark.parametrize("article_url", [
    (restricted_kb_articles["restricted_kb_article_url"]),
    (restricted_kb_articles["restricted_kb_template_url"]), ])
def test_kb_restrict_visibility_to_a_single_group(page: Page, article_url):
    sumo_pages = SumoPages(page)
    test_utilities = TestUtilities(page)
    test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
        test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
    ))
    test_utilities.navigate_to_link(article_url)
    sumo_pages.kb_article_page._click_on_article_option()
    article_url = test_utilities.get_page_url()
    with check, allure.step("Navigating to the article and verifying that 404 is not returned"):
        with page.expect_navigation() as navigation_info:
            test_utilities.navigate_to_link(article_url)
        response = navigation_info.value
        assert response.status != 404

    with check, allure.step("Verifying that the correct restricted banner is displayed"):
        assert (KBArticlePageMessages.KB_ARTICLE_RESTRICTED_BANNER in sumo_pages.kb_article_page
                ._get_restricted_visibility_banner_text())

    with allure.step("Signing out from SUMO"):
        test_utilities.delete_cookies()

    with check, allure.step("Navigating to the article and verifying that 404 is returned"):
        with page.expect_navigation() as navigation_info:
            test_utilities.navigate_to_link(article_url)
        response = navigation_info.value
        assert response.status == 404

    with check, allure.step("Signing in with a user which is not part of the whitelisted group"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_5"]
        ))

    with check, allure.step("Navigating to the article and verifying that 404 is returned"):
        with page.expect_navigation() as navigation_info:
            test_utilities.navigate_to_link(article_url)
        response = navigation_info.value
        assert response.status == 404

    with check, allure.step("Signing in with a user which is part of the whitelisted group"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_4"]
        ))

    with check, allure.step("Navigating to the article and verifying that 404 is not "
                            "returned"):
        with page.expect_navigation() as navigation_info:
            test_utilities.navigate_to_link(article_url)
        response = navigation_info.value
        assert response.status != 404

    with allure.step("Verifying that the correct restricted banner is displayed"):
        assert (KBArticlePageMessages.KB_ARTICLE_RESTRICTED_BANNER in sumo_pages.kb_article_page
                ._get_restricted_visibility_banner_text())


#  C2466510
@pytest.mark.kbRestrictedVisibilityMultipleGroups
@pytest.mark.parametrize("article_url", [
    (restricted_kb_articles["restricted_kb_article_url"]),
    (restricted_kb_articles["restricted_kb_template_url"]), ])
def test_kb_restrict_visibility_to_multiple_groups(page: Page, article_url):
    sumo_pages = SumoPages(page)
    test_utilities = TestUtilities(page)
    test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
        test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
    ))

    test_utilities.navigate_to_link(article_url)
    sumo_pages.kb_article_page._click_on_article_option()
    article_url = test_utilities.get_page_url()
    with allure.step("Signing in with a user which is part of the whitelisted groups"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_5"]
        ))

    with check, allure.step("Navigating to the article and verifying that 404 is not returned"):
        with page.expect_navigation() as navigation_info:
            test_utilities.navigate_to_link(article_url)
        response = navigation_info.value
        assert response.status != 404

    with check, allure.step("Verifying that the correct restricted banner is displayed"):
        assert (KBArticlePageMessages.KB_ARTICLE_RESTRICTED_BANNER in sumo_pages.kb_article_page
                ._get_restricted_visibility_banner_text())

    with allure.step("Signing in with a user which is part of the whitelisted groups"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_4"]
        ))

    with check, allure.step("Navigating to the article and verifying that 404 is not returned"):
        with page.expect_navigation() as navigation_info:
            test_utilities.navigate_to_link(article_url)
        response = navigation_info.value
        assert response.status != 404

    with check, allure.step("Verifying that the correct restricted banner is displayed"):
        assert (KBArticlePageMessages.KB_ARTICLE_RESTRICTED_BANNER in sumo_pages.kb_article_page
                ._get_restricted_visibility_banner_text())

    with allure.step("Signing in with a user which is not part of the whitelisted groups"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_2"]
        ))

    with allure.step("Navigating to the article and verifying that 404 is returned"):
        with page.expect_navigation() as navigation_info:
            test_utilities.navigate_to_link(article_url)
        response = navigation_info.value
        assert response.status == 404


# C2466511, C2466512
@pytest.mark.kbRestrictedVisibilitySingleGroup
@pytest.mark.parametrize("article_url", [
    (restricted_kb_articles['simple_article_url']),
    (restricted_kb_articles['simple_article_template_url'])
])
def test_kb_restricted_visibility_metadata_edit(page: Page, article_url):
    sumo_pages = SumoPages(page)
    test_utilities = TestUtilities(page)
    with allure.step("Signing in with an admin account and editing the metadata by adding a "
                     "group as whitelisted"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        test_utilities.navigate_to_link(article_url)
        if (sumo_pages.kb_article_edit_article_metadata_page
                ._is_clear_all_restricted_visibility_group_selection_visible()):
            sumo_pages.edit_article_metadata_flow._remove_a_restricted_visibility_group(
                group_name=''
            )
        sumo_pages.edit_article_metadata_flow.edit_article_metadata(
            single_group=test_utilities.kb_article_test_data['restricted_visibility_groups'][0]
        )

    with allure.step("Signing in with a user which is part of the second group"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_4"]
        ))

    with check, allure.step("Navigating to the article and verifying that 404 is not returned"):
        with page.expect_navigation() as navigation_info:
            test_utilities.navigate_to_link(article_url)
        response = navigation_info.value
        assert response.status != 404

    with allure.step("Signing in with an admin account and editing the metadata by adding a "
                     "different group as whitelisted"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        test_utilities.navigate_to_link(article_url)
        sumo_pages.edit_article_metadata_flow.edit_article_metadata(
            single_group=test_utilities.kb_article_test_data['restricted_visibility_groups'][1]
        )

    with allure.step("Signing in with a user which is part of the second group"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_5"]
        ))

    with check, allure.step("Navigating to the article and verifying that 404 is not returned"):
        with page.expect_navigation() as navigation_info:
            test_utilities.navigate_to_link(article_url)
        response = navigation_info.value
        assert response.status != 404

    with allure.step("Signing in with a user which is not part of the whitelisted groups"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_2"]
        ))

    with check, allure.step("Navigating to the article and verifying that 404 is returned"):
        with page.expect_navigation() as navigation_info:
            test_utilities.navigate_to_link(article_url)
        response = navigation_info.value
        assert response.status == 404

    with allure.step("Signing in with an admin account and removing the first group"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        sumo_pages.edit_article_metadata_flow._remove_a_restricted_visibility_group(
            test_utilities.kb_article_test_data['restricted_visibility_groups'][0])

    with allure.step("Signing in with an account belonging to the removed group"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_4"]
        ))

    with check, allure.step("Navigating to the article and verifying that the 404 is returned"):
        with page.expect_navigation() as navigation_info:
            test_utilities.navigate_to_link(article_url)
        response = navigation_info.value
        assert response.status == 404

    with allure.step("Signing in with an account that is part of the whitelisted group"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_5"]
        ))

    with check, allure.step("Navigating to the article and verifying that 404 is not returned"):
        with page.expect_navigation() as navigation_info:
            test_utilities.navigate_to_link(article_url)
        response = navigation_info.value
        assert response.status != 404

    with allure.step("Signing in with an admin account and removing all restricted groups"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        sumo_pages.edit_article_metadata_flow._remove_a_restricted_visibility_group(group_name='')

    with allure.step("Deleting user session"):
        test_utilities.delete_cookies()

    with check, allure.step("Navigating to the article and verifying that 404 is not returned"):
        with page.expect_navigation() as navigation_info:
            test_utilities.navigate_to_link(article_url)
        response = navigation_info.value
        assert response.status != 404

    with allure.step("Verifying that the restricted banner is no longer displayed"):
        assert not sumo_pages.kb_article_page._is_restricted_visibility_banner_text_displayed()


# C2466516
@pytest.mark.kbRestrictedVisibilitySingleGroup
@pytest.mark.parametrize("article_title", [
    (restricted_kb_articles['restricted_kb_article_title'])
])
def test_restricted_visibility_in_search_results(page: Page, article_title):
    sumo_pages = SumoPages(page)
    test_utilities = TestUtilities(page)
    with allure.step("Wait for ~1 minute until the kb article is available in search"):
        test_utilities.wait_for_given_timeout(60000)

    with allure.step("Clicking on the top-navbar sumo logo"):
        sumo_pages.top_navbar._click_on_sumo_nav_logo()

    with check, allure.step("Verifying that the article is not displayed inside the search "
                            "results"):
        sumo_pages.search_page._type_into_searchbar(article_title)
        expect(
            sumo_pages.search_page._get_locator_of_a_particular_article(article_title)
        ).to_be_hidden()

    with allure.step("Signing in with an account that is part of that whitelisted group"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_4"]
        ))

    with check, allure.step("Verifying that the article is not inside the search "
                            "results"):
        sumo_pages.search_page._type_into_searchbar(article_title)
        expect(sumo_pages.search_page._get_locator_of_a_particular_article(article_title)
               ).to_be_hidden()

    with allure.step("Signing in with an account that is not part of that whitelisted group"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_5"]
        ))

    with check, allure.step("Verifying that the article is not displayed inside the search "
                            "results"):
        sumo_pages.search_page._type_into_searchbar(article_title)
        expect(sumo_pages.search_page._get_locator_of_a_particular_article(article_title)
               ).to_be_hidden()

    with allure.step("Deleting the user session"):
        test_utilities.delete_cookies()

    with allure.step("Verifying that the article is not displayed inside the search results"):
        sumo_pages.search_page._type_into_searchbar(article_title)
        expect(sumo_pages.search_page._get_locator_of_a_particular_article(article_title)
               ).to_be_hidden()


# C2466518
@pytest.mark.kbRestrictedVisibilitySingleGroup
@pytest.mark.parametrize("article_title", [
    (restricted_kb_articles['restricted_kb_article_title']),
    (restricted_kb_articles['restricted_kb_template_title'])
])
def test_restricted_visibility_in_recent_revisions_single_group(page: Page, article_title):
    sumo_pages = SumoPages(page)
    test_utilities = TestUtilities(page)
    test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
        test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
    ))

    with check, allure.step("Navigating to the recent revisions page and verifying that the "
                            "article is displayed"):
        sumo_pages.top_navbar._click_on_recent_revisions_option()
        expect(sumo_pages.recent_revisions_page._get_recent_revision_based_on_article(
            article_title)).to_be_visible()

    with allure.step("Signing in with an account belonging to group one"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_4"]
        ))

    with check, allure.step("Verifying that the article is displayed"):
        expect(sumo_pages.recent_revisions_page._get_recent_revision_based_on_article(
            article_title)).to_be_visible()

    with allure.step("Signing in with a user belonging to a different user group"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_5"]
        ))

    with allure.step("Verifying that the article is not displayed"):
        expect(sumo_pages.recent_revisions_page._get_recent_revision_based_on_article(
            article_title)).to_be_hidden()


# C2466518
@pytest.mark.kbRestrictedVisibilityMultipleGroups
@pytest.mark.parametrize("article_title", [
    (restricted_kb_articles['restricted_kb_article_title']),
    (restricted_kb_articles['restricted_kb_template_title'])
])
def test_restricted_visibility_in_recent_revisions_multiple_groups(page: Page, article_title):
    sumo_pages = SumoPages(page)
    test_utilities = TestUtilities(page)
    with allure.step("Signing in with the user belonging to group 2 and verifying that the "
                     "article is displayed inside the recent revisions page"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_5"]
        ))
        sumo_pages.top_navbar._click_on_recent_revisions_option()

    with allure.step("Verifying that the article is displayed"):
        expect(sumo_pages.recent_revisions_page._get_recent_revision_based_on_article(
            article_title)).to_be_visible()


# C2466518
@pytest.mark.kbRemovedRestrictions
@pytest.mark.parametrize("article_title", [
    (restricted_kb_articles['restricted_kb_article_title']),
    (restricted_kb_articles['restricted_kb_template_title'])
])
def test_removed_restriction_in_recent_revisions(page: Page, article_title):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Navigating to the recent revisions page, signing out and verifying "
                     "that the article is displayed"):
        test_utilities.navigate_to_link(
            test_utilities.general_test_data['dashboard_links']['recent_revisions']
        )
        expect(sumo_pages.recent_revisions_page._get_recent_revision_based_on_article(
            article_title)).to_be_visible()


# C2466524
@pytest.mark.kbRestrictedVisibilitySingleGroup
@pytest.mark.parametrize("article_title", [
    (restricted_kb_articles['restricted_kb_article_title']),
    (restricted_kb_articles['restricted_kb_template_title'])
])
def test_kb_restricted_visibility_media_gallery_single_group(page: Page, article_title):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
        test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
    ))

    with allure.step("Navigating to the 'Media Gallery' page"):
        sumo_pages.top_navbar._click_on_media_gallery_option()

    with check, allure.step("Searching for the added image and verifying that the article is "
                            "displayed for admin users inside the 'Articles' image list"):
        sumo_pages.media_gallery._fill_search_media_gallery_searchbox_input_field(
            test_utilities.kb_article_test_data['article_image']
        )
        sumo_pages.media_gallery._click_on_media_gallery_searchbox_search_button()
        sumo_pages.media_gallery._select_media_file_from_list(
            test_utilities.kb_article_test_data['article_image']
        )
        assert article_title in (sumo_pages.media_gallery
                                 ._get_image_in_documents_list_items_text())

    with allure.step("Signing out from SUMO"):
        test_utilities.delete_cookies()

    with check, allure.step("Verifying that the article is not displayed for signed out "
                            "users inside the 'Articles image list'"):
        assert article_title not in (sumo_pages.media_gallery
                                     ._get_image_in_documents_list_items_text())

    with allure.step("Signing in with an account that is not part of a whitelisted group"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_5"]
        ))

    with check, allure.step("Verifying that the article is not displayed for users belonging "
                            "to a non-whitelisted group inside the 'Articles image list'"):
        assert article_title not in (sumo_pages.media_gallery
                                     ._get_image_in_documents_list_items_text())

    with allure.step("Signing in with an account that is part of the whitelisted group"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_4"]
        ))

    with allure.step("Verifying that the article is displayed for users belonging to a "
                     "whitelisted inside the 'Articles image list'"):
        assert article_title in (sumo_pages.media_gallery
                                 ._get_image_in_documents_list_items_text())


# C2466524
@pytest.mark.kbRestrictedVisibilityMultipleGroups
@pytest.mark.parametrize("article_title", [
    (restricted_kb_articles['restricted_kb_article_title']),
    (restricted_kb_articles['restricted_kb_template_title']),
])
def test_kb_restricted_visibility_media_gallery_multiple_groups(page: Page, article_title):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
        test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
    ))
    with allure.step("Navigating to the 'Media Gallery' page"):
        sumo_pages.top_navbar._click_on_media_gallery_option()

    with check, allure.step("Searching for the added image and verifying that the article is "
                            "displayed for admin users inside the 'Articles' image list"):
        sumo_pages.media_gallery._fill_search_media_gallery_searchbox_input_field(
            test_utilities.kb_article_test_data['article_image']
        )
        sumo_pages.media_gallery._click_on_media_gallery_searchbox_search_button()
        sumo_pages.media_gallery._select_media_file_from_list(
            test_utilities.kb_article_test_data['article_image']
        )

    with allure.step("Verifying that the article is displayed for users belonging to the "
                     "second whitelisted group"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_5"]
        ))
        assert article_title in (sumo_pages.media_gallery
                                 ._get_image_in_documents_list_items_text())


# C2466524
@pytest.mark.kbRemovedRestrictions
@pytest.mark.parametrize("article_title", [
    (restricted_kb_articles['restricted_kb_article_title']),
    (restricted_kb_articles['restricted_kb_template_title']),
])
def test_removed_restriction_in_media_gallery(page: Page, article_title):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
        test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
    ))

    with allure.step("Navigating to the media gallery image page and verifying that the "
                     "article is displayed for signed out users"):
        sumo_pages.top_navbar._click_on_media_gallery_option()
        sumo_pages.media_gallery._fill_search_media_gallery_searchbox_input_field(
            test_utilities.kb_article_test_data['article_image']
        )
        sumo_pages.media_gallery._click_on_media_gallery_searchbox_search_button()
        sumo_pages.media_gallery._select_media_file_from_list(
            test_utilities.kb_article_test_data['article_image']
        )
        test_utilities.delete_cookies()
        assert article_title in (sumo_pages.media_gallery
                                 ._get_image_in_documents_list_items_text())


# C2466531
@pytest.mark.kbRestrictedVisibilitySingleGroup
@pytest.mark.parametrize("thread_title", [
    (restricted_kb_articles['restricted_kb_article_thread']),
    (restricted_kb_articles['restricted_kb_template_thread'])
])
def test_kb_restricted_visibility_discussion_single_group(page: Page, thread_title):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
        test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
    ))

    with allure.step("Navigating to the Article Discussions page"):
        sumo_pages.top_navbar._click_on_article_discussions_option()

    with check, allure.step("Verifying that the the kb article is displayed for admin users"):
        expect(sumo_pages.article_discussions_page
               ._is_title_for_article_discussion_displayed(thread_title)).to_be_visible()

    with check, allure.step("Verifying that the kb article is displayed for whitelisted "
                            "group users"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_4"]
        ))
        expect(sumo_pages.article_discussions_page
               ._is_title_for_article_discussion_displayed(thread_title)).to_be_visible()

    with check, allure.step("Verifying that the kb article is not displayed for signed out "
                            "users"):
        test_utilities.delete_cookies()
        expect(sumo_pages.article_discussions_page
               ._is_title_for_article_discussion_displayed(thread_title)).to_be_hidden()

    with allure.step("Verifying that the kb article is displayed for non-whitelisted group "
                     "users"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_5"]
        ))
        expect(sumo_pages.article_discussions_page
               ._is_title_for_article_discussion_displayed(thread_title)).to_be_hidden()


# C2466531
@pytest.mark.kbRestrictedVisibilityMultipleGroups
@pytest.mark.parametrize("thread_title", [
    (restricted_kb_articles['restricted_kb_article_thread']),
    (restricted_kb_articles['restricted_kb_template_thread'])
])
def test_kb_restricted_visibility_discussion_multiple_groups(page: Page, thread_title):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Navigating to the article discussion page and verifying that the "
                     "article is displayed inside the article discussions list for the "
                     "second whitelisted group user"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_5"]
        ))
        test_utilities.navigate_to_link(
            test_utilities.general_test_data['discussions_links']['article_discussions']
        )
        expect(sumo_pages.article_discussions_page
               ._is_title_for_article_discussion_displayed(thread_title)).to_be_visible()


# C2466531
@pytest.mark.kbRemovedRestrictions
@pytest.mark.parametrize("thread_title", [
    (restricted_kb_articles['restricted_kb_article_thread']),
    (restricted_kb_articles['restricted_kb_template_thread'])
])
def test_kb_restricted_visibility_discussion_removed_restriction(page: Page, thread_title):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Navigating to the article discussion page and verifying that the "
                     "article is displayed for signed out users"):
        test_utilities.delete_cookies()
        test_utilities.navigate_to_link(
            test_utilities.general_test_data['discussions_links']['article_discussions']
        )
        expect(sumo_pages.article_discussions_page
               ._is_title_for_article_discussion_displayed(thread_title)).to_be_visible()


# C2466533
@pytest.mark.kbRestrictedVisibilitySingleGroup
@pytest.mark.parametrize("article_title, article_url", [
    (restricted_kb_articles['restricted_kb_article_title'],
     restricted_kb_articles["restricted_kb_article_url"])
])
def test_kb_restricted_visibility_in_topics_page_single_group(page: Page, article_title,
                                                              article_url):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
        test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
    ))

    test_utilities.navigate_to_link(article_url)
    sumo_pages.kb_article_page._click_on_article_option()
    with allure.step("Clicking on the article child topic"):
        sumo_pages.kb_article_page._click_on_a_particular_breadcrumb(
            restricted_kb_articles['restricted_kb_article_child_topic']
        )

    with check, allure.step("Verifying that the article is listed inside the article topic "
                            "page for admin users"):
        expect(sumo_pages.product_topics_page._get_a_particular_article_locator(article_title)
               ).to_be_visible()

    with check, allure.step("Verifying that the article is not listed for signed out users"):
        test_utilities.delete_cookies()
        expect(sumo_pages.product_topics_page._get_a_particular_article_locator(article_title)
               ).to_be_hidden()

    with check, allure.step("Verifying that the article is listed for users belonging to a "
                            "whitelisted group"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_4"]
        ))
        expect(sumo_pages.product_topics_page._get_a_particular_article_locator(article_title)
               ).to_be_visible()

    with allure.step("Verifying that the article is not listed for users belonging to a "
                     "non-whitelisted group"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_5"]
        ))
        expect(sumo_pages.product_topics_page._get_a_particular_article_locator(article_title)
               ).to_be_hidden()


# C2466533
@pytest.mark.kbRestrictedVisibilityMultipleGroups
@pytest.mark.parametrize("article_title, article_url", [
    (restricted_kb_articles['restricted_kb_article_title'],
     restricted_kb_articles["restricted_kb_article_url"])
])
def test_kb_restricted_visibility_in_topics_page_multiple_groups(page: Page, article_title,
                                                                 article_url):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
        test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
    ))

    test_utilities.navigate_to_link(article_url)
    sumo_pages.kb_article_page._click_on_article_option()
    with allure.step("Clicking on the article child topic"):
        sumo_pages.kb_article_page._click_on_a_particular_breadcrumb(
            restricted_kb_articles['restricted_kb_article_child_topic']
        )

    with allure.step("Verifying that the article is displayed for the second whitelisted "
                     "group"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_5"]
        ))
        expect(sumo_pages.product_topics_page._get_a_particular_article_locator(article_title)
               ).to_be_visible()


#  C2539825
@pytest.mark.kbRestrictedVisibilitySingleGroup
@pytest.mark.parametrize("article_title", [
    (restricted_kb_articles['restricted_kb_article_title']),
    (restricted_kb_articles['restricted_kb_template_title'])
])
def test_kb_restricted_visibility_profile_level_single_group(page: Page, article_title):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
        test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
    ))

    with allure.step("Navigating to the user profile page"):
        sumo_pages.top_navbar._click_on_view_profile_option()

    with allure.step("Clicking on the documents link"):
        sumo_pages.my_profile_page._click_on_my_profile_document_link()
        op_document_contributions_link = test_utilities.get_page_url()

    with check, allure.step("Verifying that the article is displayed inside the document "
                            "contribution page for admin users"):
        expect(sumo_pages.my_documents_page._get_a_particular_document_locator(article_title)
               ).to_be_visible()

    with check, allure.step("Verifying that the article is displayed inside the op document "
                            "contributions list for a whitelisted user"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_4"]
        ))
        test_utilities.navigate_to_link(op_document_contributions_link)
        expect(sumo_pages.my_documents_page._get_a_particular_document_locator(article_title)
               ).to_be_visible()

    with allure.step("Verifying that the article is not displayed inside the op document "
                     "contributions list for a non whitelisted user"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_5"]
        ))
        test_utilities.navigate_to_link(op_document_contributions_link)
        expect(sumo_pages.my_documents_page._get_a_particular_document_locator(article_title)
               ).to_be_hidden()


#  C2539825
@pytest.mark.kbRestrictedVisibilityMultipleGroups
@pytest.mark.parametrize("article_title", [
    (restricted_kb_articles['restricted_kb_article_title']),
    (restricted_kb_articles['restricted_kb_template_title'])])
def test_kb_restricted_visibility_profile_level_multiple_groups(page: Page, article_title):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
        test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
    ))

    with allure.step("Navigating to the user profile page"):
        sumo_pages.top_navbar._click_on_view_profile_option()

    with allure.step("Clicking on the documents link"):
        sumo_pages.my_profile_page._click_on_my_profile_document_link()

    with allure.step("Verifying that the article is displayed inside the op document "
                     "contributions list for the newly whitelisted users group"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_5"]
        ))
        expect(sumo_pages.my_documents_page._get_a_particular_document_locator(article_title)
               ).to_be_visible()


#  C2539825
@pytest.mark.kbRemovedRestrictions
@pytest.mark.parametrize("article_title", [
    (restricted_kb_articles['restricted_kb_article_title']),
    (restricted_kb_articles['restricted_kb_template_title']),
])
def test_kb_restricted_visibility_profile_level_restriction_removed(page: Page, article_title):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
        test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
    ))

    with allure.step("Navigating to the user profile page"):
        sumo_pages.top_navbar._click_on_view_profile_option()

    with allure.step("Clicking on the documents link"):
        sumo_pages.my_profile_page._click_on_my_profile_document_link()

    with allure.step("Verifying that the article is displayed inside the op document list "
                     "for signed out users"):
        test_utilities.delete_cookies()
        expect(sumo_pages.my_documents_page._get_a_particular_document_locator(article_title)
               ).to_be_visible()


# C2468303
@pytest.mark.kbRestrictedVisibilitySingleGroup
@pytest.mark.parametrize("article_title", [
    (restricted_kb_articles['restricted_kb_article_title']),
    (restricted_kb_articles['restricted_kb_template_title'])
])
def test_kb_restricted_visibility_in_l10n_dashboards_single_restriction(page: Page, article_title):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
        test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
    ))

    with check, allure.step("Verifying that the article is displayed for admin users inside "
                            "the kb-overview dashboard"):
        test_utilities.navigate_to_link(
            test_utilities.general_test_data['dashboard_links']['l10n_most_visited_translations'])
        expect(sumo_pages.kb_dashboard_page._get_a_particular_article_title_locator(article_title)
               ).to_be_visible()

    with check, allure.step("Verifying that the article is displayed for users belonging to "
                            "the whitelisted group"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_4"]
        ))
        test_utilities.navigate_to_link(
            test_utilities.general_test_data['dashboard_links']['l10n_most_visited_translations'])
        expect(sumo_pages.kb_dashboard_page._get_a_particular_article_title_locator(article_title)
               ).to_be_visible()

    with allure.step("Verifying that the article is not displayed for users belonging to "
                     "non-whitelisted groups"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_5"]
        ))
        test_utilities.navigate_to_link(
            test_utilities.general_test_data['dashboard_links']['l10n_most_visited_translations'])
        expect(sumo_pages.kb_dashboard_page._get_a_particular_article_title_locator(article_title)
               ).to_be_hidden()


# C2468303
@pytest.mark.kbRemovedRestrictions
@pytest.mark.parametrize("article_title", [
    (restricted_kb_articles['restricted_kb_article_title']),
    (restricted_kb_articles['restricted_kb_template_title'])
])
def test_kb_restricted_visibility_in_l10n_dashboards_removed_restriction(page: Page,
                                                                         article_title):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing out and verifying that the article is displayed inside the "
                     "kb-overview dashboard"):
        test_utilities.delete_cookies()
        test_utilities.navigate_to_link(
            test_utilities.general_test_data['dashboard_links']['l10n_most_visited_translations'])
        expect(sumo_pages.kb_dashboard_page._get_a_particular_article_title_locator(article_title)
               ).to_be_visible()


# C2466519
@pytest.mark.kbRestrictedVisibilitySingleGroup
@pytest.mark.parametrize("article_title", [
    (restricted_kb_articles['restricted_kb_article_title']),
    (restricted_kb_articles['restricted_kb_article_title'])
])
def test_kb_restricted_visibility_in_dashboards_single_group(page: Page, article_title):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
        test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
    ))

    with check, allure.step("Verifying that the article is displayed for admin users inside "
                            "the kb-overview dashboard"):
        test_utilities.navigate_to_link(
            test_utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page._get_a_particular_article_title_locator(article_title)
               ).to_be_visible()

    with check, allure.step("Verifying that the article is displayed for users belonging to "
                            "the whitelisted group"):
        sumo_pages.top_navbar._click_on_sumo_nav_logo()
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_4"]
        ))
        test_utilities.navigate_to_link(
            test_utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page._get_a_particular_article_title_locator(article_title)
               ).to_be_visible()

    with allure.step("Verifying that the article is not displayed for users belonging to "
                     "non-whitelisted groups"):
        sumo_pages.top_navbar._click_on_sumo_nav_logo()
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_5"]
        ))
        test_utilities.navigate_to_link(
            test_utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page._get_a_particular_article_title_locator(article_title)
               ).to_be_hidden()


# C2466519
@pytest.mark.kbRemovedRestrictions
@pytest.mark.parametrize("article_title", [
    (restricted_kb_articles['restricted_kb_article_title']),
    (restricted_kb_articles['restricted_kb_article_title'])
])
def test_kb_restricted_visibility_in_dashboards_removed_restriction(page: Page, article_title):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing out and verifying that the article is displayed inside the "
                     "kb-overview dashboard"):
        test_utilities.delete_cookies()
        test_utilities.navigate_to_link(
            test_utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page._get_a_particular_article_title_locator(article_title)
               ).to_be_visible()


# C2539174 C2101640
@pytest.mark.kbRestrictedVisibilitySingleGroup
@pytest.mark.parametrize("article_title", [
    (restricted_kb_articles['restricted_kb_article_title']),
    (restricted_kb_articles['restricted_kb_template_title'])
])
def test_kb_restricted_visibility_what_links_here_page_single_group(page: Page, article_title):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
        test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
    ))

    with allure.step("Navigating to the test article linked to the document"):
        test_utilities.navigate_to_link(test_utilities.general_test_data['test_article_link'])

    with check, allure.step("Navigating to the 'What Links Here' page and verifying that the "
                            "restricted article is displayed for admin accounts"):
        sumo_pages.kb_article_page._click_on_what_links_here_option()
        expect(
            sumo_pages.kb_what_links_here_page._get_a_particular_what_links_here_article_locator(
                article_title)).to_be_visible()

    with check, allure.step("Verifying that the restricted article is displayed for users "
                            "belonging to a whitelisted group"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_4"]
        ))
        expect(sumo_pages.kb_what_links_here_page
               ._get_a_particular_what_links_here_article_locator(article_title)).to_be_visible()

    with check, allure.step("Verifying that the restricted article is not displayed for "
                            "users belonging to a non-whitelisted group"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_5"]
        ))
        expect(
            sumo_pages.kb_what_links_here_page
            ._get_a_particular_what_links_here_article_locator(article_title)
        ).to_be_hidden()

    with allure.step("Verifying that the article is not displayed for signed out users"):
        test_utilities.delete_cookies()
        expect(sumo_pages.kb_what_links_here_page.
               _get_a_particular_what_links_here_article_locator(article_title)).to_be_hidden()


# C2539174
@pytest.mark.kbRestrictedVisibilityMultipleGroups
@pytest.mark.parametrize("article_title", [
    (restricted_kb_articles['restricted_kb_article_title']),
    (restricted_kb_articles['restricted_kb_template_title'])
])
def test_kb_restricted_visibility_what_links_here_page_multiple_groups(page: Page, article_title):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
        test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_5"]
    ))
    with allure.step("Navigating to the test article linked to the document"):
        test_utilities.navigate_to_link(test_utilities.general_test_data['test_article_link'])

    with allure.step("Navigating to the 'What Links Here' page and verifying that the linked "
                     "article is displayed to the newly added group members"):
        sumo_pages.kb_article_page._click_on_what_links_here_option()
        expect(sumo_pages.kb_what_links_here_page
               ._get_a_particular_what_links_here_article_locator(article_title)).to_be_visible()


# C2539174
@pytest.mark.kbRemovedRestrictions
@pytest.mark.parametrize("article_title", [
    (restricted_kb_articles['restricted_kb_article_title']),
    (restricted_kb_articles['restricted_kb_template_title'])
])
def test_kb_restricted_visibility_what_links_here_page_removed_restrictions(page: Page,
                                                                            article_title):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
        test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
    ))
    with allure.step("Navigating to the test article linked to the document"):
        test_utilities.navigate_to_link(test_utilities.general_test_data['test_article_link'])

    with allure.step("Navigating to the 'What Links Here' page and verifying that the "
                     "article is displayed for signed out users"):
        sumo_pages.kb_article_page._click_on_what_links_here_option()
        test_utilities.delete_cookies()
        expect(sumo_pages.kb_what_links_here_page
               ._get_a_particular_what_links_here_article_locator(article_title)).to_be_visible()


# C2539824
@pytest.mark.kbRestrictedVisibilitySingleGroup
@pytest.mark.parametrize("article_title, article_url", [
    (restricted_kb_articles['restricted_kb_article_title'],
     restricted_kb_articles['restricted_kb_article_url']),
    (restricted_kb_articles['restricted_kb_template_title'],
     restricted_kb_articles['restricted_kb_template_url'])
])
def test_kb_restricted_visibility_category_page_single_group(page: Page,
                                                             article_title, article_url):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
        test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
    ))

    with check, allure.step("Navigating to the article category field and verifying that the "
                            "restricted kb article is displayed for admin accounts"):
        test_utilities.navigate_to_link(article_url)
        sumo_pages.kb_article_page._click_on_show_history_option()
        sumo_pages.kb_article_show_history_page._click_on_show_history_category()

        expect(sumo_pages.kb_category_page._get_a_particular_article_locator_from_list(
            article_title)).to_be_visible()

    with check, allure.step("Verifying that the restricted kb article is displayed for users "
                            "belonging to a whitelisted group"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_4"]
        ))
        expect(sumo_pages.kb_category_page._get_a_particular_article_locator_from_list(
            article_title)).to_be_visible()

    with check, allure.step("Verifying that the restricted kb article is displayed for users "
                            "belonging to a non-whitelisted group"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_5"]
        ))
        expect(sumo_pages.kb_category_page._get_a_particular_article_locator_from_list(
            article_title)).to_be_hidden()

    with allure.step("Verifying that the restricted kb article is displayed for signed out "
                     "users"):
        test_utilities.delete_cookies()
        expect(sumo_pages.kb_category_page._get_a_particular_article_locator_from_list(
            article_title)).to_be_hidden()


# C2539824
@pytest.mark.kbRestrictedVisibilityMultipleGroups
@pytest.mark.parametrize("article_title, article_url", [
    (restricted_kb_articles['restricted_kb_article_title'],
     restricted_kb_articles['restricted_kb_article_url']),
    (restricted_kb_articles['restricted_kb_template_title'],
     restricted_kb_articles['restricted_kb_template_url'])
])
def test_kb_restricted_visibility_category_page_multiple_groups(page: Page, article_title,
                                                                article_url):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Verifying that the restricted kb article is displayed for the second "
                     "whitelisted group users"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_5"]
        ))
        test_utilities.navigate_to_link(article_url)
        sumo_pages.kb_article_page._click_on_show_history_option()
        sumo_pages.kb_article_show_history_page._click_on_show_history_category()
        expect(sumo_pages.kb_category_page._get_a_particular_article_locator_from_list(
            article_title)).to_be_visible()


# C2539824
@pytest.mark.kbRemovedRestrictions
@pytest.mark.parametrize("article_title, article_url", [
    (restricted_kb_articles['restricted_kb_article_title'],
     restricted_kb_articles['restricted_kb_article_url']),
    (restricted_kb_articles['restricted_kb_template_title'],
     restricted_kb_articles['restricted_kb_template_url'])
])
def test_kb_restricted_visibility_category_page_removed_restriction(page: Page, article_title,
                                                                    article_url):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
        test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
    ))
    test_utilities.navigate_to_link(article_url)
    sumo_pages.kb_article_page._click_on_show_history_option()
    sumo_pages.kb_article_show_history_page._click_on_show_history_category()

    with allure.step("Navigating to the article discussion page and verifying that the "
                     "article is displayed for signed out users"):
        test_utilities.delete_cookies()
        expect(
            sumo_pages.kb_category_page._get_a_particular_article_locator_from_list(
                article_title
            )
        ).to_be_visible()


@pytest.mark.whitelistingDifferentGroup
def test_whitelisting_a_different_group(page: Page):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
        test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
    ))

    for key, value in restricted_kb_articles.items():
        if key.endswith("_url"):
            test_utilities.navigate_to_link(value)
            sumo_pages.edit_article_metadata_flow.edit_article_metadata(
                single_group=test_utilities.kb_article_test_data['restricted_visibility_groups'][1]
            )


@pytest.mark.removingAllArticleRestrictions
def test_removing_all_article_restrictions(page: Page):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
        test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
    ))

    for key, value in restricted_kb_articles.items():
        if key.endswith("_url"):
            test_utilities.navigate_to_link(value)
            sumo_pages.edit_article_metadata_flow._remove_a_restricted_visibility_group(
                group_name=''
            )


@pytest.mark.restrictedArticleCreation
def test_create_articles_for_restriction_test(page: Page):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
        test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
    ))

    restricted_kb_article = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
        single_group=test_utilities.kb_article_test_data['restricted_visibility_groups'][0],
        article_content_image=test_utilities.kb_article_test_data['article_image']
    )

    sumo_pages.submit_kb_article_flow.approve_kb_revision(
        revision_id=sumo_pages.kb_article_show_history_page._get_last_revision_id(),
        ready_for_l10n=True
    )
    restricted_kb_article_thread = _create_discussion_thread(page)

    restricted_kb_template = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
        is_template=True,
        single_group=test_utilities.kb_article_test_data['restricted_visibility_groups'][0],
        article_content_image=test_utilities.kb_article_test_data['article_image']
    )

    sumo_pages.submit_kb_article_flow.approve_kb_revision(
        revision_id=sumo_pages.kb_article_show_history_page._get_last_revision_id(),
        ready_for_l10n=True
    )

    restricted_kb_template_thread = _create_discussion_thread(page)

    simple_article = sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

    sumo_pages.submit_kb_article_flow.approve_kb_revision(
        revision_id=sumo_pages.kb_article_show_history_page._get_last_revision_id(),
        ready_for_l10n=True
    )

    simple_article_template = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
        is_template=True
    )

    sumo_pages.submit_kb_article_flow.approve_kb_revision(
        revision_id=sumo_pages.kb_article_show_history_page._get_last_revision_id(),
        ready_for_l10n=True
    )

    # Dumping the necessary data into a JSON for further test usage
    dictionary = {
        "restricted_kb_article_title": restricted_kb_article['article_title'],
        "restricted_kb_article_url": restricted_kb_article['article_url'],
        "restricted_kb_article_thread": restricted_kb_article_thread['thread_title'],
        "restricted_kb_article_child_topic": restricted_kb_article['article_child_topic'],
        "restricted_kb_template_title": restricted_kb_template['article_title'],
        "restricted_kb_template_url": restricted_kb_template['article_url'],
        "restricted_kb_template_thread": restricted_kb_template_thread['thread_title'],
        "simple_article_url": simple_article["article_url"],
        "simple_article_template_url": simple_article_template["article_url"]
    }

    with open("test_data/restricted_visibility_articles.json", "w") as restricted_articles:
        json.dump(dictionary, restricted_articles)


def _create_discussion_thread(page: Page) -> dict[str, Any]:
    sumo_pages = SumoPages(page)
    with allure.step("Posting a new kb article discussion thread"):
        sumo_pages.kb_article_page._click_on_editing_tools_discussion_option()
        sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()
        thread = sumo_pages.kb_article_thread_flow.add_new_kb_discussion_thread()

    return thread


@pytest.mark.deleteAllRestrictedTestArticles
def test_delete_all_created_articles(page: Page):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
        test_utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
    ))

    for key, value in restricted_kb_articles.items():
        if key.endswith("_url"):
            test_utilities.navigate_to_link(value)
            sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # Deleting all articles from the JSON file
    with open("test_data/restricted_visibility_articles.json", "w") as restricted_kbs_file:
        json.dump({
            "restricted_kb_article_title": "",
            "restricted_kb_article_url": "",
            "restricted_kb_article_thread": "",
            "restricted_kb_article_child_topic": "",
            "restricted_kb_template_title": "",
            "restricted_kb_template_url": "",
            "restricted_kb_template_thread": "",
            "simple_article_url": "",
            "simple_article_template_url": ""
        }, restricted_kbs_file)
