import pytest
import pytest_check as check

from playwright_tests.core.testutilities import TestUtilities

from playwright_tests.messages.contribute_pages_messages.con_page_messages import (
    ContributePageMessages)
from playwright_tests.messages.homepage_messages import HomepageMessages
from playwright_tests.messages.support_page_messages import SupportPageMessages


class TestHomepage(TestUtilities):
    # C876542
    @pytest.mark.homePageTests
    def test_join_our_community_card_learn_more_redirects_to_contribute_page(self):
        self.logger.info("Clicking on the 'Learn More' option")
        self.sumo_pages.homepage.click_learn_more_option()
        self.logger.info("Verifying that we are redirected to the 'Contribute' page successfully")

        assert (
            self.get_page_url()
            == ContributePageMessages.STAGE_CONTRIBUTE_PAGE_URL
        ), "We are not on the Contribute page!"

    # C876542
    @pytest.mark.homePageTests
    def test_join_our_community_card_has_the_correct_content(self):
        self.logger.info(
            "Verifying that the 'Join Our Community' card has the correct strings applied"
        )

        assert (
            self.sumo_pages.homepage.get_community_card_title()
            == HomepageMessages.JOIN_OUR_COMMUNITY_CARD_TITLE
            and self.sumo_pages.homepage.get_community_card_description()
            == HomepageMessages.JOIN_OUR_COMMUNITY_CARD_DESCRIPTION
        ), "Incorrect strings are displayed"

    # C876541
    @pytest.mark.homePageTests
    def test_homepage_feature_articles_are_available_and_interactable(self):
        self.logger.info(
            "Verifying that the correct number of featured articles are present on the homepage"
        )

        check.equal(
            self.sumo_pages.homepage.get_number_of_featured_articles(),
            HomepageMessages.EXPECTED_FEATURED_ARTICLES_COUNT,
            "Unexpected featured article count"
        )

        self.logger.info(
            "Clicking on each featured article card and verifying that the user is redirected to "
            "the correct article page."
        )
        counter = 0
        for featured_article in self.sumo_pages.homepage.get_featured_articles_titles():
            articles_names = self.sumo_pages.homepage.get_featured_articles_titles()

            self.logger.info(
                f"Clicking on: {articles_names[counter]} article card"
            )
            self.sumo_pages.homepage.click_on_a_featured_card(counter)

            self.logger.info(
                "Verifying that the correct article title is displayed."
            )

            assert (
                self.sumo_pages.kb_article_page.get_text_of_article_title()
                == articles_names[counter]
            ), (f"Incorrect featured article displayed. Expected: {featured_article} "
                f"Received: {self.sumo_pages.kb_article_page.get_text_of_article_title()}")

            self.logger.info("Navigating back to the previous page")
            self.navigate_back()
            counter += 1

    # C873774
    @pytest.mark.homePageTests
    def test_product_cards_are_functional_and_redirect_to_the_proper_support_page(self):
        self.logger.info(
            "Verifying that the product cards are redirecting to the correct support page"
        )

        card_titles = self.sumo_pages.homepage.get_text_of_product_card_titles()
        counter = 0
        for product_card in card_titles:
            expected_product_title = card_titles[counter] + SupportPageMessages.TITLE_CONTAINS

            self.logger.info(expected_product_title)
            self.logger.info(f"Clicking on the: {card_titles[counter]} card")
            self.sumo_pages.homepage.click_on_product_card(counter)
            self.logger.info("Verifying that the correct product support page is displayed")
            assert (
                expected_product_title
                == self.sumo_pages.product_support_page._get_product_title_text()
            ), (f"Incorrect support page displayed. "
                f"Expected: {expected_product_title} "
                f"Received: {self.sumo_pages.product_support_page._get_product_title_text()}")

            self.logger.info("Navigating back to the previous page")
            self.navigate_back()
            counter += 1
