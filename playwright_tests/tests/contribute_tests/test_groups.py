import os
import allure
import pytest
from playwright.sync_api import Page
from pytest_check import check
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.user_groups_messages import UserGroupMessages
from playwright_tests.pages.sumo_pages import SumoPages


# C2083482
@pytest.mark.userGroupsTests
def test_edit_groups_details_visibility(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    with check, allure.step("Navigating to the general groups page and verifying that the 'edit "
                            "groups details' button is not visible while signed out"):
        utilities.navigate_to_link(utilities.general_test_data['groups'])
        assert not sumo_pages.user_groups.is_add_group_profile_button_visible()

    with check, allure.step("Signing in with a non-admin account and verifying that the 'edit "
                            "groups details' button is not visible"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts['TEST_ACCOUNT_13']
        ))
        utilities.navigate_to_link(utilities.general_test_data['groups'])
        assert not sumo_pages.user_groups.is_add_group_profile_button_visible()

    with check, allure.step("Signing in with an admin account and verifying that the 'edit group "
                            "details' button is visible"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts['TEST_ACCOUNT_MODERATOR']
        ))
        utilities.navigate_to_link(utilities.general_test_data['groups'])
        assert sumo_pages.user_groups.is_add_group_profile_button_visible()


# C2083482, C2083483, C2715808, C2715807, C2799838
@pytest.mark.userGroupsTests
def test_group_edit_buttons_visibility(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)

    with check, allure.step("Navigating to a test group and verifying that the edit buttons are "
                            "not available for signed out users"):
        utilities.navigate_to_link(utilities.general_test_data['groups'])
        sumo_pages.user_groups.click_on_a_particular_group(
            utilities.user_message_test_data['test_groups'][1])

        assert not sumo_pages.user_groups.is_change_avatar_button_visible()
        assert not sumo_pages.user_groups.is_edit_in_admin_button_visible()
        assert not sumo_pages.user_groups.is_edit_group_profile_button_visible()
        assert not sumo_pages.user_groups.is_edit_group_leaders_button_visible()
        assert not sumo_pages.user_groups.is_edit_group_members_option_visible()

    with check, allure.step("Signing in with a non-admin and a non group member and verifying "
                            "that the edit buttons are not available"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts['TEST_ACCOUNT_13']
        ))
        assert not sumo_pages.user_groups.is_change_avatar_button_visible()
        assert not sumo_pages.user_groups.is_edit_in_admin_button_visible()
        assert not sumo_pages.user_groups.is_edit_group_profile_button_visible()
        assert not sumo_pages.user_groups.is_edit_group_leaders_button_visible()
        assert not sumo_pages.user_groups.is_edit_group_members_option_visible()

    with check, allure.step("Signing in with a group member and verifying that the edit buttons "
                            "are not available"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts['TEST_ACCOUNT_MESSAGE_3']
        ))
        assert not sumo_pages.user_groups.is_change_avatar_button_visible()
        assert not sumo_pages.user_groups.is_edit_in_admin_button_visible()
        assert not sumo_pages.user_groups.is_edit_group_profile_button_visible()
        assert not sumo_pages.user_groups.is_edit_group_leaders_button_visible()
        assert not sumo_pages.user_groups.is_edit_group_members_option_visible()

    with check, allure.step("Signing in with the group leader and verifying that only the 'edit "
                            "in admin' and 'edit group leaders' buttons are available"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts['TEST_ACCOUNT_MESSAGE_4']
        ))
        assert sumo_pages.user_groups.is_change_avatar_button_visible()
        assert not sumo_pages.user_groups.is_edit_in_admin_button_visible()
        assert sumo_pages.user_groups.is_edit_group_profile_button_visible()
        assert not sumo_pages.user_groups.is_edit_group_leaders_button_visible()
        assert sumo_pages.user_groups.is_edit_group_members_option_visible()

    with check, allure.step("Signing in with an admin account and verifying that all edit options "
                            "are available"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts['TEST_ACCOUNT_MODERATOR']
        ))
        assert sumo_pages.user_groups.is_change_avatar_button_visible()
        assert sumo_pages.user_groups.is_edit_in_admin_button_visible()
        assert sumo_pages.user_groups.is_edit_group_profile_button_visible()
        assert sumo_pages.user_groups.is_edit_group_leaders_button_visible()
        assert sumo_pages.user_groups.is_edit_group_members_option_visible()


# C2783730, C2715807
@pytest.mark.userGroupsTests
def test_change_group_avatar(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    targeted_group = utilities.user_message_test_data['test_groups'][0]
    displayed_image = os.path.abspath("test_data/visual_testing/displayed_group_image.png")
    first_uploaded_image = os.path.abspath("test_data/test-image.png")
    second_uploaded_image = os.path.abspath("test_data/test-image2.png")

    with allure.step("Signing in with a group leader and accessing the test group"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts['TEST_ACCOUNT_MESSAGE_2']
        ))
        utilities.navigate_to_link(utilities.general_test_data['groups'])
        sumo_pages.user_groups.click_on_a_particular_group(targeted_group)
        group_url = utilities.get_page_url()
        utilities.screenshot_the_locator(sumo_pages.user_groups.get_group_avatar_locator(),
                                         displayed_image)

    with allure.step("Clicking on the 'Change' avatar button, uploading the image and clicking on"
                     "the 'Cancel' button"):
        sumo_pages.user_groups.click_on_change_avatar_button()
        utilities.upload_file(sumo_pages.user_groups.CHANGE_AVATAR_PAGE_LOCATORS
                              ['upload_avatar_browse_button'], first_uploaded_image)
        sumo_pages.user_groups.click_on_upload_avatar_cancel_button()

    with check, allure.step("Verifying that the uploaded avatar image is not displayed inside the "
                            "group"):
        assert utilities.are_images_different(displayed_image, first_uploaded_image)

    with allure.step("Clicking on the 'Change' avatar button, uploading the image and clicking on"
                     "the 'Upload' button"):
        sumo_pages.user_groups.click_on_change_avatar_button()
        utilities.upload_file(sumo_pages.user_groups.CHANGE_AVATAR_PAGE_LOCATORS
                              ['upload_avatar_browse_button'], first_uploaded_image)
        sumo_pages.user_groups.click_on_upload_avatar_button(expected_url=group_url)

    with check, allure.step("Verifying that the uploaded image is successfully displayed inside "
                            "the group"):
        utilities.screenshot_the_locator(sumo_pages.user_groups.get_group_avatar_locator(),
                                         displayed_image)
        assert not utilities.are_images_different(displayed_image, first_uploaded_image)

    with check, allure.step("Clicking on the 'Change' avatar option and verifying that the "
                            "uploaded image is successfully displayed inside the image preview"):
        sumo_pages.user_groups.click_on_change_uploaded_avatar_button()
        utilities.screenshot_the_locator(
            sumo_pages.user_groups.get_change_avatar_image_preview_locator(),
            displayed_image
        )
        assert not utilities.are_images_different(displayed_image,
                                                  first_uploaded_image)

    with check, allure.step("Verifying that the correct page header is displayed"):
        assert (sumo_pages.user_groups.get_upload_avatar_page_header() == UserGroupMessages.
                get_change_uploaded_avatar_page_header(targeted_group))

    with check, allure.step("Adding a new image, clicking on the 'Cancel' button and verifying "
                            "that the new image was not added to the group"):
        utilities.upload_file(sumo_pages.user_groups.CHANGE_AVATAR_PAGE_LOCATORS
                              ['upload_avatar_browse_button'], second_uploaded_image)
        sumo_pages.user_groups.click_on_upload_avatar_cancel_button()
        assert utilities.are_images_different(first_uploaded_image, second_uploaded_image)

    with check, allure.step("Adding a new image, clicking on the 'Upload' button and verifying "
                            "that the newly uploaded image is displayed inside the group"):
        sumo_pages.user_groups.click_on_change_uploaded_avatar_button()
        utilities.upload_file(sumo_pages.user_groups.CHANGE_AVATAR_PAGE_LOCATORS
                              ['upload_avatar_browse_button'], second_uploaded_image)
        sumo_pages.user_groups.click_on_upload_avatar_button(expected_url=group_url)

        utilities.screenshot_the_locator(sumo_pages.user_groups.get_group_avatar_locator(),
                                         displayed_image)
        assert not utilities.are_images_different(displayed_image, second_uploaded_image)

    with check, allure.step("Clicking on the 'Delete' avatar button and verifying the page"
                            "content"):
        sumo_pages.user_groups.click_on_delete_uploaded_avatar_button()
        assert (sumo_pages.user_groups.get_delete_avatar_page_header() == UserGroupMessages.
                get_delete_uploaded_avatar_page_header(targeted_group))

        assert (sumo_pages.user_groups.get_delete_avatar_page_info() == UserGroupMessages.
                DELETE_AVATAR_PAGE_INFO)

        utilities.screenshot_the_locator(
            sumo_pages.user_groups.get_delete_avatar_image_preview_locator(), displayed_image)
        assert not utilities.are_images_different(displayed_image, second_uploaded_image)

    with allure.step("Clicking on the 'Cancel' button and verifying that the image was not "
                     "deleted"):
        sumo_pages.user_groups.click_on_cancel_delete_avatar_button()
        utilities.screenshot_the_locator(sumo_pages.user_groups.get_group_avatar_locator(),
                                         displayed_image)
        assert not utilities.are_images_different(displayed_image, second_uploaded_image)

    with allure.step("Clicking on the 'Delete' avatar button, confirming the deletion and "
                     "verifying that the image was deleted"):
        sumo_pages.user_groups.click_on_delete_uploaded_avatar_button()
        sumo_pages.user_groups.click_on_delete_avatar_button()
        utilities.screenshot_the_locator(sumo_pages.user_groups.get_group_avatar_locator(),
                                         displayed_image)
        assert utilities.are_images_different(displayed_image, second_uploaded_image)


# C2799839
@pytest.mark.userGroupsTests
def test_add_new_group_leader(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = utilities.username_extraction_from_email(
        utilities.user_secrets_accounts["TEST_ACCOUNT_12"]
    )

    test_group = utilities.user_message_test_data['test_groups'][2]

    with allure.step("Signing in with an admin account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

    utilities.navigate_to_link(utilities.general_test_data['groups'])
    sumo_pages.user_groups.click_on_a_particular_group(test_group)

    with allure.step("Adding a new group leader"):
        sumo_pages.user_group_flow.add_a_user_to_group(test_user, is_leader=True)

    with allure.step("Verifying that the user was added in both group leaders and group members "
                     "list"):
        assert test_user in sumo_pages.user_groups.get_all_leaders_name()
        assert test_user in sumo_pages.user_groups.get_all_members_name()

    with allure.step("Verifying that the correct banner is displayed"):
        assert (sumo_pages.user_groups.get_group_update_notification() == UserGroupMessages.
                get_user_added_success_message(test_user, to_leaders=True))

    with allure.step("Clicking on the added user"):
        sumo_pages.user_groups.click_on_a_listed_group_leader(test_user)

    with allure.step("Verifying that the group is listed inside the users profile group list"):
        assert test_group in sumo_pages.my_profile_page.get_my_profile_groups_items_text()

    with allure.step("Clicking on the group link from the profile page"):
        sumo_pages.my_profile_page.click_on_a_particular_profile_group(test_group)

    with check, allure.step("Clicking on the 'Delete' button for the newly added user and "
                            "verifying that the correct page header is displayed"):
        sumo_pages.user_groups.click_on_edit_group_leaders_option()
        sumo_pages.user_groups.click_on_remove_a_user_from_group_button(test_user,
                                                                        from_leaders=True)
        assert (sumo_pages.user_groups.get_remove_leader_page_header() == UserGroupMessages.
                get_delete_user_header(test_user, test_group, delete_leader=True))

    with check, allure.step("Clicking on the 'Cancel' button and verifying that the user was not "
                            "removed from the leaders and members list"):
        sumo_pages.user_groups.click_on_remove_member_cancel_button()
        assert test_user in sumo_pages.user_groups.get_all_leaders_name()
        assert test_user in sumo_pages.user_groups.get_all_members_name()

    with check, allure.step("Deleting the user and verifying that the user was removed from the "
                            "leaders list but not from the members list"):
        sumo_pages.user_group_flow.remove_a_user_from_group(test_user, is_leader=True)
        assert test_user not in sumo_pages.user_groups.get_all_leaders_name()
        assert test_user in sumo_pages.user_groups.get_all_members_name()

    with check, allure.step("Verifying that the correct banner is displayed"):
        assert (sumo_pages.user_groups.get_group_update_notification() == UserGroupMessages.
                get_user_removed_success_message(test_user, from_leaders=True))

    with allure.step("Deleting the user from the members list"):
        sumo_pages.user_group_flow.remove_a_user_from_group(test_user)


# C2083499, C2715807
@pytest.mark.userGroupsTests
@pytest.mark.parametrize("user", ['TEST_ACCOUNT_MESSAGE_2', 'TEST_ACCOUNT_MODERATOR'])
def test_add_group_members(page: Page, user):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = utilities.username_extraction_from_email(
        utilities.user_secrets_accounts[
            "TEST_ACCOUNT_12" if user == 'TEST_ACCOUNT_MESSAGE_2' else "TEST_ACCOUNT_13"]
    )

    test_group = utilities.user_message_test_data['test_groups'][0]

    with allure.step("Signing in and accessing the test group"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts[user]
        ))

        utilities.navigate_to_link(utilities.general_test_data['groups'])
        sumo_pages.user_groups.click_on_a_particular_group(test_group)

    with allure.step("Adding a new group member"):
        sumo_pages.user_group_flow.add_a_user_to_group(test_user)

    with allure.step("Verifying that the correct banner is displayed"):
        assert (sumo_pages.user_groups.get_group_update_notification() == UserGroupMessages.
                get_user_added_success_message(test_user))

    with allure.step("Clicking on the added user"):
        sumo_pages.user_groups.click_on_a_listed_group_user(test_user)

    with allure.step("Verifying that the group is listed inside the users profile group list"):
        assert test_group in sumo_pages.my_profile_page.get_my_profile_groups_items_text()

    with allure.step("Clicking on the group link from the profile page"):
        sumo_pages.my_profile_page.click_on_a_particular_profile_group(test_group)

    with check, allure.step("Clicking on the 'Delete' button for the newly added user and "
                            "verifying that the correct page header is displayed"):
        sumo_pages.user_groups.click_on_edit_group_members()
        sumo_pages.user_groups.click_on_remove_a_user_from_group_button(test_user)
        assert (sumo_pages.user_groups.get_remove_user_page_header() == UserGroupMessages.
                get_delete_user_header(test_user, test_group))

    with check, allure.step("Clicking on the 'Cancel' button and verifying that the user was not "
                            "removed"):
        sumo_pages.user_groups.click_on_remove_member_cancel_button()
        assert test_user in sumo_pages.user_groups.get_all_members_name()

    with check, allure.step("Deleting the user and verifying that the user was removed"):
        sumo_pages.user_group_flow.remove_a_user_from_group(test_user)
        assert test_user not in sumo_pages.user_groups.get_all_members_name()

    with check, allure.step("Verifying that the correct banner is displayed"):
        assert (sumo_pages.user_groups.get_group_update_notification() == UserGroupMessages.
                get_user_removed_success_message(test_user))


# C2784450
@pytest.mark.userGroupsTests
@pytest.mark.parametrize("user", ['TEST_ACCOUNT_MESSAGE_2', 'TEST_ACCOUNT_MODERATOR'])
def test_edit_group_profile(page: Page, user):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_group = (utilities.user_message_test_data['test_groups']
                  [0] if user == 'TEST_ACCOUNT_MESSAGE_2' else utilities.
                  user_message_test_data['test_groups'][1])

    with allure.step("Signing in and accessing the test group"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts[user]
        ))

        utilities.navigate_to_link(utilities.general_test_data['groups'])
        sumo_pages.user_groups.click_on_a_particular_group(test_group)

    group_profile_info = sumo_pages.user_groups.get_profile_information()

    with check, allure.step("Clicking on the 'Edit' button and verifying that the correct page "
                            "header is displayed"):
        sumo_pages.user_groups.click_on_edit_group_profile_button()
        assert (sumo_pages.user_groups.get_edit_group_profile_page_header() == UserGroupMessages.
                get_edit_profile_information_page_header(test_group))

    with check, allure.step("Verifying that the correct information was pre-filled inside the "
                            "textarea field"):
        assert (sumo_pages.user_groups.
                get_edit_group_profile_textarea_content() == group_profile_info)

    with allure.step("Changing the group profile information and verifying that the new info is "
                     "displayed"):
        sumo_pages.user_groups.type_into_edit_group_profile_textarea(group_profile_info + " v2")
        sumo_pages.user_groups.click_on_edit_group_profile_save_button()
        assert (sumo_pages.user_groups.get_group_update_notification() == UserGroupMessages.
               GROUP_INFORMATION_UPDATE_NOTIFICATION)
        assert (sumo_pages.user_groups.get_profile_information() == group_profile_info + " v2")

    with allure.step("Signing out and verifying that the new group profile information is "
                     "displayed for signed out users"):
        utilities.delete_cookies()
        assert (sumo_pages.user_groups.get_profile_information() == group_profile_info + " v2")

    with allure.step("Signing back in and reverting the profile information change"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts[user]
        ))
        sumo_pages.user_groups.click_on_edit_group_profile_button()
        sumo_pages.user_groups.type_into_edit_group_profile_textarea(group_profile_info)
        sumo_pages.user_groups.click_on_edit_group_profile_save_button()
