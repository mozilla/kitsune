import pytest
import pytest_check as check
import requests

from selenium_tests.core.test_utilities import TestUtilities
from selenium_tests.messages.top_navbar_messages import TopNavbarMessages


class TestTopNavbar(TestUtilities):
    # C876534, C890961
    @pytest.mark.topNavbarTests
    def test_number_of_options_not_signed_in(self):
        self.logger.info("Verifying that the SUMO logo is successfully displayed")

        image = self.pages.top_navbar.get_sumo_nav_logo()
        image_link = image.get_attribute("src")
        response = requests.get(image_link, stream=True)
        check.is_true(response.status_code < 400, f"The {image_link} image is broken")

        self.logger.info(
            "Verifying that top-navbar contains only Get Help & "
            "Contribute options for non signed-in state"
        )
        top_navbar_items = self.pages.top_navbar.get_available_menu_titles()
        expected_top_navbar_items = [
            TopNavbarMessages.GET_HELP_OPTION_TEXT,
            TopNavbarMessages.CONTRIBUTE_OPTION_TEXT,
        ]

        assert top_navbar_items == expected_top_navbar_items, (
            "Incorrect elements displayed in top-navbar for " "signed out state"
        )

    #  C876539
    @pytest.mark.topNavbarTests
    def test_number_of_options_signed_in(self):
        self.logger.info("Clicking on the sign-in/sign-up button")
        self.pages.top_navbar.click_on_signin_signup_button()
        self.logger.info("Signing in with a simple user account")
        # to inspect GH secrets for username & password
        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.logger.info("Verifying that the SUMO logo is successfully displayed")

        image = self.pages.top_navbar.get_sumo_nav_logo()
        image_link = image.get_attribute("src")
        response = requests.get(image_link, stream=True)
        check.is_true(response.status_code < 400, f"The {image_link} image is broken")

        self.logger.info(
            "Verifying that the top-navbar contains Get Help, "
            "Contributor Tools and Contribute options"
        )

        top_navbar_items = self.pages.top_navbar.get_available_menu_titles()
        expected_top_navbar_items = [
            TopNavbarMessages.GET_HELP_OPTION_TEXT,
            TopNavbarMessages.CONTRIBUTOR_TOOLS_TEXT,
            TopNavbarMessages.CONTRIBUTE_OPTION_TEXT,
        ]

        assert top_navbar_items == expected_top_navbar_items, (
            "Incorrect elements displayed in top-navbar for " "signed-in state"
        )

    #  C876534
    @pytest.mark.topNavbarTests
    def test_contributor_tools_is_removed_after_user_signs_out(self):
        self.logger.info("Clicking on the sign-in/sign-up button")
        self.pages.top_navbar.click_on_signin_signup_button()

        self.logger.info("Signing in with a simple user account")

        # to inspect GH secrets for username & password
        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.logger.info("Signing the user out from SUMO")
        self.pages.top_navbar.click_on_sign_out_button()

        self.logger.info(
            "Verifying that top-navbar contains only Get Help & "
            "Contribute options for non signed-in state"
        )

        top_navbar_items = self.pages.top_navbar.get_available_menu_titles()
        expected_top_navbar_items = [
            TopNavbarMessages.GET_HELP_OPTION_TEXT,
            TopNavbarMessages.CONTRIBUTE_OPTION_TEXT,
        ]

        assert top_navbar_items == expected_top_navbar_items, (
            "Incorrect elements displayed in top-navbar for " "signed out state"
        )
