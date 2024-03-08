import allure
import pytest
from pytest_check import check
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
        with allure.step("Signing in with a non-admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_12']
            ))

        original_user = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        with allure.step("Checking all contributor checkboxes"):
            self.sumo_pages.edit_profile_flow.check_all_profile_contribution_areas(checked=False)

        with check, allure.step("Verifying that the correct notification banner text is "
                                "displayed"):
            assert self.sumo_pages.edit_my_profile_con_areas_page._edit_con_areas_pref_banner_txt(
            ) == EditContributionAreasPageMessages.PREFERENCES_SAVED_NOTIFICATION_BANNER_TEXT

        with allure.step("Verifying that all the checkboxes are checked"):
            assert (
                self.sumo_pages.edit_my_profile_con_areas_page._are_all_cont_pref_checked()
            ), "Not all checkbox options are checked!"

        contribution_options = (
            self.sumo_pages.edit_my_profile_con_areas_page._get_contrib_areas_checkbox_labels()
        )

        with allure.step("Accessing the my profile page and verifying that the displayed groups "
                         "are the correct ones"):
            self.sumo_pages.user_navbar._click_on_my_profile_option()
            assert (
                self.sumo_pages.my_profile_page._get_my_profile_groups_items_text()
                == contribution_options
            )

        with allure.step("Signing in with a different account and verifying that the original "
                         "user groups are displayed"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_13']
            ))

        with allure.step("Navigating to the user page and verifying that the user groups is "
                         "successfully displayed"):
            self.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(original_user))
            assert (
                self.sumo_pages.my_profile_page._get_my_profile_groups_items_text()
                == contribution_options
            )

        with allure.step("Signing in back with the original user"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_12']
            ))

        with allure.step("Accessing the edit contribution areas page and unchecking all "
                         "checkboxes"):
            self.sumo_pages.edit_profile_flow.check_all_profile_contribution_areas(checked=True)

        with check, allure.step("Clicking on the update button and verifying that the correct "
                                "notification banner is displayed"):
            assert self.sumo_pages.edit_my_profile_con_areas_page._edit_con_areas_pref_banner_txt(
            ) == EditContributionAreasPageMessages.PREFERENCES_SAVED_NOTIFICATION_BANNER_TEXT

        with allure.step("Verifying that the profile groups section is no longer displayed "
                         "inside the profile section"):
            self.sumo_pages.user_navbar._click_on_my_profile_option()
            expect(
                self.sumo_pages.my_profile_page._groups_section_element()
            ).to_be_hidden()

        with allure.step("Logging in with a different user and accessing the original user "
                         "profile"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_13']
            ))

        with allure.step("Navigating to the my profile page and verifying that the groups "
                         "section is no longer displayed for the original user"):
            self.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(original_user))
            expect(
                self.sumo_pages.my_profile_page._groups_section_element()
            ).to_be_hidden()
