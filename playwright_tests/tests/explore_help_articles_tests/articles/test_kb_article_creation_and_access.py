import pytest_check as check
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
        self.logger.info("Signing in with a non-Admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        self.logger.info("Create a new simple article")
        article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        self.logger.info("Verifying that the user is redirected to the article's show history "
                         "page after submission")
        expect(
            self.page
        ).to_have_url(
            KBArticlePageMessages.KB_ARTICLE_PAGE_URL + article_details
            ['article_slug'] + KBArticlePageMessages.KB_ARTICLE_HISTORY_URL_ENDPOINT)

        self.logger.info("Verifying that the revision contains the correct status")
        status = self.sumo_pages.kb_article_show_history_page._get_revision_status(
            self.sumo_pages.kb_article_show_history_page._get_last_revision_id()
        )

        check.equal(
            KBArticlePageMessages.UNREVIEWED_REVISION_STATUS,
            status
        )

        self.logger.info("Clicking on the 'Article' navbar menu")
        self.sumo_pages.kb_article_page._click_on_article_option()

        self.logger.info("Verifying that the doc content contains the correct string")
        check.equal(
            self.sumo_pages.kb_article_page._get_text_of_kb_article_content(),
            KBArticlePageMessages.KB_ARTICLE_NOT_APPROVED_CONTENT
        )

        self.logger.info("Deleting user session and verifying that the 404 page is received")
        with self.page.expect_navigation() as navigation_info:
            self.delete_cookies()
        response = navigation_info.value
        check.equal(
            response.status,
            404
        )

        self.logger.info("Signing in with an admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Clicking on the 'Show History' option")
        self.sumo_pages.kb_article_page._click_on_show_history_option()

        self.logger.info("Verifying that the revision contains the correct status")
        status = self.sumo_pages.kb_article_show_history_page._get_status_of_reviewable_revision(
            self.sumo_pages.kb_article_show_history_page._get_last_revision_id()
        )

        check.equal(
            KBArticlePageMessages.REVIEW_REVISION_STATUS,
            status
        )

        self.logger.info("Deleting the created article")
        self.sumo_pages.kb_article_show_history_page._click_on_delete_this_document_button()
        self.sumo_pages.kb_article_show_history_page._click_on_confirmation_delete_button()

    # C2081446, # C2081447
    @pytest.mark.kbArticleCreationAndAccess
    def test_articles_revision_page_and_revision_approval(self):
        self.logger.info("Signing in with a non-Admin account")
        username = self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        self.logger.info("Create a new simple article")
        article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Signing in with an Admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Clicking on the 'Show History' option")
        self.sumo_pages.kb_article_page._click_on_show_history_option()
        revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()
        self.logger.info("Clicking on the 'Review' option")
        self.sumo_pages.kb_article_show_history_page._click_on_review_revision(
            revision_id
        )

        self.logger.info("Verifying that the correct revision header is displayed")
        check.equal(
            self.sumo_pages.kb_article_revision_page._get_revision_header(),
            KBArticleRevision.KB_ARTICLE_REVISION_HEADER + article_details['article_title'],
        )

        self.logger.info("Verifying that the correct subtext is displayed")
        check.equal(
            self.sumo_pages.kb_article_revision_page._get_reviewing_revision_text()
            .replace("\n", "").strip(),
            self.get_kb_article_revision_details(
                revision_id=re.findall(r'\d+', revision_id)[0],
                username=username,
                revision_comment=article_details['article_review_description']
            ).strip()
        )

        self.logger.info("Click on the 'Back to History' option and verifying that the user is "
                         "redirected to the article history page")
        self.sumo_pages.kb_article_revision_page._click_on_back_to_history_option()
        expect(
            self.page
        ).to_have_url(
            KBArticlePageMessages.KB_ARTICLE_PAGE_URL + article_details
            ['article_slug'] + KBArticlePageMessages.KB_ARTICLE_HISTORY_URL_ENDPOINT
        )

        self.logger.info("Navigate back")
        self.navigate_back()

        self.logger.info("Verifying that the 'Keywords:' header is displayed")
        check.is_true(
            self.sumo_pages.kb_article_revision_page._is_keywords_header_visible()
        )

        self.logger.info("Verifying that the correct keyword is displayed")
        check.equal(
            self.sumo_pages.kb_article_revision_page._get_keywords_content(),
            article_details['keyword']
        )

        self.logger.info("Verifying that the 'Search results summary:' header is displayed")
        check.is_true(
            self.sumo_pages.kb_article_revision_page._is_search_results_summary_visible()
        )

        self.logger.info("Verifying that the correct search result summary is displayed")
        check.equal(
            self.sumo_pages.kb_article_revision_page._get_search_results_summary_content(),
            article_details['search_results_summary']
        )

        self.logger.info("Verifying that the 'Revision source:' header is displayed")
        check.is_true(
            self.sumo_pages.kb_article_revision_page._is_revision_source_visible()
        )

        self.logger.info("Verifying that the correct revision source content is displayed")
        check.equal(
            self.sumo_pages.kb_article_revision_page._revision_source_content(),
            article_details['article_content']
        )

        self.logger.info("Verifying that the 'Revision rendered html:' header is displayed")
        check.is_true(
            self.sumo_pages.kb_article_revision_page._is_revision_rendered_html_header_visible()
        )

        self.logger.info("Verifying that the correct 'Revision rendered html:' content is "
                         "displayed")
        check.equal(
            self.sumo_pages.kb_article_revision_page._get_revision_rendered_html_content(),
            article_details['article_content_html']
        )

        self.logger.info("Click on 'Approve Revision' button")
        self.sumo_pages.kb_article_revision_page._click_on_approve_revision_button()

        self.logger.info("Clicking on the 'Accept' button")
        self.sumo_pages.kb_article_revision_page._click_accept_revision_accept_button()

        self.logger.info("Verifying that the review status updates to 'Current'")
        check.equal(
            self.sumo_pages.kb_article_show_history_page._get_revision_status(
                revision_id
            ),
            KBArticlePageMessages.CURRENT_REVISION_STATUS
        )

        self.logger.info("Clicking on the 'Article' editing tools option")
        self.sumo_pages.kb_article_page._click_on_article_option()

        self.logger.info("Verifying that the correct html article content is displayed")
        check.equal(
            self.sumo_pages.kb_article_page._get_text_of_kb_article_content_approved(),
            article_details['article_content_html']
        )

        self.logger.info("Signing out and verifying that the correct article content is displayed")
        self.delete_cookies()

        check.equal(
            self.sumo_pages.kb_article_page._get_text_of_kb_article_content_approved(),
            article_details['article_content_html']
        )

        self.logger.info("Signing in with a non admin account and verifying that the correct "
                         "content is displayed")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_13"]
        ))

        check.equal(
            self.sumo_pages.kb_article_page._get_text_of_kb_article_content_approved(),
            article_details['article_content_html']
        )

        self.logger.info("Signing in with an admin account and deleting the article")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.sumo_pages.kb_article_page._click_on_show_history_option()
        self.sumo_pages.kb_article_show_history_page._click_on_delete_this_document_button()
        self.sumo_pages.kb_article_show_history_page._click_on_confirmation_delete_button()

    # C2091580
    @pytest.mark.kbArticleCreationAndAccess
    def test_articles_discussions_allowed(self):
        self.logger.info("Signing in with a non-Admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        self.logger.info("Create a new simple article")
        self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        self.logger.info("Clicking on the article option")
        self.sumo_pages.kb_article_page._click_on_article_option()
        article_url = self.get_page_url()

        self.logger.info("Clicking on the 'Discussion' editing tools navbar option")
        self.sumo_pages.kb_article_page._click_on_editing_tools_discussion_option()

        self.logger.info("Clicking on the 'Post a new thread button'")
        self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()

        self.logger.info("Posting a new kb article discussion thread")
        thread_info = (self.sumo_pages.post_kb_discussion_thread_flow.
                       add_new_kb_discussion_thread())

        self.logger.info("Manually navigating to the discuss endpoint")
        self.navigate_to_link(
            article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
        )

        self.logger.info("Verifying that the posted thread is successfully displayed")
        expect(
            self.sumo_pages.kb_article_discussion_page._get_posted_thread_locator(
                thread_info['thread_id']
            )
        ).to_be_visible()

        self.logger.info("Navigating to the article page")
        self.navigate_to_link(article_url)

        self.logger.info("Deleting session cookies")
        self.delete_cookies()

        self.logger.info("Signing in with an Admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Clicking on the 'Show History' option")
        self.sumo_pages.kb_article_page._click_on_show_history_option()
        revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()
        self.logger.info("Clicking on the 'Review' option")
        self.sumo_pages.kb_article_show_history_page._click_on_review_revision(
            revision_id
        )

        self.logger.info("Click on 'Approve Revision' button")
        self.sumo_pages.kb_article_revision_page._click_on_approve_revision_button()

        self.logger.info("Clicking on the 'Accept' button")
        self.sumo_pages.kb_article_revision_page._click_accept_revision_accept_button()

        self.logger.info("Navigating to the article page")
        self.navigate_to_link(article_url)

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Verifying that the discussion editing tools option is not available")
        expect(
            self.sumo_pages.kb_article_page._editing_tools_discussion_locator()
        ).to_be_hidden()

        self.logger.info("Manually navigating to the discuss endpoint")
        self.navigate_to_link(
            article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
        )

        self.logger.info("Verifying that the posted thread is successfully displayed")
        expect(
            self.sumo_pages.kb_article_discussion_page._get_posted_thread_locator(
                thread_info['thread_id']
            )
        ).to_be_visible()

        self.logger.info("Manually navigating to the discuss endpoint")
        self.navigate_to_link(
            article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
        )

        self.logger.info("Clicking on the 'Post a new thread' option")
        self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()

        self.logger.info("Verifying that the user is to the auth page")
        assert (
            FxAPageMessages.AUTH_PAGE_URL in self.get_page_url()
        )

        self.logger.info("Signing in")
        self.sumo_pages.auth_flow_page.sign_in_flow(
            username=super().user_special_chars,
            account_password=super().user_secrets_pass,
        )

        self.logger.info("Posting a new kb article discussion thread")
        thread_info = (self.sumo_pages.post_kb_discussion_thread_flow.
                       add_new_kb_discussion_thread())

        self.logger.info("Manually navigating to the discuss endpoint")
        self.navigate_to_link(
            article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
        )

        self.logger.info("Verifying that the posted thread is successfully displayed")
        expect(
            self.sumo_pages.kb_article_discussion_page._get_posted_thread_locator(
                thread_info['thread_id']
            )
        ).to_be_visible()

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Signing in with an admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Navigating to the article and deleting it")
        self.navigate_to_link(article_url)
        self.sumo_pages.kb_article_page._click_on_show_history_option()
        self.sumo_pages.kb_article_show_history_page._click_on_delete_this_document_button()
        self.sumo_pages.kb_article_show_history_page._click_on_confirmation_delete_button()

    # C2091581
    @pytest.mark.kbArticleCreationAndAccess
    def test_articles_discussions_not_allowed(self):
        self.logger.info("Signing in with a non-Admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        self.logger.info("Create a new simple article")
        self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(allow_discussion=False)

        self.logger.info("Clicking on the article option")
        self.sumo_pages.kb_article_page._click_on_article_option()

        article_url = self.get_page_url()

        self.logger.info("Verifying that the 'Discussion' option is not displayed")
        expect(
            self.sumo_pages.kb_article_page._editing_tools_discussion_locator()
        ).to_be_hidden()

        self.logger.info("Manually navigating to the 'Discuss' endpoint")
        with self.page.expect_navigation() as navigation_info:
            self.navigate_to_link(
                article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
            )
        response = navigation_info.value
        check.equal(
            response.status,
            404
        )

        self.logger.info("Navigating back to the article page and signing in with an admin accout")
        self.navigate_back()

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Clicking on the 'Show History' option")
        self.sumo_pages.kb_article_page._click_on_show_history_option()
        revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()
        self.logger.info("Clicking on the 'Review' option")
        self.sumo_pages.kb_article_show_history_page._click_on_review_revision(
            revision_id
        )

        self.logger.info("Click on 'Approve Revision' button")
        self.sumo_pages.kb_article_revision_page._click_on_approve_revision_button()

        self.logger.info("Clicking on the 'Accept' button")
        self.sumo_pages.kb_article_revision_page._click_accept_revision_accept_button()

        self.logger.info("Navigating back to the article page")
        self.navigate_to_link(article_url)

        self.logger.info("Verifying that the 'Discussion' option is not displayed")
        expect(
            self.sumo_pages.kb_article_page._editing_tools_discussion_locator()
        ).to_be_hidden()

        self.logger.info("Manually navigating to the 'Discuss' endpoint")
        with self.page.expect_navigation() as navigation_info:
            self.navigate_to_link(
                article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
            )
        response = navigation_info.value
        check.equal(
            response.status,
            404
        )

        self.logger.info("Navigating back")
        self.navigate_back()

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Verifying that the 'Discussion' option is not displayed")
        expect(
            self.sumo_pages.kb_article_page._editing_tools_discussion_locator()
        ).to_be_hidden()

        self.logger.info("Manually navigating to the 'Discuss' endpoint")
        with self.page.expect_navigation() as navigation_info:
            self.navigate_to_link(
                article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
            )
        response = navigation_info.value
        check.equal(
            response.status,
            404
        )

        self.logger.info("Navigating back to the article page")
        self.navigate_back()

        self.logger.info("Signing in with an admin account and deleting the article")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        self.sumo_pages.kb_article_page._click_on_show_history_option()
        self.sumo_pages.kb_article_show_history_page._click_on_delete_this_document_button()
        self.sumo_pages.kb_article_show_history_page._click_on_confirmation_delete_button()

    # C2091665
    @pytest.mark.kbArticleCreationAndAccess
    def test_kb_article_title_and_slug_validations(self):
        self.logger.info("Signing in with a non-Admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Create a new simple article")
        article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        self.logger.info("Verifying that the article slug was pre-populated successfully")
        check.equal(
            article_details['article_slug'],
            self.create_slug_from_title(article_details['article_title'])
        )

        self.logger.info("Navigating to the create kb article form")
        self.navigate_to_link(KBArticlePageMessages.CREATE_NEW_KB_ARTICLE_STAGE_URL)

        self.logger.info("Submitting the form without adding a title & slug")
        self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            article_title="",
            article_slug="",
        )

        self.logger.info("Verifying that we are on the same page")
        expect(
            self.page
        ).to_have_url(KBArticlePageMessages.CREATE_NEW_KB_ARTICLE_STAGE_URL)

        self.logger.info("Navigating to the create kb article form")
        self.navigate_to_link(KBArticlePageMessages.CREATE_NEW_KB_ARTICLE_STAGE_URL)

        self.logger.info("Submitting the form without adding a slug")
        self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            article_slug="",
        )

        self.logger.info("Verifying that we are on the same page")
        expect(
            self.page
        ).to_have_url(KBArticlePageMessages.CREATE_NEW_KB_ARTICLE_STAGE_URL)

        self.logger.info("Navigating to the create kb article form")
        self.navigate_to_link(KBArticlePageMessages.CREATE_NEW_KB_ARTICLE_STAGE_URL)

        self.logger.info("Submitting the form without adding a title")
        self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            article_title="",
            article_slug=self.kb_article_test_data['different_slug']
        )

        self.logger.info("Verifying that we are on the same page")
        expect(
            self.page
        ).to_have_url(KBArticlePageMessages.CREATE_NEW_KB_ARTICLE_STAGE_URL)

        self.logger.info("Navigating to the create kb article form")
        self.navigate_to_link(KBArticlePageMessages.CREATE_NEW_KB_ARTICLE_STAGE_URL)

        self.logger.info("Adding the same title and slug inside article form")
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

        self.logger.info("Submitting the question")
        self.sumo_pages.kb_submit_kb_article_form_page._click_on_submit_for_review_button()
        self.sumo_pages.kb_submit_kb_article_form_page._add_text_to_changes_description_field(
            self.kb_article_test_data["changes_description"]
        )
        self.sumo_pages.kb_submit_kb_article_form_page._click_on_changes_submit_button()

        self.logger.info("Verifying that both title and slug errors are displayed")
        for error in (self.sumo_pages.kb_submit_kb_article_form_page.
                      get_all_kb_errors()):
            check.is_in(
                error,
                KBArticlePageMessages.KB_ARTICLE_SUBMISSION_TITLE_ERRORS
            )

        self.logger.info("Navigate to the kb submission page")
        self.navigate_to_link(KBArticlePageMessages.CREATE_NEW_KB_ARTICLE_STAGE_URL)

        self.logger.info("Adding same title and a different slug")
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

        self.logger.info("Submitting the question")
        self.sumo_pages.kb_submit_kb_article_form_page._click_on_submit_for_review_button()
        self.sumo_pages.kb_submit_kb_article_form_page._add_text_to_changes_description_field(
            self.kb_article_test_data["changes_description"]
        )
        self.sumo_pages.kb_submit_kb_article_form_page._click_on_changes_submit_button()

        check.equal(
            self.sumo_pages.kb_submit_kb_article_form_page.get_all_kb_errors()[0],
            KBArticlePageMessages.KB_ARTICLE_SUBMISSION_TITLE_ERRORS[0]
        )

        self.logger.info("Navigate to the kb submission page")
        self.navigate_to_link(KBArticlePageMessages.CREATE_NEW_KB_ARTICLE_STAGE_URL)

        self.logger.info("Adding different title but same slug")
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

        self.logger.info("Submitting the question")
        self.sumo_pages.kb_submit_kb_article_form_page._click_on_submit_for_review_button()
        self.sumo_pages.kb_submit_kb_article_form_page._add_text_to_changes_description_field(
            self.kb_article_test_data["changes_description"]
        )
        self.sumo_pages.kb_submit_kb_article_form_page._click_on_changes_submit_button()

        check.equal(
            self.sumo_pages.kb_submit_kb_article_form_page.get_all_kb_errors()[0],
            KBArticlePageMessages.KB_ARTICLE_SUBMISSION_TITLE_ERRORS[1]
        )

        self.logger.info("Deleting the created article")
        self.navigate_to_link(
            KBArticlePageMessages.KB_ARTICLE_PAGE_URL + article_details
            ['article_slug'] + KBArticlePageMessages.KB_ARTICLE_HISTORY_URL_ENDPOINT)

        self.sumo_pages.kb_article_page._click_on_show_history_option()
        self.sumo_pages.kb_article_show_history_page._click_on_delete_this_document_button()
        self.sumo_pages.kb_article_show_history_page._click_on_confirmation_delete_button()

    # C2091665
    @pytest.mark.kbArticleCreationAndAccess
    def test_kb_article_relevancy_validations(self):
        self.logger.info("Signing in with a non-Admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Create a new simple article")
        self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(selected_relevancy=False)

        self.logger.info("Verifying that we are on the same page")
        expect(
            self.page
        ).to_have_url(KBArticlePageMessages.CREATE_NEW_KB_ARTICLE_STAGE_URL)

        self.logger.info("Verifying that the correct error message is displayed")
        check.equal(
            self.sumo_pages.kb_submit_kb_article_form_page.get_all_kb_errors()[0],
            KBArticlePageMessages.KB_ARTICLE_RELEVANCY_ERROR
        )

    # C2091665
    @pytest.mark.kbArticleCreationAndAccess
    def test_kb_article_topic_validation(self):
        self.logger.info("Signing in with a non-Admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Create a new simple article")
        self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(selected_topics=False)

        self.logger.info("Verifying that we are on the same page")
        expect(
            self.page
        ).to_have_url(KBArticlePageMessages.CREATE_NEW_KB_ARTICLE_STAGE_URL)

        self.logger.info("Verifying that the correct error message is displayed")
        check.equal(
            self.sumo_pages.kb_submit_kb_article_form_page.get_all_kb_errors()[0],
            KBArticlePageMessages.KB_ARTICLE_TOPIC_ERROR
        )

    # C2091665
    @pytest.mark.kbArticleCreationAndAccess
    def test_kb_article_summary_and_content_validation(self):
        self.logger.info("Signing in with a non-Admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Create a new simple article by leaving out the search summary")
        self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(search_summary="")

        self.logger.info("Verifying that we are on the same page")
        expect(
            self.page
        ).to_have_url(KBArticlePageMessages.CREATE_NEW_KB_ARTICLE_STAGE_URL)

        self.logger.info("Navigating to the create kb article form")
        self.navigate_to_link(KBArticlePageMessages.CREATE_NEW_KB_ARTICLE_STAGE_URL)

        self.logger.info("Create a new simple article by leaving out the article content")
        self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article(article_content="")

        self.logger.info("Verifying that we are on the same page")
        expect(
            self.page
        ).to_have_url(KBArticlePageMessages.CREATE_NEW_KB_ARTICLE_STAGE_URL)

    # C2091583, C2091584
    @pytest.mark.kbArticleCreationAndAccess
    @pytest.mark.parametrize("username", ['admin', 'simple_user', 'no_user'])
    def test_kb_article_keywords_and_summary(self, username):
        self.logger.info("Signing in with an Admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Create a new simple article")
        article_details = self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        self.logger.info("Clicking on the 'Show History' option")
        self.sumo_pages.kb_article_page._click_on_show_history_option()
        revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()
        self.logger.info("Clicking on the 'Review' option")
        self.sumo_pages.kb_article_show_history_page._click_on_review_revision(
            revision_id
        )

        self.logger.info("Click on 'Approve Revision' button")
        self.sumo_pages.kb_article_revision_page._click_on_approve_revision_button()

        self.logger.info("Clicking on the 'Accept' button")
        self.sumo_pages.kb_article_revision_page._click_accept_revision_accept_button()

        self.logger.info("Clicking on the top navbar sumo nav logo")
        self.sumo_pages.top_navbar._click_on_sumo_nav_logo()

        self.logger.info("Wait for ~1 minute until the kb article is available in search")
        self.wait_for_given_timeout(60000)

        if username == 'simple_user':
            self.logger.info("Deleting user session")
            self.delete_cookies()
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))
        elif username == "no_user":
            self.logger.info("Deleting user session")
            self.delete_cookies()

        self.logger.info("Typing the article keyword inside the search field")
        self.sumo_pages.search_page._type_into_searchbar(article_details['keyword'])

        self.logger.info("Verifying that the article is displayed inside the search results")
        expect(
            self.sumo_pages.search_page._get_locator_of_a_particular_article(
                article_details['article_title']
            )
        ).to_be_visible()

        self.logger.info("Verifying that the correct kb summary is displayed inside the search "
                         "results")
        check.equal(
            self.sumo_pages.search_page._get_search_result_summary_text_of_a_particular_article(
                article_details['article_title']
            ),
            article_details['search_results_summary']
        )

        self.logger.info("Clearing the searchbar")
        self.sumo_pages.search_page._clear_the_searchbar()

        self.logger.info("Typing the article summary inside the search field")
        self.sumo_pages.search_page._type_into_searchbar(article_details['search_results_summary'])

        self.logger.info("Verifying that the article is displayed inside the search results")
        expect(
            self.sumo_pages.search_page._get_locator_of_a_particular_article(
                article_details['article_title']
            )
        ).to_be_visible()

        self.logger.info("Verifying that the correct kb summary is displayed inside the search "
                         "results")
        check.equal(
            self.sumo_pages.search_page._get_search_result_summary_text_of_a_particular_article(
                article_details['article_title']
            ),
            article_details['search_results_summary']
        )

        self.logger.info("Clicking on the article and verifying that the user is redirected to "
                         "the kb article")
        self.sumo_pages.search_page._click_on_a_particular_article(
            article_details['article_title']
        )
        check.equal(
            self.sumo_pages.kb_article_page._get_text_of_article_title(),
            article_details['article_title']
        )

        self.logger.info("Deleting the created article")
        if username != 'admin':
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        self.sumo_pages.kb_article_page._click_on_show_history_option()
        self.sumo_pages.kb_article_show_history_page._click_on_delete_this_document_button()
        self.sumo_pages.kb_article_show_history_page._click_on_confirmation_delete_button()
