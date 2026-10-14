import allure
import pytest
from playwright.sync_api import Page, expect
from pytest_check import check
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.ask_a_question_messages.AAQ_messages.aaq_widget import (
    AAQWidgetMessages,
)
from playwright_tests.messages.ask_a_question_messages.contact_support_messages import (
    ContactSupportMessages,
)
from playwright_tests.pages.sumo_pages import SumoPages

troubleshooting_topic_url = "https://support.allizom.org/en-US/topics/browse"
# Splits the topic walk across xdist workers; matches CI's --numprocesses 6.
TOPIC_SHARDS = 6


#  C2663958, C2663959
@pytest.mark.exploreByTopics
@pytest.mark.parametrize("shard", range(TOPIC_SHARDS))
def test_explore_by_topic_product_filter(page: Page, shard: int):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)

    with allure.step("Navigating to the /topics/ Browse page"):
        utilities.navigate_to_link(troubleshooting_topic_url)
    for topic in sumo_pages.explore_by_topic_page.get_all_topics_side_navbar_options()[
            shard::TOPIC_SHARDS]:
        topic = topic.strip()
        if topic != "Browse":
            sumo_pages.explore_by_topic_page.click_on_a_topic_filter(topic)
        with check, allure.step("Verifying that the correct page header is displayed for the"
                                f"{topic} topic"):
            expect(sumo_pages.explore_by_topic_page.explore_by_topic_page_header).to_have_text(
                topic)
        for product in sumo_pages.explore_by_topic_page.get_all_filter_by_product_options():
            utilities.wait_for_dom_to_load()
            product = product.strip()
            if product.strip() == "All Products":
                continue
            else:
                sumo_pages.explore_by_topic_page.select_a_filter_by_product_option(product.strip())
                if not sumo_pages.explore_by_topic_page.get_metadata_of_all_listed_articles():
                    pytest.fail(f"There is no sublist for {product} for the {topic} filter")

                for sublist in (sumo_pages.explore_by_topic_page
                    .get_metadata_of_all_listed_articles()):
                    with check, allure.step(f"Verifying that '{product}' is listed in the "
                                            f"article metadata for the {topic} topic filter"):
                        assert product in sublist


# C2462867
@pytest.mark.exploreByTopics
@pytest.mark.parametrize("shard", range(TOPIC_SHARDS))
def test_explore_by_topic_aaq_widget_text(page: Page, create_user_factory, shard: int):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory()

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Navigating to the /topics/ Browse page"):
        utilities.navigate_to_link(troubleshooting_topic_url)
    for topic in sumo_pages.explore_by_topic_page.get_all_topics_side_navbar_options()[
            shard::TOPIC_SHARDS]:
        topic = topic.strip()
        if topic != "Browse":
            sumo_pages.explore_by_topic_page.click_on_a_topic_filter(topic)
        for product in sumo_pages.explore_by_topic_page.get_all_filter_by_product_options():
            product = product.strip()
            sumo_pages.explore_by_topic_page.select_a_filter_by_product_option(product)
            with check, allure.step("Verifying the correct AAQ widget text is displayed for "
                                    f"{product}"):
                if product == "All Products":
                    expect(sumo_pages.common_web_elements.still_need_help_subheading).to_have_text(
                        AAQWidgetMessages.NEUTRAL_AAQ_SUBHEADING_TEXT)
                elif product in utilities.general_test_data['subscription_redirects']:
                    with check, allure.step("Verifying that the AAQ widget is not displayed"):
                        expect(sumo_pages.common_web_elements.aaq_widget).to_be_hidden()
                elif product in utilities.general_test_data['freemium_products']:
                    expect(sumo_pages.common_web_elements.still_need_help_subheading).to_have_text(
                        AAQWidgetMessages.FREEMIUM_AAQ_SUBHEADING_TEXT)
                elif product in utilities.general_test_data['premium_products']:
                    expect(sumo_pages.common_web_elements.still_need_help_subheading).to_have_text(
                        AAQWidgetMessages.PREMIUM_AAQ_SUBHEADING_TEXT)
                elif (product not in utilities.general_test_data['premium_products'] and
                      product not in utilities.general_test_data['freemium_products']):
                    with allure.step("Verifying that the AAQ widget is not displayed for the "
                                     "product which has both AAQ and Zendesk configs disabled"):
                        expect(sumo_pages.common_web_elements.aaq_widget).to_be_hidden()


# C2663960
@pytest.mark.exploreByTopics
@pytest.mark.parametrize("shard", range(TOPIC_SHARDS))
def test_explore_by_topic_aaq_widget_redirect(page: Page, create_user_factory, shard: int):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory()

    with allure.step(f"Signing in with {test_user['username']} user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Navigating to the /topics/ Browse page"):
        utilities.navigate_to_link(troubleshooting_topic_url)

    for topic in sumo_pages.explore_by_topic_page.get_all_topics_side_navbar_options()[
            shard::TOPIC_SHARDS]:
        topic = topic.strip()
        if topic != "Browse":
            sumo_pages.explore_by_topic_page.click_on_a_topic_filter(topic)
        for product in sumo_pages.explore_by_topic_page.get_all_filter_by_product_options():
            product = product.strip()
            sumo_pages.explore_by_topic_page.select_a_filter_by_product_option(product)
            filtered_topic_url = utilities.get_page_url()

            if product == "All Products":
                with allure.step("Clicking on the AAQ button"):
                    sumo_pages.common_web_elements.click_on_aaq_button()
                with check, allure.step("Verifying that the contact support page URL is correct"):
                    expect(page).to_have_url(ContactSupportMessages.PAGE_URL)
            elif product in utilities.general_test_data['subscription_redirects']:
                with check, allure.step("Verifying that the AAQ widget is not displayed"):
                    expect(sumo_pages.common_web_elements.aaq_widget).to_be_hidden()
            elif (product not in utilities.general_test_data['premium_products'] and
                  product not in utilities.general_test_data['freemium_products']):
                with check, allure.step("Verifying that the AAQ widget is not displayed for the "
                                        "product which has both AAQ and Zendesk configs disabled"):
                    expect(sumo_pages.common_web_elements.aaq_widget).to_be_hidden()
            else:
                with allure.step("Clicking on the AAQ button"):
                    sumo_pages.common_web_elements.click_on_aaq_button()
                with check, allure.step("Verifying that the correct AAQ form URL is displayed"):
                    expect(page).to_have_url(
                        utilities.aaq_question_test_data['products_aaq_url'][product])
            # Only an AAQ click leaves the page; the user goes back to it with the back button.
            if utilities.get_page_url() != filtered_topic_url:
                utilities.navigate_back()


# C2663961
@pytest.mark.exploreByTopics
def test_incorrect_kb_topic_listing_redirect(page: Page):
    utilities = Utilities(page)
    with page.expect_navigation() as navigation_info:
        utilities.navigate_to_link("https://support.allizom.org/en-US/topics/testt")
    response = navigation_info.value
    with check, allure.step("Verifying that the page returns a 404 status code"):
        assert response.status == 404
