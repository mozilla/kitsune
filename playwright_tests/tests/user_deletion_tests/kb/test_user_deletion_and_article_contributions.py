import allure
import pytest
from playwright.sync_api import Page, expect
from pytest_check import check
from playwright_tests.core.utilities import Utilities
from playwright_tests.pages.sumo_pages import SumoPages
from playwright_tests.tests.conftest import create_user_factory


# C2952002, C2952017
@pytest.mark.userDeletion
def test_reviewed_revisions_assignment_to_system_account(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["Knowledge Base Reviewers"])
    test_user_two = create_user_factory()
    staff = utilities.username_extraction_from_email(utilities.staff_user)

    with allure.step("Signing in with the first test user and creating a new kb article"):
        utilities.start_existing_session(cookies=test_user)
        article_details = sumo_pages.submit_kb_article_flow.kb_article_creation_via_api(
            page=page, approve_revision=True)

    with allure.step("Signing in with the second account and creating a new revision"):
        utilities.start_existing_session(cookies=test_user_two)
        second_revision = sumo_pages.submit_kb_article_flow.submit_new_kb_revision()

    with allure.step("Signing in with the first test user, creating a new revision and approving "
                     "it"):
        utilities.start_existing_session(cookies=test_user)
        third_revision = sumo_pages.submit_kb_article_flow.submit_new_kb_revision(
            approve_revision= True)

    with allure.step("Signing in with the second user and deleting the account via the edit my "
                     "profile page"):
        utilities.start_existing_session(cookies=test_user_two)
        sumo_pages.edit_profile_flow.close_account()

    with check, allure.step("Navigating back to the article's show history page and verifying "
                            "that the second revision was deleted since it was not approved"):
        utilities.navigate_to_link(article_details["article_url"] + "/history")
        utilities.start_existing_session(session_file_name=staff)

        assert not sumo_pages.kb_article_show_history_page.is_revision_displayed(
            second_revision["revision_id"])

    with check, allure.step("Verifying that the other revisions are belonging to the user which "
                            "was not deleted"):
        assert sumo_pages.kb_article_show_history_page.get_revision_creator(
            article_details["first_revision_id"]) == test_user["username"]
        assert sumo_pages.kb_article_show_history_page.get_revision_creator(
            third_revision["revision_id"]) == test_user["username"]

    with allure.step("Signing in with the first user and deleting the account"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.edit_profile_flow.close_account()

    with allure.step("Navigating back to the article and verifying that all revisions belong "
                     "to SuMo Bot"):
        utilities.navigate_to_link(article_details["article_url"] + "/history")
        utilities.start_existing_session(session_file_name=staff)

        assert (sumo_pages.kb_article_show_history_page.get_revision_creator(
            article_details["first_revision_id"]
        ) == utilities.general_test_data["system_account_name"])
        assert (sumo_pages.kb_article_show_history_page.get_revision_creator(
            third_revision["revision_id"]) == utilities.general_test_data["system_account_name"])

    with allure.step("Deleting the test article"):
        sumo_pages.kb_article_deletion_flow.delete_kb_article()


# C2952003, C2952016
@pytest.mark.userDeletion
def test_unreviewed_revisions_are_not_assigned_to_system_account(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    staff = utilities.username_extraction_from_email(utilities.staff_user)

    with allure.step("Signing in with the first test user and creating a new kb article"):
        utilities.start_existing_session(cookies=test_user)
        article_details = sumo_pages.submit_kb_article_flow.kb_article_creation_via_api(page=page)
        sumo_pages.submit_kb_article_flow.submit_new_kb_revision()

    with allure.step("Navigating to the 'Edit profile' and delete the account via the "
                     "'Close account and delete all profile information' option"):
        sumo_pages.edit_profile_flow.close_account()

    with allure.step("Signing in with a staff account, navigating to the article page and "
                     "verifying that 404 is returned"):
        utilities.start_existing_session(session_file_name=staff)
        assert utilities.navigate_to_link(article_details["article_url"]).status == 404


# C2952004
@pytest.mark.userDeletion
def test_deferred_revisions_are_not_assigned_to_system_account(page:Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    test_user_two = create_user_factory(groups=["Knowledge Base Reviewers"])
    staff_user = utilities.username_extraction_from_email(utilities.staff_user)

    with allure.step("Creating a new article and approving it's first revision"):
        utilities.start_existing_session(cookies=test_user_two)
        article_details = sumo_pages.submit_kb_article_flow.kb_article_creation_via_api(
            page=page, approve_revision=True)

    with allure.step("Signing in with a different user and submitting a new article revision "
                     "without approving it"):
        utilities.start_existing_session(cookies=test_user)
        second_revision = sumo_pages.submit_kb_article_flow.submit_new_kb_revision()

    with allure.step("Signing in back with the KB reviewer and deferring the second revision"):
        utilities.start_existing_session(cookies=test_user_two)
        sumo_pages.submit_kb_article_flow.defer_revision(second_revision["revision_id"])

    with allure.step("Deleting the first user and verifying that the revision was deleted"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.edit_profile_flow.close_account()
        utilities.start_existing_session(cookies=test_user_two)
        utilities.navigate_to_link(article_details["article_url"] + "/history")
        assert not sumo_pages.kb_article_show_history_page.is_revision_displayed(
            second_revision["revision_id"])

    with allure.step("Deleting the article"):
        utilities.start_existing_session(session_file_name=staff_user)
        sumo_pages.kb_article_deletion_flow.delete_kb_article()


#  C2979501, C2979502
@pytest.mark.userDeletion
def test_localization_revisions_are_assigned_to_system_account(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["Knowledge Base Reviewers"])
    staff = utilities.username_extraction_from_email(utilities.staff_user)

    with allure.step("Signing in with the KB reviewer and creating a new kb article, approving "
                     "it's first revision and markit it as ready for localization"):
        utilities.start_existing_session(cookies=test_user)
        article_details = sumo_pages.submit_kb_article_flow.kb_article_creation_via_api(
            page=page, approve_revision=True, ready_for_l10n=True)

    with allure.step("Deleting the user"):
        sumo_pages.edit_profile_flow.close_account()

    with allure.step("Signing in with the staff user and verifying that the ready for localization"
                     " status is kept"):
        utilities.start_existing_session(session_file_name=staff)
        utilities.navigate_to_link(article_details["article_url"] + "/history")
        expect(sumo_pages.kb_article_show_history_page.get_ready_for_localization_status(
            article_details["first_revision_id"])).to_be_visible()

    with allure.step("Deleting the article"):
        sumo_pages.kb_article_deletion_flow.delete_kb_article()


# C2979502
@pytest.mark.userDeletion
def test_reviewed_by_assignment_to_system_account(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    test_user_two = create_user_factory(groups=["Knowledge Base Reviewers"])
    staff_user = utilities.username_extraction_from_email(utilities.staff_user)

    with allure.step("Signing in and creating a new kb article"):
        utilities.start_existing_session(cookies=test_user)
        article_details = sumo_pages.submit_kb_article_flow.kb_article_creation_via_api(page=page)

    with allure.step("Signing in with a KB reviewer and approving the revision"):
        utilities.start_existing_session(cookies=test_user_two)
        sumo_pages.submit_kb_article_flow.approve_kb_revision(
            revision_id=article_details["first_revision_id"])

    with allure.step("Signing in back with the first user and creating a new article revision"):
        utilities.start_existing_session(cookies=test_user)
        second_revision = sumo_pages.submit_kb_article_flow.submit_new_kb_revision()

    with allure.step("Signing in with a KB reviewer and deferring the revision"):
        utilities.start_existing_session(cookies=test_user_two)
        sumo_pages.submit_kb_article_flow.defer_revision(
            revision_id=second_revision["revision_id"])

    with allure.step("Deleting the user"):
        sumo_pages.edit_profile_flow.close_account()

    with allure.step("Navigating back to the show history page and verifying that the reviewer of "
                     "both revisions is Sumo Bot"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(article_details["article_url"] + "/history")
        sumo_pages.kb_article_show_history_page.click_on_a_revision_date(
            article_details["first_revision_id"])
        assert sumo_pages.kb_article_preview_revision_page.get_reviewed_by_text() == "SumoBot"
        utilities.navigate_back()
        sumo_pages.kb_article_show_history_page.click_on_a_revision_date(
            second_revision["revision_id"])
        assert sumo_pages.kb_article_preview_revision_page.get_reviewed_by_text() == "SumoBot"

    with allure.step("Deleting the revision"):
        utilities.start_existing_session(session_file_name=staff_user)
        sumo_pages.kb_article_deletion_flow.delete_kb_article()
