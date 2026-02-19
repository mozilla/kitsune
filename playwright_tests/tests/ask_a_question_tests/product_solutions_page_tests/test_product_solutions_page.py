import random

import allure
import pytest
from playwright.sync_api import Page, expect
from pytest_check import check

from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.ask_a_question_messages.AAQ_messages.aaq_widget import (
    AAQWidgetMessages,
)
from playwright_tests.messages.ask_a_question_messages.product_solutions_messages import (
    ProductSolutionsMessages,
)
from playwright_tests.pages.sumo_pages import SumoPages


#  C890370, C890374, C890372
@pytest.mark.smokeTest
@pytest.mark.productSolutionsPage
def test_featured_articles_redirect(page: Page, is_chromium):
    if is_chromium:
        pytest.skip("Skipping this test for chromium browser")
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Accessing the contact support page via the top navbar Get Help > "
                     "Browse All products"):
        sumo_pages.top_navbar.click_on_browse_all_products_option()

    with allure.step("Clicking on all product cards"):
        for card in sumo_pages.contact_support_page.get_all_product_card_titles():
            with check, allure.step(f"Clicking on the {card} and verifying that the correct"
                                    f" product solutions page header is displayed"):
                sumo_pages.contact_support_page.click_on_a_particular_card(card)
                assert sumo_pages.product_solutions_page.get_product_solutions_heading(
                ) == card + ProductSolutionsMessages.PAGE_HEADER

            if sumo_pages.product_solutions_page.is_featured_article_section_displayed():
                for featured_article_card in (sumo_pages.product_solutions_page
                                              .get_all_featured_articles_titles()):
                    sumo_pages.product_solutions_page.click_on_a_featured_article_card(
                        featured_article_card.strip())
                    with check, allure.step(f"Clicking on the {featured_article_card} and"
                                            f" verifying that the correct article page title is"
                                            f" displayed"):
                        with page.context.expect_page() as tab:
                            feature_article_page = tab.value
                            article_text = (feature_article_page.
                                            locator("//h1[@class='sumo-page-heading']"
                                                    ).inner_text())
                            assert article_text == featured_article_card.strip()
                            feature_article_page.close()
            else:
                print(f"{card} has no featured articles displayed!!!")
            utilities.navigate_back()


#  C2903828, C2903829, C2903831
@pytest.mark.smokeTest
@pytest.mark.productSolutionsPage
def test_popular_topics_redirect(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Accessing the contact support page via the top navbar Get Help > "
                     "Browse All products"):
        sumo_pages.top_navbar.click_on_browse_all_products_option()
        product = random.choice(sumo_pages.contact_support_page.get_all_product_card_titles())
        utilities.navigate_back()

    with allure.step("Navigating to a random product page"):
        sumo_pages.contact_support_page.click_on_a_particular_card(product)

    topic_card = random.choice(sumo_pages.common_web_elements.get_frequent_topic_card_titles())
    with allure.step(f"Verifying that the {topic_card} card heading redirects to the correct "
                     f"page topic listing page"):
        assert sumo_pages.common_web_elements.verify_topic_card_redirect(utilities, sumo_pages,
                                                                         topic_card, "heading")

    with allure.step(f"Verifying that the listed articles for the {topic_card} card are is "
                     f"redirecting to the article page successfully"):
        assert sumo_pages.common_web_elements.verify_topic_card_redirect(utilities, sumo_pages,
                                                                         topic_card, "article")

    with allure.step(f"Verifying that the 'View all articles' link for the {topic_card} card "
                     f"redirects the user to the correct topic listing page and the counter "
                     f"successfully reflects the number of articles for that topic"):
        assert sumo_pages.common_web_elements.verify_topic_card_redirect(utilities, sumo_pages,
                                                                         topic_card, "counter")


# T5696588
@pytest.mark.smokeTest
@pytest.mark.productSolutionsPage
def test_ask_now_widget_redirect(page: Page, restmail_test_account_creation):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)

    with allure.step("Accessing the contact support page via the top navbar Get Help > "
                     "Browse All products"):
        sumo_pages.top_navbar.click_on_browse_all_products_option()
        utilities.delete_cookies()

    for freemium_product in utilities.general_test_data["freemium_products"]:
        with allure.step(f"Clicking on the {freemium_product} card "):
            sumo_pages.contact_support_page.click_on_a_particular_card(freemium_product)
        with check, allure.step("Verifying that the correct 'Still need help' subtext is "
                                "displayed"):
            assert sumo_pages.common_web_elements.get_aaq_widget_text(
            ) == AAQWidgetMessages.FREEMIUM_AAQ_SUBHEADING_TEXT_SIGNED_OUT

        with check, allure.step("Verifying that the correct AAQ button text is displayed"):
            assert sumo_pages.common_web_elements.get_aaq_widget_button_name(
            ) == AAQWidgetMessages.FREEMIUM_AND_PREMIUM_PRODUCTS_AAQ_WIDGET_BUTTON_TEXT

        with allure.step("Clicking on the AAQ button and verifying that the auth page is "
                         "displayed"):
            sumo_pages.common_web_elements.click_on_aaq_button()
            sumo_pages.auth_flow_page.login_with_existing_session()

        with allure.step("Verifying that we are on the correct AAQ form page"):
            expect(page).to_have_url(
                utilities.aaq_question_test_data["products_aaq_url"][freemium_product],
                timeout=30000)

        with allure.step("Signing out and accessing the contact support page via the top "
                         "navbar Get Help > Browse All products"):
            sumo_pages.top_navbar.click_on_sign_out_button()
            sumo_pages.top_navbar.click_on_browse_all_products_option()


# C890382
@pytest.mark.smokeTest
@pytest.mark.productSolutionsPage
def test_contact_support_widget_redirect(page: Page, restmail_test_account_creation):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)

    with allure.step("Accessing the contact support page via the top navbar Get Help > "
                     "Browse All products"):
        sumo_pages.top_navbar.click_on_browse_all_products_option()
        utilities.delete_cookies()

    for premium_product in utilities.general_test_data["premium_products"]:
        with allure.step(f"Clicking on the {premium_product} card"):
            sumo_pages.contact_support_page.click_on_a_particular_card(premium_product)

        with check, allure.step("Verifying that the correct 'Still need help' subtext is "
                                "displayed"):
            assert sumo_pages.common_web_elements.get_aaq_widget_text(
            ) == AAQWidgetMessages.PREMIUM_AAQ_SUBHEADING_TEXT_SIGNED_OUT

        with check, allure.step("Verifying that the correct AAQ button text is displayed"):
            assert sumo_pages.common_web_elements.get_aaq_widget_button_name(
            ) == AAQWidgetMessages.FREEMIUM_AND_PREMIUM_PRODUCTS_AAQ_WIDGET_BUTTON_TEXT

        with allure.step("Clicking on the AAQ button, verifying that the auth page is "
                         "displayed and signing in to SUMO"):
            sumo_pages.common_web_elements.click_on_aaq_button()
            sumo_pages.auth_flow_page.login_with_existing_session()

        with allure.step("Verifying that we are on the correct AAQ form page"):
            expect(page).to_have_url(
                utilities.aaq_question_test_data["products_aaq_url"][premium_product],
                timeout=30000)

        with allure.step("Signing out and access the contact support page via the top navbar "
                         "Get Help > Browse All products"):
            sumo_pages.top_navbar.click_on_sign_out_button()
            sumo_pages.top_navbar.click_on_browse_all_products_option()
