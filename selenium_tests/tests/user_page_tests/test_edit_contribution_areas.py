import pytest
import pytest_check as check

from selenium_tests.core.test_utilities import TestUtilities
from selenium_tests.messages.my_profile_pages_messages.edit_cont_areas_page_messages import (
    EditContributionAreasPageMessages,
)
from selenium_tests.messages.my_profile_pages_messages.my_profile_page_messages import (
    MyProfileMessages,
)


class TestEditContributionAreas(TestUtilities):
    # C2206070
    @pytest.mark.userContributionTests
    def test_all_checkboxes_can_be_selected_and_saved(self):
        self.logger.info("Signing in with a simple user account")

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        original_user = self.pages.top_navbar.get_text_of_logged_in_username()

        self.logger.info("Clicking on the 'Edit Contribution areas option'")

        self.pages.top_navbar.click_on_settings_profile_option()

        self.pages.user_navbar.click_on_edit_contribution_areas_option()

        self.logger.info("Clicking on all checkboxes")

        self.pages.edit_my_profile_con_areas_page._click_on_all_unchecked_cont_areas_checkboxes()

        self.logger.info("Clicking on the 'Update' button")

        self.pages.edit_my_profile_con_areas_page._click_on_update_contribution_areas_button()

        self.logger.info("Verifying that the correct notification banner text is displayed")

        check.equal(
            self.pages.edit_my_profile_con_areas_page._get_edit_con_areas_pref_banner_txt(),
            EditContributionAreasPageMessages.PREFERENCES_SAVED_NOTIFICATION_BANNER_TEXT,
            f"Incorrect notification banner message displayed. "
            f"Expected: "
            f"{EditContributionAreasPageMessages.PREFERENCES_SAVED_NOTIFICATION_BANNER_TEXT}"
            f" received: "
            f"{self.pages.edit_my_profile_con_areas_page._get_edit_con_areas_pref_banner_txt()}",
        )

        self.logger.info(
            "Clicking on the notification banner close button and "
            "verifying that the banner is no longer displayed"
        )

        self.pages.edit_my_profile_con_areas_page._click_on_edit_cont_pref_banner_close_button()

        check.is_false(
            self.pages.edit_my_profile_con_areas_page._is_edit_cont_pref_banner_displayed(),
            "The notification banner is displayed and it shouldn't be!",
        )

        self.logger.info("Verifying that all the checkboxes are checked")

        assert (
            self.pages.edit_my_profile_con_areas_page._are_all_cont_pref_checkboxes_checked()
        ), "Not all checkbox options are checked!"

        contribution_options = (
            self.pages.edit_my_profile_con_areas_page._get_all_contribution_areas_checkbox_labels()
        )

        self.logger.info(
            "Accessing the my profile page and verifying that "
            "the displayed groups are the correct ones"
        )

        self.pages.user_navbar.click_on_my_profile_option()

        assert (
            self.pages.my_profile_page.get_my_profile_groups_items_text() == contribution_options
        ), (
            f"Not all groups are displayed. Expected:"
            f" {contribution_options} "
            f"received: {self.pages.my_profile_page.get_my_profile_groups_items_text()}"
        )

        self.logger.info(
            "Signing in with a different account and verifying "
            "that the original user groups are displayed"
        )

        self.pages.top_navbar.click_on_sign_out_button()

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_13"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.homepage.navigate_to(MyProfileMessages.get_my_profile_stage_url(original_user))

        self.logger.info(
            "Verifying that the user groups is successfully displayed for the original user"
        )

        assert (
            self.pages.my_profile_page.get_my_profile_groups_items_text() == contribution_options
        ), (
            f"Not all groups are displayed. Expected:"
            f" {contribution_options} "
            f"received: {self.pages.my_profile_page.get_my_profile_groups_items_text()}"
        )

        self.logger.info("Signing in back with the original user")

        self.pages.top_navbar.click_on_sign_out_button()

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.logger.info(
            "Accessing the edit contribution areas page and unchecking all the checkboxes"
        )

        self.pages.top_navbar.click_on_settings_profile_option()

        self.pages.user_navbar.click_on_edit_contribution_areas_option()

        self.pages.edit_my_profile_con_areas_page._click_on_all_checked_cont_areas_checkboxes()

        self.logger.info(
            "Clicking on the update button and verifying that "
            "the correct notification banner is displayed"
        )

        self.pages.edit_my_profile_con_areas_page._click_on_update_contribution_areas_button()

        check.equal(
            self.pages.edit_my_profile_con_areas_page._get_edit_con_areas_pref_banner_txt(),
            EditContributionAreasPageMessages.PREFERENCES_SAVED_NOTIFICATION_BANNER_TEXT,
            f"Incorrect notification banner text is displayed."
            f" Expected:"
            f"{EditContributionAreasPageMessages.PREFERENCES_SAVED_NOTIFICATION_BANNER_TEXT}"
            f" received: "
            f"{self.pages.edit_my_profile_con_areas_page._get_edit_con_areas_pref_banner_txt()}",
        )

        self.logger.info(
            "Closing the notification banner and verifying that is no longer displayed"
        )

        self.pages.edit_my_profile_con_areas_page._click_on_edit_cont_pref_banner_close_button()

        check.is_false(
            self.pages.edit_my_profile_con_areas_page._is_edit_cont_pref_banner_displayed(),
            "The notification banner is displayed! It shouldn't be!",
        )

        self.logger.info(
            "Verifying that the profile groups section is no longer "
            "displayed inside the profile section"
        )

        self.pages.user_navbar.click_on_my_profile_option()

        assert not (
            self.pages.my_profile_page.is_groups_section_displayed()
        ), "The user groups is displayed!. It shouldn't be!"

        self.logger.info(
            "Logging in with a different user and accessing the original user profile"
        )

        self.pages.top_navbar.click_on_sign_out_button()

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_13"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.homepage.navigate_to(MyProfileMessages.get_my_profile_stage_url(original_user))

        self.logger.info(
            "Verifying that the groups section is not longer displayed for the original user"
        )

        assert not (
            self.pages.my_profile_page.is_groups_section_displayed()
        ), "The user groups is displayed!. It shouldn't be!"
