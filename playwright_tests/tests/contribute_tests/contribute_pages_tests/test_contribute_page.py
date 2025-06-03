import allure
import pytest
from playwright.sync_api import Page
from pytest_check import check
import requests

from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.contribute_messages.con_pages.con_forum_messages import (
    ContributeForumMessages)
from playwright_tests.messages.contribute_messages.con_pages.con_help_articles_messages import (
    ContributeHelpArticlesMessages)
from playwright_tests.messages.contribute_messages.con_pages.con_localization_messages import (
    ContributeLocalizationMessages)
from playwright_tests.messages.contribute_messages.con_pages.con_page_messages import (
    ContributePageMessages)
from playwright_tests.messages.homepage_messages import HomepageMessages
from playwright_tests.pages.sumo_pages import SumoPages


# C2165413
@pytest.mark.contributePagesTests
def test_contribute_page_text(page: Page):
    sumo_pages = SumoPages(page)
    with allure.step("Clicking on the Contribute top-navbar option"):
        sumo_pages.top_navbar.click_on_contribute_top_navbar_option()

    with check, allure.step("Verifying that the correct page hero header text is displayed"):
        assert sumo_pages.contribute_page._get_page_hero_main_header_text(
        ) == ContributePageMessages.HERO_MAIN_PAGE_TITLE

    with check, allure.step("Verifying that the correct page hero need help subtext is "
                            "displayed"):
        assert sumo_pages.contribute_page._get_page_hero_main_subtext(
        ) == ContributePageMessages.HERO_HELP_MILLION_OF_USERS_TEXT

    with check, allure.step("Verifying that the correct need help header text is displayed"):
        assert sumo_pages.contribute_page._get_page_hero_need_help_header_text(
        ) == ContributePageMessages.HERO_NEED_YOUR_HELP_TITLE

    with check, allure.step("Verifying that the correct need help subtext is displayed"):
        assert sumo_pages.contribute_page._get_page_hero_need_help_subtext(
        ) == ContributePageMessages.HERO_NEED_YOUR_HELP_PARAGRAPH

    with check, allure.step("Verifying that the correct get way to contribute_messages "
                            "header is displayed"):
        assert sumo_pages.contribute_page._get_way_to_contribute_header_text(
        ) == ContributePageMessages.PICK_A_WAY_TO_CONTRIBUTE_HEADER

    card_titles = [
        ContributePageMessages.ANSWER_QUESTIONS_CARD_TITLE,
        ContributePageMessages.WRITE_ARTICLES_CARD_TITLE,
        ContributePageMessages.LOCALIZE_CONTENT_CARD_TITLE
    ]

    with check, allure.step("Verifying that the correct list of ways to contribute_messages "
                            "card titles is displayed"):
        assert card_titles == sumo_pages.contribute_page._get_way_to_contribute_cards()

    with check, allure.step("Verifying that the correct about us header text is displayed"):
        assert sumo_pages.contribute_page._get_about_us_header_text(
        ) == ContributePageMessages.ABOUT_US_HEADER

    with check, allure.step("Verifying that the correct about us subtext is displayed"):
        assert sumo_pages.contribute_page._get_about_us_subtext(
        ) == ContributePageMessages.ABOUT_US_CONTENT


# C2165413
@pytest.mark.contributePagesTests
def test_contribute_page_images_are_not_broken(page: Page):
    sumo_pages = SumoPages(page)
    with allure.step("Clicking on the 'Contribute' top-navbar option"):
        sumo_pages.top_navbar.click_on_contribute_top_navbar_option()

    for link in sumo_pages.contribute_page._get_all_page_links():
        image_link = link.get_attribute("src")
        response = requests.get(image_link, stream=True)
        with check, allure.step(f"Verifying that the {image_link} image is not broken"):
            assert response.status_code < 400


# C1949333
@pytest.mark.contributePagesTests
def test_contribute_page_breadcrumbs(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Clicking on the Contribute top-navbar option"):
        sumo_pages.top_navbar.click_on_contribute_top_navbar_option()

    breadcrumbs = [
        ContributePageMessages.FIRST_BREADCRUMB,
        ContributePageMessages.SECOND_BREADCRUMB,
    ]

    with check, allure.step("Verifying that the correct breadcrumbs are displayed"):
        assert sumo_pages.contribute_page._get_breadcrumbs_text() == breadcrumbs

    with allure.step("Verifying that the home breadcrumb redirects to the homepage"):
        sumo_pages.contribute_page._click_on_home_breadcrumb()
        assert utilities.get_page_url() == HomepageMessages.STAGE_HOMEPAGE_URL_EN_US


# C1949335,C1949336,C1949337,C1949338,C1949339,C1949355
@pytest.mark.contributePagesTests
def test_way_to_contribute_redirects_to_correct_page(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Clicking on the Contribute top-navbar option"):
        sumo_pages.top_navbar.click_on_contribute_top_navbar_option()

    ways_to_contribute_links = [
        ContributeForumMessages.STAGE_CONTRIBUTE_FORUM_PAGE_URL,
        ContributeHelpArticlesMessages.STAGE_CONTRIBUTE_HELP_ARTICLES_PAGE_URL,
        ContributeLocalizationMessages.STAGE_CONTRIBUTE_LOCALIZATION_PAGE_URL
    ]

    counter = 0
    for element in sumo_pages.contribute_page._get_list_of_contribute_cards():
        card = sumo_pages.contribute_page._get_list_of_contribute_cards()[counter]
        sumo_pages.contribute_page._click_on_way_to_contribute_card(card)
        with check, allure.step("Verifying that the 'way to contribute_messages' cards are "
                                "redirecting to the correct SUMO page"):
            assert ways_to_contribute_links[counter] == utilities.get_page_url()
        utilities.navigate_back()
        counter += 1
