import pytest
import pytest_check as check
from playwright.sync_api import expect
from playwright_tests.core.testutilities import TestUtilities
from playwright_tests.messages.contribute_messages.con_tools.kb_dashboard_messages import (
    KBDashboardPageMessages)


class TestKBDashboard(TestUtilities, KBDashboardPageMessages):

    # C891357
    @pytest.mark.kbDashboard
    def test_unreviewed_articles_visibility_in_kb_dashboard(self):
        self.logger.info("Signing in with the admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Create a new simple article")
        article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        self.sumo_pages.kb_article_page._click_on_article_option()
        article_url = self.get_page_url()

        self.logger.info("Navigating to the kb dashboards")
        self.sumo_pages.top_navbar._click_on_dashboards_option()

        self.logger.info("Clicking on the 'Complete overview' option")
        self.sumo_pages.kb_dashboard_page._click_on_the_complete_overview_link()

        self.logger.info("Verifying that we are redirected to the correct page")
        expect(
            self.page
        ).to_have_url(super().general_test_data['dashboard_links']['kb_overview'])

        self.logger.info("Verifying that the correct live status is displayed")
        check.equal(
            self.sumo_pages.kb_dashboard_page._get_a_particular_article_status(
                article_details['article_title']
            ).strip(),
            self.get_kb_not_live_status(
                revision_note=article_details['article_review_description']
            )
        )

        self.logger.info("Signing out and verifying that the article is not displayed since it "
                         "is not live yet")
        self.delete_cookies()
        expect(
            self.sumo_pages.kb_dashboard_page._get_a_particular_article_title_locator(
                article_details['article_title']
            )
        ).to_be_hidden()

        self.logger.info("Navigating to the homepage and performing the sign in step since the "
                         "kb overview takes quite a bit to refresh/load")
        self.sumo_pages.top_navbar._click_on_sumo_nav_logo()

        self.logger.info("Signing in with a non-admin account and verifying that the article is "
                         "not displayed since it is not live yet")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_13"]
        ))

        self.logger.info("Navigating to the kb overview")
        self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])
        expect(
            self.sumo_pages.kb_dashboard_page._get_a_particular_article_title_locator(
                article_details['article_title']
            )
        ).to_be_hidden()

        self.sumo_pages.top_navbar._click_on_sumo_nav_logo()
        self.logger.info("Signing back in with the admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Navigating to the kb overview")
        self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])

        self.logger.info("Clicking on the article title")
        self.sumo_pages.kb_dashboard_page._click_on_article_title(
            article_details['article_title']
        )

        self.logger.info("Verifying that the user is redirected to the correct kb page")
        expect(
            self.page
        ).to_have_url(article_url)

        self.logger.info("Approving the revision")
        self.sumo_pages.kb_article_page._click_on_show_history_option()
        revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()

        self.logger.info("Approving the revision")
        self.sumo_pages.kb_article_revision_flow.approve_kb_revision(revision_id)

        self.logger.info("Navigating to the kb overview")
        self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])

        self.logger.info("Verifying that the correct status is displayed")

        self.logger.info("Verifying that the correct live status is displayed")
        check.equal(
            self.sumo_pages.kb_dashboard_page._get_a_particular_article_status(
                article_details['article_title']
            ).strip(),
            self.KB_LIVE_STATUS
        )

        self.logger.info("Signing out and verifying that the article is visible")
        self.delete_cookies()
        expect(
            self.sumo_pages.kb_dashboard_page._get_a_particular_article_title_locator(
                article_details['article_title']
            )
        ).to_be_visible()

        self.sumo_pages.top_navbar._click_on_sumo_nav_logo()
        self.logger.info("Signing in with a non-admin user and verifying that the article is "
                         "visible")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_13"]
        ))

        self.logger.info("Navigating to the kb overview")
        self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])

        expect(
            self.sumo_pages.kb_dashboard_page._get_a_particular_article_title_locator(
                article_details['article_title']
            )
        ).to_be_visible()

        self.sumo_pages.top_navbar._click_on_sumo_nav_logo()

        self.logger.info("Signing back with an admin account and deleting the article")
        self.logger.info("Signing back in with the admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Navigating to the kb overview")
        self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])

        self.logger.info("Clicking on the article title")
        self.sumo_pages.kb_dashboard_page._click_on_article_title(
            article_details['article_title']
        )

        self.logger.info("Deleting the created article")
        self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2266376
    @pytest.mark.kbDashboard
    def test_kb_dashboard_articles_status(self):
        self.logger.info("Signing in with the admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Create a new simple article")
        article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        article_url = self.get_page_url()

        revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()

        self.logger.info("Approving the revision")
        self.sumo_pages.kb_article_revision_flow.approve_kb_revision(revision_id)

        self.logger.info("Creating a new revision for the document")
        second_revision_details = self.sumo_pages.kb_article_revision_flow.submit_new_kb_revision()

        self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])

        self.logger.info("Verifying that the correct status is displayed")
        check.equal(
            self.sumo_pages.kb_dashboard_page._get_a_particular_article_status(
                article_details['article_title']
            ).strip(),
            self.get_kb_not_live_status(
                revision_note=second_revision_details['changes_description']
            )
        )

        self.logger.info("Navigating back to the article history and deleting the revision")
        self.navigate_to_link(article_url)

        self.sumo_pages.kb_article_show_history_page._click_on_delete_revision_button(
            second_revision_details['revision_id']
        )

        self.sumo_pages.kb_article_show_history_page._click_on_confirmation_delete_button()

        self.logger.info("Navigating back to the kb dashboard and verifying that the live status "
                         "is displayed")

        self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])
        check.equal(
            self.sumo_pages.kb_dashboard_page._get_a_particular_article_status(
                article_details['article_title']
            ).strip(),
            self.KB_LIVE_STATUS
        )

        self.logger.info("Clicking on the article title")
        self.sumo_pages.kb_dashboard_page._click_on_article_title(
            article_details['article_title']
        )

        self.logger.info("Deleting the created article")
        self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    @pytest.mark.kbDashboard
    def test_kb_dashboard_revision_deferred_status(self):
        self.logger.info("Signing in with the admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Create a new simple article")
        article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        article_url = self.get_page_url()

        revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()

        self.logger.info("Approving the revision")
        self.sumo_pages.kb_article_revision_flow.approve_kb_revision(revision_id)

        self.logger.info("Creating a new revision for the document")
        second_revision_details = self.sumo_pages.kb_article_revision_flow.submit_new_kb_revision()

        self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])

        self.logger.info("Verifying that the correct status is displayed")
        check.equal(
            self.sumo_pages.kb_dashboard_page._get_a_particular_article_status(
                article_details['article_title']
            ),
            self.get_kb_not_live_status(second_revision_details['changes_description'])
        )

        self.logger.info("Navigating back to the article history page")
        self.navigate_to_link(article_url)

        self.logger.info("Deferring the revision")
        self.sumo_pages.kb_article_show_history_page._click_on_review_revision(
            second_revision_details['revision_id']
        )

        self.sumo_pages.kb_article_review_revision_page._click_on_defer_revision_button()
        self.sumo_pages.kb_article_review_revision_page._click_on_defer_confirm_button()

        self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])

        check.equal(
            self.sumo_pages.kb_dashboard_page._get_a_particular_article_status(
                article_details['article_title']
            ),
            self.KB_LIVE_STATUS
        )

        self.logger.info("Navigating back to the article page")
        self.navigate_to_link(article_url)

        self.logger.info("Deleting the created article")
        self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    @pytest.mark.kbDashboard
    def test_kb_dashboard_needs_update_when_reviewing_a_revision(self):
        self.logger.info("Signing in with the admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Create a new simple article")
        article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        article_url = self.get_page_url()

        revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()

        self.logger.info("Approving the revision")
        self.sumo_pages.kb_article_revision_flow.approve_kb_revision(revision_id)

        self.logger.info("Creating a new revision for the document")
        second_revision_details = self.sumo_pages.kb_article_revision_flow.submit_new_kb_revision(
        )

        self.logger.info("Approving the revision")
        self.sumo_pages.kb_article_revision_flow.approve_kb_revision(
            second_revision_details['revision_id'], revision_needs_change=True
        )

        self.logger.info("Navigating to the kb dashboard overview")
        self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])

        check.equal(
            self.sumo_pages.kb_dashboard_page._get_needs_update_status(
                article_details['article_title']
            ).strip(),
            super().kb_revision_test_data['needs_change_message']
        )

        self.logger.info("Navigating back to the article page")
        self.navigate_to_link(article_url)

        self.logger.info("Deleting the created article")
        self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2266377
    @pytest.mark.kbDashboard
    def test_kb_dashboard_needs_update_edit_metadata(self):
        self.logger.info("Signing in with the admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Create a new simple article")
        article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        article_url = self.get_page_url()

        revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()

        self.logger.info("Approving the revision")
        self.sumo_pages.kb_article_revision_flow.approve_kb_revision(revision_id)

        self.logger.info("Clicking on the 'Edit Article Metadata' option")
        self.sumo_pages.kb_article_page._click_on_edit_article_metadata()

        self.logger.info("Enabling Needs Change with comment")
        self.sumo_pages.edit_article_metadata_flow.edit_article_metadata(
            needs_change=True, needs_change_comment=True
        )

        self.logger.info("Navigating to the complete dashboard list")
        self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])

        self.logger.info("Verifying that the correct needs change status is displayed")
        check.equal(
            self.sumo_pages.kb_dashboard_page._get_needs_update_status(
                article_details['article_title']
            ).strip(),
            super().kb_revision_test_data['needs_change_message']
        )

        self.logger.info("Navigating back to the article")
        self.navigate_to_link(article_url)

        self.logger.info("Clicking on the 'Edit Article Metadata' option")
        self.sumo_pages.kb_article_page._click_on_edit_article_metadata()

        self.logger.info("Removing the comment from the needs change comment")
        self.sumo_pages.edit_article_metadata_flow.edit_article_metadata(needs_change=True)

        self.logger.info("Navigating to the complete dashboard list")
        self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])

        self.logger.info("Verifying that the correct needs change status is displayed")
        check.equal(
            self.sumo_pages.kb_dashboard_page._get_needs_update_status(
                article_details['article_title']
            ).strip(),
            KBDashboardPageMessages.GENERAL_POSITIVE_STATUS
        )

        self.logger.info("Navigating back to the article")
        self.navigate_to_link(article_url)

        self.logger.info("Clicking on the 'Edit Article Metadata' option")
        self.sumo_pages.kb_article_page._click_on_edit_article_metadata()

        self.logger.info("Editing the article metadata by removing the needs change updates")
        self.sumo_pages.edit_article_metadata_flow.edit_article_metadata()

        self.logger.info("Navigating to the complete dashboard list")
        self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])

        check.is_true(
            self.sumo_pages.kb_dashboard_page._is_needs_change_empty(
                article_details['article_title']
            )
        )

        self.logger.info("Deleting the article")
        self.navigate_to_link(article_url)
        self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2266378
    @pytest.mark.kbDashboard
    def test_ready_for_l10n_kb_dashboard_revision_approval(self):
        self.logger.info("Signing in with the admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Create a new simple article")
        article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        article_url = self.get_page_url()

        revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()

        self.logger.info("Approving the revision and marking it as ready for l10n")
        self.sumo_pages.kb_article_revision_flow.approve_kb_revision(
            revision_id=revision_id, ready_for_l10n=True)

        self.logger.info("Navigating to the kb dashboard overview page")
        self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])

        self.logger.info("Verifying that the correct l10n status is displayed")
        check.equal(
            self.sumo_pages.kb_dashboard_page._get_ready_for_l10n_status(
                article_details['article_title']
            ),
            KBDashboardPageMessages.GENERAL_POSITIVE_STATUS
        )

        self.logger.info("Navigating back to the article")
        self.navigate_to_link(article_url)

        self.logger.info("Deleting the article")
        self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2266378
    @pytest.mark.kbDashboard
    def test_ready_for_l10n_kb_dashboard_revision_l10n_status(self):
        self.logger.info("Signing in with the admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Create a new simple article")
        article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        article_url = self.get_page_url()

        revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()

        self.logger.info("Approving the revision")
        self.sumo_pages.kb_article_revision_flow.approve_kb_revision(revision_id=revision_id)

        self.logger.info("Navigating to the kb dashboard overview page")
        self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])

        self.logger.info("Verifying that the correct l10n status displayed")
        check.equal(
            self.sumo_pages.kb_dashboard_page._get_ready_for_l10n_status(
                article_details['article_title']
            ),
            KBDashboardPageMessages.GENERAL_NEGATIVE_STATUS
        )

        self.logger.info("Navigating back to the article page")
        self.navigate_to_link(article_url)

        self.logger.info("Mark the revision as ready for l10n")
        self.sumo_pages.kb_article_show_history_page._click_on_ready_for_l10n_option(revision_id)
        self.sumo_pages.kb_article_show_history_page._click_on_submit_l10n_readiness_button()

        self.logger.info("Navigating to the kb dashboard overview page")
        self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])

        self.logger.info("Verifying that the correct l10n status is displayed")
        check.equal(
            self.sumo_pages.kb_dashboard_page._get_ready_for_l10n_status(
                article_details['article_title']
            ),
            KBDashboardPageMessages.GENERAL_POSITIVE_STATUS
        )

        self.logger.info("Navigating to the article")
        self.navigate_to_link(article_url)

        self.logger.info("Deleting the article")
        self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2266378
    @pytest.mark.kbDashboard
    def test_article_translation_not_allowed_kb_dashboard(self):
        self.logger.info("Signing in with the admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Create a new simple article")
        article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            allow_translations=False
        )

        article_url = self.get_page_url()

        revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()

        self.logger.info("Approving the revision")
        self.sumo_pages.kb_article_revision_flow.approve_kb_revision(revision_id=revision_id)

        self.logger.info("Navigating to the kb dashboard overview page")
        self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])

        self.logger.info("Verifying that the correct l10n status displayed")
        check.equal(
            self.sumo_pages.kb_dashboard_page._get_ready_for_l10n_status(
                article_details['article_title']
            ),
            KBDashboardPageMessages.GENERAL_NEGATIVE_STATUS
        )

        self.logger.info("Navigating to the article")
        self.navigate_to_link(article_url)

        self.logger.info("Deleting the article")
        self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2266379, C2266380
    @pytest.mark.kbDashboard
    def test_article_stale_kb_dashboard(self):
        self.logger.info("Signing in with the admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Create a new simple article by adding an old expiry date")
        article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            expiry_date=self.kb_article_test_data['old_expiry_date']
        )

        article_url = self.get_page_url()

        revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()

        self.logger.info("Approving the revision")
        self.sumo_pages.kb_article_revision_flow.approve_kb_revision(revision_id)

        self.logger.info("Navigating to the kb dashboard overview page")
        self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])

        self.logger.info("Verifying that the correct stale status displayed")
        check.equal(
            self.sumo_pages.kb_dashboard_page._get_stale_status(
                article_details['article_title']
            ),
            KBDashboardPageMessages.GENERAL_POSITIVE_STATUS
        )

        self.logger.info("Verifying that the correct date is displayed")
        check.equal(
            self.sumo_pages.kb_dashboard_page._get_existing_expiry_date(
                article_details['article_title']
            ),
            self.convert_string_to_datetime(
                self.kb_article_test_data['old_expiry_date']
            )
        )

        self.logger.info("Navigating back to the article")
        self.navigate_to_link(article_url)

        self.logger.info("Creating a new revision with non-stale expiry date")
        second_revision_details = self.sumo_pages.kb_article_revision_flow.submit_new_kb_revision(
            expiry_date=self.kb_article_test_data['expiry_date']
        )

        self.logger.info("Approving the revision")
        self.sumo_pages.kb_article_revision_flow.approve_kb_revision(
            second_revision_details['revision_id']
        )

        self.logger.info("Navigating to the complete dashboard list")
        self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])

        self.logger.info("Verifying that the correct stale status is displayed")
        check.is_true(
            self.sumo_pages.kb_dashboard_page._is_stale_status_empty(
                article_details['article_title']
            )
        )

        self.logger.info("Verifying that the correct date is displayed")
        check.equal(
            self.sumo_pages.kb_dashboard_page._get_existing_expiry_date(
                article_details['article_title']
            ),
            self.convert_string_to_datetime(
                self.kb_article_test_data['expiry_date']
            )
        )

        self.logger.info("Navigating to the article")
        self.navigate_to_link(article_url)

        self.logger.info("Deleting the article")
        self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    @pytest.mark.kbDashboard
    def test_article_title_update(self):
        self.logger.info("Signing in with the admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Create a new simple article")
        article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        article_url = self.get_page_url()

        revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()

        self.logger.info("Approving the revision")
        self.sumo_pages.kb_article_revision_flow.approve_kb_revision(revision_id=revision_id)

        self.logger.info("Navigating to the kb dashboard overview page")
        self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])

        self.logger.info("Verifying that the correct title is displayed")
        expect(
            self.sumo_pages.kb_dashboard_page._get_a_particular_article_title_locator(
                article_details['article_title']
            )
        ).to_be_visible()

        self.logger.info("Navigating back to the article")
        self.navigate_to_link(article_url)

        self.logger.info("Editing the article metadata by changing the title")
        self.sumo_pages.kb_article_page._click_on_edit_article_metadata()

        new_article_title = "Updated " + article_details['article_title']
        self.sumo_pages.edit_article_metadata_flow.edit_article_metadata(title=new_article_title)

        self.logger.info("Navigating back to the kb dashboard")
        self.navigate_to_link(super().general_test_data['dashboard_links']['kb_overview'])

        self.logger.info("Verifying that the correct title is displayed")
        expect(
            self.sumo_pages.kb_dashboard_page._get_a_particular_article_title_locator(
                new_article_title
            )
        ).to_be_visible()

        self.logger.info("Navigating to the article")
        self.navigate_to_link(article_url)

        self.logger.info("Deleting the article")
        self.sumo_pages.kb_article_deletion_flow.delete_kb_article()
