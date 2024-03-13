import allure
from pytest_check import check
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
        with allure.step("Signing in with a non-admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))

        with allure.step("Create a new simple article"):
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        article_url = self.get_page_url()

        self.logger.info("Fetching the revision id")
        revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()
        revision_id_number = self.number_extraction_from_string(revision_id)

        with allure.step("Verifying that the delete button is not available for the only kb "
                         "revision"):
            expect(
                self.sumo_pages.kb_article_show_history_page._get_delete_revision_button_locator(
                    revision_id
                )
            ).to_be_hidden()

        with check, allure.step("Verifying that manually navigating to the delete revision "
                                "endpoint returns 403"):
            with self.page.expect_navigation() as navigation_info:
                self.navigate_to_link(super().get_delete_revision_endpoint(
                    article_details["article_slug"], revision_id_number
                ))
                response = navigation_info.value
                assert response.status == 403

        with allure.step("Navigating back and verifying that the delete button for the article "
                         "is not displayed"):
            self.navigate_to_link(article_url)
            expect(
                self.sumo_pages.kb_article_show_history_page
                ._get_delete_this_document_button_locator()
            ).to_be_hidden()

        with check, allure.step("Verifying that manually navigating to the delete endpoint "
                                "returns 403"):
            with self.page.expect_navigation() as navigation_info:
                self.navigate_to_link(
                    KBArticlePageMessages
                    .KB_ARTICLE_PAGE_URL + article_details['article_slug'] + QuestionPageMessages
                    .DELETE_QUESTION_URL_ENDPOINT
                )
                response = navigation_info.value
                assert response.status == 403

        with allure.step("Navigating back and deleting the user session"):
            self.navigate_to_link(article_url)
            self.delete_cookies()

        with check, allure.step("Manually navigating to the delete revision endpoint and "
                                "verifying that the auth page is returned"):
            self.navigate_to_link(super().get_delete_revision_endpoint(
                article_details["article_slug"], revision_id_number
            ))
            assert FxAPageMessages.AUTH_PAGE_URL in self.get_page_url()

        with check, allure.step("Navigating back and verifying that manually navigating to the "
                                "delete endpoint returns the auth page"):
            self.navigate_to_link(article_url)
            self.navigate_to_link(
                KBArticlePageMessages
                .KB_ARTICLE_PAGE_URL + article_details['article_slug'] + QuestionPageMessages
                .DELETE_QUESTION_URL_ENDPOINT
            )
            assert FxAPageMessages.AUTH_PAGE_URL in self.get_page_url()

        with allure.step("Navigating back and verifying that the delete button is not available "
                         "for the only revision"):
            self.navigate_to_link(article_url)
            expect(
                self.sumo_pages.kb_article_show_history_page._get_delete_revision_button_locator(
                    revision_id
                )
            ).to_be_hidden()

        with allure.step("Verifying that the delete button for the article is not displayed"):
            expect(
                self.sumo_pages.kb_article_show_history_page
                ._get_delete_this_document_button_locator()
            ).to_be_hidden()

        with allure.step("Signing in with an admin user account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with check, allure.step("Clicking on the delete revision button for the only available "
                                "revision and verifying that the correct 'Unable to delete the "
                                "revision' page header"):
            self.sumo_pages.kb_article_show_history_page._click_on_delete_revision_button(
                revision_id
            )
            assert (self.sumo_pages.kb_article_show_history_page
                    ._get_unable_to_delete_revision_header(
                    ) == KBArticleRevision.KB_REVISION_CANNOT_DELETE_ONLY_REVISION_HEADER)

        with check, allure.step("Verifying that the correct 'Unable to delete the revision' page "
                                "sub-header is displayed"):
            assert (self.sumo_pages.kb_article_show_history_page
                    ._get_unable_to_delete_revision_subheader() == KBArticleRevision.
                    KB_REVISION_CANNOT_DELETE_ONLY_REVISION_SUBHEADER)

        with allure.step("Clicking on the 'Go back to document history button' and verifying "
                         "that we are redirected to the document history page"):
            self.sumo_pages.kb_article_show_history_page._click_go_back_to_document_history_option(
            )
            expect(
                self.page
            ).to_have_url(
                KBArticlePageMessages.KB_ARTICLE_PAGE_URL + article_details
                ['article_slug'] + KBArticlePageMessages.KB_ARTICLE_HISTORY_URL_ENDPOINT
            )

        with allure.step("Clicking on the 'Delete article' button, canceling the confirmation "
                         "modal and verifying that we are back on the show history page for the "
                         "article"):
            self.sumo_pages.kb_article_show_history_page._click_on_delete_this_document_button()
            self.sumo_pages.kb_article_show_history_page._click_on_confirmation_cancel_button()
            expect(
                self.page
            ).to_have_url(
                KBArticlePageMessages.KB_ARTICLE_PAGE_URL + article_details
                ['article_slug'] + KBArticlePageMessages.KB_ARTICLE_HISTORY_URL_ENDPOINT
            )

        with check, allure.step("Deleting the article, navigating to the article and verifying "
                                "that the article was successfully deleted"):
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()
            with self.page.expect_navigation() as navigation_info:
                self.navigate_to_link(
                    KBArticlePageMessages.
                    KB_ARTICLE_PAGE_URL + article_details['article_slug'] + "/"
                )
            response = navigation_info.value
            assert response.status == 404

    # C2490047, C2490048
    @pytest.mark.kbArticleShowHistory
    def test_kb_article_category_link_and_header(self):
        with allure.step("Signing in with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        for category in self.general_test_data["kb_article_categories"]:

            if category != "Templates":
                with allure.step("Creating a new article"):
                    article_info = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                        article_category=category
                    )
            else:
                with allure.step("Creating a new template article"):
                    article_info = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                        article_category=category,
                        is_template=True
                    )

            with check, allure.step("Verifying that the correct page header is displayed"):
                assert self.sumo_pages.kb_article_show_history_page._get_show_history_page_title(
                ) == KBArticleShowHistoryPageMessages.PAGE_TITLE + article_info["article_title"]

            with check, allure.step("Verifying that the correct category is displayed inside the "
                                    "'Show History' page"):
                assert (self.sumo_pages.kb_article_show_history_page
                        ._get_show_history_category_text() == category)

            with check, allure.step("Verifying that the correct revision history for locale is "
                                    "displayed"):
                assert (self.sumo_pages.
                        kb_article_show_history_page._get_show_history_revision_for_locale_text(
                        ) == KBArticleShowHistoryPageMessages.DEFAULT_REVISION_FOR_LOCALE)

            with allure.step("Clicking on the 'Category' link and verifying that the user is "
                             "redirected to the correct page"):
                self.sumo_pages.kb_article_show_history_page._click_on_show_history_category()
                expect(
                    self.page
                ).to_have_url(self.different_endpoints['kb_categories_links'][category])

            with allure.step("Navigating back and deleting the article"):
                self.navigate_back()
                self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2101637, C2489543, C2102169
    @pytest.mark.kbArticleShowHistory
    def test_kb_article_contributor_removal(self):
        with allure.step("Signing in with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        username_one = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        with allure.step("Create a new simple article"):
            self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        article_url = self.get_page_url()

        with allure.step("Verifying that no users are added inside the contributors list"):
            expect(
                self.sumo_pages.kb_article_show_history_page._get_all_contributors_locator()
            ).to_be_hidden()

        with check, allure.step("Clicking on the Article menu option and verifying that the user "
                                "is not displayed inside the article contributors section"):
            self.sumo_pages.kb_article_page._click_on_article_option()
            assert (username_one not in self.sumo_pages.kb_article_page
                    ._get_list_of_kb_article_contributors())

        with allure.step("Navigating back to the 'Show History page and approving the revision"):
            self.sumo_pages.kb_article_page._click_on_show_history_option()
            revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()
            self.sumo_pages.kb_article_revision_flow.approve_kb_revision(revision_id)

        with check, allure.step("Verifying that the username which created the revision is added "
                                "inside the 'Contributors' list"):
            assert (username_one in self.sumo_pages.kb_article_show_history_page
                    ._get_list_of_all_contributors())

        self.logger.info("Fetching the contributor id")
        self.sumo_pages.kb_article_show_history_page._click_on_edit_contributors_option()
        (self.sumo_pages.kb_article_show_history_page.
         _click_on_delete_button_for_a_particular_contributor(username_one))
        deletion_link = self.get_page_url()

        with check, allure.step("Navigating back by hitting the cancel button. clicking on the "
                                "Article menu option and verifying that the user is displayed "
                                "inside the article contributors section"):
            (self.sumo_pages.kb_article_show_history_page.
             _click_on_delete_contributor_confirmation_page_cancel_button())
            self.sumo_pages.kb_article_page._click_on_article_option()
            assert (username_one in self.sumo_pages.kb_article_page
                    ._get_list_of_kb_article_contributors())

        with allure.step("Navigating back to the 'Show History page' and signing in with a "
                         "non-admin account"):
            self.sumo_pages.kb_article_page._click_on_show_history_option()
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))

        username_two = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        with allure.step("Creating a new revision for the document and verifying that the 'Edit "
                         "Contributors' option is not displayed for users which don't have the "
                         "necessary permissions"):
            second_revision_info = self.sumo_pages.kb_article_revision_flow.submit_new_kb_revision(
            )
            expect(
                self.sumo_pages.kb_article_show_history_page._get_edit_contributors_option_locator(
                )).to_be_hidden()

        with check, allure.step("Manually navigating to the deletion link and verifying that 403 "
                                "is returned"):
            with self.page.expect_navigation() as navigation_info:
                self.navigate_to_link(
                    deletion_link
                )
            response = navigation_info.value
            assert response.status == 403

        with check, allure.step("Navigating back, clicking on the Article menu and verifying "
                                "that the user is not displayed inside the article contributors "
                                "section"):
            self.navigate_to_link(article_url)
            self.sumo_pages.kb_article_page._click_on_article_option()
            assert (username_two not in self.sumo_pages.kb_article_page.
                    _get_list_of_kb_article_contributors())

        with allure.step("Navigating back to the 'Show History page', deleting the user session "
                         "and verifying that the 'Edit Contributors' options is not displayed"):
            self.sumo_pages.kb_article_page._click_on_show_history_option()
            self.delete_cookies()
            expect(
                self.sumo_pages.kb_article_show_history_page._get_edit_contributors_option_locator(
                )).to_be_hidden()

        with check, allure.step("Manually navigating to the deletion link and the user is "
                                "redirected to the auth page"):
            self.navigate_to_link(deletion_link)
            assert FxAPageMessages.AUTH_PAGE_URL in self.get_page_url()

        with check, allure.step("Navigating back, signing in with a non-admin account and "
                                "verifying that the username two is not displayed inside the "
                                "Contributors list"):
            self.navigate_to_link(article_url)
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))
            assert (username_two not in self.sumo_pages.kb_article_show_history_page
                    ._get_list_of_all_contributors())

        with check, allure.step("Approving the revision and verifying that the second username "
                                "is displayed inside the Contributors list"):
            self.sumo_pages.kb_article_revision_flow.approve_kb_revision(
                second_revision_info['revision_id']
            )
            assert (username_two in self.sumo_pages.kb_article_show_history_page
                    ._get_list_of_all_contributors())

        with check, allure.step("Clicking on the Article menu and verifying that the user is "
                                "displayed inside the article contributors section"):
            self.sumo_pages.kb_article_page._click_on_article_option()
            assert (username_one in self.sumo_pages.kb_article_page
                    ._get_list_of_kb_article_contributors())

        with allure.step("Clicking on the delete button for user two"):
            self.sumo_pages.kb_article_page._click_on_show_history_option()
            self.sumo_pages.kb_article_show_history_page._click_on_edit_contributors_option()
            (self.sumo_pages.kb_article_show_history_page.
             _click_on_delete_button_for_a_particular_contributor(username_two))

        with check, allure.step("Verifying that the correct delete contributor page header is "
                                "displayed"):
            assert (self.sumo_pages.kb_article_show_history_page
                    ._get_delete_contributor_confirmation_page_header() == self
                    .get_remove_contributor_page_header(username_two))

        with check, allure.step("Clicking on the 'Cancel' button and verifying that the second "
                                "username is displayed inside the Contributors list"):
            (self.sumo_pages.kb_article_show_history_page.
             _click_on_delete_contributor_confirmation_page_cancel_button())
            assert (username_two in self.sumo_pages.kb_article_show_history_page
                    ._get_list_of_all_contributors())

        with check, allure.step("Clicking on the Article menu option and verifying that the user "
                                "is displayed inside the article contributors section"):
            self.sumo_pages.kb_article_page._click_on_article_option()
            assert (username_one in self.sumo_pages.kb_article_page
                    ._get_list_of_kb_article_contributors())

        with allure.step("Navigating back to the 'Show History' page and deleting the the second "
                         "contributor"):
            self.sumo_pages.kb_article_page._click_on_show_history_option()
            self.sumo_pages.kb_article_show_history_page._click_on_edit_contributors_option()
            (self.sumo_pages.kb_article_show_history_page.
             _click_on_delete_button_for_a_particular_contributor(username_two))
            (self.sumo_pages.kb_article_show_history_page.
             _click_on_delete_contributor_confirmation_page_confirm_button())

        with check, allure.step("Verifying that the correct banner is displayed"):
            assert self.sumo_pages.kb_article_show_history_page._get_show_history_page_banner(
            ) == super().get_contributor_removed_message(username_two)

        with check, allure.step("Verifying that second username is not displayed inside the "
                                "'Contributors' list"):
            assert (username_two not in self.sumo_pages.kb_article_show_history_page
                    ._get_list_of_all_contributors())

        with check, allure.step("Clicking on the Article menu and verifying that the user is not "
                                "displayed inside the contributors section"):
            self.sumo_pages.kb_article_page._click_on_article_option()
            assert (username_two not in self.sumo_pages.kb_article_page
                    ._get_list_of_kb_article_contributors())

        with allure.step("Deleting the article"):
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2101638
    @pytest.mark.kbArticleShowHistory
    def test_contributors_can_be_manually_added(self):
        with allure.step("Signing in with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        with allure.step("Creating a new simple article"):
            self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        with allure.step("Clicking on the 'Edit Contributors' option, adding and selecting the "
                         "username from the search field"):
            self.sumo_pages.kb_article_show_history_page._click_on_edit_contributors_option()
            new_contributor = super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            )
            (self.sumo_pages.kb_article_show_history_page.
             _add_a_new_contributor_inside_the_contributor_field(new_contributor))
            (self.sumo_pages.kb_article_show_history_page.
             _click_on_new_contributor_search_result(new_contributor))

        with check, allure.step("Clicking on the 'Add Contributor' option and verifying that the "
                                "correct banner is displayed"):
            self.sumo_pages.kb_article_show_history_page._click_on_add_contributor_button()
            assert self.sumo_pages.kb_article_show_history_page._get_show_history_page_banner(
            ) == super().get_contributor_added_message(new_contributor)

        with check, allure.step("Verifying that the user was successfully added inside the "
                                "contributors list"):
            assert (new_contributor in self.sumo_pages.kb_article_show_history_page
                    ._get_list_of_all_contributors())

        with check, allure.step("Clicking on the Article menu option and verifying that the user "
                                "is displayed inside the article contributors section"):
            self.sumo_pages.kb_article_page._click_on_article_option()
            assert (new_contributor in self.sumo_pages.kb_article_page
                    ._get_list_of_kb_article_contributors())

        with allure.step("Deleting the created article"):
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2101634, C2489553, C2102186
    @pytest.mark.kbArticleShowHistory
    def test_kb_article_contributor_profile_access(self):
        with allure.step("Signing in with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        self.sumo_pages.top_navbar._get_text_of_logged_in_username()

        with allure.step("Create a new simple article"):
            self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        self.sumo_pages.kb_article_page._click_on_article_option()
        article_url = self.get_page_url()

        with allure.step("Approving the article revision"):
            self.sumo_pages.kb_article_page._click_on_show_history_option()

            revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()

            self.sumo_pages.kb_article_revision_flow.approve_kb_revision(revision_id)

        with allure.step("Signing in with a non-Admin account amd creating a new revision"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))

            username_two = self.sumo_pages.top_navbar._get_text_of_logged_in_username()

            second_revision_info = self.sumo_pages.kb_article_revision_flow.submit_new_kb_revision(
            )

        with allure.step("Signing in with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Approving the revision and deleting the user session"):
            self.sumo_pages.kb_article_revision_flow.approve_kb_revision(
                second_revision_info['revision_id']
            )
            self.delete_cookies()

        with allure.step("Clicking on the second contributor and verifying that we are "
                         "redirected to it's profile page"):
            (self.sumo_pages.kb_article_show_history_page._click_on_a_particular_contributor
             (username_two)
             )
            expect(
                self.page
            ).to_have_url(MyProfileMessages.get_my_profile_stage_url(username_two))

        with allure.step("Navigating back, clicking on the revision editor and verifying that we "
                         "are redirected to the editor homepage"):
            self.navigate_back()
            self.sumo_pages.kb_article_show_history_page._click_on_a_particular_revision_editor(
                second_revision_info['revision_id'], username_two
            )
            expect(
                self.page
            ).to_have_url(MyProfileMessages.get_my_profile_stage_url(username_two))

        with allure.step("Navigating back to the article main menu"):
            self.navigate_to_link(
                article_url
            )

        with allure.step("Clicking on the contributor listed inside the article page and "
                         "verifying that we are redirected to the editor homepage"):
            self.sumo_pages.kb_article_page._click_on_a_particular_article_contributor(
                username_two
            )
            expect(
                self.page
            ).to_have_url(MyProfileMessages.get_my_profile_stage_url(username_two))

        with allure.step("Navigating back and signin in with an admin account"):
            self.navigate_back()
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Clicking on the Article menu option, clicking on the contributor "
                         "listed inside the article page and verifying that we are redirected to "
                         "the editor homepage"):
            self.sumo_pages.kb_article_page._click_on_article_option()
            self.sumo_pages.kb_article_page._click_on_a_particular_article_contributor(
                username_two
            )
            expect(
                self.page
            ).to_have_url(MyProfileMessages.get_my_profile_stage_url(username_two))

        with allure.step("Navigating back to the article history, clicking on the second "
                         "contributor and verifying that we are redirected to it's profile page"):
            self.navigate_back()
            self.sumo_pages.kb_article_page._click_on_show_history_option()
            (self.sumo_pages.kb_article_show_history_page._click_on_a_particular_contributor
             (username_two)
             )
            expect(
                self.page
            ).to_have_url(MyProfileMessages.get_my_profile_stage_url(username_two))

        with allure.step("Navigating back and clicking on the revision editor"):
            self.navigate_back()
            self.sumo_pages.kb_article_show_history_page._click_on_a_particular_revision_editor(
                second_revision_info['revision_id'], username_two
            )

        with allure.step("Verifying that we are redirected to the editor homepage"):
            expect(
                self.page
            ).to_have_url(MyProfileMessages.get_my_profile_stage_url(username_two))

        with allure.step("Navigating back and deleting the created article"):
            self.navigate_back()
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2499415
    @pytest.mark.kbArticleShowHistory
    def test_kb_article_revision_date_functionality(self):
        with allure.step("Signing in with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))
        main_user = super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        )

        with allure.step("Create a new simple article, clicking on the 'Show History' option and "
                         "approving the revision"):
            self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()
            self.sumo_pages.kb_article_page._click_on_article_option()
            article_url = self.get_page_url()
            self.sumo_pages.kb_article_page._click_on_show_history_option()
            revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()
            self.sumo_pages.kb_article_revision_flow.approve_kb_revision(revision_id)

        with allure.step("Signing in with a non-admin account"):
            creator_username = self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_12']
            ))

        with allure.step("Submitting a new revision"):
            second_revision_info = self.sumo_pages.kb_article_revision_flow.submit_new_kb_revision(
            )

        with allure.step("Deleting the user session and clicking on the first revision"):
            self.delete_cookies()
            revision_time = self.sumo_pages.kb_article_show_history_page._get_revision_time(
                second_revision_info['revision_id']
            )
            self.sumo_pages.kb_article_show_history_page._click_on_a_revision_date(revision_id)

        with check, allure.step("Verifying that the correct 'Is current revision?' text is "
                                "displayed"):
            assert self.sumo_pages.kb_article_preview_revision_page._get_is_current_revision_text(
            ) == KBArticleRevision.KB_ARTICLE_REVISION_YES_STATUS

        with allure.step("Navigating back and clicking on the revision time"):
            self.navigate_back()
            self.sumo_pages.kb_article_show_history_page._click_on_a_revision_date(
                second_revision_info['revision_id']
            )

        with allure.step("Verifying that the revision information content is expanded by default"):
            expect(
                self.sumo_pages.kb_article_preview_revision_page.
                _get_revision_information_content_locator()
            ).to_be_visible()

        with allure.step("Clicking on the 'Revision Information' foldout section and Verifying "
                         "that the revision information content is collapsed/no longer displayed"):
            (self.sumo_pages.kb_article_preview_revision_page.
             _click_on_revision_information_foldout_section())
            expect(
                self.sumo_pages.kb_article_preview_revision_page.
                _get_revision_information_content_locator()
            ).to_be_hidden()

        with allure.step("Clicking on the 'Revision Information' foldout section"):
            (self.sumo_pages.kb_article_preview_revision_page.
             _click_on_revision_information_foldout_section())

        with allure.step("Verifying that the revision information content is displayed"):
            expect(
                self.sumo_pages.kb_article_preview_revision_page.
                _get_revision_information_content_locator()
            ).to_be_visible()

        with check, allure.step("Verifying that the revision id is the correct one"):
            assert self.sumo_pages.kb_article_preview_revision_page._get_preview_revision_id_text(
            ) == str(self.number_extraction_from_string(second_revision_info['revision_id']))

        with check, allure.step("Verifying that the correct revision time is displayed"):
            assert (self.sumo_pages.kb_article_preview_revision_page
                    ._get_preview_revision_created_date_text() == revision_time)

        with check, allure.step("Verifying that the correct creator is displayed"):
            assert (self.sumo_pages.kb_article_preview_revision_page
                    ._get_preview_revision_creator_text() == creator_username)

        with allure.step("Clicking on the creator link and verifying that we are redirected to "
                         "the username page"):
            self.sumo_pages.kb_article_preview_revision_page._click_on_creator_link()
            expect(
                self.page
            ).to_have_url(MyProfileMessages.get_my_profile_stage_url(creator_username))

        with check, allure.step("Navigating back to the revision preview page and verifying that "
                                "the correct review comment is displayed"):
            self.navigate_back()
            assert (self.sumo_pages.kb_article_preview_revision_page
                    ._get_preview_revision_comment_text() == self
                    .kb_article_test_data['changes_description'])

        with check, allure.step("Verifying that the correct reviewed status is displayed"):
            assert (self.sumo_pages.kb_article_preview_revision_page
                    ._get_preview_revision_reviewed_text() == KBArticleRevision.
                    KB_ARTICLE_REVISION_NO_STATUS)

        with allure.step("Verifying that the reviewed by locator is hidden"):
            expect(
                self.sumo_pages.kb_article_preview_revision_page._get_reviewed_by_locator()
            ).to_be_hidden()

        with allure.step("Verifying that the is approved locator is hidden"):
            expect(
                self.sumo_pages.kb_article_preview_revision_page._get_is_approved_text_locator()
            ).to_be_hidden()

        with allure.step("Verifying that the is current revision locator is hidden"):
            expect(
                self.sumo_pages.kb_article_preview_revision_page._is_current_revision_locator()
            ).to_be_hidden()

        with check, allure.step("Verifying that the correct ready for localization locator is "
                                "displayed"):
            assert (self.sumo_pages.kb_article_preview_revision_page
                    ._get_preview_revision_ready_for_localization_text() == KBArticleRevision.
                    KB_ARTICLE_REVISION_NO_STATUS)

        with allure.step("Verifying that the readied for localization by is hidden"):
            expect(
                self.sumo_pages.kb_article_preview_revision_page
                ._readied_for_localization_by_locator()
            ).to_be_hidden()

        with allure.step("Verifying that the 'Edit article based on this revision' is not "
                         "displayed"):
            expect(
                self.sumo_pages.kb_article_preview_revision_page.
                _get_edit_article_based_on_this_revision_link_locator()
            ).to_be_hidden()

        with allure.step("Verifying that the 'Revision Source' section is hidden by default"):
            expect(
                self.sumo_pages.kb_article_preview_revision_page.
                _get_preview_revision_source_textarea_locator()
            ).to_be_hidden()

        with check, allure.step("Clicking on the 'Revision Source' foldout section option and "
                                "verifying that the 'Revision Source' textarea contains the "
                                "correct details"):
            (self.sumo_pages.kb_article_preview_revision_page.
             _click_on_revision_source_foldout_section())
            assert (self.sumo_pages.kb_article_preview_revision_page
                    ._get_preview_revision_source_textarea_content() == self.
                    kb_article_test_data['updated_article_content'])

        with allure.step("Verifying that the 'Revision Content' section is hidden by default"):
            expect(
                self.sumo_pages.kb_article_preview_revision_page
                ._get_revision_content_html_locator()
            ).to_be_hidden()

        with allure.step("Clicking on the 'Revision Content' foldout option and verifying that "
                         "the 'Revision Content' section is visible"):
            (self.sumo_pages.kb_article_preview_revision_page.
             _click_on_revision_content_foldout_section())
            expect(
                self.sumo_pages.kb_article_preview_revision_page
                ._get_revision_content_html_locator()
            ).to_be_visible()

        with allure.step("Signing in with an admin account and approving the revision"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Clicking on show history option and approving the second revision"):
            self.sumo_pages.kb_article_page._click_on_show_history_option()
            self.sumo_pages.kb_article_revision_flow.approve_kb_revision(
                second_revision_info['revision_id'], ready_for_l10n=True)

        with check, allure.step("Deleting the user session, clicking on the revision time and "
                                "verifying that the correct reviewed status is displayed"):
            self.delete_cookies()
            self.sumo_pages.kb_article_show_history_page._click_on_a_revision_date(
                second_revision_info['revision_id']
            )
            assert (self.sumo_pages.kb_article_preview_revision_page
                    ._get_preview_revision_reviewed_text() == KBArticleRevision
                    .KB_ARTICLE_REVISION_YES_STATUS)

        with allure.step("Verifying that the reviewed by date is displayed"):
            expect(
                self.sumo_pages.kb_article_preview_revision_page.
                _get_preview_revision_reviewed_date_locator()
            ).to_be_visible()

        with check, allure.step("Verifying that the correct 'Reviewed by' text is displayed"):
            assert self.sumo_pages.kb_article_preview_revision_page._get_reviewed_by_text(
            ) == main_user

        with check, allure.step("Verifying that the correct is approved status displayed"):
            assert self.sumo_pages.kb_article_preview_revision_page._get_is_approved_text(
            ) == KBArticleRevision.KB_ARTICLE_REVISION_YES_STATUS

        with check, allure.step("Verifying that the correct is current revision status displayed"):
            assert self.sumo_pages.kb_article_preview_revision_page._get_is_current_revision_text(
            ) == KBArticleRevision.KB_ARTICLE_REVISION_YES_STATUS

        with check, allure.step("Verifying that the correct is ready for localization status "
                                "displayed"):
            assert (self.sumo_pages.kb_article_preview_revision_page
                    ._get_preview_revision_ready_for_localization_text() == KBArticleRevision.
                    KB_ARTICLE_REVISION_YES_STATUS)

        with allure.step("Verifying that the 'Readied for localization' date is displayed"):
            expect(
                self.sumo_pages.kb_article_preview_revision_page._ready_for_localization_date()
            ).to_be_visible()

        with check, allure.step("Verifying that the correct localization by text is displayed"):
            assert (self.sumo_pages.kb_article_preview_revision_page
                    ._readied_for_localization_by_text() == main_user)

        with allure.step("Signing in with an admin account and deleting the article"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Clicking on the 'Edit article based on this revision option' and "
                         "verifying that the correct link is displayed"):
            (self.sumo_pages.kb_article_preview_revision_page.
             _click_on_edit_article_based_on_this_revision_link())
            expect(
                self.page
            ).to_have_url(
                article_url + QuestionPageMessages.EDIT_QUESTION_URL_ENDPOINT + "/" + str(
                    self.number_extraction_from_string(second_revision_info['revision_id']))
            )

        with allure.step("Deleting the created article"):
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()
