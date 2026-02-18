import allure
import pytest
from playwright.sync_api import Page
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.contribute_messages.con_pages.con_page_messages import (
    ContributePageMessages)
from playwright_tests.messages.homepage_messages import HomepageMessages
from playwright_tests.messages.explore_help_articles.support_page_messages import (
    SupportPageMessages)
from playwright_tests.pages.sumo_pages import SumoPages


# C876542
@pytest.mark.homePageTests
def test_join_our_community_card_learn_more_redirects_to_contribute_page(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    with allure.step("Clicking on the 'Learn More' option"):
        sumo_pages.common_web_elements.click_on_volunteer_learn_more_link()

    with allure.step("Verifying that we are redirected to the 'Contribute' page successfully"):
        assert (
            utilities.get_page_url() == ContributePageMessages.STAGE_CONTRIBUTE_PAGE_URL
        ), "We are not on the Contribute page!"


# C876542
@pytest.mark.homePageTests
def test_join_our_community_card_has_the_correct_content(page: Page):
    sumo_pages = SumoPages(page)
    with allure.step("Verifying that the 'Join Our Community' card has the correct strings"
                     " applied"):
        assert (
            sumo_pages.common_web_elements.get_volunteer_learn_more_card_header()
            == HomepageMessages.JOIN_OUR_COMMUNITY_CARD_TITLE
        ), "Incorrect card header is displayed"
        assert (
            sumo_pages.common_web_elements.get_volunteer_learn_more_card_text()
            == HomepageMessages.JOIN_OUR_COMMUNITY_CARD_DESCRIPTION
        ), "Incorrect card description is displayed"


# C876541
@pytest.mark.smokeTest
@pytest.mark.homePageTests
def test_homepage_feature_articles_are_available_and_interactable(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    with allure.step("Verifying if the correct number of featured articles are present on the"
                     " homepage"):
        assert sumo_pages.homepage.get_number_of_featured_articles(
        ) == HomepageMessages.EXPECTED_FEATURED_ARTICLES_COUNT

    with allure.step("Clicking on each featured article card and verifying that the user is "
                     "redirected to the correct article page."):
        count = sumo_pages.homepage.get_number_of_featured_articles()
        for counter in range(count):
            articles_names = sumo_pages.homepage.get_featured_articles_titles()
            sumo_pages.homepage.click_on_a_featured_card(counter)
            assert (
                sumo_pages.kb_article_page.get_text_of_article_title().strip()
                == articles_names[counter].strip()
            ), (f"Incorrect featured article displayed. "
                f"Expected: {articles_names[counter]} "
                f"Received: {sumo_pages.kb_article_page.get_text_of_article_title()}")

            with allure.step("Navigating back to the previous page"):
                utilities.navigate_back()


# C873774
@pytest.mark.smokeTest
@pytest.mark.homePageTests
def test_product_cards_are_functional_and_redirect_to_the_proper_support_page(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    with allure.step("Verifying that the product cards redirect to the correct support page"):
        card_titles = sumo_pages.homepage.get_text_of_product_card_titles()
        for counter, product_card in enumerate(card_titles):
            expected_product_title = product_card + SupportPageMessages.TITLE_CONTAINS
            sumo_pages.homepage.click_on_product_card(counter)
            assert (
                expected_product_title
                == sumo_pages.product_support_page.get_product_support_title_text()
            ), (f"Incorrect support page displayed. "
                f"Expected: {expected_product_title} "
                f"Received: "
                f"{sumo_pages.product_support_page.get_product_support_title_text()}")

            with allure.step("Navigating back to the previous page"):
                utilities.navigate_back()
