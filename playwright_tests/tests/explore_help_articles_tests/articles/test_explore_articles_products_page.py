from playwright_tests.core.testutilities import TestUtilities
from playwright.sync_api import expect
import pytest_check as check
import pytest

from playwright_tests.messages.homepage_messages import HomepageMessages
from playwright_tests.messages.explore_help_articles.products_page_messages import (
    ProductsPageMessages)


class TestPostedQuestions(TestUtilities):

    # C890834, C890833
    @pytest.mark.kbProductsPage
    def test_products_page_content(self):
        self.logger.info("Navigating to products page via top-navbar")
        self.sumo_pages.top_navbar._click_on_explore_our_help_articles_option()

        self.logger.info("Verifying that the correct page header is displayed")
        check.equal(
            self.sumo_pages.products_page._get_page_header(),
            ProductsPageMessages.PRODUCTS_PAGE_HEADER
        )

        self.logger.info("Clicking on the first 'Home' breadcrumb and verifying the redirect")
        self.sumo_pages.products_page._click_on_first_breadcrumb()
        expect(
            self.page
        ).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL_EN_US)

        self.logger.info("Navigating back to the 'Products' page")
        self.navigate_back()

        for card in self.sumo_pages.products_page._get_all_product_support_titles():
            self.logger.info(f"Verifying that the {card} card contains the correct subheading")
            if card in ProductsPageMessages.PRODUCT_CARDS_SUBHEADING:
                check.equal(
                    self.sumo_pages.products_page._get_subheading_of_card(card),
                    ProductsPageMessages.PRODUCT_CARDS_SUBHEADING[card]
                )

    # C890846
    @pytest.mark.kbProductsPage
    def test_products_page_card_redirect(self):
        self.logger.info("Navigating to products page via top-navbar")
        self.sumo_pages.top_navbar._click_on_explore_our_help_articles_option()

        for card in self.sumo_pages.products_page._get_all_product_support_titles():
            if card in self.general_test_data['product_support']:
                self.logger.info(f"Clicking on {card} card and verifying that we are redirected "
                                 f"to the correct product url")
                self.sumo_pages.products_page._click_on_a_particular_product_support_card(card)
                expect(
                    self.page
                ).to_have_url(self.general_test_data['product_support'][card])

                self.logger.info("Navigating back to the products page")
                self.navigate_back()
