import allure

from playwright_tests.core.testutilities import TestUtilities
from playwright.sync_api import expect
from pytest_check import check
import pytest

from playwright_tests.messages.homepage_messages import HomepageMessages
from playwright_tests.messages.explore_help_articles.products_page_messages import (
    ProductsPageMessages)


class TestPostedQuestions(TestUtilities):

    # C890834, C890833
    @pytest.mark.kbProductsPage
    def test_products_page_content(self):
        with check, allure.step("Navigating to products page via top-navbar and verifying that "
                                "the correct page header is displayed"):
            self.sumo_pages.top_navbar._click_on_explore_our_help_articles_option()
            assert self.sumo_pages.products_page._get_page_header(
            ) == ProductsPageMessages.PRODUCTS_PAGE_HEADER

        with allure.step("Clicking on the first 'Home' breadcrumb and verifying the redirect"):
            self.sumo_pages.products_page._click_on_first_breadcrumb()
            expect(
                self.page
            ).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL_EN_US)

        with allure.step("Navigating back to the 'Products' page"):
            self.navigate_back()

        for card in self.sumo_pages.products_page._get_all_product_support_titles():
            with check, allure.step(f"Verifying that the {card} card contains the correct "
                                    f"subheading"):
                if card in ProductsPageMessages.PRODUCT_CARDS_SUBHEADING:
                    assert self.sumo_pages.products_page._get_subheading_of_card(
                        card) == ProductsPageMessages.PRODUCT_CARDS_SUBHEADING[card]

    # C890846
    @pytest.mark.kbProductsPage
    def test_products_page_card_redirect(self):
        with allure.step("Navigating to products page via top-navbar"):
            self.sumo_pages.top_navbar._click_on_explore_our_help_articles_option()

        for card in self.sumo_pages.products_page._get_all_product_support_titles():
            if card in self.general_test_data['product_support']:
                with allure.step(f"Clicking on {card} card and verifying that we are redirected "
                                 f"to the correct product url"):
                    self.sumo_pages.products_page._click_on_a_particular_product_support_card(card)
                    expect(
                        self.page
                    ).to_have_url(self.general_test_data['product_support'][card])

                with allure.step("Navigating back to the products page"):
                    self.navigate_back()
