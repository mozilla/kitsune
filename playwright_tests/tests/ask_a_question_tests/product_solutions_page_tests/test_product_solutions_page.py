import allure
import pytest
from pytest_check import check

from playwright.sync_api import expect, TimeoutError, Page
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.ask_a_question_messages.AAQ_messages.aaq_widget import (
    AAQWidgetMessages)
from playwright_tests.messages.ask_a_question_messages.product_solutions_messages import (
    ProductSolutionsMessages)
from playwright_tests.pages.sumo_pages import SumoPages


# Currently fails due to https://github.com/mozilla/sumo/issues/1608
#  C890370
@pytest.mark.skip
def test_featured_articles_redirect(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Accessing the contact support page via the top navbar Get Help > "
                     "Browse All products"):
        sumo_pages.top_navbar.click_on_browse_all_products_option()

    with allure.step("Clicking on all product cards"):
        for card in sumo_pages.contact_support_page.get_all_product_card_titles():
            with check, allure.step(f"Clicking on the {card} and verifying that the correct "
                                    f"product solutions page header is displayed"):
                sumo_pages.contact_support_page.click_on_a_particular_card(card)
                assert sumo_pages.product_solutions_page.get_product_solutions_heading(
                ) == card + ProductSolutionsMessages.PAGE_HEADER

            if sumo_pages.product_solutions_page.is_featured_article_section_displayed():
                for featured_article_card in (sumo_pages.product_solutions_page
                                              .get_all_featured_articles_titles()):
                    sumo_pages.product_solutions_page.click_on_a_featured_article_card(
                        featured_article_card)
                    with check, allure.step(f"Clicking on the {featured_article_card} and "
                                            f"verifying that the correct article page title "
                                            f"is displayed"):
                        with page.context.expect_page() as tab:
                            feature_article_page = tab.value
                        article_text = (feature_article_page.
                                        locator("//h1[@class='sumo-page-heading']").inner_text())
                        assert article_text == featured_article_card
                        feature_article_page.close()
            else:
                print(f"{card} has no featured articles displayed!!!")
            utilities.navigate_back()


#  T5696585, T5696587
@pytest.mark.productSolutionsPage
def test_popular_topics_redirect(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Accessing the contact support page via the top navbar Get Help > "
                     "Browse All products"):
        sumo_pages.top_navbar.click_on_browse_all_products_option()

    for card in sumo_pages.contact_support_page.get_all_product_card_titles():
        sumo_pages.contact_support_page.click_on_a_particular_card(card)
        with check, allure.step(f"Clicking on the {card} card and verifying that the correct "
                                f"product solutions page is displayed"):
            assert sumo_pages.product_solutions_page.get_product_solutions_heading(
            ) == card + ProductSolutionsMessages.PAGE_HEADER

        if sumo_pages.product_solutions_page.is_popular_topics_section_displayed:
            for topic in sumo_pages.product_solutions_page.get_popular_topics():
                sumo_pages.product_solutions_page.click_on_a_popular_topic_card(topic)
                with check, allure.step(f"Clicking on the {topic} topic and verifying if "
                                        f"correct topic page title is displayed"):
                    try:
                        with page.context.expect_page() as tab:
                            feature_article_page = tab.value
                            print(f"Tab open for topic: {topic}")
                    except TimeoutError:
                        print("Trying to click on the popular topic again")
                        sumo_pages.product_solutions_page.click_on_a_popular_topic_card(
                            topic)
                        with page.context.expect_page() as tab:
                            feature_article_page = tab.value
                            print(f"Tab open for topic: {topic}")

                    popular_topic = (feature_article_page
                                     .locator("//h1[@class='topic-title sumo-page-heading']")
                                     .inner_text())
                    assert popular_topic == topic
                    feature_article_page.close()
        else:
            print(f"{card} has no featured articles displayed!!!")

        utilities.navigate_back()


# T5696588
@pytest.mark.productSolutionsPage
def test_ask_now_widget_redirect(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Accessing the contact support page via the top navbar Get Help > "
                     "Browse All products"):
        sumo_pages.top_navbar.click_on_browse_all_products_option()
    count = 0
    for freemium_product in utilities.general_test_data["freemium_products"]:
        with allure.step(f"Clicking on the {freemium_product} card "):
            sumo_pages.contact_support_page.click_on_a_particular_card(freemium_product)
        with check, allure.step("verifying that the correct 'Still need help' subtext is "
                                "displayed"):
            assert sumo_pages.product_solutions_page.get_aaq_product_solutions_subheading_text(
            ) == AAQWidgetMessages.FREEMIUM_AAQ_SUBHEADING_TEXT_SIGNED_OUT

        with check, allure.step("Verifying that the correct AAQ button text is displayed"):
            assert sumo_pages.product_solutions_page.get_aaq_widget_button_name(
            ) == AAQWidgetMessages.FREEMIUM_AND_PREMIUM_PRODUCTS_AAQ_WIDGET_BUTTON_TEXT

        with allure.step("Clicking on the AAQ button and verifying that the auth page is "
                         "displayed"):
            sumo_pages.product_solutions_page.click_ask_now_button()
            if count == 0:
                sumo_pages.auth_flow_page.sign_in_flow(
                    username=utilities.user_special_chars,
                    account_password=utilities.user_secrets_pass,
                )
                count += 1
            else:
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
@pytest.mark.productSolutionsPage
def test_contact_support_widget_redirect(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Accessing the contact support page via the top navbar Get Help > "
                     "Browse All products"):
        sumo_pages.top_navbar.click_on_browse_all_products_option()
    count = 0
    for premium_product in utilities.general_test_data["premium_products"]:
        with allure.step(f"Clicking on the {premium_product} card"):
            sumo_pages.contact_support_page.click_on_a_particular_card(premium_product)

        with check, allure.step("Verifying that the correct 'Still need help' subtext is "
                                "displayed"):
            assert sumo_pages.product_solutions_page.get_aaq_product_solutions_subheading_text(
            ) == AAQWidgetMessages.PREMIUM_AAQ_SUBHEADING_TEXT_SIGNED_OUT

        with check, allure.step("Verifying that the correct AAQ button text is displayed"):
            assert sumo_pages.product_solutions_page.get_aaq_widget_button_name(
            ) == AAQWidgetMessages.FREEMIUM_AND_PREMIUM_PRODUCTS_AAQ_WIDGET_BUTTON_TEXT

        with allure.step("Clicking on the AAQ button, verifying that the auth page is "
                         "displayed and signing in to SUMO"):
            sumo_pages.product_solutions_page.click_ask_now_button()

            if count == 0:
                sumo_pages.auth_flow_page.sign_in_flow(
                    username=utilities.user_special_chars,
                    account_password=utilities.user_secrets_pass,
                )
                count += 1
            else:
                sumo_pages.auth_flow_page.login_with_existing_session()

        with allure.step("Verifying that we are on the correct AAQ form page"):
            expect(page).to_have_url(
                utilities.aaq_question_test_data["products_aaq_url"][premium_product],
                timeout=30000)

        with allure.step("Signing out and access the contact support page via the top navbar "
                         "Get Help > Browse All products"):
            sumo_pages.top_navbar.click_on_sign_out_button()
            sumo_pages.top_navbar.click_on_browse_all_products_option()
