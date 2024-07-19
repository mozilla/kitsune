import allure

from playwright.sync_api import expect, Page
from pytest_check import check
import pytest

from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.homepage_messages import HomepageMessages
from playwright_tests.messages.explore_help_articles.products_page_messages import (
    ProductsPageMessages)
from playwright_tests.pages.sumo_pages import SumoPages


# C890834, C890833
@pytest.mark.kbProductsPage
def test_products_page_content(page: Page):
    with check, allure.step("Navigating to products page via top-navbar and verifying that "
                            "the correct page header is displayed"):
        sumo_pages = SumoPages(page)
        utilities = Utilities(page)
        sumo_pages.top_navbar._click_on_explore_our_help_articles_view_all_option()
        assert sumo_pages.products_page._get_page_header(
        ) == ProductsPageMessages.PRODUCTS_PAGE_HEADER

    with allure.step("Clicking on the first 'Home' breadcrumb and verifying the redirect"):
        sumo_pages.products_page._click_on_first_breadcrumb()
        expect(page).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL_EN_US)

    with allure.step("Navigating back to the 'Products' page"):
        utilities.navigate_back()

    for card in sumo_pages.products_page._get_all_product_support_titles():
        with check, allure.step(f"Verifying that the {card} card contains the correct "
                                f"subheading"):
            if card in ProductsPageMessages.PRODUCT_CARDS_SUBHEADING:
                assert sumo_pages.products_page._get_subheading_of_card(
                    card) == ProductsPageMessages.PRODUCT_CARDS_SUBHEADING[card]


# C890846
@pytest.mark.kbProductsPage
def test_products_page_card_redirect(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    with allure.step("Navigating to products page via top-navbar"):
        sumo_pages.top_navbar._click_on_explore_our_help_articles_view_all_option()

    for card in sumo_pages.products_page._get_all_product_support_titles():
        if card in utilities.general_test_data['product_support']:
            with allure.step(f"Clicking on {card} card and verifying that we are redirected "
                             f"to the correct product url"):
                sumo_pages.products_page._click_on_a_particular_product_support_card(card)
                expect(page).to_have_url(utilities.general_test_data['product_support'][card])

            with allure.step("Navigating back to the products page"):
                utilities.navigate_back()
