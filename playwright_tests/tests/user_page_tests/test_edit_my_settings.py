import pytest
import pytest_check as check

from playwright_tests.core.testutilities import TestUtilities
from playwright_tests.messages.my_profile_pages_messages.edit_settings_page_messages import (
    EditSettingsPageMessages)


class TestEditMySettings(TestUtilities):
    # C891396,  C2108836
    @pytest.mark.userSettings
    def test_all_checkboxes_can_be_selected_and_saved(self):
        self.logger.info(
            "Signing in to a normal user account "
        )
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts['TEST_ACCOUNT_12']
        ))

        self.sumo_pages.top_navbar.click_on_settings_profile_option()

        self.logger.info("Clicking on all available checkboxes")
        self.sumo_pages.edit_my_profile_settings_page.click_on_all_settings_checkboxes()

        self.logger.info("Clicking on the 'Update' button")
        self.sumo_pages.edit_my_profile_settings_page.click_on_update_button()

        self.logger.info("Verifying that the correct notification banner is displayed")
        check.equal(
            self.sumo_pages.edit_my_profile_settings_page.settings_saved_notif_banner_txt(),
            EditSettingsPageMessages.MODIFIED_SETTINGS_NOTIFICATION_BANNER_MESSAGE,
            f"Incorrect message displayed inside the notification banner. Expected:"
            f" {EditSettingsPageMessages.MODIFIED_SETTINGS_NOTIFICATION_BANNER_MESSAGE} "
            f"but received: "
            f"{self.sumo_pages.edit_my_profile_settings_page.settings_saved_notif_banner_txt()}",
        )

        self.logger.info("Verifying that all the checkboxes are checked")

        assert (
            self.sumo_pages.edit_my_profile_settings_page.are_all_checkbox_checked()
        ), "Not all checkboxes are checked!"

        self.logger.info(
            "Unchecking all the available checkboxes and clicking on the 'Update' button"
        )

        self.sumo_pages.edit_my_profile_settings_page.click_on_all_settings_checkboxes()

        self.sumo_pages.edit_my_profile_settings_page.click_on_update_button()

        self.logger.info("Verifying that the correct notification banner is displayed")

        check.equal(
            self.sumo_pages.edit_my_profile_settings_page.settings_saved_notif_banner_txt(),
            EditSettingsPageMessages.MODIFIED_SETTINGS_NOTIFICATION_BANNER_MESSAGE,
            f"Incorrect message displayed inside the notification banner. Expected:"
            f" {EditSettingsPageMessages.MODIFIED_SETTINGS_NOTIFICATION_BANNER_MESSAGE} "
            f"but received: "
            f"{self.sumo_pages.edit_my_profile_settings_page.settings_saved_notif_banner_txt()}",
        )

        self.logger.info("Verifying that all the checkboxes are unchecked")
        assert not (
            self.sumo_pages.edit_my_profile_settings_page.are_all_checkbox_checked()
        ), "Not all checkboxes are unchecked!"
