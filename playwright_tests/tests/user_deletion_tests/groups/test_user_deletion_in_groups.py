import allure
import pytest
from playwright.sync_api import Page
from playwright_tests.core.utilities import Utilities
from playwright_tests.pages.sumo_pages import SumoPages


# C2939494 
@pytest.mark.userDeletion
def test_deleted_user_is_removed_from_groups(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    staff = utilities.username_extraction_from_email(utilities.staff_user)

    with allure.step("Signing in with the staff user and adding the test user to a test group"):
        utilities.start_existing_session(session_file_name=staff)
        utilities.navigate_to_link(utilities.general_test_data['groups'])
        sumo_pages.user_groups.click_on_a_particular_group(
            utilities.user_message_test_data['test_groups'][1])
        sumo_pages.user_group_flow.add_a_user_to_group(test_user["username"], is_leader=True)

    with allure.step("Verifying that the test user is displayed in both group leaders and group "
                     "members sections"):
        assert test_user["username"] in sumo_pages.user_groups.get_all_leaders_name()
        assert test_user["username"] in sumo_pages.user_groups.get_all_members_name()

    with allure.step("Signing in with the test user and initiating the user deletion flow"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.edit_profile_flow.close_account()

    with (allure.step("Navigating back to the test group and verifying that:"
                     "1. The deleted username is no longer displayed inside the group leaders or "
                     "members."
                     "2. The system account is not displayed as a group leader or member")):
        utilities.navigate_to_link(utilities.general_test_data['groups'])
        sumo_pages.user_groups.click_on_a_particular_group(
            utilities.user_message_test_data['test_groups'][1])
        assert test_user["username"] not in sumo_pages.user_groups.get_all_leaders_name()
        assert test_user["username"] not in sumo_pages.user_groups.get_all_members_name()

        assert (utilities.general_test_data["system_account_name"] not in sumo_pages
                .user_groups.get_all_leaders_name())
        assert (utilities.general_test_data["system_account_name"] not in sumo_pages.user_groups
                .get_all_members_name())

