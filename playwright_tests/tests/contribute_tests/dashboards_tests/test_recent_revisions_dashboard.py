import allure
import pytest
from pytest_check import check
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
        with allure.step("Signing in with a non-admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_12']
            ))

        username = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        with allure.step("Creating a new kb article"):
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        article_url = self.get_page_url()

        with allure.step("Navigating to the recent revisions dashboard and verifying that the "
                         "posted article is displayed for admin accounts"):
            self.navigate_to_link(
                self.general_test_data['dashboard_links']['recent_revisions']
            )
            expect(
                self.sumo_pages.recent_revisions_page._get_recent_revision_based_on_article(
                    article_details['article_title']
                )
            ).to_be_visible()

        with allure.step("Deleting the user session and verifying that the revision is not "
                         "displayed for signed out users"):
            self.delete_cookies()
            expect(
                self.sumo_pages.recent_revisions_page._get_recent_revision_based_on_article(
                    article_details['article_title']
                )
            ).to_be_hidden()

        with allure.step("Typing the article creator username inside the 'Users' field and "
                         "verifying that the article is not displayed"):
            self.sumo_pages.recent_revisions_page._fill_in_users_field(username)
            self.wait_for_given_timeout(2000)
            expect(
                self.sumo_pages.recent_revisions_page._get_recent_revision_based_on_article(
                    article_details['article_title']
                )
            ).to_be_hidden()

        with allure.step("Clearing the user search field and signing in with a different "
                         "non-admin account"):
            self.sumo_pages.recent_revisions_page._clearing_the_user_field()
            self.username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_6"]
            )

        with allure.step("Verifying that the revision is not displayed for non-admin accounts"):
            expect(
                self.sumo_pages.recent_revisions_page._get_recent_revision_based_on_article(
                    article_details['article_title']
                )
            ).to_be_hidden()

        with allure.step("Typing the article creator username inside the 'Users' field and "
                         "verifying that the article is not displayed"):
            self.sumo_pages.recent_revisions_page._fill_in_users_field(username)
            self.wait_for_given_timeout(2000)
            expect(
                self.sumo_pages.recent_revisions_page._get_recent_revision_based_on_article(
                    article_details['article_title']
                )
            ).to_be_hidden()

        with allure.step("Clearing the user search field and signing in back with the admin "
                         "account"):
            self.sumo_pages.recent_revisions_page._clearing_the_user_field()
            self.logger.info("Signing back in with the admin account")
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Navigating to the article page and deleting it"):
            self.navigate_to_link(article_url)
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

        with allure.step("Navigating back to the recent revisions page and verifying that the "
                         "article is no longer displayed"):
            self.navigate_to_link(
                self.general_test_data['dashboard_links']['recent_revisions']
            )
            expect(
                self.sumo_pages.recent_revisions_page._get_recent_revision_based_on_article(
                    article_details['article_title']
                )
            ).to_be_hidden()

    # C2266240
    @pytest.mark.recentRevisionsDashboard
    def test_second_revisions_availability(self):
        with allure.step("Signing back in with the admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Creating a new kb article"):
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                approve_first_revision=True
            )

        article_url = self.get_page_url()

        with allure.step("Signing in with a non-admin account"):
            self.logger.info("Signing in with a non admin account")
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_13"]
            ))

        username = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        with allure.step("Creating a new revision for the article"):
            second_revision = self.sumo_pages.submit_kb_article_flow.submit_new_kb_revision()

        with allure.step("Navigating to the Recent Revisions dashboard and verifying that own "
                         "revision is visible"):
            self.navigate_to_link(
                self.general_test_data['dashboard_links']['recent_revisions']
            )
            expect(
                self.sumo_pages.recent_revisions_page.
                _get_recent_revision_based_on_article_title_and_user(
                    article_details['article_title'], username
                )
            ).to_be_visible()

        with allure.step("Deleting user session and verifying that the recent revision is "
                         "displayed"):
            self.delete_cookies()
            expect(
                self.sumo_pages.recent_revisions_page.
                _get_recent_revision_based_on_article_title_and_user(
                    article_details['article_title'], username
                )
            ).to_be_visible()

        with allure.step("Signing in with a different non-admin user and verifying that the "
                         "revision is displayed"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_6"]
            ))
            expect(
                self.sumo_pages.recent_revisions_page.
                _get_recent_revision_based_on_article_title_and_user(
                    article_details['article_title'], username
                )
            ).to_be_visible()

        with allure.step("Signing in with an admin account and verifying that the revision is "
                         "displayed"):
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

        with allure.step("Navigating to the article and approving the revision"):
            self.navigate_to_link(article_url)
            self.sumo_pages.submit_kb_article_flow.approve_kb_revision(
                second_revision['revision_id']
            )
            self.wait_for_given_timeout(1000)

        with allure.step("Signing out and verifying that the revision is displayed inside the "
                         "Recent Revisions dashboard"):
            self.delete_cookies()
            self.navigate_to_link(self.general_test_data['dashboard_links']['recent_revisions'])
            expect(
                self.sumo_pages.recent_revisions_page.
                _get_recent_revision_based_on_article_title_and_user(
                    article_details['article_title'], username
                )
            ).to_be_visible()

        with allure.step("Signing in with a different non-admin user account and verifying that "
                         "the revision is visible"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_6"]
            ))
            expect(
                self.sumo_pages.recent_revisions_page.
                _get_recent_revision_based_on_article_title_and_user(
                    article_details['article_title'], username
                )
            ).to_be_visible()

        with allure.step("Signing back in with an admin account an deleting the article"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))
            self.navigate_to_link(article_url)
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

        with allure.step("Navigating back to the recent revision dashboard, signing out and "
                         "verifying that the revision is no longer displayed for the deleted kb "
                         "article"):
            self.navigate_to_link(
                self.general_test_data['dashboard_links']['recent_revisions']
            )
            self.wait_for_given_timeout(1000)
            self.delete_cookies()
            expect(
                self.sumo_pages.recent_revisions_page.
                _get_recent_revision_based_on_article_title_and_user(
                    article_details['article_title'], username
                )
            ).to_be_hidden()

        with allure.step("Signing in with a different non-admin account and verifying that the "
                         "revision is no longer displayed for the deleted kb article"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_6"]
            ))
            expect(
                self.sumo_pages.recent_revisions_page.
                _get_recent_revision_based_on_article_title_and_user(
                    article_details['article_title'], username
                )
            ).to_be_hidden()

    # C2266240
    @pytest.mark.recentRevisionsDashboard
    def test_recent_revisions_dashboard_links(self):
        with allure.step("Signing in with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))
        first_username = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        with allure.step("Creating a new kb article"):
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                approve_first_revision=True
            )

        self.sumo_pages.kb_article_page._click_on_article_option()
        article_url = self.get_page_url()

        with allure.step("Navigating to the recent revisions dashboard and verifying that the "
                         "'Show Diff' option is not available for first revisions"):
            self.sumo_pages.top_navbar._click_on_recent_revisions_option()
            self.wait_for_given_timeout(3000)
            expect(
                self.sumo_pages.recent_revisions_page._get_show_diff_article_locator(
                    article_title=article_details['article_title'], creator=first_username
                )
            ).to_be_hidden()

        with allure.step("Navigating to the article page, signing in with a non-admin user and "
                         "creating a new revision for the article"):
            self.navigate_to_link(article_url)
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_13"]
            ))
            username = self.sumo_pages.top_navbar._get_text_of_logged_in_username()
            second_revision = self.sumo_pages.submit_kb_article_flow.submit_new_kb_revision()

        with allure.step("Navigating to the recent revisions dashboard, signing out and clicking "
                         "on the revision date link and verifying that the user is redirected to"
                         "the correct page"):
            self.sumo_pages.top_navbar._click_on_recent_revisions_option()
            self.wait_for_given_timeout(3000)
            self.delete_cookies()
            self.sumo_pages.recent_revisions_page._click_on_revision_date_for_article(
                article_title=article_details['article_title'], username=username
            )
            expect(
                self.page
            ).to_have_url(
                article_url + KBArticleRevision.
                KB_REVISION_PREVIEW + str(self.number_extraction_from_string(
                    second_revision['revision_id']
                ))
            )

        with check, allure.step("Verifying that the revision id is the correct one"):
            assert self.sumo_pages.kb_article_preview_revision_page._get_preview_revision_id_text(
            ) == str(self.number_extraction_from_string(second_revision['revision_id']))

        with allure.step("Navigating back, clicking on the revision title and verifying that the "
                         "user is redirected to the article page"):
            self.navigate_back()
            self.sumo_pages.recent_revisions_page._click_on_article_title(
                article_title=article_details['article_title'], creator=username
            )
            expect(
                self.page
            ).to_have_url(article_url)

        with check, allure.step("Navigating back and verifying that the correct comment is "
                                "displayed"):
            self.navigate_back()
            assert self.sumo_pages.recent_revisions_page._get_revision_comment(
                article_title=article_details['article_title'], username=username
            ) == self.kb_article_test_data['changes_description']

        with allure.step("Clicking on the editor and verifying that the user was redirected to "
                         "the correct page"):
            self.sumo_pages.recent_revisions_page._click_article_creator_link(
                article_title=article_details['article_title'], creator=username
            )
            expect(
                self.page
            ).to_have_url(MyProfileMessages.get_my_profile_stage_url(username))

        with allure.step("Navigating back, clicking on the show diff option and verifying that"
                         "diff section is displayed"):
            self.navigate_back()
            self.sumo_pages.recent_revisions_page._click_on_show_diff_for_article(
                article_title=article_details['article_title'], creator=username
            )
            expect(
                self.sumo_pages.recent_revisions_page._get_diff_section_locator()
            ).to_be_visible()

        with allure.step("Hiding the diff and verifying that the diff section is not displayed"):
            self.sumo_pages.recent_revisions_page._click_on_hide_diff_for_article(
                article_title=article_details['article_title'], creator=username
            )
            expect(
                self.sumo_pages.recent_revisions_page._get_diff_section_locator()
            ).to_be_hidden()

        with allure.step("Signing in with an admin account and deleting the article"):
            self.logger.info("Signing in with an admin account")
            self.delete_cookies()
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))
            self.logger.info("Navigating back to the article page")
            self.navigate_to_link(article_url)
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2266240, C2243449
    @pytest.mark.recentRevisionsDashboard
    def test_recent_revisions_dashboard_title_and_username_update(self):
        with allure.step("Signing back in with the admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))
        first_username = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        with allure.step("Creating a new kb article"):
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                approve_first_revision=True
            )

        self.sumo_pages.kb_article_page._click_on_article_option()
        article_url = self.get_page_url()

        with allure.step("Changing the article title via the 'Edit Article Metadata' page"):
            self.sumo_pages.edit_article_metadata_flow.edit_article_metadata(
                title=self.kb_article_test_data['updated_kb_article_title'] + article_details
                ['article_title']
            )

        with allure.step("Editing the username"):
            self.sumo_pages.top_navbar._click_on_edit_profile_option()
            new_username = self.profile_edit_test_data['valid_user_edit']['username']
            self.sumo_pages.edit_my_profile_page._send_text_to_username_field(
                new_username
            )
            self.logger.info("Clicking on the 'Update My Profile' button")
            self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()

        with allure.step("Navigating to the recent revisions dashboard and verifying that the "
                         "correct new username and article title arte displayed"):
            self.sumo_pages.top_navbar._click_on_recent_revisions_option()
            self.wait_for_given_timeout(3000)
            expect(
                self.sumo_pages.recent_revisions_page._get_revision_and_username_locator(
                    article_title=self.kb_article_test_data
                    ['updated_kb_article_title'] + article_details['article_title'],
                    username=new_username
                )
            ).to_be_visible()

        with allure.step("Changing the username back"):
            self.sumo_pages.top_navbar._click_on_edit_profile_option()
            self.sumo_pages.edit_my_profile_page._send_text_to_username_field(
                first_username
            )
            self.logger.info("Clicking on the 'Update My Profile' button")
            self.sumo_pages.edit_my_profile_page._click_update_my_profile_button()

        with allure.step("Deleting the article"):
            self.navigate_to_link(article_url)
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2266241
    @pytest.mark.recentRevisionsDashboard
    def test_recent_revisions_dashboard_filters(self):
        start_date = "04052023"
        end_date = "05012023"
        with allure.step("Navigating to the 'Recent Revisions' dashboard"):
            self.navigate_to_link(
                self.general_test_data['dashboard_links']['recent_revisions']
            )

        with check, allure.step("Selecting the ro locale from the locale filter and verifying "
                                "that all the displayed revisions are for the 'ro' locale"):
            self.sumo_pages.recent_revisions_page._select_locale_option("ro")
            self.wait_for_given_timeout(3000)
            for tag in self.sumo_pages.recent_revisions_page._get_list_of_all_locale_tage():
                assert tag == "ro"

        with check, allure.step("Selecting the US filter, typing a username inside the 'Users' "
                                "filter and verifying that all the displayed revisions are for "
                                "the posted user"):
            self.sumo_pages.recent_revisions_page._select_locale_option("en-US")
            self.wait_for_given_timeout(3000)
            username = self.username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_12']
            )
            self.sumo_pages.recent_revisions_page._fill_in_users_field(username)
            self.wait_for_given_timeout(2000)
            for user in self.sumo_pages.recent_revisions_page._get_list_of_all_editors():
                assert user == username

        with allure.step("Clearing the user filter, adding data inside the start and end fields"):
            self.sumo_pages.recent_revisions_page._clearing_the_user_field()
            self.wait_for_given_timeout(2000)

            self.logger.info("Adding date inside the start field")
            self.sumo_pages.recent_revisions_page._add_start_date("04052023")

            self.logger.info("Adding date inside the end field")
            self.sumo_pages.recent_revisions_page._add_end_date("05012023")
            self.wait_for_given_timeout(2000)

        with check, allure.step("Verifying that the displayed revision dates are between ("
                                "inclusive) the set start and end date filters"):
            extracted_date = []
            date_filters = [int(start_date), int(end_date)]
            for date in self.sumo_pages.recent_revisions_page._get_all_revision_dates():
                extracted_date.append(self.extract_date_to_digit_format(
                    self.extract_month_day_year_from_string(date)
                ))

            for date in extracted_date:
                assert date_filters[0] <= date <= date_filters[1]
