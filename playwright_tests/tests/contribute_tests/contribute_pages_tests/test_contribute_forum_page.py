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
from playwright_tests.messages.contribute_messages.con_pages.con_mobile_support_messages import (
    ContributeMobileSupportMessages)
from playwright_tests.messages.contribute_messages.con_pages.con_page_messages import (
    ContributePageMessages)
from playwright_tests.messages.contribute_messages.con_pages.con_social_support_messages import (
    ContributeSocialSupportMessages)
from playwright_tests.messages.homepage_messages import HomepageMessages
from playwright_tests.pages.sumo_pages import SumoPages


# C2165414
@pytest.mark.contributePagesTests
def test_contribute_forum_page_text(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Accessing the Contribute Forum page"):
        utilities.navigate_to_link(ContributeForumMessages.STAGE_CONTRIBUTE_FORUM_PAGE_URL)
    with check, allure.step("Verifying that the Contribute Forum page contains the correct "
                            "strings"):
        assert sumo_pages.ways_to_contribute_pages._get_hero_main_header_text(
        ) == ContributeForumMessages.HERO_PAGE_TITLE
        assert sumo_pages.ways_to_contribute_pages._get_hero_second_header(
        ) == ContributeForumMessages.HERO_SECOND_TITLE
        assert sumo_pages.ways_to_contribute_pages._get_hero_text(
        ) == ContributeForumMessages.HERO_TEXT
        assert sumo_pages.ways_to_contribute_pages._get_how_to_contribute_header_text(
        ) == ContributeForumMessages.HOW_TO_CONTRIBUTE_HEADER

        # Need to add a check for the logged in state as well.
        # Excluding option four from the list since we are using a different locator

        card_titles = [
            ContributeForumMessages.HOW_TO_CONTRIBUTE_OPTION_ONE_SIGNED_OUT,
            ContributeForumMessages.HOW_TO_CONTRIBUTE_OPTION_TWO,
            ContributeForumMessages.HOW_TO_CONTRIBUTE_OPTION_THREE,
            ContributeForumMessages.HOW_TO_CONTRIBUTE_OPTION_FIVE,
        ]

        assert sumo_pages.ways_to_contribute_pages._get_how_to_contribute_link_options(
        ) == card_titles

        # We need to add here the check for when the user is signed in with a contributor
        # account
        assert sumo_pages.ways_to_contribute_pages._get_how_to_contribute_option_four(
        ) == ContributeForumMessages.HOW_TO_CONTRIBUTE_OPTION_FOUR
        assert sumo_pages.ways_to_contribute_pages._get_first_fact_text(
        ) == ContributeForumMessages.FACT_FIRST_LINE
        assert sumo_pages.ways_to_contribute_pages._get_second_fact_text(
        ) == ContributeForumMessages.FACT_SECOND_LINE
        assert sumo_pages.ways_to_contribute_pages._get_other_ways_to_contribute_header(
        ) == ContributeForumMessages.OTHER_WAYS_TO_CONTRIBUTE_HEADER

        other_ways_to_contribute_card_titles = [
            ContributeForumMessages.WRITE_ARTICLES_CARD_TITLE,
            ContributeForumMessages.LOCALIZE_CONTENT_CARD_TITLE,
            ContributeForumMessages.PROVIDE_SUPPORT_ON_SOCIAL_CHANNELS_CARD_TITLE,
            ContributeForumMessages.RESPOND_TO_MOBILE_STORE_REVIEWS_CARD_TITLE,
        ]
        assert sumo_pages.ways_to_contribute_pages._get_other_ways_to_contribute_cards(
        ) == other_ways_to_contribute_card_titles


# C2165414
@pytest.mark.contributePagesTests
def test_contribute_forum_page_images_are_not_broken(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Accessing the Contribute Forum page"):
        utilities.navigate_to_link(ContributeForumMessages.STAGE_CONTRIBUTE_FORUM_PAGE_URL)

    for link in sumo_pages.ways_to_contribute_pages._get_all_page_image_links():
        image_link = link.get_attribute("src")
        response = requests.get(image_link, stream=True)
        with check, allure.step(f"Verifying that the {image_link} link is not broken"):
            assert response.status_code < 400


# C2165415
@pytest.mark.contributePagesTests
def test_contribute_forum_page_breadcrumbs(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Accessing the Contribute Forum page"):
        utilities.navigate_to_link(ContributeForumMessages.STAGE_CONTRIBUTE_FORUM_PAGE_URL)

    breadcrumbs = [
        ContributeForumMessages.FIRST_BREADCRUMB,
        ContributeForumMessages.SECOND_BREADCRUMB,
        ContributeForumMessages.THIRD_BREADCRUMB,
    ]

    with check, allure.step("Verifying that the correct breadcrumbs are displayed"):
        assert sumo_pages.ways_to_contribute_pages._get_text_of_all_breadcrumbs() == breadcrumbs

    counter = 1
    for breadcrumb in sumo_pages.ways_to_contribute_pages._get_interactable_breadcrumbs():
        breadcrumb_to_click = (
            sumo_pages.ways_to_contribute_pages._get_interactable_breadcrumbs()[counter]
        )
        sumo_pages.ways_to_contribute_pages._click_on_breadcrumb(breadcrumb_to_click)

        if counter == 1:
            with check, allure.step("Verifying that the Contribute breadcrumb redirects to "
                                    "the Contribute page"):
                assert utilities.get_page_url() == ContributePageMessages.STAGE_CONTRIBUTE_PAGE_URL

            utilities.navigate_forward()
            counter -= 1
        elif counter == 0:
            with check, allure.step("Verifying that the Home breadcrumb redirects to the "
                                    "Homepage"):
                assert utilities.get_page_url() == HomepageMessages.STAGE_HOMEPAGE_URL_EN_US


# Need to add tests for "How you can contribute_messages" section
# C2165418
@pytest.mark.contributePagesTests
def test_contribute_forum_other_ways_to_contribute_redirect_to_the_correct_page(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Accessing the Contribute Forum page"):
        utilities.navigate_to_link(ContributeForumMessages.STAGE_CONTRIBUTE_FORUM_PAGE_URL)

    ways_to_contribute_links = [
        ContributeHelpArticlesMessages.STAGE_CONTRIBUTE_HELP_ARTICLES_PAGE_URL,
        ContributeLocalizationMessages.STAGE_CONTRIBUTE_LOCALIZATION_PAGE_URL,
        ContributeSocialSupportMessages.STAGE_CONTRIBUTE_SOCIAL_SUPPORT_PAGE_URL,
        ContributeMobileSupportMessages.STAGE_CONTRIBUTE_MOBILE_SUPPORT_PAGE_URL,
    ]

    counter = 0
    for element in sumo_pages.ways_to_contribute_pages._get_other_ways_to_contribute_card_list():
        card = (
            sumo_pages.ways_to_contribute_pages._get_other_ways_to_contribute_card_list()[counter]
        )
        sumo_pages.ways_to_contribute_pages._click_on_other_way_to_contribute_card(card)
        with check, allure.step("Verifying that the 'other ways to contribute_messages' "
                                "cards are redirecting to the correct SUMO page"):
            assert ways_to_contribute_links[counter] == utilities.get_page_url()
        utilities.navigate_back()
        counter += 1
