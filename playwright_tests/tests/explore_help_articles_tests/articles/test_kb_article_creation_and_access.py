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


class TestKBArticleCreationAndAccess(TestUtilities, KBArticleRevision, KBArticlePageMessages):

    # C890940, C2243447
    @pytest.mark.kbArticleCreationAndAccess
    @pytest.mark.parametrize("username", ['TEST_ACCOUNT_12', '', 'TEST_ACCOUNT_MODERATOR'])
    def test_kb_editing_tools_visibility(self, username):
        with allure.step("Signing in with an Admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Create a new simple article and approving it"):
            self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                approve_first_revision=True
            )

        with allure.step("Navigating to the Article page"):
            self.sumo_pages.kb_article_page._click_on_article_option()

        if username == 'TEST_ACCOUNT_13':
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_13"]
            ))
            with allure.step("Verifying that only some editing tools options are displayed"):
                expect(
                    self.sumo_pages.kb_article_page._get_article_option_locator()
                ).to_be_visible()

                expect(
                    self.sumo_pages.kb_article_page._editing_tools_discussion_locator()
                ).to_be_visible()

                expect(
                    self.sumo_pages.kb_article_page._get_edit_article_option_locator()
                ).to_be_visible()

                expect(
                    self.sumo_pages.kb_article_page._get_edit_article_metadata_locator()
                ).to_be_hidden()

                expect(
                    self.sumo_pages.kb_article_page._get_translate_article_option_locator()
                ).to_be_visible()

                expect(
                    self.sumo_pages.kb_article_page._get_show_translations_option_locator()
                ).to_be_visible()

                expect(
                    self.sumo_pages.kb_article_page._get_what_links_here_locator()
                ).to_be_visible()

                expect(
                    self.sumo_pages.kb_article_page._get_show_history_option_locator()
                ).to_be_visible()
        elif username == '':
            self.delete_cookies()
            with allure.step("Verifying that all the editing tools options are not displayed"):
                expect(
                    self.sumo_pages.kb_article_page._get_article_option_locator()
                ).to_be_hidden()

                expect(
                    self.sumo_pages.kb_article_page._editing_tools_discussion_locator()
                ).to_be_hidden()

                expect(
                    self.sumo_pages.kb_article_page._get_edit_article_option_locator()
                ).to_be_hidden()

                expect(
                    self.sumo_pages.kb_article_page._get_edit_article_metadata_locator()
                ).to_be_hidden()

                expect(
                    self.sumo_pages.kb_article_page._get_translate_article_option_locator()
                ).to_be_hidden()

                expect(
                    self.sumo_pages.kb_article_page._get_show_translations_option_locator()
                ).to_be_hidden()

                expect(
                    self.sumo_pages.kb_article_page._get_what_links_here_locator()
                ).to_be_hidden()

                expect(
                    self.sumo_pages.kb_article_page._get_show_history_option_locator()
                ).to_be_hidden()
        else:
            with allure.step("Verifying that all the editing tools options are displayed"):
                expect(
                    self.sumo_pages.kb_article_page._get_article_option_locator()
                ).to_be_visible()

                expect(
                    self.sumo_pages.kb_article_page._editing_tools_discussion_locator()
                ).to_be_visible()

                expect(
                    self.sumo_pages.kb_article_page._get_edit_article_option_locator()
                ).to_be_visible()

                expect(
                    self.sumo_pages.kb_article_page._get_edit_article_metadata_locator()
                ).to_be_visible()

                expect(
                    self.sumo_pages.kb_article_page._get_translate_article_option_locator()
                ).to_be_visible()

                expect(
                    self.sumo_pages.kb_article_page._get_show_translations_option_locator()
                ).to_be_visible()

                expect(
                    self.sumo_pages.kb_article_page._get_what_links_here_locator()
                ).to_be_visible()

                expect(
                    self.sumo_pages.kb_article_page._get_show_history_option_locator()
                ).to_be_visible()

        if username != 'TEST_ACCOUNT_MODERATOR':
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Deleting the created article"):
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

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
                article_details['first_revision_id']
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
                    article_details['first_revision_id']))
            assert KBArticlePageMessages.REVIEW_REVISION_STATUS == status

        with allure.step("Deleting the created article"):
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2081446, C2081447, C2490049,  C2490051
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
            self.sumo_pages.kb_article_show_history_page._click_on_review_revision(
                article_details['first_revision_id']
            )
            assert self.sumo_pages.kb_article_review_revision_page._get_revision_header(
            ) == KBArticleRevision.KB_ARTICLE_REVISION_HEADER + article_details['article_title']

        with check, allure.step("Verifying that the correct subtext is displayed"):
            assert (self.sumo_pages.kb_article_review_revision_page._get_reviewing_revision_text()
                    .replace("\n", "").strip() == self.get_kb_article_revision_details(
                    revision_id=re.findall(r'\d+', article_details['first_revision_id'])[0],
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
                article_details['first_revision_id']
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

        with allure.step("Signing in with an admin account and creating a new revision"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))
            second_revision = self.sumo_pages.submit_kb_article_flow.submit_new_kb_revision()

        with check, allure.step("Verifying that the first approved revision is marked as the "
                                "current"):
            assert self.sumo_pages.kb_article_show_history_page._get_revision_status(
                article_details['first_revision_id']
            ) == KBArticlePageMessages.CURRENT_REVISION_STATUS

        with check, allure.step("Approving the second revision"):
            self.sumo_pages.submit_kb_article_flow.approve_kb_revision(
                second_revision['revision_id'])

        with check, allure.step("Verifying that the first revision status is 'Approved', and the"
                                "second is 'Current'"):
            assert self.sumo_pages.kb_article_show_history_page._get_revision_status(
                article_details['first_revision_id']
            ) == KBArticlePageMessages.PREVIOUS_APPROVED_REVISION_STATUS

            assert self.sumo_pages.kb_article_show_history_page._get_revision_status(
                second_revision['revision_id']
            ) == KBArticlePageMessages.CURRENT_REVISION_STATUS

        with allure.step("Signing in with an admin account and deleting the article"):
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2091580, C954321
    @pytest.mark.kbArticleCreationAndAccess
    def test_articles_discussions_allowed(self):
        with allure.step("Signing in with a non-admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))

        with allure.step("Create a new simple article"):
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

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
            self.sumo_pages.submit_kb_article_flow.approve_kb_revision(
                article_details['first_revision_id']
            )

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
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                allow_discussion=False
            )

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
            self.sumo_pages.submit_kb_article_flow.approve_kb_revision(
                article_details['first_revision_id']
            )

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

    # C2091665, C2243453
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
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                article_keyword=super().kb_article_test_data['updated_keywords'],
                search_summary=super(
                ).kb_article_test_data['updated_search_result_summary'],
                approve_first_revision=True
            )

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

    # C2081445
    @pytest.mark.kbArticleCreationAndAccess
    def test_edit_non_approved_articles(self):
        with allure.step("Signing in with a non-admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))

        with allure.step("Creating a simple kb article without approving it"):
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        with allure.step("Creating a new revision for the kb article"):
            second_revision = self.sumo_pages.submit_kb_article_flow.submit_new_kb_revision()

        with allure.step("Verifying that both the first and second revisions are displayed"):
            expect(
                self.sumo_pages.kb_article_show_history_page._get_a_particular_revision_locator(
                    article_details['first_revision_id']
                )
            ).to_be_visible()
            expect(
                self.sumo_pages.kb_article_show_history_page._get_a_particular_revision_locator(
                    second_revision['revision_id']
                )
            ).to_be_visible()

        with allure.step("Deleting the article"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C966833, C2102177, C2091592
    @pytest.mark.kbArticleCreationAndAccess
    def test_kb_article_keyword_and_summary_update(self):
        with allure.step("Signing in with an Admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Create a new simple article"):
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                approve_first_revision=True
            )

        with allure.step("Signing in with a non-admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_1"]
            ))

        with check, allure.step("Navigating to the 'Edit Article' form and verifying that the "
                                "edit keyword field is not displayed"):
            self.sumo_pages.kb_article_page._click_on_edit_article_option()
            expect(
                self.sumo_pages.kb_edit_article_page._get_edit_keywords_field_locator()
            ).to_be_hidden()

        with allure.step("Navigating back to the article"):
            self.sumo_pages.kb_article_page._click_on_article_option()

        with allure.step("Signing in with an Admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with check, allure.step("Clicking on the 'Edit Article' option and verifying that the "
                                "correct notification banner is displayed stating that another "
                                "user is also working on an edit"):
            self.sumo_pages.kb_article_page._click_on_edit_article_option()
            check.equal(
                self.sumo_pages.kb_edit_article_page._get_edit_article_warning_message(),
                self.get_article_warning_message(
                    super().username_extraction_from_email(
                        self.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_1"]
                    )
                )
            )
            self.sumo_pages.kb_edit_article_page._click_on_edit_anyway_option()

        with allure.step("Creating a new revision for the kb article and approving it"):
            self.sumo_pages.submit_kb_article_flow.submit_new_kb_revision(
                keywords=super().kb_article_test_data['updated_keywords'],
                search_result_summary=super(
                ).kb_article_test_data['updated_search_result_summary'],
                approve_revision=True,
                is_admin=True
            )

        with allure.step("Clicking on the top navbar sumo nav logo"):
            self.sumo_pages.top_navbar._click_on_sumo_nav_logo()

        with allure.step("Wait for ~1 minute until the kb article is available in search"):
            self.wait_for_given_timeout(60000)

        with allure.step("Signing out"):
            self.delete_cookies()

        with allure.step("Typing the article keyword inside the search field"):
            self.sumo_pages.search_page._type_into_searchbar(
                super().kb_article_test_data['updated_keywords']
            )

        with allure.step("Verifying that the article is displayed inside the search results"):
            expect(
                self.sumo_pages.search_page._get_locator_of_a_particular_article(
                    article_details['article_title']
                )
            ).to_be_visible()

        with check, allure.step("Verifying that the correct kb summary is displayed inside the "
                                "search results"):
            check.equal(
                self.sumo_pages.search_page
                ._get_search_result_summary_text_of_a_particular_article(
                    article_details['article_title']
                ),
                super().kb_article_test_data['updated_search_result_summary']
            )

        with allure.step("Clearing the searchbar"):
            self.sumo_pages.search_page._clear_the_searchbar()

        with allure.step("Typing the article summary inside the search field"):
            self.sumo_pages.search_page._type_into_searchbar(
                super().kb_article_test_data['updated_search_result_summary']
            )

        with allure.step("Verifying that the article is displayed inside the search results"):
            expect(
                self.sumo_pages.search_page._get_locator_of_a_particular_article(
                    article_details['article_title']
                )
            ).to_be_visible()

        with check, allure.step("Verifying that the correct kb summary is displayed inside the "
                                "search results"):
            check.equal(
                self.sumo_pages.search_page
                ._get_search_result_summary_text_of_a_particular_article(
                    article_details['article_title']
                ),
                super().kb_article_test_data['updated_search_result_summary']
            )

        with check, allure.step("Clicking on the article and verifying that the user is "
                                "redirected to the kb article"):
            self.sumo_pages.search_page._click_on_a_particular_article(
                article_details['article_title']
            )
            check.equal(
                self.sumo_pages.kb_article_page._get_text_of_article_title(),
                article_details['article_title']
            )

        with allure.step("Deleting the created article"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2243447, C2243449
    @pytest.mark.kbArticleCreationAndAccess
    def test_edit_article_metadata_title(self):
        with allure.step("Signing in with an Admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Create a new simple article"):
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                approve_first_revision=True
            )

        with allure.step("Signing in with a non-admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))

        with allure.step("Clicking on the Article option"):
            self.sumo_pages.kb_article_page._click_on_article_option()
            article_url = self.get_page_url()

        with check, allure.step("Verifying that the 'Edit Article Metadata option is not "
                                "displayed'"):
            expect(
                self.sumo_pages.kb_article_page._get_edit_article_metadata_locator()
            ).to_be_hidden()

        with check, allure.step("Navigating to the /metadata endpoint and verifying that the "
                                "Access Denied page is returned"):
            with self.page.expect_navigation() as navigation_info:
                self.navigate_to_link(
                    article_url + KBArticleRevision.KB_EDIT_METADATA
                )
            response = navigation_info.value
            assert response.status == 403

        with allure.step("Signing in back with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))
            self.navigate_to_link(
                article_url + KBArticleRevision.KB_EDIT_METADATA
            )

        with allure.step("Changing the article title"):
            self.sumo_pages.edit_article_metadata_flow.edit_article_metadata(
                title=self.kb_article_test_data['updated_kb_article_title'] + article_details
                ['article_title']
            )

        with check, allure.step("Clicking on the 'Edit Article Metadata' option and verifying "
                                "that the updated title and original slug is displayed"):
            self.sumo_pages.kb_article_page._click_on_edit_article_metadata()
            check.equal(
                (self.sumo_pages.kb_article_edit_article_metadata_page
                 ._get_text_of_title_input_field()),
                self.kb_article_test_data['updated_kb_article_title'] + article_details
                ['article_title']
            )

            check.equal(
                self.sumo_pages.kb_article_edit_article_metadata_page._get_slug_input_field(),
                article_details['article_slug']
            )

        with allure.step("Deleting the article"):
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2243450, C2091589
    @pytest.mark.kbArticleCreationAndAccess
    def test_edit_article_metadata_slug(self):
        with allure.step("Signing in with an Admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Create a new simple article"):
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                approve_first_revision=True
            )

        with allure.step("Trying to update an article with an already existing slug"):
            self.sumo_pages.edit_article_metadata_flow.edit_article_metadata(
                slug="donotdelete"
            )

        with check, allure.step("Verifying that the correct error message is displayed"):
            check.equal(
                self.sumo_pages.kb_article_edit_article_metadata_page._get_error_message(),
                KBArticlePageMessages.KB_ARTICLE_SUBMISSION_TITLE_ERRORS[1]
            )

        with allure.step("Changing the article slug"):
            self.sumo_pages.edit_article_metadata_flow.edit_article_metadata(
                slug=article_details['article_slug'] + "1"
            )

        with check, allure.step("Verifying that the article url has updated with the new slug"):
            check.is_in(
                article_details['article_slug'] + "1",
                self.get_page_url()
            )

        with check, allure.step("Clicking on the 'Edit Article Metadata' option and verifying "
                                "that the slug was updated"):
            self.sumo_pages.kb_article_page._click_on_edit_article_metadata()

            check.equal(
                self.sumo_pages.kb_article_edit_article_metadata_page._get_slug_input_field(),
                article_details['article_slug'] + "1"
            )

        with allure.step("Deleting the article"):
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2243451
    @pytest.mark.kbArticleCreationAndAccess
    def test_edit_article_metadata_category(self):
        with allure.step("Signing in with an Admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Create a new simple article"):
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                approve_first_revision=True
            )

        with allure.step("Selecting a different category"):
            self.sumo_pages.edit_article_metadata_flow.edit_article_metadata(
                category="Templates"
            )

        with check, allure.step("Verifying that the correct error message is displayed"):
            check.equal(
                self.sumo_pages.kb_article_edit_article_metadata_page._get_error_message(),
                super().get_template_error(article_details['article_title'])
            )

        with allure.step("Selecting a different category"):
            self.sumo_pages.edit_article_metadata_flow.edit_article_metadata(
                category="Navigation"
            )

        with check, allure.step("Verifying that the article is no longer displayed inside the "
                                "old category"):
            self.navigate_to_link(
                self.different_endpoints['kb_categories_links']
                [article_details['article_category']]
            )
            expect(
                self.sumo_pages.kb_category_page._get_a_particular_article_locator_from_list(
                    article_details['article_title']
                )
            ).to_be_hidden()

        with check, allure.step("Verifying that the article is displayed inside the new category"):
            self.navigate_to_link(
                self.different_endpoints['kb_categories_links']["Navigation"]
            )
            expect(
                self.sumo_pages.kb_category_page._get_a_particular_article_locator_from_list(
                    article_details['article_title']
                )
            ).to_be_visible()

        article_template_title = "Template:" + article_details['article_title']
        with allure.step("Changing the category and title of the kb article to match the "
                         "template category"):
            self.navigate_to_link(article_details['article_url'])
            self.sumo_pages.edit_article_metadata_flow.edit_article_metadata(
                title=article_template_title, category="Templates"
            )

        with check, allure.step("Verifying that the article is no longer displayed inside the "
                                "old category"):
            self.navigate_to_link(
                self.different_endpoints['kb_categories_links']["Navigation"]
            )
            expect(
                self.sumo_pages.kb_category_page._get_a_particular_article_locator_from_list(
                    article_template_title
                )
            ).to_be_hidden()

        with check, allure.step("Verifying that the article is displayed inside the new category"):
            self.navigate_to_link(
                self.different_endpoints['kb_categories_links']["Templates"]
            )
            expect(
                self.sumo_pages.kb_category_page._get_a_particular_article_locator_from_list(
                    article_template_title
                )
            ).to_be_visible()

        with allure.step("Deleting the article"):
            self.navigate_to_link(article_details['article_url'])
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2243452, C2243453
    @pytest.mark.kbArticleCreationAndAccess
    def test_edit_article_metadata_relevancy_and_topic(self):
        with allure.step("Signing in with an Admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Create a new simple article"):
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                approve_first_revision=True
            )

        with check, allure.step("Editing the article metadata by deselecting the relevancy and "
                                "verifying that the correct error message is displayed"):
            self.sumo_pages.edit_article_metadata_flow.edit_article_metadata(
                relevancy=article_details['article_relevancy']
            )
            check.equal(
                self.sumo_pages.kb_article_edit_article_metadata_page._get_error_message(),
                KBArticlePageMessages.KB_ARTICLE_RELEVANCY_ERROR
            )

        with check, allure.step("Selecting a different relevancy group, deselecting the topics "
                                "option and verifying that the correct error message is "
                                "displayed"):
            self.sumo_pages.edit_article_metadata_flow.edit_article_metadata(
                relevancy="Pocket", topics=article_details['article_topic']
            )
            check.equal(
                self.sumo_pages.kb_article_edit_article_metadata_page._get_error_message(),
                KBArticlePageMessages.KB_ARTICLE_TOPIC_ERROR
            )

        with allure.step("Selecting a different topic relevant to the relevancy group"):
            self.sumo_pages.edit_article_metadata_flow.edit_article_metadata(
                topics=["Pocket", "Getting Started"]
            )

        with check, allure.step("Verifying that the correct breadcrumb is displayed"):
            check.is_in(
                "Pocket",
                self.sumo_pages.kb_article_page._get_text_of_all_breadcrumbs()
            )
            check.is_in(
                "Getting Started",
                self.sumo_pages.kb_article_page._get_text_of_all_breadcrumbs()
            )

        with allure.step("Deleting the article"):
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2243455
    @pytest.mark.kbArticleCreationAndAccess
    def test_edit_metadata_article_discussions(self):
        with allure.step("Signing in with an Admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Create a new simple article"):
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                approve_first_revision=True
            )

        with check, allure.step("Verifying that the 'Discussion' is visible for admin users"):
            expect(
                self.sumo_pages.kb_article_page._editing_tools_discussion_locator()
            ).to_be_visible()

        with allure.step("Signing in with a non-admin user and verifying that the discussion "
                         "options is visible"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))

        with check, allure.step("Verifying that the 'Discussion' is visible for non-admin users"):
            expect(
                self.sumo_pages.kb_article_page._editing_tools_discussion_locator()
            ).to_be_visible()

        with allure.step("Signing in with an admin account and disabling article discussions via "
                         "edit article metadata form"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))
            self.sumo_pages.edit_article_metadata_flow.edit_article_metadata(discussions=False)

        with check, allure.step("Verifying that 'Discussion' is not displayed for admin users"):
            expect(
                self.sumo_pages.kb_article_page._editing_tools_discussion_locator()
            ).to_be_hidden()

        with check, allure.step("Navigating to the /discuss endpoint and verifying that 404 is "
                                "returned"):
            with self.page.expect_navigation() as navigation_info:
                self.navigate_to_link(
                    article_details['article_url'] + (KBArticlePageMessages
                                                      .KB_ARTICLE_DISCUSSIONS_ENDPOINT))
            response = navigation_info.value
            assert response.status == 404

        with check, allure.step("Verifying that the discussion option is not displayed for "
                                "non-admin users"):
            self.navigate_to_link(article_details['article_url'])
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))
            expect(
                self.sumo_pages.kb_article_page._editing_tools_discussion_locator()
            ).to_be_hidden()

        with check, allure.step("Navigating to the /discuss endpoint and verifying that 404 is "
                                "returned"):
            with self.page.expect_navigation() as navigation_info:
                self.navigate_to_link(
                    article_details['article_url'] + (KBArticlePageMessages
                                                      .KB_ARTICLE_DISCUSSIONS_ENDPOINT))
            response = navigation_info.value
            assert response.status == 404

        with allure.step("Signing in with an admin account and enabling the discussion option "
                         "via the edit article metadata page"):
            self.navigate_to_link(article_details['article_url'])
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))
            self.sumo_pages.edit_article_metadata_flow.edit_article_metadata(discussions=True)

        with check, allure.step("Verifying that the 'Discussion' is visible for admin users"):
            expect(
                self.sumo_pages.kb_article_page._editing_tools_discussion_locator()
            ).to_be_visible()

        with check, allure.step("Verifying that the 'Discussion' is visible for non-admin users"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))
            expect(
                self.sumo_pages.kb_article_page._editing_tools_discussion_locator()
            ).to_be_visible()

        with allure.step("Deleting the article"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2244014
    @pytest.mark.kbArticleCreationAndAccess
    def test_edit_metadata_article_multiple_users(self):
        with allure.step("Signing in with an Admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Create a new simple article"):
            self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                approve_first_revision=True
            )

        with allure.step("Clicking on the 'Edit Article Metadata' option"):
            self.sumo_pages.kb_article_page._click_on_edit_article_metadata()

        with allure.step("Navigating back to the article page and signing in with a non-admin "
                         "user account"):
            self.sumo_pages.kb_article_page._click_on_article_option()
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_13"]
            ))

        with allure.step("Clicking on the 'Edit Article Metadata' option"):
            self.sumo_pages.kb_article_page._click_on_edit_article_metadata()

        with check, allure.step("Verifying that the correct error message is displayed"):
            check.equal(
                self.sumo_pages.kb_edit_article_page._get_edit_article_warning_message(),
                self.get_article_warning_message(
                    super().username_extraction_from_email(
                        self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
                    )
                )
            )

        with allure.step("Clicking on the 'Edit Anyway' option and verifying that the warning "
                         "banner is no longer displayed"):
            self.sumo_pages.kb_edit_article_page._click_on_edit_anyway_option()
            expect(
                self.sumo_pages.kb_edit_article_page._get_warning_banner_locator()
            ).to_be_hidden()

        with allure.step("Deleting the article"):
            self.sumo_pages.kb_article_page._click_on_article_option()
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2271119, C2243454
    @pytest.mark.kbArticleCreationAndAccess
    def test_archived_kb_article_edit(self):
        with allure.step("Signing in with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Creating a simple kb article and approving it"):
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                approve_first_revision=True
            )

        with allure.step("Marking the article as Obsolete via the 'Edit Article Metadata' page"):
            self.sumo_pages.edit_article_metadata_flow.edit_article_metadata(obsolete=True)

        with allure.step("Signing in with a non-admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_13']
            ))

        with allure.step("Verifying that the 'Edit Article' navbar option is not displayed"):
            expect(
                self.sumo_pages.kb_article_page._get_edit_article_option_locator()
            ).to_be_hidden()

        with allure.step("Navigating to the 'Show History' page and clicking on the existing "
                         "revision"):
            self.sumo_pages.kb_article_page._click_on_show_history_option()
            self.sumo_pages.kb_article_show_history_page._click_on_a_revision_date(
                article_details['first_revision_id']
            )

        with allure.step("Clicking on the 'Edit Article based on this Revision' and submitting a "
                         "new article edit"):
            (self.sumo_pages.kb_article_preview_revision_page
             ._click_on_edit_article_based_on_this_revision_link())

            self.sumo_pages.kb_edit_article_page._fill_edit_article_content_field(
                self.kb_article_test_data['updated_article_content']
            )
            # Submitting for preview steps
            self.sumo_pages.kb_edit_article_page._click_submit_for_review_button()

            (self.sumo_pages.kb_edit_article_page
                ._fill_edit_article_changes_panel_comment(
                    self.kb_article_test_data['changes_description']
                ))

            (self.sumo_pages.kb_edit_article_page
             ._click_edit_article_changes_panel_submit_button())

        with allure.step("Verifying that the revision was successfully submitted"):
            second_revision = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()
            assert (article_details['first_revision_id'] != second_revision)

        with allure.step("Deleting the article"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    # C2490052
    @pytest.mark.kbArticleCreationAndAccess
    def test_revision_significance(self):
        with allure.step("Signing in with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Creating a simple kb article and approving the first revision"):
            article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                approve_first_revision=True
            )

        with check, allure.step("Verifying that the significance is the correct one"):
            check.equal(
                self.sumo_pages.kb_article_show_history_page._get_revision_significance(
                    article_details['first_revision_id']
                ),
                KBArticlePageMessages.MAJOR_SIGNIFICANCE
            )

        with check, allure.step("Creating a new revision, approving it wih minor significance "
                                "and verifying that the correct significance is displayed"):
            second_revision = self.sumo_pages.submit_kb_article_flow.submit_new_kb_revision()
            self.sumo_pages.submit_kb_article_flow.approve_kb_revision(
                revision_id=second_revision['revision_id'],
                significance_type='minor'
            )
            check.equal(
                self.sumo_pages.kb_article_show_history_page._get_revision_significance(
                    second_revision['revision_id']
                ),
                KBArticlePageMessages.MINOR_SIGNIFICANCE
            )

        with check, allure.step("Creating a new revision and approving it with normal "
                                "significance which is the default one and verifying that the "
                                "correct significance is displayed"):
            third_revision = self.sumo_pages.submit_kb_article_flow.submit_new_kb_revision(
                approve_revision=True
            )
            check.equal(
                self.sumo_pages.kb_article_show_history_page._get_revision_significance(
                    third_revision['revision_id']
                ),
                KBArticlePageMessages.NORMAL_SIGNIFICANCE
            )

        with check, allure.step("Creating a new revision, approving it with major significance "
                                "and verifying that the correct significance is displayed"):
            forth_revision = self.sumo_pages.submit_kb_article_flow.submit_new_kb_revision()
            self.sumo_pages.submit_kb_article_flow.approve_kb_revision(
                revision_id=forth_revision['revision_id'],
                significance_type='major'
            )
            check.equal(
                self.sumo_pages.kb_article_show_history_page._get_revision_significance(
                    forth_revision['revision_id']
                ),
                KBArticlePageMessages.MAJOR_SIGNIFICANCE
            )

        with allure.step("Deleting the article"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()
