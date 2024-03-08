import allure
import pytest
from pytest_check import check
from playwright.sync_api import expect
from playwright_tests.core.testutilities import TestUtilities
from playwright_tests.messages.contribute_messages.con_tools.kb_dashboard_messages import (
    KBDashboardPageMessages)


class TestKBDashboard(TestUtilities, KBDashboardPageMessages):

    # C891357
    @pytest.mark.kbDashboard
    def test_unreviewed_articles_visibility_in_kb_dashboard(self):
        with allure.step("Signing in with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Create a new simple article"):
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()
            self.sumo_pages.kb_article_page._click_on_article_option()
            article_url = self.get_page_url()

        with allure.step("Navigating to the kb dashboards and clicking on the 'Complete "
                         "overview' option"):
            self.sumo_pages.top_navbar._click_on_dashboards_option()
            self.sumo_pages.kb_dashboard_page._click_on_the_complete_overview_link()

        with allure.step("Verifying that we are redirected to the correct page"):
            expect(
                self.page
            ).to_have_url(super().general_test_data['dashboard_links']['kb_overview'])

        with check, allure.step("Verifying that the correct live status is displayed"):
            assert self.sumo_pages.kb_dashboard_page._get_a_particular_article_status(
                article_details['article_title']
            ).strip() == self.get_kb_not_live_status(
                revision_note=article_details['article_review_description']
            )

        with allure.step("Signing out and verifying that the article is not displayed since it "
                         "is not live yet"):
            self.delete_cookies()
            expect(
                self.sumo_pages.kb_dashboard_page._get_a_particular_article_title_locator(
                    article_details['article_title']
                )
            ).to_be_hidden()

        with allure.step("Navigating to the homepage and performing the sign in step since the "
                         "kb overview takes quite a bit to refresh/load"):
            self.sumo_pages.top_navbar._click_on_sumo_nav_logo()
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_13"]
            ))

        with allure.step("Navigating to the kb overview verifying that the article is not "
                         "displayed since it is not live yet"):
            self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])
            expect(
                self.sumo_pages.kb_dashboard_page._get_a_particular_article_title_locator(
                    article_details['article_title']
                )
            ).to_be_hidden()

        with allure.step("Signing in with an admin account"):
            self.sumo_pages.top_navbar._click_on_sumo_nav_logo()
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Navigating to the kb overview page and clicking on the article title"):
            self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])
            self.sumo_pages.kb_dashboard_page._click_on_article_title(
                article_details['article_title']
            )

        with allure.step("Verifying that the user is redirected to the correct kb page"):
            expect(
                self.page
            ).to_have_url(article_url)

        with allure.step("Approving the article revision"):
            self.sumo_pages.kb_article_page._click_on_show_history_option()
            revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()
            self.sumo_pages.kb_article_revision_flow.approve_kb_revision(revision_id)

        with check, allure.step("Navigating back to the kb overview page and verifying that the "
                                "correct live status is displayed"):
            self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])
            assert self.sumo_pages.kb_dashboard_page._get_a_particular_article_status(
                article_details['article_title']
            ).strip() == self.KB_LIVE_STATUS

        with allure.step("Signing out and verifying that the article is visible"):
            self.delete_cookies()
            expect(
                self.sumo_pages.kb_dashboard_page._get_a_particular_article_title_locator(
                    article_details['article_title']
                )
            ).to_be_visible()

        with allure.step("Signing in with a non-admin user"):
            self.sumo_pages.top_navbar._click_on_sumo_nav_logo()
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_13"]
            ))

        with allure.step("Navigating to the kb overview and verifying that the article is "
                         "visible"):
            self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])
            expect(
                self.sumo_pages.kb_dashboard_page._get_a_particular_article_title_locator(
                    article_details['article_title']
                )
            ).to_be_visible()

        with allure.step("Signing back with an admin account and deleting the article"):
            self.sumo_pages.top_navbar._click_on_sumo_nav_logo()
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))
            self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])
            self.sumo_pages.kb_dashboard_page._click_on_article_title(
                article_details['article_title']
            )
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2266376
    @pytest.mark.kbDashboard
    def test_kb_dashboard_articles_status(self):
        with allure.step("Signing in with the admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Creating a new simple article"):
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        article_url = self.get_page_url()

        revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()

        with allure.step("Approving the first article revision"):
            self.sumo_pages.kb_article_revision_flow.approve_kb_revision(revision_id)

        with allure.step("Creating a anew revision for the document"):
            second_revision = self.sumo_pages.kb_article_revision_flow.submit_new_kb_revision()

        with check, allure.step("Navigating to the kb overview dashboard and verifying that the "
                                "correct status is displayed"):
            self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])
            assert self.sumo_pages.kb_dashboard_page._get_a_particular_article_status(
                article_details['article_title']
            ).strip() == self.get_kb_not_live_status(
                revision_note=second_revision['changes_description']
            )

        with allure.step("Navigating back to the article history and deleting the revision"):
            self.navigate_to_link(article_url)
            self.sumo_pages.kb_article_show_history_page._click_on_delete_revision_button(
                second_revision['revision_id']
            )
            self.sumo_pages.kb_article_show_history_page._click_on_confirmation_delete_button()

        with check, allure.step("Navigating back to the kb dashboard and verifying that the live "
                                "status is displayed"):
            self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])
            assert self.sumo_pages.kb_dashboard_page._get_a_particular_article_status(
                article_details['article_title']
            ).strip() == self.KB_LIVE_STATUS

        with allure.step("Clicking on the article title and deleting it"):
            self.sumo_pages.kb_dashboard_page._click_on_article_title(
                article_details['article_title']
            )
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    @pytest.mark.kbDashboard
    def test_kb_dashboard_revision_deferred_status(self):
        with allure.step("Signing in with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Creating a new simple article"):
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        article_url = self.get_page_url()

        revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()

        with allure.step("Approving the first article revision"):
            self.sumo_pages.kb_article_revision_flow.approve_kb_revision(revision_id)

        with allure.step("Creating a new revision for the document"):
            second_revision = self.sumo_pages.kb_article_revision_flow.submit_new_kb_revision()

        with check, allure.step("Navigating to the kb overview page and verifying that the "
                                "correct kb status is displayed"):
            self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])
            assert self.sumo_pages.kb_dashboard_page._get_a_particular_article_status(
                article_details['article_title']
            ) == self.get_kb_not_live_status(second_revision['changes_description'])

        with allure.step("Navigating back to the article history page and deferring the revision"):
            self.navigate_to_link(article_url)
            self.sumo_pages.kb_article_show_history_page._click_on_review_revision(
                second_revision['revision_id']
            )
            self.sumo_pages.kb_article_review_revision_page._click_on_defer_revision_button()
            self.sumo_pages.kb_article_review_revision_page._click_on_defer_confirm_button()

        with check, allure.step("Navigating back to the kb overview page and verifying that the "
                                "correct status is displayed"):
            self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])
            assert self.sumo_pages.kb_dashboard_page._get_a_particular_article_status(
                article_details['article_title']
            ) == self.KB_LIVE_STATUS

        with allure.step("Deleting the article"):
            self.navigate_to_link(article_url)
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    @pytest.mark.kbDashboard
    def test_kb_dashboard_needs_update_when_reviewing_a_revision(self):
        with allure.step("Signing in with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Creating a new simple article"):
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        article_url = self.get_page_url()

        revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()

        with allure.step("Approving the first article revision"):
            self.sumo_pages.kb_article_revision_flow.approve_kb_revision(revision_id)

        with allure.step("Creating an new article revision for the document"):
            second_revision = self.sumo_pages.kb_article_revision_flow.submit_new_kb_revision(
            )
            self.sumo_pages.kb_article_revision_flow.approve_kb_revision(
                second_revision['revision_id'], revision_needs_change=True
            )

        with check, allure.step("Navigating to the kb dashboard overview page and verifying that "
                                "the correct article status is displayed"):
            self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])
            assert self.sumo_pages.kb_dashboard_page._get_needs_update_status(
                article_details['article_title']
            ).strip() == super().kb_revision_test_data['needs_change_message']

        with allure.step("Deleting the article"):
            self.navigate_to_link(article_url)
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2266377
    @pytest.mark.kbDashboard
    def test_kb_dashboard_needs_update_edit_metadata(self):
        with allure.step("Signing in with the admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Create a new simple article"):
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        article_url = self.get_page_url()

        revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()

        with allure.step("Approving the first article revision"):
            self.sumo_pages.kb_article_revision_flow.approve_kb_revision(revision_id)

        with allure.step("Clicking on the 'Edit Article Metadata' option and enabling the 'Needs "
                         "change with comment' option"):
            self.sumo_pages.kb_article_page._click_on_edit_article_metadata()
            self.sumo_pages.edit_article_metadata_flow.edit_article_metadata(
                needs_change=True, needs_change_comment=True
            )

        with check, allure.step("Navigating to the kb dashboard and verifying that the correct "
                                "needs change status is displayed"):
            self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])
            assert self.sumo_pages.kb_dashboard_page._get_needs_update_status(
                article_details['article_title']
            ).strip() == super().kb_revision_test_data['needs_change_message']

        with allure.step("Navigating back to the article's 'Edit Article Metadata' page and "
                         "removing the comment from the needs change textarea"):
            self.navigate_to_link(article_url)
            self.sumo_pages.kb_article_page._click_on_edit_article_metadata()
            self.sumo_pages.edit_article_metadata_flow.edit_article_metadata(needs_change=True)

        with allure.step("Navigating to the complete dashboard list and verifying that the "
                         "correct needs change status is displayed"):
            self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])
            assert self.sumo_pages.kb_dashboard_page._get_needs_update_status(
                article_details['article_title']
            ).strip() == KBDashboardPageMessages.GENERAL_POSITIVE_STATUS

        with allure.step("Navigating back to the article's 'Edit Article Metadata' page and "
                         "removing the needs change updates"):
            self.navigate_to_link(article_url)
            self.sumo_pages.kb_article_page._click_on_edit_article_metadata()
            self.sumo_pages.edit_article_metadata_flow.edit_article_metadata()

        with check, allure.step("Navigating to the kb overview page and verifying that the "
                                "correct needs change status is displayed"):
            self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])
            assert self.sumo_pages.kb_dashboard_page._is_needs_change_empty(
                article_details['article_title']
            )

        with allure.step("Deleting the article"):
            self.navigate_to_link(article_url)
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2266378
    @pytest.mark.kbDashboard
    def test_ready_for_l10n_kb_dashboard_revision_approval(self):
        with allure.step("Signing in with the admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Create a new simple article"):
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        article_url = self.get_page_url()

        revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()

        with allure.step("Approving the first revision and marking it as ready for l10n"):
            self.sumo_pages.kb_article_revision_flow.approve_kb_revision(
                revision_id=revision_id, ready_for_l10n=True)

        with check, allure.step("Navigating to the kb dashboard overview page and verifying that "
                                "the correct l10n status is displayed"):
            self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])
            assert self.sumo_pages.kb_dashboard_page._get_ready_for_l10n_status(
                article_details['article_title']
            ) == KBDashboardPageMessages.GENERAL_POSITIVE_STATUS

        with allure.step("Deleting the article"):
            self.navigate_to_link(article_url)
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2266378
    @pytest.mark.kbDashboard
    def test_ready_for_l10n_kb_dashboard_revision_l10n_status(self):
        with allure.step("Signing in with the admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Creating a new kb article"):
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        article_url = self.get_page_url()

        revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()

        with allure.step("Approving the first kb revision"):
            self.sumo_pages.kb_article_revision_flow.approve_kb_revision(revision_id=revision_id)

        with check, allure.step("Navigating to the kb dashboard overview page and verifying that "
                                "the correct l10n status is displayed"):
            self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])
            assert self.sumo_pages.kb_dashboard_page._get_ready_for_l10n_status(
                article_details['article_title']
            ) == KBDashboardPageMessages.GENERAL_NEGATIVE_STATUS

        with allure.step("Navigating back to the article page and marking the revision as ready "
                         "for l10n"):
            self.navigate_to_link(article_url)
            self.sumo_pages.kb_article_show_history_page._click_on_ready_for_l10n_option(
                revision_id
            )
            self.sumo_pages.kb_article_show_history_page._click_on_submit_l10n_readiness_button()

        with allure.step("Navigating to the kb dashboard overview page and verifying that the "
                         "correct l10n status is displayed"):
            self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])
            assert self.sumo_pages.kb_dashboard_page._get_ready_for_l10n_status(
                article_details['article_title']
            ) == KBDashboardPageMessages.GENERAL_POSITIVE_STATUS

        with allure.step("Navigating to the article and deleting it"):
            self.navigate_to_link(article_url)
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2266378
    @pytest.mark.kbDashboard
    def test_article_translation_not_allowed_kb_dashboard(self):
        with allure.step("Signing in with the admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Creating a new simple article & unchecking the allow translations"):
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                allow_translations=False
            )

        article_url = self.get_page_url()

        revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()

        with allure.step("Approving the first revision"):
            self.sumo_pages.kb_article_revision_flow.approve_kb_revision(revision_id=revision_id)

        with allure.step("Navigating to the kb dashboard overview page and verifying that the "
                         "correct l10n status is displayed"):
            self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])
            assert self.sumo_pages.kb_dashboard_page._get_ready_for_l10n_status(
                article_details['article_title']
            ) == KBDashboardPageMessages.GENERAL_NEGATIVE_STATUS

        with allure.step("Deleting the article"):
            self.navigate_to_link(article_url)
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2266379, C2266380
    @pytest.mark.kbDashboard
    def test_article_stale_kb_dashboard(self):
        with allure.step("Signing in with the admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Create a new simple article & adding an old expiry date"):
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                expiry_date=self.kb_article_test_data['old_expiry_date']
            )

        article_url = self.get_page_url()

        revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()

        with allure.step("Approving the first kb article revision"):
            self.sumo_pages.kb_article_revision_flow.approve_kb_revision(revision_id)

        with check, allure.step("Navigating to the kb dashboard overview page and verifying that "
                                "the correct stale status and date is displayed"):
            self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])
            assert self.sumo_pages.kb_dashboard_page._get_stale_status(
                article_details['article_title']
            ) == KBDashboardPageMessages.GENERAL_POSITIVE_STATUS
            assert self.sumo_pages.kb_dashboard_page._get_existing_expiry_date(
                article_details['article_title']
            ) == self.convert_string_to_datetime(
                self.kb_article_test_data['old_expiry_date']
            )

        with allure.step("Navigating back to the article and creating a new revision with a "
                         "non-stale expiry date"):
            self.navigate_to_link(article_url)
            second_revision = self.sumo_pages.kb_article_revision_flow.submit_new_kb_revision(
                expiry_date=self.kb_article_test_data['expiry_date']
            )

        with allure.step("Approving the revision"):
            self.sumo_pages.kb_article_revision_flow.approve_kb_revision(
                second_revision['revision_id']
            )

        with check, allure.step("Navigating to the kb dashboard and verifying that the correct "
                                "stale status and date is displayed"):
            self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])
            assert self.sumo_pages.kb_dashboard_page._is_stale_status_empty(
                article_details['article_title']
            )
            assert self.sumo_pages.kb_dashboard_page._get_existing_expiry_date(
                article_details['article_title']
            ) == self.convert_string_to_datetime(
                self.kb_article_test_data['expiry_date']
            )

        with allure.step("Deleting the article"):
            self.navigate_to_link(article_url)
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    @pytest.mark.kbDashboard
    def test_article_title_update(self):
        with allure.step("Signing in with the admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Creating a new kb article"):
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        article_url = self.get_page_url()

        revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()

        with allure.step("Approving the first kb article revision"):
            self.sumo_pages.kb_article_revision_flow.approve_kb_revision(revision_id=revision_id)

        with allure.step("Navigating to the kb dashboard overview page and verifying that the "
                         "correct title is displayed"):
            self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])
            expect(
                self.sumo_pages.kb_dashboard_page._get_a_particular_article_title_locator(
                    article_details['article_title']
                )
            ).to_be_visible()

        with allure.step("Navigating to the article's 'Edit Metadata page' page and changing the "
                         "title"):
            self.navigate_to_link(article_url)
            self.sumo_pages.kb_article_page._click_on_edit_article_metadata()
            new_article_title = "Updated " + article_details['article_title']
            self.sumo_pages.edit_article_metadata_flow.edit_article_metadata(
                title=new_article_title
            )

        with allure.step("Navigating back to the kb dashboard page and verifying that the "
                         "correct title is displayed"):
            self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])
            expect(
                self.sumo_pages.kb_dashboard_page._get_a_particular_article_title_locator(
                    new_article_title
                )
            ).to_be_visible()

        with allure.step("Deleting the kb article"):
            self.navigate_to_link(article_url)
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()
