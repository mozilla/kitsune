import allure
import pytest
from pytest_check import check
from playwright.sync_api import expect, Page
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.explore_help_articles.kb_article_revision_page_messages import (
    KBArticleRevision)
from playwright_tests.messages.my_profile_pages_messages.my_profile_page_messages import (
    MyProfileMessages)
from playwright_tests.pages.sumo_pages import SumoPages


# C2499112
@pytest.mark.recentRevisionsDashboard
def test_recent_revisions_revision_availability(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with a non-admin account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts['TEST_ACCOUNT_12']
        ))

    username = sumo_pages.top_navbar.get_text_of_logged_in_username()

    with allure.step("Creating a new kb article"):
        article_details = sumo_pages.submit_kb_article_flow.kb_article_creation_via_api(page=page)

    with allure.step("Navigating to the recent revisions dashboard and verifying that the "
                     "posted article is displayed for admin accounts"):
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['recent_revisions']
        )
        expect(
            sumo_pages.recent_revisions_page._get_recent_revision_based_on_article(
                article_details['article_title']
            )
        ).to_be_visible()

    with allure.step("Deleting the user session and verifying that the revision is not "
                     "displayed for signed out users"):
        utilities.delete_cookies()
        expect(
            sumo_pages.recent_revisions_page._get_recent_revision_based_on_article(
                article_details['article_title']
            )
        ).to_be_hidden()

    with allure.step("Typing the article creator username inside the 'Users' field and "
                     "verifying that the article is not displayed"):
        sumo_pages.recent_revisions_page._fill_in_users_field(username)
        utilities.wait_for_given_timeout(2000)
        expect(
            sumo_pages.recent_revisions_page._get_recent_revision_based_on_article(
                article_details['article_title']
            )
        ).to_be_hidden()

    with allure.step("Clearing the user search field and signing in with a different "
                     "non-admin account"):
        sumo_pages.recent_revisions_page._clearing_the_user_field()
        utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_6"]
        )

    with allure.step("Verifying that the revision is not displayed for non-admin accounts"):
        expect(
            sumo_pages.recent_revisions_page._get_recent_revision_based_on_article(
                article_details['article_title']
            )
        ).to_be_hidden()

    with allure.step("Typing the article creator username inside the 'Users' field and "
                     "verifying that the article is not displayed"):
        sumo_pages.recent_revisions_page._fill_in_users_field(username)
        utilities.wait_for_given_timeout(2000)
        expect(
            sumo_pages.recent_revisions_page._get_recent_revision_based_on_article(
                article_details['article_title']
            )
        ).to_be_hidden()

    with allure.step("Clearing the user search field and signing in back with the admin "
                     "account"):
        sumo_pages.recent_revisions_page._clearing_the_user_field()
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

    with allure.step("Navigating to the article page and deleting it"):
        utilities.navigate_to_link(article_details["article_show_history_url"])
        sumo_pages.kb_article_deletion_flow.delete_kb_article()

    with allure.step("Navigating back to the recent revisions page and verifying that the "
                     "article is no longer displayed"):
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['recent_revisions']
        )
        expect(
            sumo_pages.recent_revisions_page._get_recent_revision_based_on_article(
                article_details['article_title']
            )
        ).to_be_hidden()


# C2266240
@pytest.mark.recentRevisionsDashboard
def test_second_revisions_availability(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing back in with the admin account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

    with allure.step("Creating a new kb article"):
        article_details = sumo_pages.submit_kb_article_flow.kb_article_creation_via_api(
            page=page, approve_revision=True)

    with allure.step("Signing in with a non-admin account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_13"]
        ))

    username = sumo_pages.top_navbar.get_text_of_logged_in_username()

    with allure.step("Creating a new revision for the article"):
        second_revision = sumo_pages.submit_kb_article_flow.submit_new_kb_revision()

    with allure.step("Navigating to the Recent Revisions dashboard and verifying that own "
                     "revision is visible"):
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['recent_revisions']
        )
        expect(
            sumo_pages.recent_revisions_page._get_recent_revision_based_on_article_title_and_user(
                article_details['article_title'], username
            )
        ).to_be_visible()

    with allure.step("Deleting user session and verifying that the recent revision is "
                     "displayed"):
        utilities.delete_cookies()
        expect(
            sumo_pages.recent_revisions_page._get_recent_revision_based_on_article_title_and_user(
                article_details['article_title'], username
            )
        ).to_be_visible()

    with allure.step("Signing in with a different non-admin user and verifying that the "
                     "revision is displayed"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_6"]
        ))
        expect(
            sumo_pages.recent_revisions_page._get_recent_revision_based_on_article_title_and_user(
                article_details['article_title'], username
            )
        ).to_be_visible()

    with allure.step("Signing in with an admin account and verifying that the revision is "
                     "displayed"):
        utilities.delete_cookies()
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        expect(
            sumo_pages.recent_revisions_page._get_recent_revision_based_on_article_title_and_user(
                article_details['article_title'], username
            )
        ).to_be_visible()

    with allure.step("Navigating to the article and approving the revision"):
        utilities.navigate_to_link(article_details["article_show_history_url"])
        sumo_pages.submit_kb_article_flow.approve_kb_revision(second_revision['revision_id'])
        utilities.wait_for_given_timeout(1000)

    with allure.step("Signing out and verifying that the revision is displayed inside the "
                     "Recent Revisions dashboard"):
        utilities.delete_cookies()
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['recent_revisions'])
        expect(
            sumo_pages.recent_revisions_page._get_recent_revision_based_on_article_title_and_user(
                article_details['article_title'], username
            )
        ).to_be_visible()

    with allure.step("Signing in with a different non-admin user account and verifying that "
                     "the revision is visible"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_6"]
        ))
        expect(
            sumo_pages.recent_revisions_page._get_recent_revision_based_on_article_title_and_user(
                article_details['article_title'], username
            )
        ).to_be_visible()

    with allure.step("Signing back in with an admin account an deleting the article"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        utilities.navigate_to_link(article_details["article_show_history_url"])
        sumo_pages.kb_article_deletion_flow.delete_kb_article()

    with allure.step("Navigating back to the recent revision dashboard, signing out and "
                     "verifying that the revision is no longer displayed for the deleted kb "
                     "article"):
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['recent_revisions']
        )
        utilities.wait_for_given_timeout(1000)
        utilities.delete_cookies()
        expect(
            sumo_pages.recent_revisions_page._get_recent_revision_based_on_article_title_and_user(
                article_details['article_title'], username
            )
        ).to_be_hidden()

    with allure.step("Signing in with a different non-admin account and verifying that the "
                     "revision is no longer displayed for the deleted kb article"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_6"]
        ))
        expect(
            sumo_pages.recent_revisions_page._get_recent_revision_based_on_article_title_and_user(
                article_details['article_title'], username
            )
        ).to_be_hidden()


# C2266240
@pytest.mark.recentRevisionsDashboard
def test_recent_revisions_dashboard_links(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with an admin account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
    first_username = sumo_pages.top_navbar.get_text_of_logged_in_username()

    with allure.step("Creating a new kb article"):
        article_details = sumo_pages.submit_kb_article_flow.kb_article_creation_via_api(
            page=page, approve_revision=True)

    with allure.step("Navigating to the recent revisions dashboard and verifying that the "
                     "'Show Diff' option is not available for first revisions"):
        sumo_pages.top_navbar.click_on_recent_revisions_option()
        utilities.wait_for_given_timeout(3000)
        expect(
            sumo_pages.recent_revisions_page._get_show_diff_article_locator(
                article_title=article_details['article_title'], creator=first_username
            )
        ).to_be_hidden()

    with allure.step("Navigating to the article page, signing in with a non-admin user and "
                     "creating a new revision for the article"):
        utilities.navigate_to_link(article_details['article_url'])
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_13"]
        ))
        username = sumo_pages.top_navbar.get_text_of_logged_in_username()
        second_revision = sumo_pages.submit_kb_article_flow.submit_new_kb_revision()

    with allure.step("Navigating to the recent revisions dashboard, signing out and clicking "
                     "on the revision date link and verifying that the user is redirected to"
                     "the correct page"):
        sumo_pages.top_navbar.click_on_recent_revisions_option()
        utilities.wait_for_given_timeout(3000)
        utilities.delete_cookies()
        sumo_pages.recent_revisions_page._click_on_revision_date_for_article(
            article_title=article_details['article_title'], username=username
        )
        expect(page).to_have_url(
            article_details['article_url'] + KBArticleRevision.
            KB_REVISION_PREVIEW + str(utilities.number_extraction_from_string(
                second_revision['revision_id']
            ))
        )

    with check, allure.step("Verifying that the revision id is the correct one"):
        assert sumo_pages.kb_article_preview_revision_page._get_preview_revision_id_text(
        ) == str(utilities.number_extraction_from_string(second_revision['revision_id']))

    with allure.step("Navigating back, clicking on the revision title and verifying that the "
                     "user is redirected to the article page"):
        utilities.navigate_back()
        sumo_pages.recent_revisions_page._click_on_article_title(
            article_title=article_details['article_title'], creator=username
        )
        expect(page).to_have_url(article_details['article_url'])

    with check, allure.step("Navigating back and verifying that the correct comment is "
                            "displayed"):
        utilities.navigate_back()
        assert sumo_pages.recent_revisions_page._get_revision_comment(
            article_title=article_details['article_title'], username=username
        ) == utilities.kb_article_test_data['changes_description']

    with allure.step("Clicking on the editor and verifying that the user was redirected to "
                     "the correct page"):
        sumo_pages.recent_revisions_page._click_article_creator_link(
            article_title=article_details['article_title'], creator=username
        )
        expect(page).to_have_url(MyProfileMessages.get_my_profile_stage_url(username))

    with allure.step("Navigating back, clicking on the show diff option and verifying that"
                     "diff section is displayed"):
        utilities.navigate_back()
        sumo_pages.recent_revisions_page._click_on_show_diff_for_article(
            article_title=article_details['article_title'], creator=username
        )
        expect(sumo_pages.recent_revisions_page._get_diff_section_locator()).to_be_visible()

    with allure.step("Hiding the diff and verifying that the diff section is not displayed"):
        sumo_pages.recent_revisions_page._click_on_hide_diff_for_article(
            article_title=article_details['article_title'], creator=username
        )
        expect(sumo_pages.recent_revisions_page._get_diff_section_locator()).to_be_hidden()

    with allure.step("Signing in with an admin account and deleting the article"):
        utilities.delete_cookies()
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        utilities.navigate_to_link(article_details['article_url'])
        sumo_pages.kb_article_deletion_flow.delete_kb_article()


# C2266240, C2243449
@pytest.mark.recentRevisionsDashboard
def test_recent_revisions_dashboard_title_and_username_update(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing back in with the admin account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
    first_username = sumo_pages.top_navbar.get_text_of_logged_in_username()

    with allure.step("Creating a new kb article"):
        article_details = sumo_pages.submit_kb_article_flow.kb_article_creation_via_api(
            page=page, approve_revision=True)

    with allure.step("Changing the article title via the 'Edit Article Metadata' page"):
        sumo_pages.edit_article_metadata_flow.edit_article_metadata(
            title=utilities.kb_article_test_data['updated_kb_article_title'] + article_details
            ['article_title']
        )

    with allure.step("Editing the username"):
        sumo_pages.top_navbar.click_on_edit_profile_option()
        new_username = utilities.profile_edit_test_data['valid_user_edit']['username']
        sumo_pages.edit_my_profile_page.send_text_to_username_field(new_username)
        sumo_pages.edit_my_profile_page.click_update_my_profile_button(
            expected_url=MyProfileMessages.get_my_profile_stage_url(new_username)
        )

    with allure.step("Navigating to the recent revisions dashboard and verifying that the "
                     "correct new username and article title arte displayed"):
        sumo_pages.top_navbar.click_on_recent_revisions_option()
        utilities.wait_for_given_timeout(3000)
        expect(
            sumo_pages.recent_revisions_page._get_revision_and_username_locator(
                article_title=(utilities.kb_article_test_data
                               ['updated_kb_article_title'] + article_details['article_title']),
                username=new_username
            )
        ).to_be_visible()

    with allure.step("Changing the username back"):
        sumo_pages.top_navbar.click_on_edit_profile_option()
        sumo_pages.edit_my_profile_page.send_text_to_username_field(first_username)
        sumo_pages.edit_my_profile_page.click_update_my_profile_button(
            expected_url=MyProfileMessages.get_my_profile_stage_url(first_username)
        )

    with allure.step("Deleting the article"):
        utilities.navigate_to_link(article_details['article_url'])
        sumo_pages.kb_article_deletion_flow.delete_kb_article()


# C2266241
@pytest.mark.recentRevisionsDashboard
def test_recent_revisions_dashboard_filters(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    start_date = "04052023"
    end_date = "05012023"
    with allure.step("Navigating to the 'Recent Revisions' dashboard"):
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['recent_revisions']
        )

    with check, allure.step("Selecting the ro locale from the locale filter and verifying "
                            "that all the displayed revisions are for the 'ro' locale"):
        sumo_pages.recent_revisions_page._select_locale_option("ro")
        utilities.wait_for_given_timeout(3000)
        for tag in sumo_pages.recent_revisions_page._get_list_of_all_locale_tage():
            assert tag == "ro"

    with check, allure.step("Selecting the US filter, typing a username inside the 'Users' "
                            "filter and verifying that all the displayed revisions are for "
                            "the posted user"):
        sumo_pages.recent_revisions_page._select_locale_option("en-US")
        utilities.wait_for_given_timeout(3000)
        username = utilities.username_extraction_from_email(
            utilities.user_secrets_accounts['TEST_ACCOUNT_12']
        )
        sumo_pages.recent_revisions_page._fill_in_users_field(username)
        utilities.wait_for_given_timeout(2000)
        for user in sumo_pages.recent_revisions_page._get_list_of_all_editors():
            assert user == username

    with allure.step("Clearing the user filter, adding data inside the start and end fields"):
        sumo_pages.recent_revisions_page._clearing_the_user_field()
        utilities.wait_for_given_timeout(2000)

        sumo_pages.recent_revisions_page._add_start_date("04052023")
        sumo_pages.recent_revisions_page._add_end_date("05012023")
        utilities.wait_for_given_timeout(2000)

    with check, allure.step("Verifying that the displayed revision dates are between ("
                            "inclusive) the set start and end date filters"):
        extracted_date = []
        date_filters = [int(start_date), int(end_date)]
        for date in sumo_pages.recent_revisions_page._get_all_revision_dates():
            extracted_date.append(utilities.extract_date_to_digit_format(
                utilities.extract_month_day_year_from_string(date)
            ))

        for date in extracted_date:
            assert date_filters[0] <= date <= date_filters[1]
