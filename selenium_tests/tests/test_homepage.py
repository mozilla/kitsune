import pytest
import pytest_check as check

from selenium_tests.core.test_utilities import TestUtilities
from selenium_tests.messages.contribute_pages_messages.contribute_page_messages import ContributePageMessages
from selenium_tests.messages.homepage_messages import HomepageMessages
from selenium_tests.messages.support_page_messages import SupportPageMessages


class TestHomepage(TestUtilities):
    # C876542
    @pytest.mark.smokeTest
    def test_join_our_community_card_learn_more_redirects_to_contribute_page(self):
        self.logger.info("Clicking on the 'Learn More' option")
        self.pages.homepage.click_learn_more_option()
        self.logger.info("Verifying that we are redirected to the 'Contribute' page successfully")

        assert (
                self.pages.contribute_page.current_url
                == ContributePageMessages.STAGE_CONTRIBUTE_PAGE_URL
        ), "We are not on the Contribute page!"

    # C876542
    @pytest.mark.smokeTest
    def test_join_our_community_card_has_the_correct_content(self):
        self.logger.info(
            "Verifying that the 'Join Our Community' card has the correct strings applied"
        )

        assert (
                self.pages.homepage.get_community_card_title()
                == HomepageMessages.JOIN_OUR_COMMUNITY_CARD_TITLE
                and self.pages.homepage.get_community_card_description()
                == HomepageMessages.JOIN_OUR_COMMUNITY_CARD_DESCRIPTION
        ), "Incorrect strings are displayed"

    # C876541
    @pytest.mark.smokeTest
    def test_homepage_feature_articles_are_available_and_interactable(self):
        self.logger.info(
            "Verify that the correct number of featured articles are present on the homepage "
        )

        check.equal(
            self.pages.homepage.get_number_of_featured_articles(),
            HomepageMessages.EXPECTED_FEATURED_ARTICLES_COUNT,
            "Unexpected featured article count"
        )

        article_name = self.pages.homepage.get_featured_articles_titles()[0]

        self.pages.homepage.click_on_featured_article()

        self.logger.info(
            "Verifying that the featured article card redirects to the correct article"
        )

        check.equal(
            self.pages.kb_article.get_text_of_article_title(),
            article_name,
            "Incorrect featured article displayed on click"
        )

    # C873774
    @pytest.mark.smokeTest
    def test_product_cards_are_functional_and_redirect_to_proper_support_page(self):
        self.logger.info(
            "Verifying that the product cards are redirecting to the correct support page"
        )

        card_titles = self.pages.homepage.get_text_of_product_card_titles()
        counter = 0
        for element in self.pages.homepage.get_list_of_product_cards():
            card = self.pages.homepage.get_list_of_product_cards()[counter]
            self.pages.homepage.click_on_product_card(card)
            support_page_title = self.pages.product_support_page.get_product_title_text()
            check.equal(
                card_titles[counter] + " " + SupportPageMessages.TITLE_CONTAINS,
                support_page_title,
                f"Incorrect support page title: {support_page_title} for clicked card with title: {card_titles[counter]}!"
            )
            self.pages.homepage.navigate_back()
            counter += 1
