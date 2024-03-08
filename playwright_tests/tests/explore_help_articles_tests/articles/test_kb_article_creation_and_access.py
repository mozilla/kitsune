import allure
from pytest_check import check
import pytest
import re
from playwright.sync_api import expect
from playwright_tests.core.testutilities import TestUtilities
from playwright_tests.messages.auth_pages_messages.fxa_page_messages import FxAPageMessages
from playwright_tests.messages.explore_help_articles.kb_article_page_messages import (
    KBArticlePageMessages)
from playwright_tests.messages.explore_help_articles.kb_article_revision_page_messages import (
    KBArticleRevision)


class TestKBArticleCreationAndAccess(TestUtilities, KBArticleRevision):

    # C891308, C2081444
    @pytest.mark.kbArticleCreationAndAccess
    def test_non_admin_users_kb_article_submission(self):
        with allure.step("Signing in with a non-Admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))

        with allure.step("Create a new simple article"):
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        with allure.step("Verifying that the user is redirected to the article's show history "
                         "page after submission"):
            expect(
                self.page
            ).to_have_url(
                KBArticlePageMessages.KB_ARTICLE_PAGE_URL + article_details
                ['article_slug'] + KBArticlePageMessages.KB_ARTICLE_HISTORY_URL_ENDPOINT)

        with check, allure.step("Verifying that the revision contains the correct status"):
            status = self.sumo_pages.kb_article_show_history_page._get_revision_status(
                self.sumo_pages.kb_article_show_history_page._get_last_revision_id()
            )
            assert KBArticlePageMessages.UNREVIEWED_REVISION_STATUS == status

        with check, allure.step("Clicking on the 'Article' navbar menu and verifying that the "
                                "doc content contains the correct string"):
            self.sumo_pages.kb_article_page._click_on_article_option()
            assert self.sumo_pages.kb_article_page._get_text_of_kb_article_content(
            ) == KBArticlePageMessages.KB_ARTICLE_NOT_APPROVED_CONTENT

        with check, allure.step("Deleting user session and verifying that the 404 page is "
                                "received"):
            with self.page.expect_navigation() as navigation_info:
                self.delete_cookies()
            response = navigation_info.value
            assert response.status == 404

        with allure.step("Signing in with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with check, allure.step("Clicking on the 'Show History' option and verifying that the "
                                "revision contains the correct status"):
            self.sumo_pages.kb_article_page._click_on_show_history_option()
            status = (
                self.sumo_pages.kb_article_show_history_page._get_status_of_reviewable_revision(
                    self.sumo_pages.kb_article_show_history_page._get_last_revision_id()))
            assert KBArticlePageMessages.REVIEW_REVISION_STATUS == status

        with allure.step("Deleting the created article"):
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2081446, # C2081447
    @pytest.mark.kbArticleCreationAndAccess
    def test_articles_revision_page_and_revision_approval(self):
        with allure.step("Signing in with a non-admin account"):
            username = self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))

        with allure.step("Create a new simple article"):
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        with allure.step("Signing in with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with check, allure.step("Clicking on the first review and verifying that the correct "
                                "revision header is displayed"):
            self.sumo_pages.kb_article_page._click_on_show_history_option()
            revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()
            self.logger.info("Clicking on the 'Review' option")
            self.sumo_pages.kb_article_show_history_page._click_on_review_revision(
                revision_id
            )
            assert self.sumo_pages.kb_article_review_revision_page._get_revision_header(
            ) == KBArticleRevision.KB_ARTICLE_REVISION_HEADER + article_details['article_title']

        with check, allure.step("Verifying that the correct subtext is displayed"):
            assert (self.sumo_pages.kb_article_review_revision_page._get_reviewing_revision_text()
                    .replace("\n", "").strip() == self.get_kb_article_revision_details(
                    revision_id=re.findall(r'\d+', revision_id)[0],
                    username=username,
                    revision_comment=article_details['article_review_description']
                    ).strip())

        with allure.step("Click on the 'Back to History' option and verifying that the user is "
                         "redirected to the article history page"):
            self.sumo_pages.kb_article_review_revision_page._click_on_back_to_history_option()
            expect(
                self.page
            ).to_have_url(
                KBArticlePageMessages.KB_ARTICLE_PAGE_URL + article_details
                ['article_slug'] + KBArticlePageMessages.KB_ARTICLE_HISTORY_URL_ENDPOINT
            )

        with check, allure.step("Navigate back and verifying that the 'Keywords:' header is "
                                "displayed"):
            self.navigate_back()
            assert self.sumo_pages.kb_article_review_revision_page._is_keywords_header_visible()

        with check, allure.step("Verifying that the correct keyword is displayed"):
            assert self.sumo_pages.kb_article_review_revision_page._get_keywords_content(
            ) == article_details['keyword']

        with check, allure.step("Verifying that the correct header is displayed"):
            assert (self.sumo_pages.kb_article_review_revision_page
                    ._is_search_results_summary_visible())

        with check, allure.step("Verifying that the correct search result summary is displayed"):
            assert (self.sumo_pages.kb_article_review_revision_page
                    ._get_search_results_summary_content(
                    ) == article_details['search_results_summary'])

        with check, allure.step("Verifying that the 'Revision source:' header is displayed"):
            assert self.sumo_pages.kb_article_review_revision_page._is_revision_source_visible()

        with check, allure.step("Verifying that the correct revision source content is displayed"):
            assert self.sumo_pages.kb_article_review_revision_page._revision_source_content(
            ) == article_details['article_content']

        with check, allure.step("Verifying that the correct header is displayed"):
            assert (self.sumo_pages.kb_article_review_revision_page
                    ._is_revision_rendered_html_header_visible())

        with check, allure.step("Verifying that the correct 'Revision rendered html:' content is "
                                "displayed"):
            assert (self.sumo_pages.kb_article_review_revision_page
                    ._get_revision_rendered_html_content(
                    ) == article_details['article_content_html'])

        with allure.step("Approving the revision"):
            self.sumo_pages.kb_article_review_revision_page._click_on_approve_revision_button()
            self.sumo_pages.kb_article_review_revision_page._click_accept_revision_accept_button()

        with check, allure.step("Verifying that the review status updates to 'Current'"):
            assert self.sumo_pages.kb_article_show_history_page._get_revision_status(
                revision_id
            ) == KBArticlePageMessages.CURRENT_REVISION_STATUS

        with allure.step("Clicking on the 'Article' editing tools option"):
            self.sumo_pages.kb_article_page._click_on_article_option()

        with check, allure.step("Verifying that the correct html article content is displayed"):
            assert self.sumo_pages.kb_article_page._get_text_of_kb_article_content_approved(
            ) == article_details['article_content_html']

        with check, allure.step("Signing out and verifying that the correct article content is "
                                "displayed"):
            self.delete_cookies()
            assert self.sumo_pages.kb_article_page._get_text_of_kb_article_content_approved(
            ) == article_details['article_content_html']

        with check, allure.step("Signing in with a non admin account and verifying if the "
                                "correct content is displayed"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_13"]
            ))
            assert self.sumo_pages.kb_article_page._get_text_of_kb_article_content_approved(
            ) == article_details['article_content_html']

        with allure.step("Signing in with an admin account and deleting the article"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2091580, C954321
    @pytest.mark.kbArticleCreationAndAccess
    def test_articles_discussions_allowed(self):
        with allure.step("Signing in with a non-admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))

        with allure.step("Create a new simple article"):
            self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        with allure.step("Clicking on the article option and posting a new article thread"):
            self.sumo_pages.kb_article_page._click_on_article_option()
            article_url = self.get_page_url()
            self.sumo_pages.kb_article_page._click_on_editing_tools_discussion_option()
            self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()
            thread_info = (self.sumo_pages.post_kb_discussion_thread_flow.
                           add_new_kb_discussion_thread())

        with allure.step("Manually navigating to the discuss endpoint"):
            self.navigate_to_link(
                article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
            )

        with allure.step("Verifying that the posted thread is successfully displayed"):
            expect(
                self.sumo_pages.kb_article_discussion_page._get_posted_thread_locator(
                    thread_info['thread_id']
                )
            ).to_be_visible()

        with allure.step("Navigating to the article page"):
            self.navigate_to_link(article_url)
            expect(
                self.page
            ).to_have_url(article_url)

        with allure.step("Signing in with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Approving the article revision"):
            self.sumo_pages.kb_article_page._click_on_show_history_option()
            revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()
            self.sumo_pages.kb_article_revision_flow.approve_kb_revision(revision_id)

        with allure.step("Navigating to the article page"):
            self.navigate_to_link(article_url)
            expect(
                self.page
            ).to_have_url(article_url)

        with allure.step("Deleting user session and verifying that the discussion editing tools "
                         "option is not available"):
            self.delete_cookies()
            expect(
                self.sumo_pages.kb_article_page._editing_tools_discussion_locator()
            ).to_be_hidden()

        with allure.step("Manually navigating to the discuss endpoint and verifying that the "
                         "posted thread is successfully displayed"):
            self.navigate_to_link(
                article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
            )
            expect(
                self.sumo_pages.kb_article_discussion_page._get_posted_thread_locator(
                    thread_info['thread_id']
                )
            ).to_be_visible()

        with allure.step("Manually navigating to the discuss endpoint"):
            self.navigate_to_link(
                article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
            )

        with allure.step("Clicking on the 'Post a new thread' option and verifying that the user "
                         "is redirected to the auth page"):
            self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()
            assert (
                FxAPageMessages.AUTH_PAGE_URL in self.get_page_url()
            )

        with allure.step("Signing in with a different account and posting a new kb article "
                         "discussion thread"):
            self.sumo_pages.auth_flow_page.sign_in_flow(
                username=super().user_special_chars,
                account_password=super().user_secrets_pass,
            )
            thread_info = (self.sumo_pages.post_kb_discussion_thread_flow.
                           add_new_kb_discussion_thread())

        with allure.step("Manually navigating to the discuss endpoint and verifying that the "
                         "posted thread is successfully displayed"):
            self.navigate_to_link(
                article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
            )
            expect(
                self.sumo_pages.kb_article_discussion_page._get_posted_thread_locator(
                    thread_info['thread_id']
                )
            ).to_be_visible()

        with allure.step("Signing in with an admin account and deleting the article"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))
            self.navigate_to_link(article_url)
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2091581
    @pytest.mark.kbArticleCreationAndAccess
    def test_articles_discussions_not_allowed(self):
        with allure.step("Signing in with a non-admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))

        with allure.step("Create a new simple article"):
            self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(allow_discussion=False)

        with allure.step("Clicking on the article option and verifying that the 'Discussion' "
                         "option is not displayed"):
            self.sumo_pages.kb_article_page._click_on_article_option()
            article_url = self.get_page_url()
            expect(
                self.sumo_pages.kb_article_page._editing_tools_discussion_locator()
            ).to_be_hidden()

        with check, allure.step("Manually navigating to the 'Discuss' endpoint and verifying "
                                "that the 404 is displayed"):
            with self.page.expect_navigation() as navigation_info:
                self.navigate_to_link(
                    article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
                )
            response = navigation_info.value
            assert response.status == 404

        with allure.step("Navigating back to the article page and signing in with admin"):
            self.navigate_to_link(article_url)
            expect(
                self.page
            ).to_have_url(article_url)
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Approving the revision"):
            self.sumo_pages.kb_article_page._click_on_show_history_option()
            revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()
            self.sumo_pages.kb_article_revision_flow.approve_kb_revision(revision_id)

        with allure.step("Navigating back to the article page and verifying that the "
                         "'Discussion' option is not displayed"):
            self.navigate_to_link(article_url)
            expect(
                self.sumo_pages.kb_article_page._editing_tools_discussion_locator()
            ).to_be_hidden()

        with check, allure.step("Manually navigating to the 'Discuss' endpoint and verifying "
                                "that the 404 page is returned"):
            with self.page.expect_navigation() as navigation_info:
                self.navigate_to_link(
                    article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
                )
            response = navigation_info.value
            assert response.status == 404

        with allure.step("Navigating back and deleting the user session"):
            self.navigate_to_link(article_url)
            expect(
                self.page
            ).to_have_url(article_url)
            self.delete_cookies()

        with allure.step("Verifying that the 'Discussion' option is not displayed"):
            expect(
                self.sumo_pages.kb_article_page._editing_tools_discussion_locator()
            ).to_be_hidden()

        with check, allure.step("Manually navigating to the 'Discuss' endpoint and verifying "
                                "that the 404 page is displayed"):
            with self.page.expect_navigation() as navigation_info:
                self.navigate_to_link(
                    article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
                )
            response = navigation_info.value
            assert response.status == 404

        with allure.step("Navigating back to the article page and deleting the article"):
            self.navigate_to_link(article_url)
            expect(
                self.page
            ).to_have_url(article_url)
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2091665
    @pytest.mark.kbArticleCreationAndAccess
    def test_kb_article_title_and_slug_validations(self):
        with allure.step("Signing in with a non-admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Create a new simple article"):
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        with check, allure.step("Verifying that the article slug was pre-populated successfully"):
            assert article_details['article_slug'] == self.create_slug_from_title(
                article_details['article_title'])

        with allure.step("Navigating to the create kb article form and submitting the form "
                         "without adding a title & slug"):
            self.navigate_to_link(KBArticlePageMessages.CREATE_NEW_KB_ARTICLE_STAGE_URL)
            self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                article_title="",
                article_slug="",
            )

        with allure.step("Verifying that we are on the same page"):
            expect(
                self.page
            ).to_have_url(KBArticlePageMessages.CREATE_NEW_KB_ARTICLE_STAGE_URL)

        with allure.step("Navigating to the create kb article form, submitting the form without "
                         "adding a slug and verifying that we are on the same page"):
            self.navigate_to_link(KBArticlePageMessages.CREATE_NEW_KB_ARTICLE_STAGE_URL)
            self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                article_slug="",
            )
            expect(
                self.page
            ).to_have_url(KBArticlePageMessages.CREATE_NEW_KB_ARTICLE_STAGE_URL)

        with allure.step("Navigating to the create kb article form and submitting the form "
                         "without adding a title"):
            self.navigate_to_link(KBArticlePageMessages.CREATE_NEW_KB_ARTICLE_STAGE_URL)
            self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                article_title="",
                article_slug=self.kb_article_test_data['different_slug']
            )

        with allure.step("Verifying that we are on the same page"):
            expect(
                self.page
            ).to_have_url(KBArticlePageMessages.CREATE_NEW_KB_ARTICLE_STAGE_URL)

        with allure.step("Navigating to the create kb article form and adding the same title and "
                         "slug inside article form"):
            self.navigate_to_link(KBArticlePageMessages.CREATE_NEW_KB_ARTICLE_STAGE_URL)
            self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                article_title=article_details['article_title'],
                article_slug=article_details['article_slug'],
                submit_article=False
            )

        # Currently fails due to https://github.com/mozilla/sumo/issues/1641
        # self.logger.info("Verifying that the correct errors are displayed")
        # check.equal(
        #     self.sumo_pages.submit_kb_article_flow.get_kb_title_error_text(),
        #     KBArticlePageMessages.KB_ARTICLE_SUBMISSION_TITLE_ERRORS[0]
        # )
        #
        # check.equal(
        #     self.sumo_pages.submit_kb_article_flow.get_kb_slug_error_text(),
        #     KBArticlePageMessages.KB_ARTICLE_SUBMISSION_TITLE_ERRORS[1]
        # )

        with check, allure.step("Submitting the form and verifying that both title and slug "
                                "errors are displayed"):
            self.sumo_pages.kb_submit_kb_article_form_page._click_on_submit_for_review_button()
            self.sumo_pages.kb_submit_kb_article_form_page._add_text_to_changes_description_field(
                self.kb_article_test_data["changes_description"]
            )
            self.sumo_pages.kb_submit_kb_article_form_page._click_on_changes_submit_button()
            for error in (self.sumo_pages.kb_submit_kb_article_form_page.
                          get_all_kb_errors()):
                assert error in KBArticlePageMessages.KB_ARTICLE_SUBMISSION_TITLE_ERRORS

        with allure.step("Navigate to the kb submission page and adding same title and a "
                         "different slug"):
            self.navigate_to_link(KBArticlePageMessages.CREATE_NEW_KB_ARTICLE_STAGE_URL)
            self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                article_title=article_details['article_title'],
                article_slug=self.kb_article_test_data['different_slug'],
                submit_article=False
            )

        # # Currently fails due to https://github.com/mozilla/sumo/issues/1641
        # self.logger.info("Verifying that the title error is displayed")
        # expect(
        #     self.sumo_pages.kb_submit_kb_article_form_page.get_kb_title_error_locator()
        # ).to_be_visible()
        #
        # self.logger.info("Verifying that the slug error is not displayed")
        # expect(
        #     self.sumo_pages.kb_submit_kb_article_form_page.get_kb_slug_error()
        # ).to_be_hidden()

        with check, allure.step("Submitting the form and verifying that the correct error is "
                                "displayed"):
            self.sumo_pages.kb_submit_kb_article_form_page._click_on_submit_for_review_button()
            self.sumo_pages.kb_submit_kb_article_form_page._add_text_to_changes_description_field(
                self.kb_article_test_data["changes_description"]
            )
            self.sumo_pages.kb_submit_kb_article_form_page._click_on_changes_submit_button()
            assert self.sumo_pages.kb_submit_kb_article_form_page.get_all_kb_errors(
            )[0] == KBArticlePageMessages.KB_ARTICLE_SUBMISSION_TITLE_ERRORS[0]

        with allure.step("Navigate to the kb submission page and adding different title but same "
                         "slug"):
            self.navigate_to_link(KBArticlePageMessages.CREATE_NEW_KB_ARTICLE_STAGE_URL)
            self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                article_slug=article_details['article_slug'],
                submit_article=False
            )

        # # Currently fails due to https://github.com/mozilla/sumo/issues/1641
        # self.logger.info("Verifying that the title error is not displayed")
        # expect(
        #     self.sumo_pages.kb_submit_kb_article_form_page.get_kb_title_error_locator()
        # ).to_be_hidden()
        #
        # self.logger.info("Verifying that the slug error is displayed")
        # expect(
        #     self.sumo_pages.kb_submit_kb_article_form_page.get_kb_slug_error()
        # ).to_be_visible()

        with check, allure.step("Submitting the form and verifying that the correct error "
                                "message is displayed"):
            self.sumo_pages.kb_submit_kb_article_form_page._click_on_submit_for_review_button()
            self.sumo_pages.kb_submit_kb_article_form_page._add_text_to_changes_description_field(
                self.kb_article_test_data["changes_description"]
            )
            self.sumo_pages.kb_submit_kb_article_form_page._click_on_changes_submit_button()
            assert self.sumo_pages.kb_submit_kb_article_form_page.get_all_kb_errors(
            )[0] == KBArticlePageMessages.KB_ARTICLE_SUBMISSION_TITLE_ERRORS[1]

        with allure.step("Deleting the created article"):
            self.navigate_to_link(
                KBArticlePageMessages.KB_ARTICLE_PAGE_URL + article_details
                ['article_slug'] + KBArticlePageMessages.KB_ARTICLE_HISTORY_URL_ENDPOINT)
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2091665
    @pytest.mark.kbArticleCreationAndAccess
    def test_kb_article_relevancy_validations(self):
        with allure.step("Signing in with a non-admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Create a new simple article and verifying that we are on the same page"):
            self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                selected_relevancy=False
            )
            expect(
                self.page
            ).to_have_url(KBArticlePageMessages.CREATE_NEW_KB_ARTICLE_STAGE_URL)

        with check, allure.step("Verifying that the correct error message is displayed"):
            assert self.sumo_pages.kb_submit_kb_article_form_page.get_all_kb_errors(
            )[0] == KBArticlePageMessages.KB_ARTICLE_RELEVANCY_ERROR

    # C2091665
    @pytest.mark.kbArticleCreationAndAccess
    def test_kb_article_topic_validation(self):
        with allure.step("Signing in with a non-admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Create a new simple article and verifying that we are on the same page"):
            self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                selected_topics=False
            )
            expect(
                self.page
            ).to_have_url(KBArticlePageMessages.CREATE_NEW_KB_ARTICLE_STAGE_URL)

        with check, allure.step("Verifying that the correct error message is displayed"):
            assert self.sumo_pages.kb_submit_kb_article_form_page.get_all_kb_errors(
            )[0] == KBArticlePageMessages.KB_ARTICLE_TOPIC_ERROR

    # C2091665
    @pytest.mark.kbArticleCreationAndAccess
    def test_kb_article_summary_and_content_validation(self):
        with allure.step("Signing in with a non-admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Create a new simple article by leaving out the search summary"):
            self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(search_summary="")

        with allure.step("Verifying that we are on the same page"):
            expect(
                self.page
            ).to_have_url(KBArticlePageMessages.CREATE_NEW_KB_ARTICLE_STAGE_URL)

        with allure.step("Create a new simple article by leaving out the article content and "
                         "verifying that we are on the same page"):
            self.navigate_to_link(KBArticlePageMessages.CREATE_NEW_KB_ARTICLE_STAGE_URL)
            self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(article_content="")
            expect(
                self.page
            ).to_have_url(KBArticlePageMessages.CREATE_NEW_KB_ARTICLE_STAGE_URL)

    # C2091583, C2091584
    @pytest.mark.kbArticleCreationAndAccess
    @pytest.mark.parametrize("username", ['admin', 'simple_user', 'no_user'])
    def test_kb_article_keywords_and_summary(self, username):
        with allure.step("Signing in with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Create a new simple article and approving the revision"):
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()
            self.sumo_pages.kb_article_page._click_on_show_history_option()
            revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()
            self.sumo_pages.kb_article_revision_flow.approve_kb_revision(revision_id)

        with allure.step("Clicking on the top navbar sumo nav logo"):
            self.sumo_pages.top_navbar._click_on_sumo_nav_logo()
            self.wait_for_given_timeout(65000)

        if username == 'simple_user':
            with allure.step("Signing in with a non-admin account"):
                self.start_existing_session(super().username_extraction_from_email(
                    self.user_secrets_accounts["TEST_ACCOUNT_12"]
                ))
        elif username == "no_user":
            with allure.step("Deleting user session"):
                self.delete_cookies()

        with allure.step("Typing the article keyword inside the search field and verifying that "
                         "the article is displayed inside the search results"):
            self.sumo_pages.search_page._type_into_searchbar(article_details['keyword'])
            expect(
                self.sumo_pages.search_page._get_locator_of_a_particular_article(
                    article_details['article_title']
                )
            ).to_be_visible()

        with check, allure.step("Verifying that the correct kb summary is displayed inside the "
                                "search results"):
            assert (self.sumo_pages.search_page
                    ._get_search_result_summary_text_of_a_particular_article(
                        article_details['article_title']
                    )) == article_details['search_results_summary']

        with allure.step("Clearing the searchbar, typing the article summary inside the search "
                         "field and verifying that the article is displayed inside the search "
                         "results"):
            self.sumo_pages.search_page._clear_the_searchbar()
            self.sumo_pages.search_page._type_into_searchbar(
                article_details['search_results_summary']
            )
            expect(
                self.sumo_pages.search_page._get_locator_of_a_particular_article(
                    article_details['article_title']
                )
            ).to_be_visible()

        with allure.step("Verifying that the correct kb summary is displayed inside the search "
                         "results"):
            assert (self.sumo_pages.search_page
                    ._get_search_result_summary_text_of_a_particular_article(
                        article_details['article_title'])
                    ) == article_details['search_results_summary']

        with check, allure.step("Clicking on the article and verifying that the user is "
                                "redirected to the kb article"):
            self.sumo_pages.search_page._click_on_a_particular_article(
                article_details['article_title']
            )
            assert self.sumo_pages.kb_article_page._get_text_of_article_title(
            ) == article_details['article_title']

        with allure.step("Deleting the created article"):
            if username != 'admin':
                self.start_existing_session(super().username_extraction_from_email(
                    self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
                ))
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()
