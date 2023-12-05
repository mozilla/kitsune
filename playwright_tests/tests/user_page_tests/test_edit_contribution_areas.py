import pytest
import pytest_check as check
from playwright.sync_api import expect

from playwright_tests.core.testutilities import TestUtilities
from playwright_tests.messages.mess_system_pages_messages.edit_cont_areas_page_messages import (
    EditContributionAreasPageMessages)
from playwright_tests.messages.my_profile_pages_messages.my_profile_page_messages import (
    MyProfileMessages)


class TestEditContributionAreas(TestUtilities):
    # C2206070
    @pytest.mark.userContributionTests
    def test_all_checkboxes_can_be_selected_and_saved(self):
        self.logger.info("Signing in with a simple user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts['TEST_ACCOUNT_12']
        ))

        original_user = self.sumo_pages.top_navbar.get_text_of_logged_in_username()

        self.logger.info("Clicking on the 'Edit Contribution areas option'")
        self.sumo_pages.top_navbar.click_on_settings_profile_option()

        self.sumo_pages.user_navbar.click_on_edit_contribution_areas_option()

        self.logger.info("Clicking on all checkboxes")
        self.sumo_pages.edit_my_profile_con_areas_page._click_on_unchecked_cont_areas_checkboxes()

        self.logger.info("Clicking on the 'Update' button")

        self.sumo_pages.edit_my_profile_con_areas_page._click_on_update_contribution_areas_button()

        self.logger.info("Verifying that the correct notification banner text is displayed")

        check.equal(
            self.sumo_pages.edit_my_profile_con_areas_page._edit_con_areas_pref_banner_txt(),
            EditContributionAreasPageMessages.PREFERENCES_SAVED_NOTIFICATION_BANNER_TEXT,
            f"Incorrect notification banner message displayed. "
            f"Expected: "
            f"{EditContributionAreasPageMessages.PREFERENCES_SAVED_NOTIFICATION_BANNER_TEXT}"
            f" received: "
            f"{self.sumo_pages.edit_my_profile_con_areas_page._edit_con_areas_pref_banner_txt()}",
        )

        self.logger.info("Verifying that all the checkboxes are checked")
        assert (
            self.sumo_pages.edit_my_profile_con_areas_page._are_all_cont_pref_checkboxes_checked()
        ), "Not all checkbox options are checked!"

        contribution_options = (
            self.sumo_pages.edit_my_profile_con_areas_page._get_contrib_areas_checkbox_labels()
        )

        self.logger.info(
            "Accessing the my profile page and verifying that "
            "the displayed groups are the correct ones"
        )
        self.sumo_pages.user_navbar.click_on_my_profile_option()

        assert (
            self.sumo_pages.my_profile_page.get_my_profile_groups_items_text()
            == contribution_options
        ), (
            f"Not all groups are displayed. Expected:"
            f" {contribution_options} "
            f"received: {self.sumo_pages.my_profile_page.get_my_profile_groups_items_text()}"
        )

        self.logger.info(
            "Signing in with a different account and verifying "
            "that the original user groups are displayed"
        )
        self.delete_cookies()
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts['TEST_ACCOUNT_13']
        ))

        self.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(original_user))

        self.logger.info(
            "Verifying that the user groups is successfully displayed for the original user"
        )
        assert (
            self.sumo_pages.my_profile_page.get_my_profile_groups_items_text()
            == contribution_options
        ), (
            f"Not all groups are displayed. Expected:"
            f" {contribution_options} "
            f"received: {self.sumo_pages.my_profile_page.get_my_profile_groups_items_text()}"
        )

        self.logger.info("Signing in back with the original user")
        self.delete_cookies()
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts['TEST_ACCOUNT_12']
        ))

        self.logger.info(
            "Accessing the edit contribution areas page and unchecking all the checkboxes"
        )
        self.sumo_pages.top_navbar.click_on_settings_profile_option()

        self.sumo_pages.user_navbar.click_on_edit_contribution_areas_option()

        (self.sumo_pages.edit_my_profile_con_areas_page
         ._click_on_all_checked_cont_areas_checkboxes())

        self.logger.info(
            "Clicking on the update button and verifying that "
            "the correct notification banner is displayed"
        )
        self.sumo_pages.edit_my_profile_con_areas_page._click_on_update_contribution_areas_button()

        check.equal(
            self.sumo_pages.edit_my_profile_con_areas_page._edit_con_areas_pref_banner_txt(),
            EditContributionAreasPageMessages.PREFERENCES_SAVED_NOTIFICATION_BANNER_TEXT,
            f"Incorrect notification banner text is displayed."
            f" Expected:"
            f"{EditContributionAreasPageMessages.PREFERENCES_SAVED_NOTIFICATION_BANNER_TEXT}"
            f" received: "
            f"{self.sumo_pages.edit_my_profile_con_areas_page._edit_con_areas_pref_banner_txt()}",
        )

        self.logger.info(
            "Verifying that the profile groups section is no longer "
            "displayed inside the profile section"
        )
        self.sumo_pages.user_navbar.click_on_my_profile_option()

        expect(
            self.sumo_pages.my_profile_page.groups_section_element()
        ).to_be_hidden()

        self.logger.info(
            "Logging in with a different user and accessing the original user profile"
        )
        self.delete_cookies()
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts['TEST_ACCOUNT_13']
        ))

        self.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(original_user))

        self.logger.info(
            "Verifying that the groups section is not longer displayed for the original user"
        )

        expect(
            self.sumo_pages.my_profile_page.groups_section_element()
        ).to_be_hidden()
