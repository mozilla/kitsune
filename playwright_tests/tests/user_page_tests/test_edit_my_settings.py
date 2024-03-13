import allure
import pytest
from pytest_check import check

from playwright_tests.core.testutilities import TestUtilities
from playwright_tests.messages.my_profile_pages_messages.edit_settings_page_messages import (
    EditSettingsPageMessages)


class TestEditMySettings(TestUtilities):
    # C891396,  C2108836
    @pytest.mark.userSettings
    def test_all_checkboxes_can_be_selected_and_saved(self):
        with allure.step("Signing in with a non-admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_12']
            ))

        with check, allure.step("Checking all user settings and verifying that the correct "
                                "notification banner is displayed and all checkboxes are checked"):
            self.sumo_pages.edit_profile_flow.check_all_user_settings()
            assert self.sumo_pages.edit_my_profile_settings_page._settings_saved_notif_banner_txt(
            ) == EditSettingsPageMessages.MODIFIED_SETTINGS_NOTIFICATION_BANNER_MESSAGE
            assert (
                self.sumo_pages.edit_my_profile_settings_page._are_all_checkbox_checked()
            ), "Not all checkboxes are checked!"

        with check, allure.step("Unchecking all the checkboxes and verifying that the correct "
                                "notification banner is displayed and all checkboxes are "
                                "unchecked"):
            self.sumo_pages.edit_profile_flow.check_all_user_settings()
            assert self.sumo_pages.edit_my_profile_settings_page._settings_saved_notif_banner_txt(
            ) == EditSettingsPageMessages.MODIFIED_SETTINGS_NOTIFICATION_BANNER_MESSAGE
            assert not (
                self.sumo_pages.edit_my_profile_settings_page._are_all_checkbox_checked()
            ), "Not all checkboxes are unchecked!"
