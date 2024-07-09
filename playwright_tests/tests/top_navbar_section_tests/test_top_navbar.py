import allure
import pytest
from playwright.sync_api import Page
from pytest_check import check
import requests

from playwright_tests.core.testutilities import TestUtilities
from playwright_tests.messages.top_navbar_messages import TopNavbarMessages
from playwright_tests.pages.sumo_pages import SumoPages


# C876534, C890961
@pytest.mark.topNavbarTests
def test_number_of_options_not_signed_in(page: Page):
    sumo_pages = SumoPages(page)
    with check, allure.step("Verifying that the SUMO logo is successfully displayed"):
        image = sumo_pages.top_navbar._get_sumo_nav_logo()
        image_link = image.get_attribute("src")
        response = requests.get(image_link, stream=True)
        assert response.status_code < 400

    with allure.step("Verifying that the top-navbar for signed in users contains: Explore "
                     "Help Articles, Community Forums, Ask a Question and Contribute"):
        top_navbar_items = sumo_pages.top_navbar._get_available_menu_titles()
        assert top_navbar_items == TopNavbarMessages.TOP_NAVBAR_OPTIONS, (
            "Incorrect elements displayed in top-navbar for signed out state"
        )


# C876539
@pytest.mark.topNavbarTests
def test_number_of_options_signed_in(page: Page):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in using a non-admin user"):
        test_utilities.start_existing_session(test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts['TEST_ACCOUNT_12']
        ))

    with check, allure.step("Verifying that the SUMO logo is successfully displayed"):
        image = sumo_pages.top_navbar._get_sumo_nav_logo()
        image_link = image.get_attribute("src")
        response = requests.get(image_link, stream=True)
        assert response.status_code < 400

    with allure.step("Verifying that the top-navbar contains: Explore Help Articles, "
                     "Community Forums, Ask a Question, Contribute"):
        top_navbar_items = sumo_pages.top_navbar._get_available_menu_titles()
        assert top_navbar_items == TopNavbarMessages.TOP_NAVBAR_OPTIONS, (
            "Incorrect elements displayed in top-navbar for " "signed-in state"
        )
