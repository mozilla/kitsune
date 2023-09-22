import pytest
import pytest_check as check

from selenium_tests.core.test_utilities import TestUtilities
from selenium_tests.messages.my_profile_pages_messages.edit_settings_page_messages import (
    EditSettingsPageMessages,
)


class TestEditMySettings(TestUtilities):
    # C891396,  C2108836
    @pytest.mark.userSettings
    def test_all_checkboxes_can_be_selected_and_saved(self):
        self.logger.info(
            "Signing in to a normal user account "
            "and accessing edit settings page via the top-navbar menu"
        )

        self.pages.top_navbar.click_on_signin_signup_button()

        self.pages.auth_flow_page.sign_in_flow(
            username=super().user_secrets_data["TEST_ACCOUNT_12"],
            account_password=super().user_secrets_data["TEST_ACCOUNTS_PS"],
            sign_in_with_same_account=False,
        )

        self.pages.top_navbar.click_on_settings_profile_option()

        self.logger.info("Clicking on all available checkboxes")

        self.pages.edit_my_profile_settings_page.click_on_all_settings_checkboxes()

        self.logger.info("Clicking on the 'Update' button")

        self.pages.edit_my_profile_settings_page.click_on_update_button()

        self.logger.info("Verifying that the correct notification banner is displayed")

        check.equal(
            self.pages.edit_my_profile_settings_page.get_settings_saved_notif_banner_text(),
            EditSettingsPageMessages.MODIFIED_SETTINGS_NOTIFICATION_BANNER_MESSAGE,
            f"Incorrect message displayed inside the notification banner. Expected:"
            f" {EditSettingsPageMessages.MODIFIED_SETTINGS_NOTIFICATION_BANNER_MESSAGE} "
            f"but received: "
            f"{self.pages.edit_my_profile_settings_page.get_settings_saved_notif_banner_text()}",
        )

        self.logger.info(
            "Closing the notification banner and verifying that the banner is no longer displayed"
        )

        self.pages.edit_my_profile_settings_page.click_settings_saved_notification_banner()

        check.is_false(
            self.pages.edit_my_profile_settings_page.is_notification_banner_displayed(),
            "The notification banner is displayed. It shouldn't be!",
        )

        self.logger.info("Verifying that all the checkboxes are checked")

        assert (
            self.pages.edit_my_profile_settings_page.are_all_checkbox_checked()
        ), "Not all checkboxes are checked!"

        self.logger.info(
            "Unchecking all the available checkboxes and clicking on the 'Update' button"
        )

        self.pages.edit_my_profile_settings_page.click_on_all_settings_checkboxes()

        self.pages.edit_my_profile_settings_page.click_on_update_button()

        self.logger.info("Verifying that the correct notification banner is displayed")

        check.equal(
            self.pages.edit_my_profile_settings_page.get_settings_saved_notif_banner_text(),
            EditSettingsPageMessages.MODIFIED_SETTINGS_NOTIFICATION_BANNER_MESSAGE,
            f"Incorrect message displayed inside the notification banner. Expected:"
            f" {EditSettingsPageMessages.MODIFIED_SETTINGS_NOTIFICATION_BANNER_MESSAGE} "
            f"but received: "
            f"{self.pages.edit_my_profile_settings_page.get_settings_saved_notif_banner_text()}",
        )

        self.logger.info(
            "Closing the notification banner and verifying that the banner is no longer displayed"
        )

        self.pages.edit_my_profile_settings_page.click_settings_saved_notification_banner()

        check.is_false(
            self.pages.edit_my_profile_settings_page.is_notification_banner_displayed(),
            "The notification banner is displayed. It shouldn't be!",
        )

        self.logger.info("Verifying that all the checkboxes are unchecked")

        assert not (
            self.pages.edit_my_profile_settings_page.are_all_checkbox_checked()
        ), "Not all checkboxes are unchecked!"
