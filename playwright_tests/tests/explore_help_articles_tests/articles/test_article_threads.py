import pytest
from playwright.sync_api import expect
import pytest_check as check
from playwright_tests.core.testutilities import TestUtilities
from playwright_tests.messages.explore_help_articles.kb_article_page_messages import (
    KBArticlePageMessages)


class TestArticleThreads(TestUtilities):
    with open('test_data/test_article', 'r') as file:
        article_url = file.read()

    # C2188031
    @pytest.mark.articleThreads
    def test_article_thread_field_validation(self):
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        self.logger.info("Manually navigating to the article endpoint")
        self.navigate_to_link(TestArticleThreads.article_url)
        self.logger.info("Clicking on the 'Discussion' editing tools navbar option")
        self.sumo_pages.kb_article_page._click_on_editing_tools_discussion_option()

        self.logger.info("Clicking on the 'Post a new thread button'")
        self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()

        self.logger.info("Clicking on the 'Post Thread' button without adding any data in the "
                         "form fields")
        self.sumo_pages.kb_article_discussion_page._click_on_submit_new_thread_button()

        self.logger.info("Verifying that we are on the same page")
        expect(
            self.page
        ).to_have_url(
            TestArticleThreads.article_url + KBArticlePageMessages.
            KB_ARTICLE_DISCUSSIONS_NEW_ENDPOINT)

        self.logger.info("Adding one character inside the 'Title' field and clicking the 'Post "
                         "Thread' button")
        self.sumo_pages.kb_article_discussion_page._add_text_to_new_thread_title_field("t")
        self.sumo_pages.kb_article_discussion_page._click_on_submit_new_thread_button()

        self.logger.info("Verifying that we are on the same page")
        expect(
            self.page
        ).to_have_url(TestArticleThreads.article_url + KBArticlePageMessages.
                      KB_ARTICLE_DISCUSSIONS_NEW_ENDPOINT)

        self.logger.info("Clearing the input field")
        self.sumo_pages.kb_article_discussion_page._clear_new_thread_title_field()

        self.logger.info("Adding input with 5 characters inside the title field")
        self.sumo_pages.kb_article_discussion_page._add_text_to_new_thread_title_field(
            super().kb_new_thread_test_data['new_thread_reduced_title']
        )

        self.logger.info("Clicking on the 'Post Thread' button")
        self.sumo_pages.kb_article_discussion_page._click_on_submit_new_thread_button()

        self.logger.info("Verifying that we are on the same page")
        expect(
            self.page
        ).to_have_url(TestArticleThreads.article_url + KBArticlePageMessages.
                      KB_ARTICLE_DISCUSSIONS_NEW_ENDPOINT)

        self.logger.info("Adding one character inside the content field")
        self.sumo_pages.kb_article_discussion_page._add_text_to_new_thread_body_input_field("a")

        self.logger.info("Clicking on the 'Post Thread' button")
        self.sumo_pages.kb_article_discussion_page._click_on_submit_new_thread_button()

        self.logger.info("Verifying that we are on the same page")
        expect(
            self.page
        ).to_have_url(TestArticleThreads.article_url + KBArticlePageMessages.
                      KB_ARTICLE_DISCUSSIONS_NEW_ENDPOINT)

        self.logger.info("Clearing the content field")
        self.sumo_pages.kb_article_discussion_page._clear_new_thread_body_field()

        self.logger.info("Clearing both title and content fields")
        self.sumo_pages.kb_article_discussion_page._clear_new_thread_title_field()
        self.sumo_pages.kb_article_discussion_page._clear_new_thread_body_field()

        self.logger.info("Adding 5 characters inside the thread content field")
        self.sumo_pages.kb_article_discussion_page._add_text_to_new_thread_body_input_field(
            super().kb_new_thread_test_data['new_thread_reduced_body']
        )

        self.logger.info("Clicking on the 'Post Thread' button")
        self.sumo_pages.kb_article_discussion_page._click_on_submit_new_thread_button()

        self.logger.info("Verifying that we are on the same page")
        expect(
            self.page
        ).to_have_url(TestArticleThreads.article_url + KBArticlePageMessages.
                      KB_ARTICLE_DISCUSSIONS_NEW_ENDPOINT)

        self.logger.info("Adding 5 characters inside the thread title field")
        self.sumo_pages.kb_article_discussion_page._add_text_to_new_thread_title_field(
            super().kb_new_thread_test_data['new_thread_reduced_title']
        )

        self.logger.info("Clicking on the 'Cancel' button")
        self.sumo_pages.kb_article_discussion_page._click_on_cancel_new_thread_button()

        self.logger.info("Verifying that the article is not displayed inside the discussion "
                         "thread list")
        expect(
            self.sumo_pages.kb_article_discussion_page._get_thread_by_title_locator(
                super().kb_new_thread_test_data['new_thread_reduced_title']
            )
        ).to_be_hidden()

        self.logger.info("Clicking on the 'Post a new thread' button")
        self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()

        self.logger.info("Adding the minimum required characters inside both title and content "
                         "fields")
        self.sumo_pages.kb_article_discussion_page._add_text_to_new_thread_title_field(
            super().kb_new_thread_test_data['new_thread_reduced_title']
        )
        self.sumo_pages.kb_article_discussion_page._add_text_to_new_thread_body_input_field(
            super().kb_new_thread_test_data['new_thread_reduced_body']
        )

        self.logger.info("Clicking on the 'Post Thread' button")
        self.sumo_pages.kb_article_discussion_page._click_on_submit_new_thread_button()

        thread_url = self.get_page_url()
        thread_id = str(super().number_extraction_from_string_endpoint(
            KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT, thread_url)
        )

        self.logger.info("Manually navigating to the discuss endpoint")
        self.navigate_to_link(
            TestArticleThreads.article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
        )

        self.logger.info("Verifying that the posted thread is successfully displayed")
        expect(
            self.sumo_pages.kb_article_discussion_page._get_posted_thread_locator(
                thread_id
            )
        ).to_be_visible()

        self.__clearing_newly_created_thread(thread_id)

    # C2260840
    @pytest.mark.articleThreads
    def test_thread_replies_counter_increment(self):
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        self.logger.info("Manually navigating to the article endpoint")
        self.navigate_to_link(TestArticleThreads.article_url)
        self.logger.info("Clicking on the article option")
        self.sumo_pages.kb_article_page._click_on_article_option()

        self.logger.info("Clicking on the 'Discussion' editing tools navbar option")
        self.sumo_pages.kb_article_page._click_on_editing_tools_discussion_option()

        self.logger.info("Clicking on the 'Post a new thread button'")
        self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()

        self.logger.info("Posting a new kb article discussion thread")
        thread_info = (self.sumo_pages.post_kb_discussion_thread_flow.
                       add_new_kb_discussion_thread())

        self.logger.info("Verifying that the thread counter is not 0")
        check.equal(
            self.number_extraction_from_string(
                self.sumo_pages.kb_article_discussion_page._get_thread_page_counter_replies_text()
            ),
            0,
            "Thread counter is not 0!"
        )

        self.logger.info("Manually navigating to the discuss endpoint")
        self.navigate_to_link(
            TestArticleThreads.article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
        )

        self.logger.info("Verifying that the reply counter for the posted thread has incremented "
                         "successfully")
        check.equal(
            self.number_extraction_from_string(
                self.sumo_pages.kb_article_discussion_page._get_article_discussions_thread_counter(
                    thread_info['thread_id']
                )
            ),
            0,
            "Incorrect number of replies!"
        )

        self.logger.info("Navigating back to the thread")
        self.sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
            thread_info['thread_id']
        )

        self.logger.info("Posting a new reply with the same user")
        self.sumo_pages.kb_article_discussion_page._fill_the_thread_post_a_reply_textarea_field(
            self.kb_new_thread_test_data['thread_reply_body']
        )
        self.sumo_pages.kb_article_discussion_page._click_on_thread_post_reply_button()

        self.logger.info("Verifying that the thread counter is 1")
        check.equal(
            self.number_extraction_from_string(
                self.sumo_pages.kb_article_discussion_page._get_thread_page_counter_replies_text()
            ),
            1,
            "Thread counter is not 0!"
        )

        self.logger.info("Manually navigating to the discuss endpoint")
        self.navigate_to_link(
            TestArticleThreads.article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
        )

        self.logger.info("Verifying that the reply counter for the posted thread has incremented "
                         "successfully")
        check.equal(
            self.number_extraction_from_string(
                self.sumo_pages.kb_article_discussion_page._get_article_discussions_thread_counter(
                    thread_info['thread_id']
                )
            ),
            1,
            "Incorrect number of replies!"
        )

        self.__clearing_newly_created_thread(thread_info['thread_id'])

    # C2260840, C2260809
    @pytest.mark.articleThreads
    def test_thread_replies_counter_decrement(self):
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        self.logger.info("Manually navigating to the article endpoint")
        self.navigate_to_link(TestArticleThreads.article_url)
        self.logger.info("Clicking on the 'Discussion' editing tools navbar option")
        self.sumo_pages.kb_article_page._click_on_editing_tools_discussion_option()

        self.logger.info("Deleting session cookies and signing in with a normal account")
        self.delete_cookies()
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts['TEST_ACCOUNT_12']
        ))

        self.logger.info("Clicking on the 'Post a new thread button'")
        self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()

        self.logger.info("Posting a new kb article discussion thread")
        thread_info = (self.sumo_pages.post_kb_discussion_thread_flow.
                       add_new_kb_discussion_thread())

        self.logger.info("Posting a new reply with the same user")
        self.sumo_pages.kb_article_discussion_page._fill_the_thread_post_a_reply_textarea_field(
            self.kb_new_thread_test_data['thread_reply_body']
        )
        self.sumo_pages.kb_article_discussion_page._click_on_thread_post_reply_button()

        thread_reply_id = self.sumo_pages.kb_article_discussion_page._get_thread_reply_id(
            self.get_page_url()
        )

        self.logger.info("Deleting session cookies and signing in with an admin account")
        self.delete_cookies()
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts['TEST_ACCOUNT_MODERATOR']
        ))

        self.logger.info("Posting a new reply with the same user")
        self.sumo_pages.kb_article_discussion_page._fill_the_thread_post_a_reply_textarea_field(
            self.kb_new_thread_test_data['thread_reply_body']
        )
        self.sumo_pages.kb_article_discussion_page._click_on_thread_post_reply_button()

        self.logger.info("Verifying that the reply counter for the posted thread has incremented "
                         "successfully")
        check.equal(
            self.number_extraction_from_string(
                self.sumo_pages.kb_article_discussion_page._get_thread_page_counter_replies_text()
            ),
            2,
            "Incorrect number of replies!"
        )

        self.logger.info("Manually navigating to the discuss endpoint")
        self.navigate_to_link(
            TestArticleThreads.article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
        )

        self.logger.info("Verifying that the reply counter for the posted thread has incremented "
                         "successfully")
        check.equal(
            self.number_extraction_from_string(
                self.sumo_pages.kb_article_discussion_page._get_article_discussions_thread_counter(
                    thread_info['thread_id']
                )
            ),
            2,
            "Incorrect number of replies!"
        )

        self.sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
            thread_info['thread_id']
        )

        self.logger.info("Clicking on the 3 dotted menu for the posted reply")
        self.sumo_pages.kb_article_discussion_page._click_on_dotted_menu_for_a_certain_reply(
            thread_reply_id
        )

        self.logger.info("Clicking on the 'Delete this post' option")
        self.sumo_pages.kb_article_discussion_page._click_on_delete_this_thread_reply(
            thread_reply_id
        )
        (self.sumo_pages.kb_article_discussion_page
         ._click_on_delete_this_thread_reply_confirmation_button())

        self.logger.info("Verifying that the reply counter for the posted thread has incremented "
                         "successfully")
        check.equal(
            self.number_extraction_from_string(
                self.sumo_pages.kb_article_discussion_page._get_thread_page_counter_replies_text()
            ),
            1,
            "Incorrect number of replies!"
        )

        self.logger.info("Manually navigating to the discuss endpoint")
        self.navigate_to_link(
            TestArticleThreads.article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
        )

        self.logger.info("Verifying that the reply counter for the posted thread has incremented "
                         "successfully")
        check.equal(
            self.number_extraction_from_string(
                self.sumo_pages.kb_article_discussion_page._get_article_discussions_thread_counter(
                    thread_info['thread_id']
                )
            ),
            1,
            "Incorrect number of replies!"
        )

        self.__clearing_newly_created_thread(thread_info['thread_id'])

    @pytest.mark.articleThreads
    @pytest.mark.parametrize("username", ['TEST_ACCOUNT_12', 'TEST_ACCOUNT_MODERATOR', ''])
    def test_article_thread_author_filter(self, username):
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        self.logger.info("Manually navigating to the article endpoint")
        self.navigate_to_link(TestArticleThreads.article_url)
        self.logger.info("Clicking on the 'Discussion' editing tools navbar option")
        self.sumo_pages.kb_article_page._click_on_editing_tools_discussion_option()

        self.logger.info("Clicking on the 'Post a new thread button'")
        self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()

        self.logger.info("Posting a new kb article discussion thread")
        thread_info = self.sumo_pages.post_kb_discussion_thread_flow.add_new_kb_discussion_thread()

        self.logger.info("Navigating back to the article discussion page")
        self.navigate_to_link(
            TestArticleThreads.article_url + KBArticlePageMessages.
            KB_ARTICLE_DISCUSSIONS_ENDPOINT
        )

        self.logger.info("Deleting user session and signing in with a non-admin account")
        self.delete_cookies()

        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        self.logger.info("Clicking on the 'Post a new thread button'")
        self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()

        self.logger.info("Posting a new kb article discussion thread")
        thread_info_two = (self.sumo_pages.post_kb_discussion_thread_flow.
                           add_new_kb_discussion_thread())

        self.logger.info("Navigating back to the article discussion page")
        self.navigate_to_link(
            TestArticleThreads.article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
        )

        if username == 'TEST_ACCOUNT_MODERATOR':
            self.delete_cookies()
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))
        elif username != 'TEST_ACCOUNT_12':
            self.delete_cookies()

        self.logger.info("Clicking on the 'Author' filter")
        self.sumo_pages.kb_article_discussion_page._click_on_article_thread_author_replies_filter()

        self.logger.info("Verifying that the authors are in reverse alphabetical order")
        check.not_equal(
            self.sumo_pages.kb_article_discussion_page._get_all_article_threads_authors(),
            sorted(
                self.sumo_pages.kb_article_discussion_page._get_all_article_threads_authors()
            )
        )

        self.logger.info("Clicking on the 'Author' filter again")
        self.sumo_pages.kb_article_discussion_page._click_on_article_thread_author_replies_filter()

        self.logger.info("Verifying that the authors are in alphabetical order")
        check.equal(
            self.sumo_pages.kb_article_discussion_page._get_all_article_threads_authors(),
            sorted(self.sumo_pages.kb_article_discussion_page._get_all_article_threads_authors())
        )

        self.__clearing_newly_created_thread(thread_info['thread_id'])
        self.__clearing_newly_created_thread(thread_info_two['thread_id'])

    @pytest.mark.articleThreads
    @pytest.mark.parametrize("username", ['TEST_ACCOUNT_12', 'TEST_ACCOUNT_MODERATOR', ''])
    def test_article_thread_replies_filter(self, username):
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        self.logger.info("Manually navigating to the article endpoint")
        self.navigate_to_link(TestArticleThreads.article_url)
        self.logger.info("Clicking on the 'Discussion' editing tools navbar option")
        self.sumo_pages.kb_article_page._click_on_editing_tools_discussion_option()

        self.logger.info("Clicking on the 'Post a new thread button'")
        self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()

        self.logger.info("Posting a new kb article discussion thread")
        thread_info = self.sumo_pages.post_kb_discussion_thread_flow.add_new_kb_discussion_thread()

        self.logger.info("Posting a new reply with the same user")
        self.sumo_pages.kb_article_discussion_page._fill_the_thread_post_a_reply_textarea_field(
            self.kb_new_thread_test_data['thread_reply_body']
        )
        self.sumo_pages.kb_article_discussion_page._click_on_thread_post_reply_button()

        self.logger.info("Navigating back to the article discussion page")
        self.navigate_to_link(
            TestArticleThreads.article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
        )

        self.logger.info("Clicking on the 'Post a new thread button'")
        self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()

        self.logger.info("Posting a new kb article discussion thread")
        thread_info_two = (self.sumo_pages.post_kb_discussion_thread_flow.
                           add_new_kb_discussion_thread())

        self.logger.info("Navigating back to the article discussion page")
        self.navigate_to_link(
            TestArticleThreads.article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
        )

        if username == "TEST_ACCOUNT_12":
            self.delete_cookies()
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_12"]
            ))
        elif username == '':
            self.delete_cookies()

        self.logger.info("Clicking on the 'Replies' filter")
        self.sumo_pages.kb_article_discussion_page._click_on_article_thread_replies_filter()

        self.logger.info("Verifying that the replies is in descending order")
        check.is_true(
            self.is_descending(
                self.sumo_pages.kb_article_discussion_page._get_all_article_threads_replies()
            )
        )

        self.logger.info("Clicking on the 'Replies' filter again")
        self.sumo_pages.kb_article_discussion_page._click_on_article_thread_replies_filter()

        self.logger.info("Verifying that the replies is in descending order")
        check.is_false(
            self.is_descending(
                self.sumo_pages.kb_article_discussion_page._get_all_article_threads_replies()
            )
        )

        self.__clearing_newly_created_thread(thread_info['thread_id'])
        self.__clearing_newly_created_thread(thread_info_two['thread_id'])

    @pytest.mark.articleThreads
    def test_article_lock_thread_non_admin_users(self):
        self.logger.info("Signing in with a normal user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts['TEST_ACCOUNT_12']
        ))

        kb_url = self.__posting_a_new_test_article_manually(approve_it=False,
                                                            post_it=True)

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Signing in with an admin account and approving the article")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.__posting_a_new_test_article_manually(approve_it=True, post_it=False)

        self.logger.info("Clicking on the 'Discussion' editing tools navbar option")
        self.sumo_pages.kb_article_page._click_on_editing_tools_discussion_option()

        self.logger.info("Clicking on the 'Post a new thread button'")
        self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()

        self.logger.info("Posting a new kb article discussion thread")
        thread_info_one = (self.sumo_pages.post_kb_discussion_thread_flow.
                           add_new_kb_discussion_thread())

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Signing in with a normal user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts['TEST_ACCOUNT_12']
        ))

        self.logger.info("Navigating back to the discussions page")
        self.navigate_to_link(
            kb_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
        )

        self.logger.info("Clicking on the 'Post a new thread button'")
        self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()

        self.logger.info("Posting a new kb article discussion thread")
        thread_info_two = (self.sumo_pages.post_kb_discussion_thread_flow.
                           add_new_kb_discussion_thread())

        self.logger.info("Navigating back to the discussions page")
        self.navigate_to_link(
            kb_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
        )

        self.logger.info("Clicking on the thread posted by another user")
        self.sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
            thread_info_one['thread_id']
        )

        self.logger.info("Verifying that the 'Lock thread' option is not available'")
        expect(
            self.sumo_pages.kb_article_discussion_page._get_lock_this_article_thread_locator()
        ).to_be_hidden()

        self.logger.info("Navigating back to the article discussions page")
        self.navigate_to_link(
            kb_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
        )

        self.logger.info("Clicking on the thread posted by self")
        self.sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
            thread_info_two['thread_id']
        )

        self.logger.info("Verifying that the 'Lock thread' option is not available'")
        expect(
            self.sumo_pages.kb_article_discussion_page._get_lock_this_article_thread_locator()
        ).to_be_hidden()

        self.logger.info("Deleting user sessions")
        self.delete_cookies()

        self.logger.info("Verifying that the 'Lock thread' option is not available")
        expect(
            self.sumo_pages.kb_article_discussion_page._get_lock_this_article_thread_locator()
        ).to_be_hidden()

        self.logger.info("Signing in with an admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Navigating to the article and deleting it")
        self.navigate_to_link(kb_url)
        self.sumo_pages.kb_article_page._click_on_show_history_option()
        self.sumo_pages.kb_article_show_history_page._click_on_delete_this_document_button()
        self.sumo_pages.kb_article_show_history_page._click_on_confirmation_delete_button()

    #  C2260810
    @pytest.mark.articleThreads
    @pytest.mark.parametrize("username", ['TEST_ACCOUNT_MODERATOR', 'TEST_ACCOUNT_12', ''])
    def test_article_lock_thread_functionality(self, username):
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        self.logger.info("Manually navigating to the article endpoint")
        self.navigate_to_link(TestArticleThreads.article_url)
        self.logger.info("Clicking on the 'Discussion' editing tools navbar option")
        self.sumo_pages.kb_article_page._click_on_editing_tools_discussion_option()

        self.logger.info("Clicking on the 'Post a new thread button'")
        self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()

        self.logger.info("Posting a new kb article discussion thread")
        thread_info_one = (self.sumo_pages.post_kb_discussion_thread_flow.
                           add_new_kb_discussion_thread())

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Signing in with a normal user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts['TEST_ACCOUNT_12']
        ))

        self.logger.info("Navigating back to the discussions page")
        self.navigate_to_link(
            TestArticleThreads.article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
        )

        self.logger.info("Clicking on the 'Post a new thread button'")
        self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()

        self.logger.info("Posting a new kb article discussion thread")
        thread_info_two = (self.sumo_pages.post_kb_discussion_thread_flow.
                           add_new_kb_discussion_thread())

        self.logger.info("Navigating back to the discussions page")
        self.navigate_to_link(
            TestArticleThreads.article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
        )

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Signing in with an admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Clicking on the thread posted by self user")
        self.sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
            thread_info_one['thread_id']
        )

        self.logger.info("Clicking on 'Lock this thread' option")
        self.sumo_pages.kb_article_discussion_page._click_on_lock_this_article_thread_option()

        if username == 'TEST_ACCOUNT_12':
            self.logger.info("Deleting user session")
            self.delete_cookies()
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_12']
            ))

            self.logger.info("Verifying that the correct thread locked message is displayed")
            check.equal(
                self.sumo_pages.kb_article_discussion_page.
                _get_text_of_locked_article_thread_text(),
                KBArticlePageMessages.KB_ARTICLE_LOCKED_THREAD_MESSAGE
            )
        elif username == '':
            self.logger.info("Deleting user session")
            self.delete_cookies()

        self.logger.info("Verifying that the 'Post a reply' textarea field is not displayed")
        expect(
            self.sumo_pages.kb_article_discussion_page._get_thread_post_a_reply_textarea_field()
        ).to_be_hidden()

        self.logger.info("Verifying that the 'Locked' status is displayed under article header")
        expect(
            self.sumo_pages.kb_article_discussion_page._get_locked_article_status()
        ).to_be_visible()

        self.logger.info("Navigating back to the discussions page")
        self.navigate_to_link(
            TestArticleThreads.article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
        )

        if username != 'TEST_ACCOUNT_MODERATOR':
            self.delete_cookies()
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        self.logger.info("Clicking on the thread posted by the other user")
        self.sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
            thread_info_two['thread_id']
        )

        self.logger.info("Clicking on 'Lock this thread' option")
        self.sumo_pages.kb_article_discussion_page._click_on_lock_this_article_thread_option()

        if username == 'TEST_ACCOUNT_12':
            self.logger.info("Deleting user session")
            self.delete_cookies()
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_12']
            ))
            self.logger.info("Verifying that the correct thread locked message is displayed")
            check.equal(
                self.sumo_pages.kb_article_discussion_page.
                _get_text_of_locked_article_thread_text(),
                KBArticlePageMessages.KB_ARTICLE_LOCKED_THREAD_MESSAGE
            )
        elif username == '':
            self.logger.info("Deleting user session")
            self.delete_cookies()

        self.logger.info("Verifying that the 'Locked' status is displayed under article header")
        expect(
            self.sumo_pages.kb_article_discussion_page._get_locked_article_status()
        ).to_be_visible()

        self.logger.info("Verifying that the 'Post a reply' textarea field is not displayed")
        expect(
            self.sumo_pages.kb_article_discussion_page._get_thread_post_a_reply_textarea_field()
        ).to_be_hidden()

        self.__clearing_newly_created_thread(thread_info_one['thread_id'])
        self.__clearing_newly_created_thread(thread_info_two['thread_id'])

    # C2260810
    @pytest.mark.articleThreads
    @pytest.mark.parametrize("username", ['TEST_ACCOUNT_MODERATOR', 'TEST_ACCOUNT_12', ''])
    def test_article_unlock_thread_functionality(self, username):
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        self.logger.info("Manually navigating to the article endpoint")
        self.navigate_to_link(TestArticleThreads.article_url)
        self.logger.info("Clicking on the 'Discussion' editing tools navbar option")
        self.sumo_pages.kb_article_page._click_on_editing_tools_discussion_option()

        self.logger.info("Clicking on the 'Post a new thread button'")
        self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()

        self.logger.info("Posting a new kb article discussion thread")
        thread_info_one = (self.sumo_pages.post_kb_discussion_thread_flow.
                           add_new_kb_discussion_thread())

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Signing in with a normal user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts['TEST_ACCOUNT_12']
        ))

        self.logger.info("Navigating back to the discussions page")
        self.navigate_to_link(
            TestArticleThreads.article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
        )

        self.logger.info("Clicking on the 'Post a new thread button'")
        self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()

        self.logger.info("Posting a new kb article discussion thread")
        thread_info_two = (self.sumo_pages.post_kb_discussion_thread_flow.
                           add_new_kb_discussion_thread())

        self.logger.info("Navigating back to the discussions page")
        self.navigate_to_link(
            TestArticleThreads.article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
        )

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Signing in with an admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Clicking on the thread posted by self user")
        self.sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
            thread_info_one['thread_id']
        )

        self.logger.info("Verifying that the correct 'Lock this thread' option text is displayed")
        check.equal(
            self.sumo_pages.kb_article_discussion_page._get_lock_this_article_thread_option_text(),
            KBArticlePageMessages.KB_ARTICLE_LOCK_THIS_THREAD_OPTION
        )

        self.logger.info("Clicking on 'Lock this thread' option")
        self.sumo_pages.kb_article_discussion_page._click_on_lock_this_article_thread_option()

        self.logger.info("Verifying that the correct 'Unlock this thread' text is displayed")
        check.equal(
            self.sumo_pages.kb_article_discussion_page._get_lock_this_article_thread_option_text(),
            KBArticlePageMessages.KB_ARTICLE_UNLOCK_THIS_THREAD_OPTION
        )

        if username == 'TEST_ACCOUNT_12':
            self.logger.info("Deleting user session")
            self.delete_cookies()
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_12']
            ))
            self.logger.info("Verifying that the 'Unlock this thread' option is no displayed")
            expect(
                self.sumo_pages.kb_article_discussion_page._get_lock_this_article_thread_locator()
            ).to_be_hidden()
        if username == '':
            self.logger.info("Deleting user session")
            self.delete_cookies()
            self.logger.info("Verifying that the 'Unlock this thread' option is no displayed")
            expect(
                self.sumo_pages.kb_article_discussion_page._get_lock_this_article_thread_locator()
            ).to_be_hidden()

        if username != 'TEST_ACCOUNT_MODERATOR':
            self.logger.info("Deleting user session")
            self.delete_cookies()
            self.logger.info("Signing in with an admin account")
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        self.logger.info("Clicking on the 'Unlock this thread'")
        self.sumo_pages.kb_article_discussion_page._click_on_lock_this_article_thread_option()

        if username == 'TEST_ACCOUNT_12':
            self.logger.info("Deleting user session")
            self.delete_cookies()
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_12']
            ))
            self.logger.info("Verifying that the textarea field is available")
            expect(
                self.sumo_pages.kb_article_discussion_page._get_thread_post_a_reply_textarea_field(
                )
            ).to_be_visible()
        if username == '':
            self.logger.info("Deleting user session")
            self.delete_cookies()
            self.logger.info("Verifying that the textarea field is not available")
            expect(
                self.sumo_pages.kb_article_discussion_page._get_thread_post_a_reply_textarea_field(
                )
            ).to_be_hidden()

        self.logger.info("Verifying that the 'Locked' header text is not displayed")
        expect(
            self.sumo_pages.kb_article_discussion_page._get_locked_article_status()
        ).to_be_hidden()

        self.logger.info("Verifying that the 'Thread locked' thread page message is not displayed")
        expect(
            self.sumo_pages.kb_article_discussion_page._get_text_of_locked_article_thread_locator()
        ).to_be_hidden()

        if username != "TEST_ACCOUNT_MODERATOR":
            self.logger.info("Deleting user session")
            self.delete_cookies()
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        self.logger.info("Navigating back to the discussions page")
        self.navigate_to_link(
            TestArticleThreads.article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
        )

        self.logger.info("Clicking on the thread posted by another user")
        self.sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
            thread_info_two['thread_id']
        )

        self.logger.info("Verifying that the correct 'Lock this thread' option text is displayed")
        check.equal(
            self.sumo_pages.kb_article_discussion_page._get_lock_this_article_thread_option_text(),
            KBArticlePageMessages.KB_ARTICLE_LOCK_THIS_THREAD_OPTION
        )

        self.logger.info("Clicking on 'Lock this thread' option")
        self.sumo_pages.kb_article_discussion_page._click_on_lock_this_article_thread_option()

        self.logger.info("Verifying that the correct 'Unlock this thread' text is displayed")
        check.equal(
            self.sumo_pages.kb_article_discussion_page._get_lock_this_article_thread_option_text(),
            KBArticlePageMessages.KB_ARTICLE_UNLOCK_THIS_THREAD_OPTION
        )

        if username == 'TEST_ACCOUNT_12':
            self.logger.info("Deleting user session")
            self.delete_cookies()
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_12']
            ))
            self.logger.info("Verifying that the 'Unlock this thread' option is no displayed")
            expect(
                self.sumo_pages.kb_article_discussion_page._get_lock_this_article_thread_locator()
            ).to_be_hidden()
        if username == '':
            self.logger.info("Deleting user session")
            self.delete_cookies()
            self.logger.info("Verifying that the 'Unlock this thread' option is no displayed")
            expect(
                self.sumo_pages.kb_article_discussion_page._get_lock_this_article_thread_locator()
            ).to_be_hidden()

        if username != 'TEST_ACCOUNT_MODERATOR':
            self.logger.info("Deleting user session")
            self.delete_cookies()
            self.logger.info("Signing in with an admin account")
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        self.logger.info("Clicking on the 'Unlock this thread'")
        self.sumo_pages.kb_article_discussion_page._click_on_lock_this_article_thread_option()

        if username == 'TEST_ACCOUNT_12':
            self.logger.info("Deleting user session")
            self.delete_cookies()
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_12']
            ))
            self.logger.info("Verifying that the textarea field is available")
            expect(
                self.sumo_pages.kb_article_discussion_page._get_thread_post_a_reply_textarea_field(
                )
            ).to_be_visible()
        if username == '':
            self.logger.info("Deleting user session")
            self.delete_cookies()
            self.logger.info("Verifying that the textarea field is not available")
            expect(
                self.sumo_pages.kb_article_discussion_page._get_thread_post_a_reply_textarea_field(
                )
            ).to_be_hidden()

        self.logger.info("Verifying that the 'Locked' header text is not displayed")
        expect(
            self.sumo_pages.kb_article_discussion_page._get_locked_article_status()
        ).to_be_hidden()

        self.logger.info("Verifying that the 'Thread locked' thread page message is not displayed")
        expect(
            self.sumo_pages.kb_article_discussion_page._get_text_of_locked_article_thread_locator()
        ).to_be_hidden()

        self.__clearing_newly_created_thread(thread_info_one['thread_id'])
        self.__clearing_newly_created_thread(thread_info_two['thread_id'])

    # C2260811
    @pytest.mark.articleThreads
    @pytest.mark.parametrize("username", ['TEST_ACCOUNT_MODERATOR', 'TEST_ACCOUNT_12', ''])
    def test_article_thread_sticky(self, username):
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        kb_article_url = self.__posting_a_new_test_article_manually(post_it=True, approve_it=True)

        self.logger.info("Clicking on the 'Discussion' editing tools navbar option")
        self.sumo_pages.kb_article_page._click_on_editing_tools_discussion_option()

        self.logger.info("Clicking on the 'Post a new thread button'")
        self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()

        self.logger.info("Posting a new kb article discussion thread")
        thread_info_one = (self.sumo_pages.post_kb_discussion_thread_flow.
                           add_new_kb_discussion_thread())

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Signing in with a normal user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts['TEST_ACCOUNT_12']
        ))

        self.logger.info("Navigating back to the discussions page")
        self.navigate_to_link(
            kb_article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
        )

        self.logger.info("Clicking on the 'Post a new thread button'")
        self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()

        self.logger.info("Posting a new kb article discussion thread")
        thread_info_two = (self.sumo_pages.post_kb_discussion_thread_flow.
                           add_new_kb_discussion_thread(title='Other test thread'))

        self.logger.info("Verifying that the 'Sticky this thread' option is not displayed")
        expect(
            self.sumo_pages.kb_article_discussion_page._get_sticky_this_thread_locator()
        ).to_be_hidden()

        self.logger.info("Navigating back to the discussions page")
        self.navigate_to_link(
            kb_article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
        )

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Signing in with an admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Clicking on the thread self posted thread")
        self.sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
            thread_info_one['thread_id']
        )

        self.logger.info("Clicking on the sticky this thread option")
        self.sumo_pages.kb_article_discussion_page._click_on_sticky_this_thread_option()

        self.logger.info("Verifying that the text changed to 'Unsticky this thread'")
        check.equal(
            self.sumo_pages.kb_article_discussion_page._get_text_of_sticky_this_thread_option(),
            KBArticlePageMessages.KB_ARTICLE_UNSTICKY_OPTION
        )

        if username == 'TEST_ACCOUNT_12':
            self.delete_cookies()
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_12']
            ))
            self.logger.info("Verifying that the unsitcky this thread option is not availabe")
            expect(
                self.sumo_pages.kb_article_discussion_page._get_sticky_this_thread_locator()
            ).to_be_hidden()
        if username == '':
            self.delete_cookies()
            self.logger.info("Verifying that the unsitcky this thread option is not availabe")
            expect(
                self.sumo_pages.kb_article_discussion_page._get_sticky_this_thread_locator()
            ).to_be_hidden()

        self.logger.info("Verifying that the 'Sticky' status is displayed")
        expect(
            self.sumo_pages.kb_article_discussion_page._get_sticky_this_thread_status_locator()
        ).to_be_visible()

        self.logger.info("Navigating back to the discussions page")
        self.navigate_to_link(
            kb_article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
        )

        self.logger.info("Verifying that the sticky article is displayed in top of the list")
        check.equal(
            self.sumo_pages.kb_article_discussion_page._get_all_article_threads_titles()[0],
            thread_info_one['thread_title']
        )

        if username != 'TEST_ACCOUNT_MODERATOR':
            self.delete_cookies()
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            ))

        self.logger.info("Clicking on the thread self posted thread")
        self.sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
            thread_info_one['thread_id']
        )

        self.logger.info("Clicking on the unsticky this thread option")
        self.sumo_pages.kb_article_discussion_page._click_on_sticky_this_thread_option()

        self.logger.info("Verifying that the text changed to 'Sticky this thread'")
        check.equal(
            self.sumo_pages.kb_article_discussion_page._get_text_of_sticky_this_thread_option(),
            KBArticlePageMessages.KB_ARTICLE_STICKY_THIS_THREAD_OPTION
        )

        if username == 'TEST_ACCOUNT_12':
            self.delete_cookies()
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts['TEST_ACCOUNT_12']
            ))
        if username == '':
            self.delete_cookies()

        self.logger.info("Verifying that the 'Sticky' status is not displayed")
        expect(
            self.sumo_pages.kb_article_discussion_page._get_sticky_this_thread_status_locator()
        ).to_be_hidden()

        self.logger.info("Navigating back to the discussions page")
        self.navigate_to_link(
            kb_article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
        )

        self.logger.info("Verifying that the sticky article is not displayed in top of the list")
        check.equal(
            self.sumo_pages.kb_article_discussion_page._get_all_article_threads_titles()[0],
            thread_info_two['thread_title']
        )

        self.delete_cookies()
        self.start_existing_session(self.username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        self.navigate_to_link(kb_article_url)
        self.sumo_pages.kb_article_page._click_on_show_history_option()
        self.sumo_pages.kb_article_show_history_page._click_on_delete_this_document_button()
        self.sumo_pages.kb_article_show_history_page._click_on_confirmation_delete_button()

    #  C2260808, C2260823
    @pytest.mark.articleThreads
    @pytest.mark.parametrize("thread_author", ['self', 'other'])
    def test_article_thread_content_edit(self, thread_author):
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        self.logger.info("Manually navigating to the article endpoint")
        self.navigate_to_link(TestArticleThreads.article_url)
        self.logger.info("Clicking on the 'Discussion' editing tools navbar option")
        self.sumo_pages.kb_article_page._click_on_editing_tools_discussion_option()

        self.logger.info("Clicking on the 'Post a new thread button'")
        self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()

        self.logger.info("Posting a new kb article discussion thread")
        thread_info_one = (self.sumo_pages.post_kb_discussion_thread_flow.
                           add_new_kb_discussion_thread())

        self.logger.info("Deleting user session")
        self.delete_cookies()

        self.logger.info("Signing in with a normal user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts['TEST_ACCOUNT_12']
        ))

        self.logger.info("Navigating back to the discussions page")
        self.navigate_to_link(
            TestArticleThreads.article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
        )

        self.logger.info("Clicking on the 'Post a new thread button'")
        self.sumo_pages.kb_article_discussion_page._click_on_post_a_new_thread_option()

        self.logger.info("Posting a new kb article discussion thread")
        thread_info_two = (self.sumo_pages.post_kb_discussion_thread_flow.
                           add_new_kb_discussion_thread())

        self.logger.info("Clicking on the 'Edit this thread' option")
        self.sumo_pages.kb_article_discussion_page._click_on_edit_this_thread_option()

        self.logger.info("Adding data inside the title field")
        self.sumo_pages.kb_article_discussion_page._add_text_to_edit_article_thread_title_field(
            self.kb_new_thread_test_data['updated_thread_title']
        )

        self.logger.info("Clicking on the 'Cancel' button")
        self.sumo_pages.kb_article_discussion_page._click_on_edit_article_thread_cancel_button()

        self.logger.info("Verifying that the thread title was not changed")
        check.equal(
            self.sumo_pages.kb_article_discussion_page._get_thread_title_text(),
            thread_info_two['thread_title']
        )

        self.logger.info("Clicking on the 'Edit this thread' option")
        self.sumo_pages.kb_article_discussion_page._click_on_edit_this_thread_option()

        self.logger.info("Adding data inside the title field")
        self.sumo_pages.kb_article_discussion_page._add_text_to_edit_article_thread_title_field(
            self.kb_new_thread_test_data['updated_thread_title']
        )

        self.logger.info("Clicking on the 'Update' button")
        self.sumo_pages.kb_article_discussion_page._click_on_edit_article_thread_update_button()

        self.logger.info("Verifying that the thread title was changed")
        check.equal(
            self.sumo_pages.kb_article_discussion_page._get_thread_title_text(),
            self.kb_new_thread_test_data['updated_thread_title']
        )

        self.logger.info("Deleting user session")
        self.delete_cookies()

        expect(
            self.sumo_pages.kb_article_discussion_page._get_edit_this_thread_locator()
        ).to_be_hidden()

        self.logger.info("Signing in with an Admin account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Navigating back to the discussions page")
        self.navigate_to_link(
            TestArticleThreads.article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
        )

        if thread_author == 'self':
            self.logger.info("Clicking on the self posted thread")
            self.sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
                thread_info_one["thread_id"]
            )
        else:
            self.logger.info("Clicking on the other user posted thread")
            self.sumo_pages.kb_article_discussion_page._click_on_a_particular_thread(
                thread_info_two["thread_id"])

        self.logger.info("Clicking on the 'Edit this thread' option")
        self.sumo_pages.kb_article_discussion_page._click_on_edit_this_thread_option()

        self.logger.info("Adding data inside the title field")
        self.sumo_pages.kb_article_discussion_page._add_text_to_edit_article_thread_title_field(
            self.kb_new_thread_test_data['second_thread_updated_title']
        )

        self.logger.info("Clicking on the 'Cancel' button")
        self.sumo_pages.kb_article_discussion_page._click_on_edit_article_thread_cancel_button()

        if thread_author == 'self':
            self.logger.info("Verifying that the thread title was not changed")
            check.equal(
                self.sumo_pages.kb_article_discussion_page._get_thread_title_text(),
                thread_info_one['thread_title']
            )
        else:
            self.logger.info("Verifying that the thread title was not changed")
            check.equal(
                self.sumo_pages.kb_article_discussion_page._get_thread_title_text(),
                self.kb_new_thread_test_data['updated_thread_title']
            )

        self.logger.info("Clicking on the 'Edit this thread' option")
        self.sumo_pages.kb_article_discussion_page._click_on_edit_this_thread_option()

        self.logger.info("Adding data inside the title field")
        self.sumo_pages.kb_article_discussion_page._add_text_to_edit_article_thread_title_field(
            self.kb_new_thread_test_data['second_thread_updated_title']
        )

        self.logger.info("Clicking on the 'Update' button")
        self.sumo_pages.kb_article_discussion_page._click_on_edit_article_thread_update_button()

        self.logger.info("Verifying that the thread title was changed")
        check.equal(
            self.sumo_pages.kb_article_discussion_page._get_thread_title_text(),
            self.kb_new_thread_test_data['second_thread_updated_title']
        )

        self.logger.info("Navigating back to the discussions page")
        self.navigate_to_link(
            TestArticleThreads.article_url + KBArticlePageMessages.KB_ARTICLE_DISCUSSIONS_ENDPOINT
        )

        self.logger.info("Verifying that the updated thread title is displayed inside the "
                         "threads list")
        check.is_in(
            self.kb_new_thread_test_data['second_thread_updated_title'],
            self.sumo_pages.kb_article_discussion_page._get_all_article_threads_titles()
        )

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

        self.sumo_pages.kb_article_show_history_page._click_on_review_revision(
            revision_id
        )

        self.sumo_pages.kb_article_review_revision_page._click_on_approve_revision_button()

        self.sumo_pages.kb_article_review_revision_page._click_accept_revision_accept_button()

    # Will perform a cleanup by deleting the test article at the end.
    # Need be executed after all other methods from this test class in th GH workflow file.
    @pytest.mark.afterThreadTests
    def test_delete_kb_test_article(self):
        self.start_existing_session(self.username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        self.navigate_to_link(TestArticleThreads.article_url)
        self.sumo_pages.kb_article_page._click_on_show_history_option()
        self.sumo_pages.kb_article_show_history_page._click_on_delete_this_document_button()
        self.sumo_pages.kb_article_show_history_page._click_on_confirmation_delete_button()

        with open("test_data/test_article", 'w'):
            pass

    # Clears all posted article threads.
    def __clearing_newly_created_thread(self, thread_id: str):
        self.delete_cookies()
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
