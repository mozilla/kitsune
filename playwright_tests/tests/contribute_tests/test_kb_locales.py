import allure
import pytest
from playwright.sync_api import Page, expect
from pytest_check import check

from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.contribute_messages.con_tools.kb_locale_messages import (
    KBLocalePageMessages,
)
from playwright_tests.messages.mess_system_pages_messages.inbox_page_messages import (
    InboxPageMessages,
)
from playwright_tests.messages.mess_system_pages_messages.new_message_page_messages import (
    NewMessagePageMessages,
)
from playwright_tests.pages.sumo_pages import SumoPages

LOCALE = KBLocalePageMessages.TARGET_LOCALE


def _create_de_translation_with_pending_revision(sumo_pages, utilities) -> dict:
    article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
        approve_first_revision=True, ready_for_localization=True)

    utilities.navigate_to_link(article_details["article_url"])
    sumo_pages.kb_article_page.click_on_translate_article_option()
    sumo_pages.translate_article_page.click_on_locale_from_list(LOCALE)
    return sumo_pages.submit_kb_translation_flow._add_article_translation(
        approve_translation_revision=False)


# C2643306
@pytest.mark.kbLocales
def test_locale_list_entry_redirects_to_the_correct_locale_team_page(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)

    with allure.step("Navigating to the /kb/locales page and verifying that locales are listed"):
        utilities.navigate_to_link(KBLocalePageMessages.LOCALES_LIST_URL)
        expect(sumo_pages.kb_locale_page.locale_list_heading).to_have_text(
            KBLocalePageMessages.LOCALES_LIST_HEADING)
        assert sumo_pages.kb_locale_page.get_locale_list_entries_count() > 0, (
            "No locales are listed on the /kb/locales page")

    with allure.step(f"Clicking on the '{LOCALE}' locale entry"):
        sumo_pages.kb_locale_page.click_on_locale_entry(LOCALE)

    with check, allure.step("Verifying that the correct locale team page is displayed"):
        expect(page).to_have_url(KBLocalePageMessages.get_locale_details_url(LOCALE))
        expect(sumo_pages.kb_locale_page.locale_team_heading).to_have_text(
            KBLocalePageMessages.get_locale_team_heading(LOCALE))


# C2643307
@pytest.mark.kbLocales
def test_locale_team_edit_options_are_gated_by_permission(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    roles = [KBLocalePageMessages.LEADER, KBLocalePageMessages.REVIEWER,
             KBLocalePageMessages.EDITOR]

    with allure.step("Creating a simple user and a user with the change_locale permission"):
        simple_user = create_user_factory()
        privileged_user = create_user_factory(permissions=["change_locale"])

    with allure.step("Signing in with the simple user and navigating to the locale team page"):
        utilities.start_existing_session(cookies=simple_user)
        utilities.navigate_to_link(KBLocalePageMessages.get_locale_details_url(LOCALE))

    for role in roles:
        with check, allure.step(f"Verifying that the 'Edit locale {role}s' option is not "
                                f"available to a user without the proper permissions"):
            expect(sumo_pages.kb_locale_page.edit_role_option(role)).to_be_hidden()

    with allure.step("Signing in with the privileged user and navigating to the locale team "
                     "page"):
        utilities.start_existing_session(cookies=privileged_user)
        utilities.navigate_to_link(KBLocalePageMessages.get_locale_details_url(LOCALE))

    for role in roles:
        with check, allure.step(f"Verifying that the 'Edit locale {role}s' option is available "
                                f"to a user with the change_locale permission"):
            expect(sumo_pages.kb_locale_page.edit_role_option(role)).to_be_visible()


# C2643308
@pytest.mark.kbLocales
def test_locale_leader_can_be_added_and_gains_team_edit_permission(page: Page,
                                                                   create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    role = KBLocalePageMessages.LEADER

    with allure.step("Creating a privileged user and the future locale leader"):
        privileged_user = create_user_factory(permissions=["change_locale"])
        leader_user = create_user_factory()

    with allure.step("Signing in with the privileged user and adding the user as a locale "
                     "leader"):
        utilities.start_existing_session(cookies=privileged_user)
        utilities.navigate_to_link(KBLocalePageMessages.get_locale_details_url(LOCALE))
        sumo_pages.kb_locale_page.add_user_to_role(leader_user["username"], role)

    with check, allure.step("Verifying that the user is now listed as a locale leader"):
        expect(sumo_pages.kb_locale_page.role_member(
            role, leader_user["username"])).to_be_visible()

    with allure.step("Signing in with the newly added leader and navigating to the locale team "
                     "page"):
        utilities.start_existing_session(cookies=leader_user)
        utilities.navigate_to_link(KBLocalePageMessages.get_locale_details_url(LOCALE))

    with check, allure.step("Verifying that the leader now has the locale team edit permission"):
        expect(sumo_pages.kb_locale_page.edit_role_option(role)).to_be_visible()


# C2643309
@pytest.mark.kbLocales
def test_locale_leader_can_be_removed_and_loses_team_edit_permission(page: Page,
                                                                     create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    role = KBLocalePageMessages.LEADER

    with allure.step("Creating a privileged user and a locale leader"):
        privileged_user = create_user_factory(permissions=["change_locale"])
        leader_user = create_user_factory()

    with allure.step("Signing in with the privileged user and adding the user as a locale "
                     "leader"):
        utilities.start_existing_session(cookies=privileged_user)
        utilities.navigate_to_link(KBLocalePageMessages.get_locale_details_url(LOCALE))
        sumo_pages.kb_locale_page.add_user_to_role(leader_user["username"], role)
        expect(sumo_pages.kb_locale_page.role_member(
            role, leader_user["username"])).to_be_visible()

    with allure.step("Removing the user from the locale leaders"):
        sumo_pages.kb_locale_page.click_on_remove_user_from_role(leader_user["username"], role)
        sumo_pages.kb_locale_page.click_on_confirm_remove_button()

    with check, allure.step("Verifying that the user is no longer listed as a locale leader"):
        expect(sumo_pages.kb_locale_page.role_member(
            role, leader_user["username"])).to_be_hidden()

    with allure.step("Signing in with the removed leader and navigating to the locale team "
                     "page"):
        utilities.start_existing_session(cookies=leader_user)
        utilities.navigate_to_link(KBLocalePageMessages.get_locale_details_url(LOCALE))

    with check, allure.step("Verifying that the user lost the locale team edit permission"):
        expect(sumo_pages.kb_locale_page.edit_role_option(role)).to_be_hidden()


# C2643310
@pytest.mark.kbLocales
def test_locale_reviewer_can_be_added_and_gains_review_permission(page: Page,
                                                                  create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    role = KBLocalePageMessages.REVIEWER

    with allure.step("Creating a privileged author and the future locale reviewer"):
        privileged_user = create_user_factory(
            permissions=["review_revision", "mark_ready_for_l10n", "change_locale"])
        reviewer_user = create_user_factory()

    with allure.step("Signing in with the privileged user and creating a translation with a "
                     "pending revision"):
        utilities.start_existing_session(cookies=privileged_user)
        translation = _create_de_translation_with_pending_revision(sumo_pages, utilities)
        history_url = translation["translation_url"].rstrip("/") + "/history"

    with allure.step("Adding the reviewer user to the locale reviewers"):
        utilities.navigate_to_link(KBLocalePageMessages.get_locale_details_url(LOCALE))
        sumo_pages.kb_locale_page.add_user_to_role(reviewer_user["username"], role)
        expect(sumo_pages.kb_locale_page.role_member(
            role, reviewer_user["username"])).to_be_visible()

    with allure.step("Signing in with the newly added reviewer and navigating to the "
                     "translation history"):
        utilities.start_existing_session(cookies=reviewer_user)
        utilities.navigate_to_link(history_url)

    with check, allure.step("Verifying that the reviewer can review the pending revision"):
        expect(sumo_pages.kb_article_show_history_page.reviewable_revision(
            translation["revision_id"])).to_be_visible()

    with check, allure.step("Approving the revision and verifying it becomes the current one"):
        sumo_pages.submit_kb_translation_flow.approve_kb_translation(translation["revision_id"])
        assert sumo_pages.kb_article_show_history_page.is_revision_current(
            translation["revision_id"]), (
            "The reviewer was not able to approve the pending revision")


# C2643311
@pytest.mark.kbLocales
def test_locale_reviewer_can_be_removed_and_loses_review_permission(page: Page,
                                                                    create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    role = KBLocalePageMessages.REVIEWER

    with allure.step("Creating a privileged author and a locale reviewer"):
        privileged_user = create_user_factory(
            permissions=["review_revision", "mark_ready_for_l10n", "change_locale"])
        reviewer_user = create_user_factory()

    with allure.step("Signing in with the privileged user and creating a translation with a "
                     "pending revision"):
        utilities.start_existing_session(cookies=privileged_user)
        translation = _create_de_translation_with_pending_revision(sumo_pages, utilities)
        history_url = translation["translation_url"].rstrip("/") + "/history"

    with allure.step("Adding then removing the reviewer user from the locale reviewers"):
        utilities.navigate_to_link(KBLocalePageMessages.get_locale_details_url(LOCALE))
        sumo_pages.kb_locale_page.add_user_to_role(reviewer_user["username"], role)
        expect(sumo_pages.kb_locale_page.role_member(
            role, reviewer_user["username"])).to_be_visible()
        sumo_pages.kb_locale_page.click_on_remove_user_from_role(reviewer_user["username"], role)
        sumo_pages.kb_locale_page.click_on_confirm_remove_button()
        expect(sumo_pages.kb_locale_page.role_member(
            role, reviewer_user["username"])).to_be_hidden()

    with allure.step("Signing in with the removed reviewer and navigating to the translation "
                     "history"):
        utilities.start_existing_session(cookies=reviewer_user)
        utilities.navigate_to_link(history_url)

    with check, allure.step("Verifying that the user can no longer review the pending revision"):
        expect(sumo_pages.kb_article_show_history_page.reviewable_revision(
            translation["revision_id"])).to_be_hidden()


# C2643312
@pytest.mark.kbLocales
def test_locale_editor_can_be_added_and_removed(page: Page, create_user_factory):
    # Note: the locale editor role does not gate any functional permission in Kitsune (it is only
    # surfaced in the 'active contributors' listing), so there is no capability to assert on -
    # this test verifies list membership on add and removal only.
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    role = KBLocalePageMessages.EDITOR

    with allure.step("Creating a privileged user and the future locale editor"):
        privileged_user = create_user_factory(permissions=["change_locale"])
        editor_user = create_user_factory()

    with allure.step("Signing in with the privileged user and adding the user as a locale "
                     "editor"):
        utilities.start_existing_session(cookies=privileged_user)
        utilities.navigate_to_link(KBLocalePageMessages.get_locale_details_url(LOCALE))
        sumo_pages.kb_locale_page.add_user_to_role(editor_user["username"], role)

    with check, allure.step("Verifying that the user is now listed as a locale editor"):
        expect(sumo_pages.kb_locale_page.role_member(
            role, editor_user["username"])).to_be_visible()

    with allure.step("Removing the user from the locale editors"):
        sumo_pages.kb_locale_page.click_on_remove_user_from_role(editor_user["username"], role)
        sumo_pages.kb_locale_page.click_on_confirm_remove_button()

    with check, allure.step("Verifying that the user is no longer listed as a locale editor"):
        expect(sumo_pages.kb_locale_page.role_member(
            role, editor_user["username"])).to_be_hidden()


# C2643313
@pytest.mark.kbLocales
def test_private_message_can_be_sent_via_the_locale_team_page(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    role = KBLocalePageMessages.EDITOR
    message_body = "Test " + utilities.generate_random_number(1, 1000)

    with allure.step("Creating a privileged user and the message recipient"):
        privileged_user = create_user_factory(permissions=["change_locale"])
        recipient_user = create_user_factory()

    with allure.step("Signing in with the privileged user and listing the recipient on the "
                     "locale team page"):
        utilities.start_existing_session(cookies=privileged_user)
        utilities.navigate_to_link(KBLocalePageMessages.get_locale_details_url(LOCALE))
        sumo_pages.kb_locale_page.add_user_to_role(recipient_user["username"], role)
        expect(sumo_pages.kb_locale_page.role_member(
            role, recipient_user["username"])).to_be_visible()

    with allure.step("Clicking on the recipient's 'Private message' link"):
        sumo_pages.kb_locale_page.click_on_private_message_link_for_user(
            recipient_user["username"], role,
            expected_url=(NewMessagePageMessages.NEW_MESSAGE_PAGE_STAGE_URL
                          + f"?to={recipient_user['username']}"))

    with allure.step("Sending a private message to the recipient"):
        sumo_pages.messaging_system_flow.complete_send_message_form_with_data(
            message_body=message_body,
            expected_locator=sumo_pages.inbox_page.message_action_banner)

    with check, allure.step("Verifying that the correct message sent banner is displayed"):
        expect(sumo_pages.inbox_page.message_action_banner).to_have_text(
            InboxPageMessages.MESSAGE_SENT_BANNER_TEXT)

    with check, allure.step("Verifying that the message is displayed in the sent messages list"):
        sumo_pages.mess_system_user_navbar.click_on_messaging_system_nav_sent_messages()
        expect(sumo_pages.sent_message_page.sent_message_by_subject(
            message_body)).to_be_visible()

    with allure.step("Deleting the sent message"):
        sumo_pages.messaging_system_flow.delete_message_flow(
            excerpt=message_body, from_sent_list=True)
