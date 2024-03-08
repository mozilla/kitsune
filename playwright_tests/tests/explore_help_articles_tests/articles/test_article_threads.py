import allure
import pytest
from playwright.sync_api import expect
from pytest_check import check
from playwright_tests.core.testutilities import TestUtilities
from playwright_tests.messages.explore_help_articles.kb_article_page_messages import (
    KBArticlePageMessages)


class TestArticleThreads(TestUtilities):
    with open('test_data/test_article', 'r') as file:
        article_url = file.read()

    # C2188031
    @pytest.mark.articleThreads
    def test_article_thread_field_validation(self):
        with allure.step("Signing in with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Manually navigating to the article endpoint and clicking on the "
                         "'Discussion' editing tools navbar option"):
            self.navigate_to_link(TestArticleThreads.article_url)
            self.sumo_pages.kb_article_page._click_on_editing_tools_discussion_option()

        with allure.step("Clicking on the 'Post a new thread button' and clicking on the 'Post "
                         "Thread' button without adding any data in the form fields"):
            self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()
            self.sumo_pages.kb_article_discussion_page._click_on_submit_new_thread_button()

        with allure.step("Verifying that we are on the same page"):
            expect(
                self.page
            ).to_have_url(
                TestArticleThreads.article_url + KBArticlePageMessages.
                KB_ARTICLE_DISCUSSIONS_NEW_ENDPOINT)

        with allure.step("Adding one character inside the 'Title' field, clicking the 'Post "
                         "Thread' button and verifying that we are on the same page"):
            self.sumo_pages.kb_article_discussion_page._add_text_to_new_thread_title_field("t")
            self.sumo_pages.kb_article_discussion_page._click_on_submit_new_thread_button()

            self.logger.info("Verifying that we are on the same page")
            expect(
                self.page
            ).to_have_url(TestArticleThreads.article_url + KBArticlePageMessages.
                          KB_ARTICLE_DISCUSSIONS_NEW_ENDPOINT)

        with allure.step("Clearing the input field and adding 5 characters inside the title "
                         "input field"):
            self.sumo_pages.kb_article_discussion_page._clear_new_thread_title_field()
            self.sumo_pages.kb_article_discussion_page._add_text_to_new_thread_title_field(
                super().kb_new_thread_test_data['new_thread_reduced_title']
            )

        with allure.step("Clicking on the 'Post Thread' button and verifying that we are on the "
                         "same page"):
            self.sumo_pages.kb_article_discussion_page._click_on_submit_new_thread_button()
            expect(
                self.page
            ).to_have_url(TestArticleThreads.article_url + KBArticlePageMessages.
                          KB_ARTICLE_DISCUSSIONS_NEW_ENDPOINT)

        with allure.step("Adding one character inside the content field, clicking on the 'Post "
                         "Thread' button and verifying that we are on the same page"):
            self.sumo_pages.kb_article_discussion_page._add_text_to_new_thread_body_input_field(
                "a"
            )
            self.sumo_pages.kb_article_discussion_page._click_on_submit_new_thread_button()
            expect(
                self.page
            ).to_have_url(TestArticleThreads.article_url + KBArticlePageMessages.
                          KB_ARTICLE_DISCUSSIONS_NEW_ENDPOINT)

        with allure.step("Clearing both title and content fields and adding 5 characters inside "
                         "the thread content field"):
            self.sumo_pages.kb_article_discussion_page._clear_new_thread_body_field()
            self.sumo_pages.kb_article_discussion_page._clear_new_thread_title_field()
            self.sumo_pages.kb_article_discussion_page._clear_new_thread_body_field()
            self.sumo_pages.kb_article_discussion_page._add_text_to_new_thread_body_input_field(
                super().kb_new_thread_test_data['new_thread_reduced_body']
            )

        with allure.step("Clicking on the 'Post Thread' button and verifying that we are on the "
                         "same page"):
            self.sumo_pages.kb_article_discussion_page._click_on_submit_new_thread_button()
            expect(
                self.page
            ).to_have_url(TestArticleThreads.article_url + KBArticlePageMessages.
                          KB_ARTICLE_DISCUSSIONS_NEW_ENDPOINT)

        with allure.step("Adding 5 characters inside the thread title field, clicking on the "
                         "'Cancel' button and verifying that the article is not displayed inside "
                         "the discussion thread list"):
            self.sumo_pages.kb_article_discussion_page._add_text_to_new_thread_title_field(
                super().kb_new_thread_test_data['new_thread_reduced_title']
            )
            self.sumo_pages.kb_article_discussion_page._click_on_cancel_new_thread_button()
            expect(
                self.sumo_pages.kb_article_discussion_page._get_thread_by_title_locator(
                    super().kb_new_thread_test_data['new_thread_reduced_title']
                )
            ).to_be_hidden()

        with allure.step("Clicking on the 'Post a new thread' button and adding the minimum "
                         "required characters inside both title and content fields"):
            self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()
            self.sumo_pages.kb_article_discussion_page._add_text_to_new_thread_title_field(
                super().kb_new_thread_test_data['new_thread_reduced_title']
            )
            self.sumo_pages.kb_article_discussion_page._add_text_to_new_thread_body_input_field(
                super().kb_new_thread_test_data['new_thread_reduced_body']
            )

        with allure.step("Clicking on the 'Post Thread' button, manually navigating to the "
                         "discuss endpoint and verifying that the posted thread is successfully "
                         "displayed"):
            self.sumo_pages.kb_article_discussion_page._click_on_submit_new_thread_button()
            thread_url = self.get_page_url()
            thread_id = str(super().number_extraction_from_string_endpoint(
                KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT, thread_url)
            )
            self.navigate_to_link(
                TestArticleThreads.article_url + KBArticlePageMessages.
                KB_ARTICLE_DISCUSSIONS_ENDPOINT
            )
            expect(
                self.sumo_pages.kb_article_discussion_page._get_posted_thread_locator(
                    thread_id
                )
            ).to_be_visible()

        with allure.step("Clearing the newly created thread"):
            self.__clearing_newly_created_thread(thread_id)

    # C2260840
    @pytest.mark.articleThreads
    def test_thread_replies_counter_increment(self):
        with allure.step("Signing in with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Manually navigating to the article endpoint and clicking on the "
                         "article option"):
            self.navigate_to_link(TestArticleThreads.article_url)
            self.sumo_pages.kb_article_page._click_on_article_option()

        with allure.step("Clicking on the 'Discussion' editing tools navbar option"):
            self.sumo_pages.kb_article_page._click_on_editing_tools_discussion_option()

        with check, allure.step("Clicking on the 'Post a new thread button', posting a new kb "
                                "article discussion thread and verifying that the thread counter"
                                " is not 0"):
            self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()
            thread_info = (self.sumo_pages.post_kb_discussion_thread_flow.
                           add_new_kb_discussion_thread())
            assert (self.number_extraction_from_string(
                self.sumo_pages.kb_article_discussion_page._get_thread_page_counter_replies_text(
                ))) == 0

        with check, allure.step("Manually navigating to the discuss endpoint "
                                "and verifying that the reply counter for the posted thread has "
                                "incremented successfully"):
            self.navigate_to_link(TestArticleThreads.article_url + KBArticlePageMessages
                                  .KB_ARTICLE_DISCUSSIONS_ENDPOINT)
            assert (self.number_extraction_from_string(
                self.sumo_pages.kb_article_discussion_page._get_article_discussions_thread_counter(
                    thread_info['thread_id']))) == 0

        with allure.step("Navigating back to the thread and posting a new reply with the same "
                         "user"):
            self.sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
                thread_info['thread_id']
            )
            self.sumo_pages.kb_article_discussion_page._fill_the_thread_post_a_reply_textarea(
                self.kb_new_thread_test_data['thread_reply_body']
            )
            self.sumo_pages.kb_article_discussion_page._click_on_thread_post_reply_button()

        with check, allure.step("Verifying that the thread counter is 1"):
            assert (self.number_extraction_from_string(
                self.sumo_pages.kb_article_discussion_page
                ._get_thread_page_counter_replies_text())) == 1

        with check, allure.step("Manually navigating to the discuss endpoint and verifying that "
                                "the reply counter for the posted thread has incremented "
                                "successfully"):
            self.navigate_to_link(
                TestArticleThreads.article_url + KBArticlePageMessages.
                KB_ARTICLE_DISCUSSIONS_ENDPOINT
            )
            assert (self.number_extraction_from_string(
                self.sumo_pages.kb_article_discussion_page._get_article_discussions_thread_counter(
                    thread_info['thread_id']))) == 1

        with allure.step("Clearing the newly created thread"):
            self.__clearing_newly_created_thread(thread_info['thread_id'])

    # C2260840, C2260809
    @pytest.mark.articleThreads
    def test_thread_replies_counter_decrement(self):
        with allure.step("Signing in with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Manually navigating to the article endpoint and clicking on the "
                         "'Discussion' editing tool navbar option"):
            self.navigate_to_link(TestArticleThreads.article_url)
            self.sumo_pages.kb_article_page._click_on_editing_tools_discussion_option()

        with allure.step("Signing in with a normal account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_12']
            ))

        with allure.step("Clicking on the 'Post a new thread button' and posting a new kb "
                         "article discussion thread"):
            self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()
            thread_info = (self.sumo_pages.post_kb_discussion_thread_flow.
                           add_new_kb_discussion_thread())

        with allure.step("Posting a new reply with the same user"):
            self.sumo_pages.kb_article_discussion_page._fill_the_thread_post_a_reply_textarea(
                self.kb_new_thread_test_data['thread_reply_body']
            )
            self.sumo_pages.kb_article_discussion_page._click_on_thread_post_reply_button()

            thread_reply_id = self.sumo_pages.kb_article_discussion_page._get_thread_reply_id(
                self.get_page_url()
            )

        with allure.step("Signing in with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_MODERATOR']
            ))

        with check, allure.step("Posting a new reply with the same user and verifying that the "
                                "reply counter for the posted thread has incremented "
                                "successfully"):
            self.sumo_pages.kb_article_discussion_page._fill_the_thread_post_a_reply_textarea(
                self.kb_new_thread_test_data['thread_reply_body']
            )
            self.sumo_pages.kb_article_discussion_page._click_on_thread_post_reply_button()
            assert (self.number_extraction_from_string(
                self.sumo_pages.kb_article_discussion_page._get_thread_page_counter_replies_text()
            ) == 2)

        with allure.step("Manually navigating to the discuss endpoint and verifying that the "
                         "reply counter for the posted thread has incremented successfully"):
            self.navigate_to_link(
                TestArticleThreads.article_url + KBArticlePageMessages
                .KB_ARTICLE_DISCUSSIONS_ENDPOINT
            )
            assert (self.number_extraction_from_string(
                self.sumo_pages.kb_article_discussion_page._get_article_discussions_thread_counter(
                    thread_info['thread_id'])) == 2)

        with allure.step("Clicking on the 3 dotted menu for a posted thread reply"):
            self.sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
                thread_info['thread_id']
            )
            self.sumo_pages.kb_article_discussion_page._click_on_dotted_menu_for_a_certain_reply(
                thread_reply_id
            )

        with check, allure.step("Clicking on the 'Delete this post' option and verifying that "
                                "the reply counter for the posted thread has incremented "
                                "successfully"):
            self.sumo_pages.kb_article_discussion_page._click_on_delete_this_thread_reply(
                thread_reply_id
            )
            (self.sumo_pages.kb_article_discussion_page
             ._click_on_delete_this_thread_reply_confirmation_button())
            assert (self.number_extraction_from_string(
                self.sumo_pages.kb_article_discussion_page._get_thread_page_counter_replies_text(
                )) == 1)

        with check, allure.step("Manually navigating to the discuss endpoint and verifying that "
                                "the reply counter for the posted thread has incremented "
                                "successfully"):
            self.navigate_to_link(
                TestArticleThreads.article_url + KBArticlePageMessages.
                KB_ARTICLE_DISCUSSIONS_ENDPOINT
            )
            assert (self.number_extraction_from_string(
                self.sumo_pages.kb_article_discussion_page._get_article_discussions_thread_counter(
                    thread_info['thread_id'])) == 1)

        with allure.step("Clearing the newly created thread"):
            self.__clearing_newly_created_thread(thread_info['thread_id'])

    @pytest.mark.articleThreads
    @pytest.mark.parametrize("username", ['TEST_ACCOUNT_12', 'TEST_ACCOUNT_MODERATOR', ''])
    def test_article_thread_author_filter(self, username):
        with allure.step("Signing in with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Manually navigating to the article endpoint and clicking on the "
                         "'Discussion' editing tools navbar option"):
            self.navigate_to_link(TestArticleThreads.article_url)
            self.sumo_pages.kb_article_page._click_on_editing_tools_discussion_option()

        with allure.step("Posting a new kb article discussion thread"):
            self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()
            thread_info = (self.sumo_pages.post_kb_discussion_thread_flow
                           .add_new_kb_discussion_thread())

        with allure.step("Navigating back to the article discussion page and signing in with a "
                         "non-admin account"):
            self.navigate_to_link(
                TestArticleThreads.article_url + KBArticlePageMessages.
                KB_ARTICLE_DISCUSSIONS_ENDPOINT
            )
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))

        with allure.step("Posting a new kb article discussion thread"):
            self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()
            thread_info_two = (self.sumo_pages.post_kb_discussion_thread_flow.
                               add_new_kb_discussion_thread())

        with allure.step("Navigating back to the article discussion page"):
            self.navigate_to_link(
                TestArticleThreads.article_url + KBArticlePageMessages.
                KB_ARTICLE_DISCUSSIONS_ENDPOINT
            )

        if username == 'TEST_ACCOUNT_MODERATOR':
            with allure.step("Signing in with an admin account"):
                self.start_existing_session(super().username_extraction_from_email(
                    self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
                ))
        elif username != 'TEST_ACCOUNT_12':
            with allure.step("Signing out from SUMO"):
                self.delete_cookies()

        with check, allure.step("Clicking on the 'Author' filter and verifying that the authors "
                                "are in reverse alphabetical order"):
            (self.sumo_pages.kb_article_discussion_page
             ._click_on_article_thread_author_replies_filter())
            assert self.sumo_pages.kb_article_discussion_page._get_all_article_threads_authors(
            ) != sorted(
                self.sumo_pages.kb_article_discussion_page._get_all_article_threads_authors()
            )

        with check, allure.step("Clicking on the 'Author' filter again and verifying that the "
                                "authors are in alphabetical order"):
            (self.sumo_pages.kb_article_discussion_page
             ._click_on_article_thread_author_replies_filter())
            assert self.sumo_pages.kb_article_discussion_page._get_all_article_threads_authors(
            ) == sorted(
                self.sumo_pages.kb_article_discussion_page._get_all_article_threads_authors()
            )

        with allure.step("Clearing both created threads"):
            self.__clearing_newly_created_thread(thread_info['thread_id'])
            self.__clearing_newly_created_thread(thread_info_two['thread_id'])

    @pytest.mark.articleThreads
    @pytest.mark.parametrize("username", ['TEST_ACCOUNT_12', 'TEST_ACCOUNT_MODERATOR', ''])
    def test_article_thread_replies_filter(self, username):
        with allure.step("Signing in with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Manually navigating to the article endpoint and clicking on the "
                         "'Discussion' editing tools navbar option"):
            self.navigate_to_link(TestArticleThreads.article_url)
            self.sumo_pages.kb_article_page._click_on_editing_tools_discussion_option()

        with allure.step("Clicking on the 'Post a new thread button' and posting a new kb "
                         "article discussion thread"):
            self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()
            thread_info = (self.sumo_pages.post_kb_discussion_thread_flow.
                           add_new_kb_discussion_thread())

        with allure.step("Posting a new reply with the same user"):
            self.sumo_pages.kb_article_discussion_page._fill_the_thread_post_a_reply_textarea(
                self.kb_new_thread_test_data['thread_reply_body']
            )
            self.sumo_pages.kb_article_discussion_page._click_on_thread_post_reply_button()

        with allure.step("Navigating back to the article discussion page and posting a new kb "
                         "article discussion thread"):
            self.navigate_to_link(
                TestArticleThreads.article_url + KBArticlePageMessages.
                KB_ARTICLE_DISCUSSIONS_ENDPOINT
            )
            self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()
            thread_info_two = (self.sumo_pages.post_kb_discussion_thread_flow.
                               add_new_kb_discussion_thread())

        with allure.step("Navigating back to the article discussion page"):
            self.navigate_to_link(
                TestArticleThreads.article_url + KBArticlePageMessages.
                KB_ARTICLE_DISCUSSIONS_ENDPOINT
            )

        if username == "TEST_ACCOUNT_12":
            with allure.step("Signing in with a non admin account"):
                self.start_existing_session(super().username_extraction_from_email(
                    self.user_secrets_accounts["TEST_ACCOUNT_12"]
                ))
        elif username == '':
            with allure.step("Deleting user session"):
                self.delete_cookies()

        with allure.step("Clicking on the 'Replies' filter and verifying that the replies is in "
                         "descending order"):
            self.sumo_pages.kb_article_discussion_page._click_on_article_thread_replies_filter()
            assert self.is_descending(
                self.sumo_pages.kb_article_discussion_page._get_all_article_threads_replies()
            )

        with check, allure.step("Clicking on the 'Replies' filter again and verifying that the "
                                "replies is in ascending order"):
            self.sumo_pages.kb_article_discussion_page._click_on_article_thread_replies_filter()
            assert not self.is_descending(
                self.sumo_pages.kb_article_discussion_page._get_all_article_threads_replies()
            )

        with allure.step("Clearing both created threads"):
            self.__clearing_newly_created_thread(thread_info['thread_id'])
            self.__clearing_newly_created_thread(thread_info_two['thread_id'])

    @pytest.mark.articleThreads
    def test_article_lock_thread_non_admin_users(self):
        with allure.step("Signing in with a non-admin account and creating an article"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_12']
            ))

        kb_url = self.__posting_a_new_test_article_manually(approve_it=False,
                                                            post_it=True)

        with allure.step("Signing in with an admin account and approving the article"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))
            self.__posting_a_new_test_article_manually(approve_it=True, post_it=False)

        with allure.step("Clicking on the 'Discussion' editing tools navbar option and posting a "
                         "new kb article discussion thread"):
            self.sumo_pages.kb_article_page._click_on_editing_tools_discussion_option()
            self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()
            thread_info_one = (self.sumo_pages.post_kb_discussion_thread_flow.
                               add_new_kb_discussion_thread())

        with allure.step("Signing in with a non-admin user account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_12']
            ))

        with allure.step("Navigating back to the discussions page and posting a new kb article "
                         "discussion thread"):
            self.navigate_to_link(
                kb_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
            )
            self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()
            thread_info_two = (self.sumo_pages.post_kb_discussion_thread_flow.
                               add_new_kb_discussion_thread())

        with allure.step("Navigating back to the discussions page, clicking on the thread posted "
                         "by another user and verifying that the 'Lock thread' option is not "
                         "available"):
            self.navigate_to_link(
                kb_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
            )
            self.sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
                thread_info_one['thread_id']
            )
            expect(
                self.sumo_pages.kb_article_discussion_page._get_lock_this_article_thread_locator()
            ).to_be_hidden()

        with allure.step("Navigating back to the article discussions page, clicking on the "
                         "thread posted by self and verifying that the 'Lock thread' option is "
                         "not available"):
            self.navigate_to_link(
                kb_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
            )
            self.sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
                thread_info_two['thread_id']
            )
            expect(
                self.sumo_pages.kb_article_discussion_page._get_lock_this_article_thread_locator()
            ).to_be_hidden()

        with allure.step("Deleting user sessions and verifying that the 'Lock thread' options is "
                         "not available"):
            self.delete_cookies()
            expect(
                self.sumo_pages.kb_article_discussion_page._get_lock_this_article_thread_locator()
            ).to_be_hidden()

        with allure.step("Signing in with an admin account and deleting the kb article"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))
            self.navigate_to_link(kb_url)
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    #  C2260810
    @pytest.mark.articleThreads
    @pytest.mark.parametrize("username", ['TEST_ACCOUNT_MODERATOR', 'TEST_ACCOUNT_12', ''])
    def test_article_lock_thread_functionality(self, username):
        with allure.step("Signing in with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Manually navigating to the article endpoint and clicking on the "
                         "'Discussion' editing tools navbar option"):
            self.navigate_to_link(TestArticleThreads.article_url)
            self.sumo_pages.kb_article_page._click_on_editing_tools_discussion_option()

        with allure.step("Posting a new kb article discussion thread"):
            self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()
            thread_info_one = (self.sumo_pages.post_kb_discussion_thread_flow.
                               add_new_kb_discussion_thread())

        with allure.step("Signing in with a non-admin user account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_12']
            ))

        with allure.step("Navigating back to the discussions page and posting a new discussion "
                         "thread"):
            self.navigate_to_link(
                TestArticleThreads.article_url + KBArticlePageMessages.
                KB_ARTICLE_DISCUSSIONS_ENDPOINT
            )
            self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()
            thread_info_two = (self.sumo_pages.post_kb_discussion_thread_flow.
                               add_new_kb_discussion_thread())

        with allure.step("Navigating back to the discussions page"):
            self.navigate_to_link(
                TestArticleThreads.article_url + KBArticlePageMessages.
                KB_ARTICLE_DISCUSSIONS_ENDPOINT
            )

        with allure.step("Signing in with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Clicking on the thread posted by self user and locking the thread"):
            self.sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
                thread_info_one['thread_id']
            )
            self.sumo_pages.kb_article_discussion_page._click_on_lock_this_article_thread_option()

        if username == 'TEST_ACCOUNT_12':
            with check, allure.step("Signing in with a non-admin account and verifying that the "
                                    "correct thread locked message is displayed"):
                self.start_existing_session(super().username_extraction_from_email(
                    self.user_secrets_accounts['TEST_ACCOUNT_12']
                ))
                assert (self.sumo_pages.kb_article_discussion_page
                        ._get_text_of_locked_article_thread_text() == KBArticlePageMessages
                        .KB_ARTICLE_LOCKED_THREAD_MESSAGE)

        elif username == '':
            with allure.step("Deleting user session"):
                self.delete_cookies()

        with allure.step("Verifying that the 'Post a reply' textarea field is not displayed"):
            expect(
                self.sumo_pages.kb_article_discussion_page._get_thread_post_a_reply_textarea_field(
                )
            ).to_be_hidden()

        with allure.step("Verifying that the 'Locked' status is displayed under article header"):
            expect(
                self.sumo_pages.kb_article_discussion_page._get_locked_article_status()
            ).to_be_visible()

        with allure.step("Navigating back to the discussions page"):
            self.navigate_to_link(
                TestArticleThreads.article_url + KBArticlePageMessages
                .KB_ARTICLE_DISCUSSIONS_ENDPOINT
            )

        if username != 'TEST_ACCOUNT_MODERATOR':
            with allure.step("Signing in with an admin account"):
                self.start_existing_session(super().username_extraction_from_email(
                    self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
                ))

        with allure.step("Clicking on the thread posted by the other user and clicking on the "
                         "'Lock this thread' option"):
            self.sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
                thread_info_two['thread_id']
            )
            self.sumo_pages.kb_article_discussion_page._click_on_lock_this_article_thread_option()

        if username == 'TEST_ACCOUNT_12':
            with check, allure.step("Signing in with a non-admin account and verifying that the "
                                    "correct thread locked message is displayed"):
                self.start_existing_session(super().username_extraction_from_email(
                    self.user_secrets_accounts['TEST_ACCOUNT_12']
                ))
                assert (self.sumo_pages.kb_article_discussion_page
                        ._get_text_of_locked_article_thread_text() == KBArticlePageMessages
                        .KB_ARTICLE_LOCKED_THREAD_MESSAGE)
        elif username == '':
            with allure.step("Deleting user session"):
                self.delete_cookies()

        with allure.step("Verifying that the 'Locked' status is displayed under article header"):
            expect(
                self.sumo_pages.kb_article_discussion_page._get_locked_article_status()
            ).to_be_visible()

        with allure.step("Verifying that the 'Post a reply' textarea field is not displayed"):
            expect(
                self.sumo_pages.kb_article_discussion_page._get_thread_post_a_reply_textarea_field(
                )
            ).to_be_hidden()

        with allure.step("Clearing both created threads"):
            self.__clearing_newly_created_thread(thread_info_one['thread_id'])
            self.__clearing_newly_created_thread(thread_info_two['thread_id'])

    # C2260810
    @pytest.mark.articleThreads
    @pytest.mark.parametrize("username", ['TEST_ACCOUNT_MODERATOR', 'TEST_ACCOUNT_12', ''])
    def test_article_unlock_thread_functionality(self, username):
        with allure.step("Signing in with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Navigating to the article endpoint"):
            self.navigate_to_link(TestArticleThreads.article_url)

        with allure.step("Posting a new kb article discussion thread"):
            self.sumo_pages.kb_article_page._click_on_editing_tools_discussion_option()
            self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()
            thread_info_one = (self.sumo_pages.post_kb_discussion_thread_flow.
                               add_new_kb_discussion_thread())

        with allure.step("Signing in with a normal user account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_12']
            ))

        with allure.step("Navigating back to the discussions page"):
            self.navigate_to_link(
                TestArticleThreads.article_url + KBArticlePageMessages.
                KB_ARTICLE_DISCUSSIONS_ENDPOINT
            )

        with allure.step("Posting a new kb article discussion thread"):
            self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()
            thread_info_two = (self.sumo_pages.post_kb_discussion_thread_flow.
                               add_new_kb_discussion_thread())

        with allure.step("Navigating back to the discussions page"):
            self.navigate_to_link(
                TestArticleThreads.article_url + KBArticlePageMessages.
                KB_ARTICLE_DISCUSSIONS_ENDPOINT
            )

        with allure.step("Signing in with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with check, allure.step("Clicking on the thread posted by self user and verifying that "
                                "the correct 'Lock this thread' option text is displayed"):
            self.sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
                thread_info_one['thread_id']
            )
            assert (self.sumo_pages.kb_article_discussion_page
                    ._get_lock_this_article_thread_option_text() == KBArticlePageMessages
                    .KB_ARTICLE_LOCK_THIS_THREAD_OPTION)

        with check, allure.step("Clicking on 'Lock this thread' option and verifying that the "
                                "correct 'Unlock this thread' text is displayed"):
            self.sumo_pages.kb_article_discussion_page._click_on_lock_this_article_thread_option()
            assert (self.sumo_pages.kb_article_discussion_page
                    ._get_lock_this_article_thread_option_text() == KBArticlePageMessages.
                    KB_ARTICLE_UNLOCK_THIS_THREAD_OPTION)

        if username == 'TEST_ACCOUNT_12':
            with allure.step("Signing in with a non-admin account and verifying that the 'Unlock "
                             "this thread' option is not displayed"):
                self.start_existing_session(super().username_extraction_from_email(
                    self.user_secrets_accounts['TEST_ACCOUNT_12']
                ))
                expect(
                    self.sumo_pages.kb_article_discussion_page.
                    _get_lock_this_article_thread_locator()
                ).to_be_hidden()
        if username == '':
            with allure.step("Deleting user session and verifying that the 'Unlock this thread' "
                             "option is no displayed"):
                self.delete_cookies()
                expect(
                    self.sumo_pages.kb_article_discussion_page.
                    _get_lock_this_article_thread_locator()
                ).to_be_hidden()

        if username != 'TEST_ACCOUNT_MODERATOR':
            with allure.step("Signing in with an admin account"):
                self.start_existing_session(super().username_extraction_from_email(
                    self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
                ))

        with allure.step("Clicking on the 'Unlock this thread'"):
            self.sumo_pages.kb_article_discussion_page._click_on_lock_this_article_thread_option()

        if username == 'TEST_ACCOUNT_12':
            with allure.step("Signing in with a non-admin account and verifying that the "
                             "textarea field is available"):
                self.start_existing_session(super().username_extraction_from_email(
                    self.user_secrets_accounts['TEST_ACCOUNT_12']
                ))
                expect(
                    self.sumo_pages.kb_article_discussion_page
                    ._get_thread_post_a_reply_textarea_field(
                    )
                ).to_be_visible()
        if username == '':
            with allure.step("Deleting user session and verifying that the textarea field is not "
                             "available"):
                self.delete_cookies()
                expect(
                    self.sumo_pages.kb_article_discussion_page
                    ._get_thread_post_a_reply_textarea_field(
                    )
                ).to_be_hidden()

        with allure.step("Verifying that the 'Locked' header text is not displayed"):
            expect(
                self.sumo_pages.kb_article_discussion_page._get_locked_article_status()
            ).to_be_hidden()

        with allure.step("Verifying that the 'Thread locked' page message is not displayed"):
            expect(
                self.sumo_pages.kb_article_discussion_page
                ._get_text_of_locked_article_thread_locator()
            ).to_be_hidden()

        if username != "TEST_ACCOUNT_MODERATOR":
            with allure.step("Signing in with an admin account"):
                self.start_existing_session(super().username_extraction_from_email(
                    self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
                ))

        with allure.step("Navigating back the article page and clicking on the thread posted by "
                         "another user"):
            self.navigate_to_link(
                TestArticleThreads.article_url + KBArticlePageMessages
                .KB_ARTICLE_DISCUSSIONS_ENDPOINT
            )
            self.sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
                thread_info_two['thread_id']
            )

        with check, allure.step("Verifying that the correct 'Lock this thread' option text is "
                                "displayed"):
            assert (self.sumo_pages.kb_article_discussion_page
                    ._get_lock_this_article_thread_option_text() == KBArticlePageMessages
                    .KB_ARTICLE_LOCK_THIS_THREAD_OPTION)

        with check, allure.step("Clicking on 'Lock this thread' option and verifying that the "
                                "correct 'Unlock this thread' text is displayed"):
            self.sumo_pages.kb_article_discussion_page._click_on_lock_this_article_thread_option()
            assert (self.sumo_pages.kb_article_discussion_page
                    ._get_lock_this_article_thread_option_text() == KBArticlePageMessages
                    .KB_ARTICLE_UNLOCK_THIS_THREAD_OPTION)

        if username == 'TEST_ACCOUNT_12':
            with allure.step("Signing in with a non-admin account and verifying that the 'Unlock "
                             "this thread' option is displayed"):
                self.start_existing_session(super().username_extraction_from_email(
                    self.user_secrets_accounts['TEST_ACCOUNT_12']
                ))
                expect(
                    self.sumo_pages.kb_article_discussion_page
                    ._get_lock_this_article_thread_locator()
                ).to_be_hidden()
        if username == '':
            with allure.step("Deleting the user session and verifying that the 'Unlock this "
                             "thread' option is not displayed"):
                self.delete_cookies()
                expect(
                    self.sumo_pages.kb_article_discussion_page
                    ._get_lock_this_article_thread_locator()
                ).to_be_hidden()

        if username != 'TEST_ACCOUNT_MODERATOR':
            with allure.step("Signing in with an admin account and clicking on the 'Unlock this "
                             "thread' option"):
                self.start_existing_session(super().username_extraction_from_email(
                    self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
                ))
        self.sumo_pages.kb_article_discussion_page._click_on_lock_this_article_thread_option()

        if username == 'TEST_ACCOUNT_12':
            with allure.step("Signing in with a non-admin account and verifying that the "
                             "textarea field is available"):
                self.start_existing_session(super().username_extraction_from_email(
                    self.user_secrets_accounts['TEST_ACCOUNT_12']
                ))
                expect(
                    self.sumo_pages.kb_article_discussion_page
                    ._get_thread_post_a_reply_textarea_field(
                    )
                ).to_be_visible()
        if username == '':
            with allure.step("Deleting user session and verifying that the textarea field is not "
                             "available"):
                self.delete_cookies()
                expect(
                    self.sumo_pages.kb_article_discussion_page
                    ._get_thread_post_a_reply_textarea_field(
                    )
                ).to_be_hidden()

        with allure.step("Verifying that the 'Locked' header text is not displayed"):
            expect(
                self.sumo_pages.kb_article_discussion_page._get_locked_article_status()
            ).to_be_hidden()

        with allure.step("Verifying that the 'Thread locked' page message is not displayed"):
            expect(
                self.sumo_pages.kb_article_discussion_page
                ._get_text_of_locked_article_thread_locator()
            ).to_be_hidden()

        with allure.step("Clearing the newly created thread"):
            self.__clearing_newly_created_thread(thread_info_one['thread_id'])
            self.__clearing_newly_created_thread(thread_info_two['thread_id'])

    # C2260811
    @pytest.mark.articleThreads
    @pytest.mark.parametrize("username", ['TEST_ACCOUNT_MODERATOR', 'TEST_ACCOUNT_12', ''])
    def test_article_thread_sticky(self, username):
        with allure.step("Signing in with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Posting a new kb article"):
            kb_article_url = self.__posting_a_new_test_article_manually(
                post_it=True, approve_it=True
            )

        with allure.step("Posting a new kb article discussion thread"):
            self.sumo_pages.kb_article_page._click_on_editing_tools_discussion_option()
            self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()
            thread_info_one = (self.sumo_pages.post_kb_discussion_thread_flow.
                               add_new_kb_discussion_thread())

        with allure.step("Signing in with a normal user account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_12']
            ))

        with allure.step("Navigating back to the discussions page"):
            self.navigate_to_link(
                kb_article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
            )

        with allure.step("Posting a new kb article discussion thread"):
            self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()
            thread_info_two = (self.sumo_pages.post_kb_discussion_thread_flow.
                               add_new_kb_discussion_thread(title='Other test thread'))

        with allure.step("Verifying that the 'Sticky this thread' option is not displayed"):
            expect(
                self.sumo_pages.kb_article_discussion_page._get_sticky_this_thread_locator()
            ).to_be_hidden()

        with allure.step("Navigating back to the discussions page"):
            self.navigate_to_link(
                kb_article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
            )

        with allure.step("Signing in with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Clicking on the thread posted by self and clicking on the 'sticky this "
                         "thread' option"):
            self.sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
                thread_info_one['thread_id']
            )
            self.sumo_pages.kb_article_discussion_page._click_on_sticky_this_thread_option()

        with check, allure.step("Verifying that the text changed to 'Unsticky this thread'"):
            assert (self.sumo_pages.kb_article_discussion_page
                    ._get_text_of_sticky_this_thread_option() == KBArticlePageMessages
                    .KB_ARTICLE_UNSTICKY_OPTION)

        if username == 'TEST_ACCOUNT_12':
            with allure.step("Signing in with a non-admin account and verifying that the "
                             "unsticky this thread option is not available"):
                self.start_existing_session(super().username_extraction_from_email(
                    self.user_secrets_accounts['TEST_ACCOUNT_12']
                ))
                expect(
                    self.sumo_pages.kb_article_discussion_page._get_sticky_this_thread_locator()
                ).to_be_hidden()
        if username == '':
            with allure.step("Deleting user session and verifying that the unsticky this thread "
                             "option is not available"):
                self.delete_cookies()
                expect(
                    self.sumo_pages.kb_article_discussion_page._get_sticky_this_thread_locator()
                ).to_be_hidden()

        with allure.step("Verifying that the 'Sticky' status is displayed"):
            expect(
                self.sumo_pages.kb_article_discussion_page._get_sticky_this_thread_status_locator()
            ).to_be_visible()

        with check, allure.step("Navigating back to the discussions page and verifying that the "
                                "sticky article is displayed in top of the list"):
            self.navigate_to_link(
                kb_article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
            )
            assert self.sumo_pages.kb_article_discussion_page._get_all_article_threads_titles(
            )[0] == thread_info_one['thread_title']

        if username != 'TEST_ACCOUNT_MODERATOR':
            with allure.step("Signing in with an admin account"):
                self.start_existing_session(super().username_extraction_from_email(
                    self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
                ))

        with check, allure.step("Clicking on the unsitcky this thread and verifying that the "
                                "text changed to 'Sticky this thread'"):
            self.sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
                thread_info_one['thread_id']
            )
            self.sumo_pages.kb_article_discussion_page._click_on_sticky_this_thread_option()
            assert (self.sumo_pages.kb_article_discussion_page
                    ._get_text_of_sticky_this_thread_option() == KBArticlePageMessages.
                    KB_ARTICLE_STICKY_THIS_THREAD_OPTION)

        if username == 'TEST_ACCOUNT_12':
            with allure.step("Signing in with a non-admin account"):
                self.start_existing_session(super().username_extraction_from_email(
                    self.user_secrets_accounts['TEST_ACCOUNT_12']
                ))
        if username == '':
            with allure.step("Deleting user session"):
                self.delete_cookies()

        with allure.step("Verifying that the 'Sticky' status is not displayed"):
            expect(
                self.sumo_pages.kb_article_discussion_page._get_sticky_this_thread_status_locator()
            ).to_be_hidden()

        with check, allure.step("Navigating back to the discussions page and verifying that the "
                                "sticky article is not displayed in top of the list"):
            self.navigate_to_link(
                kb_article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
            )
            assert self.sumo_pages.kb_article_discussion_page._get_all_article_threads_titles(
            )[0] == thread_info_two['thread_title']

        with allure.step("Signing in with an admin account and deleting the kb article"):
            self.start_existing_session(self.username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))
            self.navigate_to_link(kb_article_url)
            self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

    #  C2260808, C2260823
    @pytest.mark.articleThreads
    @pytest.mark.parametrize("thread_author", ['self', 'other'])
    def test_article_thread_content_edit(self, thread_author):
        with allure.step("Signing in with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Manually navigating to the article endpoint and posting a new kb "
                         "article discussion thread"):
            self.navigate_to_link(TestArticleThreads.article_url)
            self.sumo_pages.kb_article_page._click_on_editing_tools_discussion_option()
            self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()
            thread_info_one = (self.sumo_pages.post_kb_discussion_thread_flow.
                               add_new_kb_discussion_thread())

        with allure.step("Signing in with a non-admin user account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_12']
            ))

        with allure.step("Navigating back to the discussions page and posting a new kb article "
                         "discussion thread"):
            self.navigate_to_link(
                TestArticleThreads.article_url + KBArticlePageMessages.
                KB_ARTICLE_DISCUSSIONS_ENDPOINT
            )
            self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()
            thread_info_two = (self.sumo_pages.post_kb_discussion_thread_flow.
                               add_new_kb_discussion_thread())

        with allure.step("Adding data inside the edit this thread title field and clicking on "
                         "the cancel button"):
            self.sumo_pages.kb_article_discussion_page._click_on_edit_this_thread_option()
            (self.sumo_pages.kb_article_discussion_page
                ._add_text_to_edit_article_thread_title_field(
                    self.kb_new_thread_test_data['updated_thread_title']))
            self.sumo_pages.kb_article_discussion_page._click_on_edit_article_thread_cancel_button(
            )

        with check, allure.step("Verifying that the thread title was not changed"):
            assert self.sumo_pages.kb_article_discussion_page._get_thread_title_text(
            ) == thread_info_two['thread_title']

        with allure.step("Adding data inside the edit this thread title field and clicking on "
                         "the update button"):
            self.sumo_pages.kb_article_discussion_page._click_on_edit_this_thread_option()
            (self.sumo_pages.kb_article_discussion_page
                ._add_text_to_edit_article_thread_title_field(
                    self.kb_new_thread_test_data['updated_thread_title']))
            self.sumo_pages.kb_article_discussion_page._click_on_edit_article_thread_update_button(
            )

        with check, allure.step("Verifying that the thread title was changed"):
            assert self.sumo_pages.kb_article_discussion_page._get_thread_title_text(
            ) == self.kb_new_thread_test_data['updated_thread_title']

        with allure.step("Deleting user session adn verifying that the edit this thread option "
                         "is not displayed"):
            self.delete_cookies()
            expect(
                self.sumo_pages.kb_article_discussion_page._get_edit_this_thread_locator()
            ).to_be_hidden()

        with allure.step("Signing in with an admin account"):
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        with allure.step("Navigating back to the discussions page"):
            self.navigate_to_link(
                TestArticleThreads.article_url + KBArticlePageMessages.
                KB_ARTICLE_DISCUSSIONS_ENDPOINT
            )

        if thread_author == 'self':
            with allure.step("Clicking on the self posted thread"):
                self.sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
                    thread_info_one["thread_id"]
                )
        else:
            with allure.step("Clicking on the other user posted thread"):
                self.sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
                    thread_info_two["thread_id"])

        with allure.step("Clicking on the 'Edit this thread', adding data inside the title field "
                         "and clicking on the cancel button"):
            self.sumo_pages.kb_article_discussion_page._click_on_edit_this_thread_option()
            (self.sumo_pages.kb_article_discussion_page
                ._add_text_to_edit_article_thread_title_field(
                    self.kb_new_thread_test_data['second_thread_updated_title']))
            self.sumo_pages.kb_article_discussion_page._click_on_edit_article_thread_cancel_button(
            )

        if thread_author == 'self':
            with check, allure.step("Verifying that the thread title was not changed"):
                assert self.sumo_pages.kb_article_discussion_page._get_thread_title_text(
                ) == thread_info_one['thread_title']
        else:
            with check, allure.step("Verifying that the thread title was not changed"):
                assert self.sumo_pages.kb_article_discussion_page._get_thread_title_text(
                ) == self.kb_new_thread_test_data['updated_thread_title']

        with allure.step("Adding data inside the edit this thread title field and clicking on "
                         "the update button"):
            self.sumo_pages.kb_article_discussion_page._click_on_edit_this_thread_option()
            (self.sumo_pages.kb_article_discussion_page
                ._add_text_to_edit_article_thread_title_field(
                    self.kb_new_thread_test_data['second_thread_updated_title']))
            self.sumo_pages.kb_article_discussion_page._click_on_edit_article_thread_update_button(
            )

        with check, allure.step("Verifying that the thread title was changed"):
            assert self.sumo_pages.kb_article_discussion_page._get_thread_title_text(
            ) == self.kb_new_thread_test_data['second_thread_updated_title']

        with allure.step("Navigating back to the discussions page"):
            self.navigate_to_link(
                TestArticleThreads.article_url + KBArticlePageMessages.
                KB_ARTICLE_DISCUSSIONS_ENDPOINT
            )

        with check, allure.step("Verifying that the updated thread title is displayed inside the "
                                "threads list"):
            assert (self.kb_new_thread_test_data['second_thread_updated_title'] in self.sumo_pages
                    .kb_article_discussion_page._get_all_article_threads_titles())

        with allure.step("Clearing all the created threads"):
            self.__clearing_newly_created_thread(thread_info_one['thread_id'])
            self.__clearing_newly_created_thread(thread_info_two['thread_id'])

    # To be used in specific tests
    def __posting_a_new_test_article_manually(self, approve_it: bool,
                                              post_it: bool) -> str:
        if post_it:
            self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()
            self.sumo_pages.kb_article_page._click_on_article_option()
        kb_article_url = self.get_page_url()

        if approve_it:
            self.sumo_pages.kb_article_page._click_on_show_history_option()
            revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()

            self.sumo_pages.kb_article_show_history_page._click_on_review_revision(
                revision_id
            )

            self.sumo_pages.kb_article_review_revision_page._click_on_approve_revision_button()

            self.sumo_pages.kb_article_review_revision_page._click_accept_revision_accept_button()

        return kb_article_url

    # Creating a test kb article to be used across the entire test suite.
    # Needs to take higher priority than the other test methods of this class inside the gh
    # workflow file.
    @pytest.mark.beforeThreadTests
    def test_posting_a_new_kb_test_article(self, request, only_approve_it=False):
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

        self.sumo_pages.kb_article_page._click_on_article_option()
        with open("test_data/test_article", 'w') as file:
            file.write(self.get_page_url())

        TestArticleThreads.article_url = self.get_page_url()

        self.sumo_pages.kb_article_page._click_on_show_history_option()
        revision_id = self.sumo_pages.kb_article_show_history_page._get_last_revision_id()

        self.logger.info("Approving the revision")
        self.sumo_pages.kb_article_revision_flow.approve_kb_revision(revision_id)

    # Will perform a cleanup by deleting the test article at the end.
    # Need be executed after all other methods from this test class in th GH workflow file.
    @pytest.mark.afterThreadTests
    def test_delete_kb_test_article(self):
        self.start_existing_session(self.username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        self.navigate_to_link(TestArticleThreads.article_url)

        self.logger.info("Deleting the created article")
        self.sumo_pages.kb_article_deletion_flow.delete_kb_article()

        with open("test_data/test_article", 'w'):
            pass

    # Clears all posted article threads.
    def __clearing_newly_created_thread(self, thread_id: str):
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.navigate_to_link(
            TestArticleThreads.article_url + KBArticlePageMessages.
            KB_ARTICLE_DISCUSSIONS_ENDPOINT
        )

        self.sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(thread_id)
        self.sumo_pages.kb_article_discussion_page._click_on_delete_this_thread_option()
        (self.sumo_pages.kb_article_discussion_page.
         _click_on_delete_this_thread_reply_confirmation_button())
        self.navigate_to_link(
            TestArticleThreads.article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT)
