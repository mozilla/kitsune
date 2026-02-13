import allure
import pytest
from pytest_check import check
from playwright.sync_api import TimeoutError, expect, Error, Page
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.ask_a_question_messages.AAQ_messages.aaq_widget import (
    AAQWidgetMessages)
from playwright_tests.messages.contribute_messages.con_pages.con_page_messages import (
    ContributePageMessages)
from playwright_tests.messages.homepage_messages import HomepageMessages
from playwright_tests.pages.sumo_pages import SumoPages


# C890379
@pytest.mark.productTopicsPage
def test_popular_topics_navbar(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)

    with allure.step("Navigating to product topics pages"):
        for product_topic in utilities.general_test_data["product_topics"]:
            topic_url = utilities.general_test_data["product_topics"][product_topic]
            page.wait_for_timeout(400)
            utilities.navigate_to_link(topic_url)
            utilities.wait_for_url_to_be(topic_url)

            for option in sumo_pages.product_topics_page.get_navbar_links_text():
                with allure.step(f"Clicking on {option} navbar option"):
                    option_url = (HomepageMessages.STAGE_HOMEPAGE_URL + sumo_pages.
                                  product_topics_page.get_navbar_option_link(option))
                    sumo_pages.product_topics_page.click_on_a_navbar_option(option)
                    try:
                        utilities.wait_for_url_to_be(option_url)
                    except (TimeoutError, Error):
                        sumo_pages.product_topics_page.click_on_a_navbar_option(option)
                        utilities.wait_for_url_to_be(option_url)

                with check, allure.step("Verifying that the correct option is displayed"):
                    assert sumo_pages.product_topics_page.get_page_title() == option

                with allure.step("Verifying that the correct nav option is selected"):
                    assert sumo_pages.product_topics_page.get_selected_navbar_option() == option


#  T5696796
@pytest.mark.productTopicsPage
def test_learn_more_redirect(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Navigating to product topics pages"):
        for product_topic in utilities.general_test_data["product_topics"]:
            topic_url = utilities.general_test_data["product_topics"][product_topic]
            utilities.navigate_to_link(topic_url)
            utilities.wait_for_url_to_be(topic_url)

            with allure.step("Clicking on the 'Learn More' button"):
                sumo_pages.common_web_elements.click_on_volunteer_learn_more_link()

            with allure.step("Verifying that the user is redirected to the contribute messages "
                             "page"):
                expect(page).to_have_url(ContributePageMessages.STAGE_CONTRIBUTE_PAGE_URL)


# T5696738
@pytest.mark.smokeTest
@pytest.mark.productTopicsPage
def test_aaq_redirect(page: Page, restmail_test_account_creation):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    utilities.delete_cookies()

    with allure.step("Navigating to product topics pages"):
        for product_topic in utilities.general_test_data["product_topics"]:
            topic_url = utilities.general_test_data["product_topics"][product_topic]
            utilities.navigate_to_link(topic_url)
            utilities.wait_for_url_to_be(topic_url)

            with check, allure.step(f"Verifying that the correct subheading page for"
                                    f" {product_topic} is displayed"):
                if product_topic in utilities.general_test_data["premium_products"]:
                    assert sumo_pages.common_web_elements.get_aaq_widget_text(
                    ) == AAQWidgetMessages.PREMIUM_AAQ_SUBHEADING_TEXT_SIGNED_OUT, (
                        f"Incorrect AAQ widget text displayed for the {product_topic} product")
                else:
                    assert sumo_pages.common_web_elements.get_aaq_widget_text(
                    ) == AAQWidgetMessages.FREEMIUM_AAQ_SUBHEADING_TEXT_SIGNED_OUT, (
                        f"Incorrect AAQ widget text displayed for the {product_topic} product")

            with allure.step("Clicking on the AAQ button"):
                sumo_pages.common_web_elements.click_on_aaq_button()

            with allure.step("Signing in to SUMO and verifying that we are on the correct AAQ "
                             "form page"):
                sumo_pages.auth_flow_page.login_with_existing_session()
                expect(page).to_have_url(
                    utilities.aaq_question_test_data["products_aaq_url"][product_topic],
                    timeout=30000)

            with allure.step("Signing out from SUMO"):
                sumo_pages.top_navbar.click_on_sign_out_button()
