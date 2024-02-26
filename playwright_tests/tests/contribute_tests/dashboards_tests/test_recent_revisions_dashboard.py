import pytest
import pytest_check as check
from playwright.sync_api import expect
from playwright_tests.core.testutilities import TestUtilities
from playwright_tests.messages.explore_help_articles.kb_article_revision_page_messages import (
    KBArticleRevision)
from playwright_tests.messages.my_profile_pages_messages.my_profile_page_messages import (
    MyProfileMessages)


class TestRecentRevisionsDashboard(TestUtilities):

    # C2499112
    @pytest.mark.recentRevisionsDashboard
    def test_recent_revisions_revision_availability(self):
        self.logger.info("Signing in with a non-Admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts['TEST_ACCOUNT_12']
        ))

        username = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        self.logger.info("Create a new simple article")
        article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        article_url = self.get_page_url()

        self.logger.info("Navigating to the recent revisions dashboard")
        self.sumo_pages.top_navbar._click_on_recent_revisions_option()

        self.logger.info("Verifying that the posted article is displayed for admin accounts")
        expect(
            self.sumo_pages.recent_revisions_page._get_recent_revision_based_on_article_locator(
                article_details['article_title']
            )
        ).to_be_visible()

        self.logger.info("Deleting user session and verifying that the revision is not displayed")
        self.delete_cookies()

        expect(
            self.sumo_pages.recent_revisions_page._get_recent_revision_based_on_article_locator(
                article_details['article_title']
            )
        ).to_be_hidden()

        self.logger.info("Typing the article creator username inside the 'Users' field and "
                         "verifying that the article is not displayed")
        self.sumo_pages.recent_revisions_page._fill_in_users_field(username)

        self.wait_for_given_timeout(2000)

        expect(
            self.sumo_pages.recent_revisions_page._get_recent_revision_based_on_article_locator(
                article_details['article_title']
            )
        ).to_be_hidden()

        self.logger.info("Clearing the user search field")
        self.sumo_pages.recent_revisions_page._clearing_the_user_field()

        self.logger.info("Signing in with a different user account")
        self.username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_6"]
        )

        self.logger.info("Verifying that the revision is not displayed")
        expect(
            self.sumo_pages.recent_revisions_page._get_recent_revision_based_on_article_locator(
                article_details['article_title']
            )
        ).to_be_hidden()

        self.logger.info("Typing the article creator username inside the 'Users' field and "
                         "verifying that the article is not displayed")
        self.sumo_pages.recent_revisions_page._fill_in_users_field(username)
        self.wait_for_given_timeout(2000)

        expect(
            self.sumo_pages.recent_revisions_page._get_recent_revision_based_on_article_locator(
                article_details['article_title']
            )
        ).to_be_hidden()

        self.logger.info("Clearing the user search field")
        self.sumo_pages.recent_revisions_page._clearing_the_user_field()

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Signing back in with the admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Navigating to the article page and deleting it")
        self.navigate_to_link(article_url)
        self.sumo_pages.kb_article_show_history_page._click_on_delete_this_document_button()
        self.sumo_pages.kb_article_show_history_page._click_on_confirmation_delete_button()

        self.logger.info("Navigating back to the recent revisions page and verifying that the "
                         "article is no longer displayed")

        self.logger.info("Navigating to the recent revisions dashboard")
        self.sumo_pages.top_navbar._click_on_recent_revisions_option()

        self.logger.info("Verifying that the posted article is no longer displayed for admin "
                         "accounts")
        expect(
            self.sumo_pages.recent_revisions_page._get_recent_revision_based_on_article_locator(
                article_details['article_title']
            )
        ).to_be_hidden()

    # C2266240
    @pytest.mark.recentRevisionsDashboard
    def test_second_revisions_availability(self):
        self.logger.info("Signing back in with the admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Create a new simple article")
        article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        article_url = self.get_page_url()
        revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()

        self.logger.info("Clicking on the 'Review' option")
        self.sumo_pages.kb_article_show_history_page._click_on_review_revision(
            revision_id
        )

        self.logger.info("Click on 'Approve Revision' button")
        self.sumo_pages.kb_article_review_revision_page._click_on_approve_revision_button()

        self.logger.info("Clicking on the 'Accept' button")
        self.sumo_pages.kb_article_review_revision_page._click_accept_revision_accept_button()

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Signing in with a non admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_13"]
        ))

        username = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        self.logger.info("Creating a new revision for the article")
        second_revision_id = self.sumo_pages.kb_article_revision_flow.submit_new_kb_revision()

        self.logger.info("Navigating to the Recent Revisions dashboard and verifying that own "
                         "revision is visible")
        self.sumo_pages.top_navbar._click_on_recent_revisions_option()
        expect(
            self.sumo_pages.recent_revisions_page.
            _get_recent_revision_based_on_article_title_and_user(
                article_details['article_title'], username
            )
        ).to_be_visible()

        self.logger.info("Deleting user session and verifying that the recent revision is "
                         "displayed")
        self.delete_cookies()
        expect(
            self.sumo_pages.recent_revisions_page.
            _get_recent_revision_based_on_article_title_and_user(
                article_details['article_title'], username
            )
        ).to_be_visible()

        self.logger.info("Signing in with a different non-admin user and verifying that the "
                         "revision is displayed")
        self.username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_6"]
        )
        expect(
            self.sumo_pages.recent_revisions_page.
            _get_recent_revision_based_on_article_title_and_user(
                article_details['article_title'], username
            )
        ).to_be_visible()

        self.logger.info("Signing in with an admin account and verifying that the revision is "
                         "displayed")
        self.delete_cookies()

        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        expect(
            self.sumo_pages.recent_revisions_page.
            _get_recent_revision_based_on_article_title_and_user(
                article_details['article_title'], username
            )
        ).to_be_visible()

        self.logger.info("Navigating to the article and approving the revision")
        self.navigate_to_link(article_url)

        self.logger.info("Clicking on the 'Review' option")
        self.sumo_pages.kb_article_show_history_page._click_on_review_revision(
            second_revision_id
        )

        self.logger.info("Click on 'Approve Revision' button")
        self.sumo_pages.kb_article_review_revision_page._click_on_approve_revision_button()

        self.logger.info("Clicking on the 'Accept' button")
        self.sumo_pages.kb_article_review_revision_page._click_accept_revision_accept_button()
        self.sumo_pages.top_navbar._click_on_recent_revisions_option()

        expect(
            self.page
        ).to_have_url(self.general_test_data['dashboard_links']['recent_revisions'])

        self.logger.info("Signing out and verifying that the revision is displayed inside the "
                         "Recent Revisions dashboard")
        self.delete_cookies()
        expect(
            self.sumo_pages.recent_revisions_page.
            _get_recent_revision_based_on_article_title_and_user(
                article_details['article_title'], username
            )
        ).to_be_visible()

        self.logger.info("Signing in with a different non-admin user account and verifying that "
                         "the revision is visible")
        self.username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_6"]
        )
        expect(
            self.sumo_pages.recent_revisions_page.
            _get_recent_revision_based_on_article_title_and_user(
                article_details['article_title'], username
            )
        ).to_be_visible()

        self.logger.info("Signing back in with an admin account an deleting the article")
        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Signing back in with the admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Navigating to the article page and deleting it")
        self.navigate_to_link(article_url)
        self.sumo_pages.kb_article_show_history_page._click_on_delete_this_document_button()
        self.sumo_pages.kb_article_show_history_page._click_on_confirmation_delete_button()
        self.sumo_pages.top_navbar._click_on_recent_revisions_option()

        expect(
            self.page
        ).to_have_url(self.general_test_data['dashboard_links']['recent_revisions'])

        self.logger.info("Signing out and and verifying that the revision is no longer displayed "
                         "inside the Recent Revisions dashboard")
        self.delete_cookies()
        expect(
            self.sumo_pages.recent_revisions_page.
            _get_recent_revision_based_on_article_title_and_user(
                article_details['article_title'], username
            )
        ).to_be_hidden()

        self.logger.info("Signing in with a different non-admin user account and verifying that "
                         "the revision is not visible")
        self.username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_6"]
        )
        expect(
            self.sumo_pages.recent_revisions_page.
            _get_recent_revision_based_on_article_title_and_user(
                article_details['article_title'], username
            )
        ).to_be_hidden()

    # C2266240
    @pytest.mark.recentRevisionsDashboard
    def test_recent_revisions_dashboard_links(self):
        self.logger.info("Signing back in with the admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        first_username = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        self.logger.info("Create a new simple article")
        article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        self.sumo_pages.kb_article_page._click_on_article_option()
        article_url = self.get_page_url()

        self.logger.info("Clicking on the 'Show History' option")
        self.sumo_pages.kb_article_page._click_on_show_history_option()

        revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()

        self.logger.info("Clicking on the 'Review' option")
        self.sumo_pages.kb_article_show_history_page._click_on_review_revision(
            revision_id
        )

        self.logger.info("Click on 'Approve Revision' button")
        self.sumo_pages.kb_article_review_revision_page._click_on_approve_revision_button()

        self.logger.info("Clicking on the 'Accept' button")
        self.sumo_pages.kb_article_review_revision_page._click_accept_revision_accept_button()

        self.logger.info("Navigating to the recent revisions dashboard")
        self.sumo_pages.top_navbar._click_on_recent_revisions_option()

        expect(
            self.page
        ).to_have_url(self.general_test_data['dashboard_links']['recent_revisions'])

        self.logger.info("Verifying that the Show Diff option is not available for first revision")
        expect(
            self.sumo_pages.recent_revisions_page._get_show_diff_article_locator(
                article_title=article_details['article_title'], creator=first_username
            )
        ).to_be_hidden()

        self.navigate_to_link(article_url)

        self.logger.info("Signing in with a different user non-admin user")
        self.delete_cookies()

        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))
        username = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        self.logger.info("Creating a new revision for the article")
        second_revision_id = self.sumo_pages.kb_article_revision_flow.submit_new_kb_revision()

        self.logger.info("Navigating to the Recent Revisions dashboard")
        self.sumo_pages.top_navbar._click_on_recent_revisions_option()

        expect(
            self.page
        ).to_have_url(self.general_test_data['dashboard_links']['recent_revisions'])

        self.logger.info("Signing out from SUMO")
        self.delete_cookies()

        self.logger.info("Clicking on the revision date link")
        self.sumo_pages.recent_revisions_page._click_on_revision_date_for_article(
            article_title=article_details['article_title'], username=username
        )

        self.logger.info("Verifying that the user is redirected to the correct page")
        expect(
            self.page
        ).to_have_url(
            article_url + KBArticleRevision.
            KB_REVISION_PREVIEW + str(self.number_extraction_from_string(second_revision_id))
        )

        self.logger.info("Verifying that the revision id is the correct one")
        check.equal(
            self.sumo_pages.kb_article_preview_revision_page._get_preview_revision_id_text(),
            str(self.number_extraction_from_string(second_revision_id))
        )

        self.logger.info("Navigating back")
        self.navigate_back()

        self.logger.info("Clicking on the revision title")
        self.sumo_pages.recent_revisions_page._click_on_article_title(
            article_title=article_details['article_title'], creator=username
        )

        self.logger.info("Verifying that the user is redirected to the article title")
        expect(
            self.page
        ).to_have_url(article_url)

        self.logger.info("Navigating back")
        self.navigate_back()

        self.logger.info("Verifying that the correct comment is displayed")
        check.equal(
            self.sumo_pages.recent_revisions_page._get_revision_comment(
                article_title=article_details['article_title'], username=username
            ),
            self.kb_article_test_data['changes_description']
        )

        self.logger.info("Clicking on the editor")
        self.sumo_pages.recent_revisions_page._click_article_creator_link(
            article_title=article_details['article_title'], creator=username
        )

        self.logger.info("Verifying that the user was redirected to the correct user page")
        expect(
            self.page
        ).to_have_url(MyProfileMessages.get_my_profile_stage_url(username))

        self.logger.info("Navigating back")
        self.navigate_back()

        self.logger.info("Clicking on show diff option")
        self.sumo_pages.recent_revisions_page._click_on_show_diff_for_article(
            article_title=article_details['article_title'], creator=username
        )

        self.logger.info("Verifying that the diff section is displayed")
        expect(
            self.sumo_pages.recent_revisions_page._get_diff_section_locator()
        ).to_be_visible()

        self.logger.info("Hiding the diff")
        self.sumo_pages.recent_revisions_page._click_on_hide_diff_for_article(
            article_title=article_details['article_title'], creator=username
        )

        self.logger.info("Verifying that the diff section is not displayed")
        expect(
            self.sumo_pages.recent_revisions_page._get_diff_section_locator()
        ).to_be_hidden()

        self.logger.info("Signing in with an admin account")
        self.delete_cookies()
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Navigating back to the article page")
        self.navigate_to_link(article_url)

        self.logger.info("Clicking on the 'Show History' option")
        self.sumo_pages.kb_article_page._click_on_show_history_option()

        self.logger.info("Clicking on the 'Delete article' button")
        self.sumo_pages.kb_article_show_history_page._click_on_delete_this_document_button()

        self.logger.info("Clicking on the 'Delete' button")
        self.sumo_pages.kb_article_show_history_page._click_on_confirmation_delete_button()

    # C2266240
    @pytest.mark.recentRevisionsDashboard
    def test_recent_revisions_dashboard_title_and_username_update(self):
        self.logger.info("Signing back in with the admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        first_username = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        self.logger.info("Create a new simple article")
        article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        self.sumo_pages.kb_article_page._click_on_article_option()
        article_url = self.get_page_url()

        self.logger.info("Clicking on the 'Show History' option")
        self.sumo_pages.kb_article_page._click_on_show_history_option()

        revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()

        self.logger.info("Clicking on the 'Review' option")
        self.sumo_pages.kb_article_show_history_page._click_on_review_revision(
            revision_id
        )

        self.logger.info("Click on 'Approve Revision' button")
        self.sumo_pages.kb_article_review_revision_page._click_on_approve_revision_button()

        self.logger.info("Clicking on the 'Accept' button")
        self.sumo_pages.kb_article_review_revision_page._click_accept_revision_accept_button()

        self.logger.info("Clicking on the 'Edit Article Metadata' option")
        self.sumo_pages.kb_article_page._click_on_edit_article_metadata()

        self.sumo_pages.kb_article_edit_article_metadata_page._add_text_to_title_field(
            self.kb_article_test_data['updated_kb_article_title'] + article_details
            ['article_title']
        )

        self.logger.info("Clicking on the 'Save' button")
        self.sumo_pages.kb_article_edit_article_metadata_page._click_on_save_changes_button()

        self.logger.info("Editing the username")
        self.sumo_pages.top_navbar._click_on_edit_profile_option()

        new_username = self.profile_edit_test_data['valid_user_edit']['username']
        self.sumo_pages.edit_my_profile_page._send_text_to_username_field(
            new_username
        )

        self.logger.info("Clicking on the 'Update My Profile' button")
        self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()

        self.logger.info("Navigating to the recent revisions dashboard")
        self.sumo_pages.top_navbar._click_on_recent_revisions_option()

        expect(
            self.page
        ).to_have_url(self.general_test_data['dashboard_links']['recent_revisions'])

        expect(
            self.sumo_pages.recent_revisions_page._get_revision_and_username_locator(
                self.kb_article_test_data['updated_kb_article_title'] + article_details
                ['article_title'],
                new_username
            )
        ).to_be_visible()

        self.logger.info("Editing the username back")
        self.sumo_pages.top_navbar._click_on_edit_profile_option()

        self.sumo_pages.edit_my_profile_page._send_text_to_username_field(
            first_username
        )

        self.logger.info("Clicking on the 'Update My Profile' button")
        self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()

        self.logger.info("Deleting the article")
        self.navigate_to_link(article_url)

        self.logger.info("Clicking on the 'Show History' option")
        self.sumo_pages.kb_article_page._click_on_show_history_option()

        self.logger.info("Clicking on the 'Delete article' button")
        self.sumo_pages.kb_article_show_history_page._click_on_delete_this_document_button()

        self.logger.info("Clicking on the 'Delete' button")
        self.sumo_pages.kb_article_show_history_page._click_on_confirmation_delete_button()

    # C2266241
    @pytest.mark.recentRevisionsDashboard
    def test_recent_revisions_dashboard_filters(self):
        start_date = "04052023"
        end_date = "05012023"
        self.logger.info("Navigating to the 'Recent Revisions' dashboard")
        self.navigate_to_link(
            self.general_test_data['dashboard_links']['recent_revisions']
        )

        self.logger.info("Selecting the ro locale from the locale filter")
        self.sumo_pages.recent_revisions_page._select_locale_option("ro")

        self.wait_for_given_timeout(3000)

        self.logger.info("Verifying that all the displayed revisions are for the 'ro' locale")
        for tag in self.sumo_pages.recent_revisions_page._get_list_of_all_locale_tage():
            check.equal(
                tag,
                "ro"
            )

        self.logger.info("Select the US filter")
        self.sumo_pages.recent_revisions_page._select_locale_option("en-US")

        self.wait_for_given_timeout(3000)

        self.logger.info("Typing a username inside the 'Users' filter")
        username = self.username_extraction_from_email(
            self.user_secrets_accounts['TEST_ACCOUNT_12']
        )

        self.sumo_pages.recent_revisions_page._fill_in_users_field(username)

        self.wait_for_given_timeout(2000)

        self.logger.info("Verifying that all the displayed revisions are for the posted user")
        for user in self.sumo_pages.recent_revisions_page._get_list_of_all_editors():
            check.equal(
                user,
                username
            )

        self.sumo_pages.recent_revisions_page._clearing_the_user_field()
        self.wait_for_given_timeout(2000)

        self.logger.info("Adding date inside the start field")
        self.sumo_pages.recent_revisions_page._add_start_date("04052023")

        self.logger.info("Adding date inside the end field")
        self.sumo_pages.recent_revisions_page._add_end_date("05012023")

        self.wait_for_given_timeout(2000)

        self.logger.info("Verifying that the displayed revision dates are between (inclusive) "
                         "the set start and end date filters")
        extracted_date = []
        date_filters = [int(start_date), int(end_date)]
        for date in self.sumo_pages.recent_revisions_page._get_all_revision_dates():
            extracted_date.append(self.extract_date_to_digit_format(
                self.extract_month_day_year_from_string(date)
            ))

        for date in extracted_date:
            check.between_equal(
                date,
                date_filters[0],
                date_filters[1]
            )
