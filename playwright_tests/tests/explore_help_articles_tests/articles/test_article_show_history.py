import pytest_check as check
import pytest
from playwright_tests.core.testutilities import TestUtilities
from playwright.sync_api import expect

from playwright_tests.messages.ask_a_question_messages.AAQ_messages.question_page_messages import \
    QuestionPageMessages
from playwright_tests.messages.auth_pages_messages.fxa_page_messages import FxAPageMessages
from playwright_tests.messages.explore_help_articles.kb_article_page_messages import (
    KBArticlePageMessages)
from playwright_tests.messages.explore_help_articles.kb_article_revision_page_messages import (
    KBArticleRevision)
from playwright_tests.messages.explore_help_articles.kb_article_show_history_page_messages import \
    KBArticleShowHistoryPageMessages
from playwright_tests.messages.my_profile_pages_messages.my_profile_page_messages import (
    MyProfileMessages)


class TestKBArticleShowHistory(TestUtilities, KBArticleShowHistoryPageMessages):

    # C891309, C2102170,  C2102168, C2489545
    @pytest.mark.kbArticleShowHistory
    def test_kb_article_removal(self):
        self.logger.info("Signing in with a normal account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        self.logger.info("Create a new simple article")
        article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        self.logger.info("Fetching the revision id")
        revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()
        revision_id_number = self.number_extraction_from_string(revision_id)

        self.logger.info("Verifying that the delete button is not available for the only revision")
        expect(
            self.sumo_pages.kb_article_show_history_page._get_delete_revision_button_locator(
                revision_id
            )
        ).to_be_hidden()

        self.logger.info("Verifying that manually navigating to the delete revision endpoint "
                         "returns 403")
        with self.page.expect_navigation() as navigation_info:
            self.navigate_to_link(super().get_delete_revision_endpoint(
                article_details["article_slug"], revision_id_number
            ))
            response = navigation_info.value
            check.equal(
                response.status,
                403
            )

        self.logger.info("Navigating back")
        self.navigate_back()

        self.logger.info("Verifying that the delete button for the article is not displayed")
        expect(
            self.sumo_pages.kb_article_show_history_page._get_delete_this_document_button_locator()
        ).to_be_hidden()

        self.logger.info("Verifying that manually navigating to the delete endpoint returns 403")
        with self.page.expect_navigation() as navigation_info:
            self.navigate_to_link(
                KBArticlePageMessages
                .KB_ARTICLE_PAGE_URL + article_details['article_slug'] + QuestionPageMessages
                .DELETE_QUESTION_URL_ENDPOINT
            )
            response = navigation_info.value
            check.equal(
                response.status,
                403
            )

        self.logger.info("Navigating back")
        self.navigate_back()

        self.logger.info("Delete user session")
        self.delete_cookies()

        self.logger.info("Manually navigating to the delete revision endpoint and verifying that "
                         "the auth page is returned")
        self.navigate_to_link(super().get_delete_revision_endpoint(
            article_details["article_slug"], revision_id_number
        ))

        check.is_true(
            FxAPageMessages.AUTH_PAGE_URL in self.get_page_url()
        )
        self.logger.info("Navigating back")
        self.navigate_back()

        self.logger.info("Verifying that manually navigating to the delete endpoint returns the "
                         "auth page")
        self.navigate_to_link(
            KBArticlePageMessages
            .KB_ARTICLE_PAGE_URL + article_details['article_slug'] + QuestionPageMessages
            .DELETE_QUESTION_URL_ENDPOINT
        )

        check.is_true(
            FxAPageMessages.AUTH_PAGE_URL in self.get_page_url()
        )

        self.logger.info("Navigating back")
        self.navigate_back()

        self.logger.info("Verifying that the delete button is not available for the only revision")
        expect(
            self.sumo_pages.kb_article_show_history_page._get_delete_revision_button_locator(
                revision_id
            )
        ).to_be_hidden()

        self.logger.info("Verifying that the delete button for the article is not displayed")
        expect(
            self.sumo_pages.kb_article_show_history_page._get_delete_this_document_button_locator()
        ).to_be_hidden()

        self.logger.info("Signing in with a admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Clicking on the delete revision button for the only available revision")
        self.sumo_pages.kb_article_show_history_page._click_on_delete_revision_button(revision_id)

        self.logger.info("Verifying that the correct 'Unable to delete the revision' page header")
        check.equal(
            self.sumo_pages.kb_article_show_history_page._get_unable_to_delete_revision_header(),
            KBArticleRevision.KB_REVISION_CANNOT_DELETE_ONLY_REVISION_HEADER
        )

        self.logger.info("Verifying that the correct 'Unable to delete the revision' page "
                         "subheader")
        check.equal(
            self.sumo_pages.kb_article_show_history_page.
            _get_unable_to_delete_revision_subheader(),
            KBArticleRevision.KB_REVISION_CANNOT_DELETE_ONLY_REVISION_SUBHEADER
        )

        self.logger.info("Clicking on the 'Go back to document history button'")
        self.sumo_pages.kb_article_show_history_page._click_go_back_to_document_history_option()

        self.logger.info("Verifying that we are redirected to the document history page")
        expect(
            self.page
        ).to_have_url(
            KBArticlePageMessages.KB_ARTICLE_PAGE_URL + article_details
            ['article_slug'] + KBArticlePageMessages.KB_ARTICLE_HISTORY_URL_ENDPOINT
        )

        self.logger.info("Clicking on the 'Delete article' button")
        self.sumo_pages.kb_article_show_history_page._click_on_delete_this_document_button()

        self.logger.info("Clicking on the cancel button")
        self.sumo_pages.kb_article_show_history_page._click_on_confirmation_cancel_button()

        self.logger.info("Verifying that we are back on the show history page for the article")
        expect(
            self.page
        ).to_have_url(
            KBArticlePageMessages.KB_ARTICLE_PAGE_URL + article_details
            ['article_slug'] + KBArticlePageMessages.KB_ARTICLE_HISTORY_URL_ENDPOINT
        )

        self.logger.info("Clicking on the 'Delete article' button")
        self.sumo_pages.kb_article_show_history_page._click_on_delete_this_document_button()

        self.logger.info("Clicking on the 'Delete' button")
        self.sumo_pages.kb_article_show_history_page._click_on_confirmation_delete_button()

        self.logger.info("Verifying that the article was successfully deleted by navigating to "
                         "the article")

        with self.page.expect_navigation() as navigation_info:
            self.navigate_to_link(
                KBArticlePageMessages.KB_ARTICLE_PAGE_URL + article_details['article_slug'] + "/"
            )
        response = navigation_info.value
        check.equal(
            response.status,
            404
        )

    # C2490047, C2490048
    @pytest.mark.kbArticleShowHistory
    def test_kb_article_category_link_and_header(self):
        self.logger.info("Signing in with an admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        for category in self.general_test_data["kb_article_categories"]:

            if category != "Templates":
                self.logger.info("Create a new article")
                article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                    article_category=category
                )
            else:
                self.logger.info("Create a new article")
                article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                    article_category=category,
                    is_template=True
                )

            self.logger.info("Verifying that the correct page header is displayed")
            check.equal(
                self.sumo_pages.kb_article_show_history_page._get_show_history_page_title(),
                KBArticleShowHistoryPageMessages.PAGE_TITLE + article_details["article_title"]
            )

            self.logger.info("Verifying that the correct category is displayed inside the 'Show "
                             "History' page")
            check.equal(
                self.sumo_pages.kb_article_show_history_page._get_show_history_category_text(),
                category
            )

            self.logger.info("Verifying that the correct revision history for locale is displayed")
            check.equal(
                self.sumo_pages.kb_article_show_history_page.
                _get_show_history_revision_for_locale_text(),
                KBArticleShowHistoryPageMessages.DEFAULT_REVISION_FOR_LOCALE
            )

            self.logger.info("Clicking on the 'Category' link")
            self.sumo_pages.kb_article_show_history_page._click_on_show_history_category()

            self.logger.info("Verifying that the user is redirected to the correct page")
            expect(
                self.page
            ).to_have_url(self.different_endpoints['kb_categories_links'][category])

            self.logger.info("Navigating back")
            self.navigate_back()

            self.logger.info("Clicking on the 'Show History' option")
            self.sumo_pages.kb_article_page._click_on_show_history_option()

            self.logger.info("Clicking on the 'Delete article' button")
            self.sumo_pages.kb_article_show_history_page._click_on_delete_this_document_button()

            self.logger.info("Clicking on the 'Delete' button")
            self.sumo_pages.kb_article_show_history_page._click_on_confirmation_delete_button()

    # C2101637, C2489543, C2102169
    @pytest.mark.kbArticleShowHistory
    def test_kb_article_contributor_removal(self):
        self.logger.info("Signing in with an admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        username_one = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        self.logger.info("Create a new simple article")
        self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        self.logger.info("Verifying that no users are added inside the contributors list")
        expect(
            self.sumo_pages.kb_article_show_history_page._get_all_contributors_locator()
        ).to_be_hidden()

        self.logger.info("Clicking on the Article menu option")
        self.sumo_pages.kb_article_page._click_on_article_option()

        self.logger.info("Verifying that the user is not displayed inside the article "
                         "contributors section")
        check.is_not_in(
            username_one,
            self.sumo_pages.kb_article_page._get_list_of_kb_article_contributors()
        )

        self.logger.info("Navigating back to the 'Show History page'")
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

        self.logger.info("Verifying that the username which created the revision is added inside "
                         "the 'Contributors' list")
        check.is_in(
            username_one,
            self.sumo_pages.kb_article_show_history_page._get_list_of_all_contributors(),
        )

        self.logger.info("Fetching the contributor id")
        self.sumo_pages.kb_article_show_history_page._click_on_edit_contributors_option()
        (self.sumo_pages.kb_article_show_history_page.
         _click_on_delete_button_for_a_particular_contributor(username_one))
        deletion_link = self.get_page_url()

        self.logger.info("Navigating back by hitting the cancel button")
        (self.sumo_pages.kb_article_show_history_page.
         _click_on_delete_contributor_confirmation_page_cancel_button())

        self.logger.info("Clicking on the Article menu option")
        self.sumo_pages.kb_article_page._click_on_article_option()

        self.logger.info("Verifying that the user is displayed inside the article "
                         "contributors section")
        check.is_in(
            username_one,
            self.sumo_pages.kb_article_page._get_list_of_kb_article_contributors()
        )

        self.logger.info("Navigating back to the 'Show History page'")
        self.sumo_pages.kb_article_page._click_on_show_history_option()

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Signing in with a non-Admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        username_two = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        self.logger.info("Creating a new revision for the document")
        self.sumo_pages.kb_article_revision_flow.submit_new_kb_revision()

        self.logger.info("Verifying that the 'Edit Contributors' option is not displayed for "
                         "users which don't have the necessary permissions")
        expect(
            self.sumo_pages.kb_article_show_history_page._get_edit_contributors_option_locator()
        ).to_be_hidden()

        self.logger.info("Manually navigating to the deletion link and verifying that 403 is "
                         "returned")

        with self.page.expect_navigation() as navigation_info:
            self.navigate_to_link(
                deletion_link
            )
        response = navigation_info.value
        check.equal(
            response.status,
            403
        )

        self.logger.info("Navigating back")
        self.navigate_back()

        self.logger.info("Clicking on the Article menu option")
        self.sumo_pages.kb_article_page._click_on_article_option()

        self.logger.info("Verifying that the user is not displayed inside the article "
                         "contributors section")
        check.is_not_in(
            username_two,
            self.sumo_pages.kb_article_page._get_list_of_kb_article_contributors()
        )

        self.logger.info("Navigating back to the 'Show History page'")
        self.sumo_pages.kb_article_page._click_on_show_history_option()

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Verifying that the 'Edit Contributors' option is not displayed for "
                         "signed out users")
        expect(
            self.sumo_pages.kb_article_show_history_page._get_edit_contributors_option_locator()
        ).to_be_hidden()

        self.logger.info("Manually navigating to the deletion link and the user is redirected to "
                         "the auth page")

        self.navigate_to_link(deletion_link)
        check.is_true(
            FxAPageMessages.AUTH_PAGE_URL in self.get_page_url()
        )

        self.logger.info("Navigating back")
        self.navigate_back()

        self.logger.info("Signing in with a normal account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Verifying that the username two is not displayed inside the "
                         "Contributors list")
        check.is_not_in(
            username_two,
            self.sumo_pages.kb_article_show_history_page._get_list_of_all_contributors()
        )

        revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()

        self.logger.info("Clicking on the 'Review' option")
        self.sumo_pages.kb_article_show_history_page._click_on_review_revision(
            revision_id
        )

        self.logger.info("Click on 'Approve Revision' button")
        self.sumo_pages.kb_article_review_revision_page._click_on_approve_revision_button()

        self.logger.info("Clicking on the 'Accept' button")
        self.sumo_pages.kb_article_review_revision_page._click_accept_revision_accept_button()

        self.logger.info("Verifying that second username is displayed inside the 'Contributors' "
                         "list")
        check.is_in(
            username_two,
            self.sumo_pages.kb_article_show_history_page._get_list_of_all_contributors()
        )

        self.logger.info("Clicking on the Article menu option")
        self.sumo_pages.kb_article_page._click_on_article_option()

        self.logger.info("Verifying that the user is displayed inside the article "
                         "contributors section")
        check.is_in(
            username_one,
            self.sumo_pages.kb_article_page._get_list_of_kb_article_contributors()
        )

        self.logger.info("Navigating back to the 'Show History page'")
        self.sumo_pages.kb_article_page._click_on_show_history_option()

        self.logger.info("Clicking on the 'Edit contributors' option")
        self.sumo_pages.kb_article_show_history_page._click_on_edit_contributors_option()

        self.logger.info("Clicking on the delete button for user two")
        (self.sumo_pages.kb_article_show_history_page.
         _click_on_delete_button_for_a_particular_contributor(username_two))

        self.logger.info("Verifying that the correct delete contributor page header is displayed")
        check.equal(
            self.sumo_pages.kb_article_show_history_page.
            _get_delete_contributor_confirmation_page_header(),
            self.get_remove_contributor_page_header(username_two)
        )

        self.logger.info("Clicking on the 'Cancel' button")
        (self.sumo_pages.kb_article_show_history_page.
         _click_on_delete_contributor_confirmation_page_cancel_button())

        self.logger.info("Verifying that second username is displayed inside the 'Contributors' "
                         "list")
        check.is_in(
            username_two,
            self.sumo_pages.kb_article_show_history_page._get_list_of_all_contributors()
        )

        self.logger.info("Clicking on the Article menu option")
        self.sumo_pages.kb_article_page._click_on_article_option()

        self.logger.info("Verifying that the user is displayed inside the article "
                         "contributors section")
        check.is_in(
            username_one,
            self.sumo_pages.kb_article_page._get_list_of_kb_article_contributors()
        )

        self.logger.info("Navigating back to the 'Show History page'")
        self.sumo_pages.kb_article_page._click_on_show_history_option()

        self.logger.info("Clicking on the 'Edit contributors' option")
        self.sumo_pages.kb_article_show_history_page._click_on_edit_contributors_option()

        self.logger.info("Clicking on the delete button for user two")
        (self.sumo_pages.kb_article_show_history_page.
         _click_on_delete_button_for_a_particular_contributor(username_two))

        self.logger.info("Clicking on the 'Remove contributor' button")
        (self.sumo_pages.kb_article_show_history_page.
         _click_on_delete_contributor_confirmation_page_confirm_button())

        self.logger.info("Verifying that the correct banner is displayed")
        check.equal(
            self.sumo_pages.kb_article_show_history_page._get_show_history_page_banner(),
            super().get_contributor_removed_message(username_two)
        )

        self.logger.info("Verifying that second username is not displayed inside the "
                         "'Contributors' list")
        check.is_not_in(
            username_two,
            self.sumo_pages.kb_article_show_history_page._get_list_of_all_contributors()
        )

        self.logger.info("Clicking on the Article menu option")
        self.sumo_pages.kb_article_page._click_on_article_option()

        self.logger.info("Verifying that the user is not displayed inside the article "
                         "contributors section")
        check.is_not_in(
            username_two,
            self.sumo_pages.kb_article_page._get_list_of_kb_article_contributors()
        )

        self.logger.info("Navigating back to the 'Show History page'")
        self.sumo_pages.kb_article_page._click_on_show_history_option()

        self.logger.info("Clicking on the 'Delete article' button")
        self.sumo_pages.kb_article_show_history_page._click_on_delete_this_document_button()

        self.logger.info("Clicking on the 'Delete' button")
        self.sumo_pages.kb_article_show_history_page._click_on_confirmation_delete_button()

    # C2101638
    @pytest.mark.kbArticleShowHistory
    def test_contributors_can_be_manually_added(self):
        self.logger.info("Signing in with an admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        self.logger.info("Create a new simple article")
        self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        self.logger.info("Clicking on the 'Edit contributors' option")
        self.sumo_pages.kb_article_show_history_page._click_on_edit_contributors_option()

        new_contributor = super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        )

        self.logger.info("Adding and selecting the username from the search field")
        (self.sumo_pages.kb_article_show_history_page.
         _add_a_new_contributor_inside_the_contributor_field(new_contributor))

        (self.sumo_pages.kb_article_show_history_page.
         _click_on_new_contributor_search_result(new_contributor))

        self.logger.info("Clicking on the 'Add Contributor' option")
        self.sumo_pages.kb_article_show_history_page._click_on_add_contributor_button()

        self.logger.info("Verifying that the correct banner is displayed")
        check.equal(
            self.sumo_pages.kb_article_show_history_page._get_show_history_page_banner(),
            super().get_contributor_added_message(new_contributor)
        )

        self.logger.info("Verifying that the user was successfully added inside the contributors "
                         "list")
        check.is_in(
            new_contributor,
            self.sumo_pages.kb_article_show_history_page._get_list_of_all_contributors(),
        )

        self.logger.info("Clicking on the Article menu option")
        self.sumo_pages.kb_article_page._click_on_article_option()

        self.logger.info("Verifying that the user is displayed inside the article "
                         "contributors section")
        check.is_in(
            new_contributor,
            self.sumo_pages.kb_article_page._get_list_of_kb_article_contributors()
        )

        self.logger.info("Navigating back to the 'Show History page'")
        self.sumo_pages.kb_article_page._click_on_show_history_option()

        self.logger.info("Clicking on the 'Delete article' button")
        self.sumo_pages.kb_article_show_history_page._click_on_delete_this_document_button()

        self.logger.info("Clicking on the 'Delete' button")
        self.sumo_pages.kb_article_show_history_page._click_on_confirmation_delete_button()

    # C2101634, C2489553
    @pytest.mark.kbArticleShowHistory
    def test_kb_article_contributor_profile_access(self):
        self.logger.info("Signing in with an admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        self.logger.info("Create a new simple article")
        self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

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

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Signing in with a non-Admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        username_two = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        self.logger.info("Creating a new revision for the document")
        self.sumo_pages.kb_article_revision_flow.submit_new_kb_revision()

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Signing in with a normal account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

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

        self.logger.info("Clicking on the second contributor and verifying that we are "
                         "redirected to it's profile page")
        (self.sumo_pages.kb_article_show_history_page._click_on_a_particular_contributor
         (username_two)
         )

        expect(
            self.page
        ).to_have_url(MyProfileMessages.get_my_profile_stage_url(username_two))

        self.logger.info("Navigating back")
        self.navigate_back()

        self.logger.info("Clicking on the revision editor")
        self.sumo_pages.kb_article_show_history_page._click_on_a_particular_revision_editor(
            revision_id, username_two
        )

        self.logger.info("Verifying that we are redirected to the editor homepage")
        expect(
            self.page
        ).to_have_url(MyProfileMessages.get_my_profile_stage_url(username_two))

        self.logger.info("Navigating back")
        self.navigate_back()

        self.logger.info("Navigating to the article main menu")
        self.navigate_to_link(
            article_url
        )

        self.logger.info("Clicking on the contributor listed inside the article page")
        self.sumo_pages.kb_article_page._click_on_a_particular_article_contributor(username_two)

        self.logger.info("Verifying that we are redirected to the editor homepage")
        expect(
            self.page
        ).to_have_url(MyProfileMessages.get_my_profile_stage_url(username_two))

        self.logger.info("Navigating back")
        self.navigate_back()

        self.logger.info("Signing in with an admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Clicking on the Article menu option")
        self.sumo_pages.kb_article_page._click_on_article_option()

        self.logger.info("Clicking on the contributor listed inside the article page")
        self.sumo_pages.kb_article_page._click_on_a_particular_article_contributor(username_two)

        self.logger.info("Verifying that we are redirected to the editor homepage")
        expect(
            self.page
        ).to_have_url(MyProfileMessages.get_my_profile_stage_url(username_two))

        self.logger.info("Navigating back")
        self.navigate_back()

        self.logger.info("Navigating to the show history page")
        self.sumo_pages.kb_article_page._click_on_show_history_option()

        self.logger.info("Clicking on the second contributor and verifying that we are "
                         "redirected to it's profile page")
        (self.sumo_pages.kb_article_show_history_page._click_on_a_particular_contributor
         (username_two)
         )

        expect(
            self.page
        ).to_have_url(MyProfileMessages.get_my_profile_stage_url(username_two))

        self.logger.info("Navigating back")
        self.navigate_back()

        self.logger.info("Clicking on the revision editor")
        self.sumo_pages.kb_article_show_history_page._click_on_a_particular_revision_editor(
            revision_id, username_two
        )

        self.logger.info("Verifying that we are redirected to the editor homepage")
        expect(
            self.page
        ).to_have_url(MyProfileMessages.get_my_profile_stage_url(username_two))

        self.logger.info("Navigating back")
        self.navigate_back()

        self.logger.info("Clicking on the 'Delete article' button")
        self.sumo_pages.kb_article_show_history_page._click_on_delete_this_document_button()

        self.logger.info("Clicking on the 'Delete' button")
        self.sumo_pages.kb_article_show_history_page._click_on_confirmation_delete_button()

    # C2499415
    @pytest.mark.kbArticleShowHistory
    def test_kb_article_revision_date_functionality(self):
        self.logger.info("Signing in with an admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        main_user = super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        )

        self.logger.info("Create a new simple article")
        self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

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

        self.logger.info("Delete user session")
        self.delete_cookies()

        self.logger.info("Signing in with a non-admin account")
        creator_username = self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts['TEST_ACCOUNT_12']
        ))

        self.logger.info("Submitting a new revision")
        second_revision_id = self.sumo_pages.kb_article_revision_flow.submit_new_kb_revision()

        self.logger.info("Deleting user session")
        self.delete_cookies()
        revision_time = self.sumo_pages.kb_article_show_history_page._get_revision_time(
            second_revision_id
        )

        self.logger.info("Clicking on the first revision")
        self.sumo_pages.kb_article_show_history_page._click_on_a_revision_date(revision_id)

        self.logger.info("Verifying that the correct 'Is current revision?' text is displayed")
        check.equal(
            self.sumo_pages.kb_article_preview_revision_page._get_is_current_revision_text(),
            KBArticleRevision.KB_ARTICLE_REVISION_YES_STATUS
        )

        self.logger.info("Navigating back")
        self.navigate_back()

        self.logger.info("Clicking on the revision time")
        self.sumo_pages.kb_article_show_history_page._click_on_a_revision_date(second_revision_id)

        self.logger.info("Verifying that the revision information content is expanded by default")
        expect(
            self.sumo_pages.kb_article_preview_revision_page.
            _get_revision_information_content_locator()
        ).to_be_visible()

        self.logger.info("Clicking on the 'Revision Information' foldout section")
        (self.sumo_pages.kb_article_preview_revision_page.
         _click_on_revision_information_foldout_section())

        self.logger.info("Verifying that the revision information content is collapsed/no longer "
                         "displayed")
        expect(
            self.sumo_pages.kb_article_preview_revision_page.
            _get_revision_information_content_locator()
        ).to_be_hidden()

        self.logger.info("Clicking on the 'Revision Information' foldout section")
        (self.sumo_pages.kb_article_preview_revision_page.
         _click_on_revision_information_foldout_section())

        self.logger.info("Verifying that the revision information content is displayed")
        expect(
            self.sumo_pages.kb_article_preview_revision_page.
            _get_revision_information_content_locator()
        ).to_be_visible()

        self.logger.info("Verifying that the preview revision page contains the correct info "
                         "inside the 'revision information' section")

        self.logger.info("Verifying that the revision id is the correct one")
        check.equal(
            self.sumo_pages.kb_article_preview_revision_page._get_preview_revision_id_text(),
            str(self.number_extraction_from_string(second_revision_id))
        )

        self.logger.info("Verifying that the correct revision time is displayed")
        check.equal(
            self.sumo_pages.kb_article_preview_revision_page.
            _get_preview_revision_created_date_text(),
            revision_time
        )

        self.logger.info("Verifying that the correct creator is displayed")
        check.equal(
            self.sumo_pages.kb_article_preview_revision_page._get_preview_revision_creator_text(),
            creator_username
        )

        self.logger.info("Clicking on the creator link and verifying that we are redirected to "
                         "the username page")
        self.sumo_pages.kb_article_preview_revision_page._click_on_creator_link()

        expect(
            self.page
        ).to_have_url(MyProfileMessages.get_my_profile_stage_url(creator_username))

        self.logger.info("Navigating back to the revision preview page")
        self.navigate_back()

        self.logger.info("Verifying that the correct review comment is displayed")
        check.equal(
            self.sumo_pages.kb_article_preview_revision_page._get_preview_revision_comment_text(),
            self.kb_article_test_data['changes_description']
        )

        self.logger.info("Verifying that the correct reviewed status is displayed")
        check.equal(
            self.sumo_pages.kb_article_preview_revision_page._get_preview_revision_reviewed_text(),
            KBArticleRevision.KB_ARTICLE_REVISION_NO_STATUS
        )

        self.logger.info("Verifying that the reviewed by locator is hidden")
        expect(
            self.sumo_pages.kb_article_preview_revision_page._get_reviewed_by_locator()
        ).to_be_hidden()

        self.logger.info("Verifying that the is approved locator is hidden")
        expect(
            self.sumo_pages.kb_article_preview_revision_page._get_is_approved_text_locator()
        ).to_be_hidden()

        self.logger.info("Verifying that the is current revision locator is hidden")
        expect(
            self.sumo_pages.kb_article_preview_revision_page._is_current_revision_locator()
        ).to_be_hidden()

        self.logger.info("Verifying that the correct ready for localization locator is displayed")
        check.equal(
            self.sumo_pages.kb_article_preview_revision_page.
            _get_preview_revision_ready_for_localization_text(),
            KBArticleRevision.KB_ARTICLE_REVISION_NO_STATUS
        )

        self.logger.info("Verifying that the readied for localization by is hidden")
        expect(
            self.sumo_pages.kb_article_preview_revision_page._readied_for_localization_by_locator()
        ).to_be_hidden()

        self.logger.info("Verifying that the 'Edit article based on this revision' is not "
                         "displayed")
        expect(
            self.sumo_pages.kb_article_preview_revision_page.
            _get_edit_article_based_on_this_revision_link_locator()
        ).to_be_hidden()

        self.logger.info("Verifying that the 'Revision Source' section is hidden by default")
        expect(
            self.sumo_pages.kb_article_preview_revision_page.
            _get_preview_revision_source_textarea_locator()
        ).to_be_hidden()

        self.logger.info("Clicking on the 'Revision Source' foldout section option")
        (self.sumo_pages.kb_article_preview_revision_page.
         _click_on_revision_source_foldout_section())

        self.logger.info("Verifying that the 'Revision Source' textarea contains the correct "
                         "details")
        check.equal(
            self.sumo_pages.kb_article_preview_revision_page.
            _get_preview_revision_source_textarea_content(),
            self.kb_article_test_data['updated_article_content']
        )

        self.logger.info("Verifying that the 'Revision Content' section is hidden by default")
        expect(
            self.sumo_pages.kb_article_preview_revision_page._get_revision_content_html_locator()
        ).to_be_hidden()

        self.logger.info("Clicking on the 'Revision Content' foldout option")
        (self.sumo_pages.kb_article_preview_revision_page.
         _click_on_revision_content_foldout_section())

        self.logger.info("Verifying that the 'Revision Content' section is visible")
        expect(
            self.sumo_pages.kb_article_preview_revision_page._get_revision_content_html_locator()
        ).to_be_visible()

        self.logger.info("Signing in with an admin account and approving the revision")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.sumo_pages.kb_article_page._click_on_show_history_option()

        self.logger.info("Clicking on the 'Review' option")
        self.sumo_pages.kb_article_show_history_page._click_on_review_revision(
            second_revision_id
        )

        self.logger.info("Click on 'Approve Revision' button")
        self.sumo_pages.kb_article_review_revision_page._click_on_approve_revision_button()

        self.logger.info("Clicking on the 'Ready for Localization' checkbox")
        self.sumo_pages.kb_article_review_revision_page._check_ready_for_localization_checkbox()

        self.logger.info("Clicking on the 'Accept' button")
        self.sumo_pages.kb_article_review_revision_page._click_accept_revision_accept_button()

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Clicking on the revision time")
        self.sumo_pages.kb_article_show_history_page._click_on_a_revision_date(second_revision_id)

        self.logger.info("Verifying that the correct reviewed status is displayed")
        check.equal(
            self.sumo_pages.kb_article_preview_revision_page._get_preview_revision_reviewed_text(),
            KBArticleRevision.KB_ARTICLE_REVISION_YES_STATUS
        )

        self.logger.info("Verifying that the reviewed by date is displayed")
        expect(
            self.sumo_pages.kb_article_preview_revision_page.
            _get_preview_revision_reviewed_date_locator()
        ).to_be_visible()

        self.logger.info("Verifying that the correct 'Reviewed by' text is displayed")
        check.equal(
            self.sumo_pages.kb_article_preview_revision_page._get_reviewed_by_text(),
            main_user
        )

        self.logger.info("Verifying that the correct is approved status displayed")
        check.equal(
            self.sumo_pages.kb_article_preview_revision_page._get_is_approved_text(),
            KBArticleRevision.KB_ARTICLE_REVISION_YES_STATUS
        )

        self.logger.info("Verifying that the correct is current revision status displayed")
        check.equal(
            self.sumo_pages.kb_article_preview_revision_page._get_is_current_revision_text(),
            KBArticleRevision.KB_ARTICLE_REVISION_YES_STATUS
        )

        self.logger.info("Verifying that the correct is ready for localization status displayed")
        check.equal(
            self.sumo_pages.kb_article_preview_revision_page.
            _get_preview_revision_ready_for_localization_text(),
            KBArticleRevision.KB_ARTICLE_REVISION_YES_STATUS
        )

        self.logger.info("Verifying that the 'Readied for localization' date is displayed")
        expect(
            self.sumo_pages.kb_article_preview_revision_page._ready_for_localization_date()
        ).to_be_visible()

        self.logger.info("Verifying that the correct localization by text is displayed")
        check.equal(
            self.sumo_pages.kb_article_preview_revision_page._readied_for_localization_by_text(),
            main_user
        )

        self.logger.info("Signing in with an admin account and deleting the article")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Clicking on the 'Edit article based on this revision option'")
        (self.sumo_pages.kb_article_preview_revision_page.
         _click_on_edit_article_based_on_this_revision_link())

        self.logger.info("Verifying that the correct link is displayed")
        expect(
            self.page
        ).to_have_url(
            article_url + QuestionPageMessages.EDIT_QUESTION_URL_ENDPOINT + "/" + str(
                self.number_extraction_from_string(second_revision_id))
        )

        self.logger.info("Clicking on the 'Show History' option")
        self.sumo_pages.kb_article_page._click_on_show_history_option()

        self.logger.info("Clicking on the 'Delete article' button")
        self.sumo_pages.kb_article_show_history_page._click_on_delete_this_document_button()

        self.logger.info("Clicking on the 'Delete' button")
        self.sumo_pages.kb_article_show_history_page._click_on_confirmation_delete_button()
