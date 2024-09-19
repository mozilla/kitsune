import re

import allure
import pytest
from playwright.sync_api import Page
from pytest_check import check
import requests

from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.ask_a_question_messages.contact_support_messages import \
    ContactSupportMessages
from playwright_tests.messages.contribute_messages.con_discussions.support_forums_messages import \
    SupportForumsPageMessages
from playwright_tests.messages.explore_help_articles.products_page_messages import \
    ProductsPageMessages
from playwright_tests.messages.top_navbar_messages import TopNavbarMessages
from playwright_tests.pages.sumo_pages import SumoPages


# C876534, C890961
@pytest.mark.topNavbarTests
def test_number_of_options_not_signed_in(page: Page):
    sumo_pages = SumoPages(page)
    with check, allure.step("Verifying that the SUMO logo is successfully displayed"):
        image = sumo_pages.top_navbar.get_sumo_nav_logo()
        image_link = image.get_attribute("src")
        response = requests.get(image_link, stream=True)
        assert response.status_code < 400

    with allure.step("Verifying that the top-navbar for signed in users contains: Explore "
                     "Help Articles, Community Forums, Ask a Question and Contribute"):
        top_navbar_items = sumo_pages.top_navbar.get_available_menu_titles()
        assert top_navbar_items == TopNavbarMessages.TOP_NAVBAR_OPTIONS, (
            "Incorrect elements displayed in top-navbar for signed out state"
        )


# C876539
@pytest.mark.topNavbarTests
def test_number_of_options_signed_in(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in using a non-admin user"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts['TEST_ACCOUNT_12']
        ))

    with check, allure.step("Verifying that the SUMO logo is successfully displayed"):
        image = sumo_pages.top_navbar.get_sumo_nav_logo()
        image_link = image.get_attribute("src")
        response = requests.get(image_link, stream=True)
        assert response.status_code < 400

    with allure.step("Verifying that the top-navbar contains: Explore Help Articles, "
                     "Community Forums, Ask a Question, Contribute"):
        top_navbar_items = sumo_pages.top_navbar.get_available_menu_titles()
        assert top_navbar_items == TopNavbarMessages.TOP_NAVBAR_OPTIONS, (
            "Incorrect elements displayed in top-navbar for " "signed-in state"
        )


# C2462866
@pytest.mark.topNavbarTests
def test_explore_by_product_redirects(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    with allure.step("Clicking on all options from the 'Explore Help Articles' and verifying the "
                     "redirect"):
        for index, option in enumerate(sumo_pages.top_navbar
                                       .get_all_explore_by_product_options_locators()):
            if index > 0:
                sumo_pages.top_navbar.hover_over_explore_by_product_top_navbar_option()
            current_option = re.sub(
                r'\s+', ' ', sumo_pages.top_navbar._get_text_of_locator(option)).strip()
            if sumo_pages.top_navbar._is_locator_visible(option):
                sumo_pages.top_navbar._click(option)
            else:
                sumo_pages.top_navbar.hover_over_explore_by_product_top_navbar_option()
                sumo_pages.top_navbar._click(option)

            if current_option == "Firefox desktop":
                current_option = utilities.remove_character_from_string(current_option, 'desktop')

            if current_option != "View all products":
                support_page = sumo_pages.product_support_page._get_product_support_title_text()
                assert current_option in support_page
            else:
                assert (sumo_pages.products_page._get_page_header() == ProductsPageMessages.
                        PRODUCTS_PAGE_HEADER)


# C2462867, C2663957
@pytest.mark.topNavbarTests
def test_explore_by_topic_redirects(page: Page):
    sumo_pages = SumoPages(page)
    with allure.step("Clicking on all options from the 'Explore by topic' and verifying the "
                     "redirect"):
        for index, option in enumerate(sumo_pages.top_navbar.get_all_explore_by_topic_locators()):
            if index > 0:
                sumo_pages.top_navbar.hover_over_explore_by_product_top_navbar_option()
            current_option = re.sub(
                r'\s+', ' ', sumo_pages.top_navbar._get_text_of_locator(option)).strip()
            if sumo_pages.top_navbar._is_locator_visible(option):
                sumo_pages.top_navbar._click(option)
            else:
                sumo_pages.top_navbar.hover_over_explore_by_product_top_navbar_option()
                sumo_pages.top_navbar._click(option)

            assert (current_option == sumo_pages.explore_by_topic_page
                    ._get_explore_by_topic_page_header())

            with allure.step("Verifying that the correct option is selected inside the 'All "
                             "Topics' side navbar"):
                assert (current_option == sumo_pages.explore_by_topic_page
                        ._get_selected_topic_side_navbar_option())

            with allure.step("Verifying that the 'All Products' option is displayed inside the "
                             "'Filter by product' dropdown"):
                assert (sumo_pages.explore_by_topic_page
                        ._get_current_product_filter_dropdown_option()) == 'All Products'


# C2462868
@pytest.mark.topNavbarTests
def test_browse_by_product_community_forum_redirect(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    utilities.start_existing_session(utilities.username_extraction_from_email(
        utilities.user_secrets_accounts['TEST_ACCOUNT_12']
    ))
    with allure.step("Clicking on all options from the 'Browse by product' and verifying the "
                     "redirect"):
        for index, option in enumerate(sumo_pages.top_navbar
                                       .get_all_browse_by_product_options_locators()):
            if index > 0:
                sumo_pages.top_navbar.hover_over_community_forums_top_navbar_option()
            current_option = re.sub(
                r'\s+', ' ', sumo_pages.top_navbar._get_text_of_locator(option)).strip()
            if sumo_pages.top_navbar._is_locator_visible(option):
                sumo_pages.top_navbar._click(option)
            else:
                sumo_pages.top_navbar.hover_over_community_forums_top_navbar_option()
                sumo_pages.top_navbar._click(option)

            if current_option == "Firefox desktop":
                current_option = utilities.remove_character_from_string(
                    current_option, 'desktop').rstrip()

            if current_option != "View all forums":
                assert (f"{current_option} Community Forum" == sumo_pages.product_support_page
                        ._get_product_support_title_text())
            else:
                assert utilities.get_page_url() == SupportForumsPageMessages.PAGE_URL


# C2462869
@pytest.mark.topNavbarTests
def test_browse_all_forum_threads_by_topic_redirect(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    utilities.start_existing_session(utilities.username_extraction_from_email(
        utilities.user_secrets_accounts['TEST_ACCOUNT_12']
    ))
    with allure.step("Clicking on all options from the 'Browse all forum threads by topic' and "
                     "verifying the redirect"):
        for index, option in enumerate(sumo_pages.top_navbar
                                       .get_all_browse_all_forum_threads_by_topic_locators()):
            if index > 0:
                sumo_pages.top_navbar.hover_over_community_forums_top_navbar_option()
            current_option = re.sub(
                r'\s+', ' ', sumo_pages.top_navbar._get_text_of_locator(option)).strip()
            if sumo_pages.top_navbar._is_locator_visible(option):
                sumo_pages.top_navbar._click(option)
            else:
                sumo_pages.top_navbar.hover_over_community_forums_top_navbar_option()
                sumo_pages.top_navbar._click(option)

            assert (sumo_pages.product_support_page._get_product_support_title_text()
                    == "All Products Community Forum")

            with allure.step("Verifying that the correct default topic filter is selected"):
                assert (sumo_pages.product_support_forum._get_selected_topic_option()
                        == current_option)


# T5696576, T5696591
@pytest.mark.topNavbarTests
def test_ask_a_question_top_navbar_redirect(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    with allure.step("Clicking on all options from the 'Ask a Question' and verifying the "
                     "redirect"):
        for index, option in enumerate(sumo_pages.top_navbar.get_all_ask_a_question_locators()):
            if index > 0:
                sumo_pages.top_navbar.hover_over_ask_a_question_top_navbar()
            current_option = re.sub(
                r'\s+', ' ', sumo_pages.top_navbar._get_text_of_locator(option)).strip()
            if sumo_pages.top_navbar._is_locator_visible(option):
                sumo_pages.top_navbar._click(option)
            else:
                sumo_pages.top_navbar.hover_over_ask_a_question_top_navbar()
                sumo_pages.top_navbar._click(option)

            if current_option == "Firefox desktop":
                current_option = utilities.remove_character_from_string(
                    current_option, 'desktop').rstrip()
            elif current_option == "Monitor":
                current_option = f"Mozilla {current_option}"

            if current_option != "View all":
                assert (f"{current_option} Solutions" == sumo_pages.product_solutions_page
                        ._get_product_solutions_heading())
            else:
                assert utilities.get_page_url() == ContactSupportMessages.PAGE_URL


# C2462871
@pytest.mark.topNavbarTests
def test_contribute_top_navbar_redirects(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    utilities.start_existing_session(utilities.username_extraction_from_email(
        utilities.user_secrets_accounts['TEST_ACCOUNT_13']
    ))

    with allure.step("Clicking on the 'Contributor discussions' top-navbar option and verifying "
                     "the redirect"):
        sumo_pages.top_navbar.click_on_community_discussions_top_navbar_option()
        assert (sumo_pages.contributor_discussions_page._get_contributor_discussions_page_title()
                == "Contributor Discussions")

    with allure.step("Clicking on the 'Contributor discussions' top-navbar options and verifying "
                     "the redirects"):
        for index, option in enumerate(sumo_pages.top_navbar
                                       .get_all_contributor_discussions_locators()):
            if index > 0:
                sumo_pages.top_navbar.hover_over_contribute_top_navbar()
            current_option = re.sub(
                r'\s+', ' ', sumo_pages.top_navbar._get_text_of_locator(option)).strip()
            if sumo_pages.top_navbar._is_locator_visible(option):
                sumo_pages.top_navbar._click(option)
            else:
                sumo_pages.top_navbar.hover_over_contribute_top_navbar()
                sumo_pages.top_navbar._click(option)

            if current_option == "Article discussions":
                assert (sumo_pages.discussions_page._get_contributor_discussions_page_title()
                        .lower()
                        == "english knowledge base discussions")
                with allure.step("Verifying that the correct option is highlighted inside the "
                                 "'Contributor discussions' side navbar"):
                    assert (sumo_pages.discussions_page
                            ._get_contributor_discussions_side_nav_selected_option()
                            == current_option)
            elif current_option == "View all discussions":
                assert (sumo_pages.contributor_discussions_page
                        ._get_contributor_discussions_page_title(
                        ).lower() == "contributor discussions")
            else:
                assert (sumo_pages.discussions_page._get_contributor_discussions_page_title()
                        .lower() == current_option.lower())
                with allure.step("Verifying that the correct option is highlighted inside the "
                                 "'Contributor discussions' side navbar"):
                    assert (sumo_pages.discussions_page
                            ._get_contributor_discussions_side_nav_selected_option()
                            == current_option)
