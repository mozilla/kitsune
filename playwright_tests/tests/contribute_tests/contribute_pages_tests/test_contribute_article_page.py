import allure
import pytest
import requests
from playwright.sync_api import Page, expect
from pytest_check import check
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.contribute_messages.con_pages.con_forum_messages import (
    ContributeForumMessages,
)
from playwright_tests.messages.contribute_messages.con_pages.con_help_articles_messages import (
    ContributeHelpArticlesMessages,
)
from playwright_tests.messages.contribute_messages.con_pages.con_localization_messages import (
    ContributeLocalizationMessages,
)
from playwright_tests.messages.contribute_messages.con_pages.con_page_messages import (
    ContributePageMessages,
)
from playwright_tests.messages.homepage_messages import HomepageMessages
from playwright_tests.pages.sumo_pages import SumoPages


# C2165414
@pytest.mark.contributePagesTests
def test_contribute_article_page_text(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Accessing the Contribute with help Article page"):
        utilities.navigate_to_link(
            ContributeHelpArticlesMessages.STAGE_CONTRIBUTE_HELP_ARTICLES_PAGE_URL
        )

    with check, allure.step("Verifying that the page header is successfully displayed and contains"
                            " the correct strings"):
        expect(sumo_pages.ways_to_contribute_pages.hero_main_header).to_have_text(
            ContributeHelpArticlesMessages.HERO_PAGE_TITLE)

    with check, allure.step("Verifying that the h2 is successfully displayed and contains the"
                            " correct strings"):
        expect(sumo_pages.ways_to_contribute_pages.hero_second_header).to_have_text(
            ContributeHelpArticlesMessages.HERO_SECOND_TITLE)

    with check, allure.step("Verifying tha the paragraph under h2 is successfully displayed and"
                            " contains the correct strings"):
        expect(sumo_pages.ways_to_contribute_pages.hero_text).to_have_text(
            ContributeHelpArticlesMessages.HERO_TEXT)

    with check, allure.step("Verifying that the 'How you can contribute_messages' header is"
                            " successfully displayed and contains the correct strings"):
        expect(sumo_pages.ways_to_contribute_pages.how_to_contribute_header).to_have_text(
            ContributeHelpArticlesMessages.HOW_TO_CONTRIBUTE_HEADER)

    # Need to add a check for the logged in state as well.
    # Excluding option four from the list since we are using a different locator

    card_titles = [
        ContributeHelpArticlesMessages.HOW_TO_CONTRIBUTE_OPTION_ONE_SIGNED_OUT,
        ContributeHelpArticlesMessages.HOW_TO_CONTRIBUTE_OPTION_TWO,
        ContributeHelpArticlesMessages.HOW_TO_CONTRIBUTE_OPTION_THREE,
        ContributeHelpArticlesMessages.HOW_TO_CONTRIBUTE_OPTION_FIVE,
    ]

    with check, allure.step("Verifying that the 'How you can contribute_messages' cards are "
                            "successfully displayed"):
        expect(sumo_pages.ways_to_contribute_pages.all_how_to_contribute_option_links
               ).to_contain_text(card_titles)

    with check, allure.step("Signing up with a FxA contributor account and Verifying that the"
                            " step 4 option is successfully displayed and the text contains the"
                            " expected string"):
        # We need to add here the check for when the user is signed in with a contributor
        # account
        expect(sumo_pages.ways_to_contribute_pages.start_answering_how_to_contribute_option_text
               ).to_have_text(ContributeHelpArticlesMessages.HOW_TO_CONTRIBUTE_OPTION_FOUR)

    with check, allure.step("Verifying that the first line from the fact text is successfully"
                            " displayed and contains the expected string"):
        expect(sumo_pages.ways_to_contribute_pages.first_fact_text).to_have_text(
            ContributeHelpArticlesMessages.FACT_FIRST_LINE)

    with check, allure.step("Verifying that the second line from the fact section text is "
                            "successfully displayed and contains the expected string"):
        expect(sumo_pages.ways_to_contribute_pages.second_fact_text).to_have_text(
            ContributeHelpArticlesMessages.FACT_SECOND_LINE)

    with check, allure.step("Verifying that the 'Other ways to contribute_messages' header is "
                            "successfully displayed and contains the expected string"):
        expect(sumo_pages.ways_to_contribute_pages.other_ways_to_contribute_header).to_have_text(
            ContributeHelpArticlesMessages.OTHER_WAYS_TO_CONTRIBUTE_HEADER)

    other_ways_to_contribute_card_titles = [
        ContributeHelpArticlesMessages.ANSWER_QUESTIONS_IN_SUPPORT_FORUM_TITLE,
        ContributeHelpArticlesMessages.LOCALIZE_CONTENT_CARD_TITLE
    ]

    with check, allure.step("Verifying that the 'Other ways to contribute_messages' are "
                            "successfully displayed and in the correct order"):
        expect(sumo_pages.ways_to_contribute_pages.other_ways_to_contribute_card_titles
               ).to_contain_text(other_ways_to_contribute_card_titles)


# C2165414
@pytest.mark.contributePagesTests
def test_contribute_article_page_images_are_not_broken(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Accessing the Contribute with help Article page"):
        utilities.navigate_to_link(
            ContributeHelpArticlesMessages.STAGE_CONTRIBUTE_HELP_ARTICLES_PAGE_URL
        )

    for link in sumo_pages.ways_to_contribute_pages.get_all_page_image_links():
        image_link = link.get_attribute("src")
        response = requests.get(image_link, stream=True)
        with allure.step(f"Verifying that {image_link} is not broken"):
            assert response.status_code < 400


# C2165415
@pytest.mark.contributePagesTests
def test_contribute_article_page_breadcrumbs(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Accessing the Contribute Forum page"):
        utilities.navigate_to_link(
            ContributeHelpArticlesMessages.STAGE_CONTRIBUTE_HELP_ARTICLES_PAGE_URL
        )

    breadcrumbs = [
        ContributeHelpArticlesMessages.FIRST_BREADCRUMB,
        ContributeHelpArticlesMessages.SECOND_BREADCRUMB,
        ContributeHelpArticlesMessages.THIRD_BREADCRUMB,
    ]

    with allure.step("Verifying that the correct breadcrumbs are displayed"):
        expect(sumo_pages.ways_to_contribute_pages.all_breadcrumbs).to_contain_text(breadcrumbs)

    sumo_pages.ways_to_contribute_pages.click_on_breadcrumb(
        sumo_pages.ways_to_contribute_pages.get_interactable_breadcrumbs()[1]
    )
    with allure.step("Verifying that the Contribute breadcrumb redirects to the Contribute page"):
        expect(page).to_have_url(ContributePageMessages.STAGE_CONTRIBUTE_PAGE_URL)
    utilities.navigate_forward()

    sumo_pages.ways_to_contribute_pages.click_on_breadcrumb(
        sumo_pages.ways_to_contribute_pages.get_interactable_breadcrumbs()[0]
    )
    with allure.step("Verifying that the Home breadcrumb redirects to the Homepage"):
        expect(page).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL_EN_US)


# Need to add tests for "How you can contribute_messages" section
# C2165418
@pytest.mark.contributePagesTests
def test_contribute_article_other_ways_to_contribute_redirect_to_the_correct_page(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Accessing the Contribute Forum page"):
        utilities.navigate_to_link(
            ContributeHelpArticlesMessages.STAGE_CONTRIBUTE_HELP_ARTICLES_PAGE_URL
        )

    ways_to_contribute_links = [
        ContributeForumMessages.STAGE_CONTRIBUTE_FORUM_PAGE_URL,
        ContributeLocalizationMessages.STAGE_CONTRIBUTE_LOCALIZATION_PAGE_URL
    ]

    for counter, expected_url in enumerate(ways_to_contribute_links):
        card = (
            sumo_pages.ways_to_contribute_pages.get_other_ways_to_contribute_card_list()[counter]
        )
        sumo_pages.ways_to_contribute_pages.click_on_other_way_to_contribute_card(card)
        with allure.step(f"Verifying that the {expected_url} redirects to the correct page"):
            expect(page).to_have_url(expected_url)
        utilities.navigate_back()
