# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
from random import randrange

import pytest

from pages.desktop.questions_page import AskNewQuestionsPage, QuestionsPage


class TestQuestions:

    @pytest.mark.native
    def test_that_posting_question_works(self, base_url, selenium, variables):
        """Posts a question to /questions"""
        user = variables['users']['default']
        timestamp = datetime.datetime.today()
        q_to_ask = "automation test question %s" % (timestamp)
        q_details = "This is a test. %s" % (timestamp)

        # go to the /questions/new page and log in
        ask_new_questions_page = AskNewQuestionsPage(base_url, selenium).open()
        ask_new_questions_page.sign_in(user['username'], user['password'])

        # post a question
        ask_new_questions_page.click_firefox_product_link()
        ask_new_questions_page.click_category_problem_link()
        ask_new_questions_page.type_question(q_to_ask)
        ask_new_questions_page.close_stage_site_banner()
        ask_new_questions_page.click_none_of_these_solve_my_problem_button()
        view_question_pg = ask_new_questions_page.fill_up_questions_form(q_to_ask, q_details)

        assert q_to_ask == view_question_pg.question
        assert q_details == view_question_pg.question_detail

    @pytest.mark.nondestructive
    def test_that_questions_sorts_correctly_by_filter_equal_to_solved(self, base_url, selenium):
        """
           Goes to the /questions page,
           Verifies the sort filter=solved works
        """
        expected_sorted_text = "SOLVED"

        questions_page = QuestionsPage(base_url, selenium).open()
        questions_page.click_all_products()
        questions_page.click_questions_done_tab()

        questions_page.click_sort_by_solved_questions()
        # if there are no questions in the list then skip the test
        if not questions_page.are_questions_present:
            pytest.skip("No questions present for filter=%s" % expected_sorted_text)

        for question in questions_page.questions:
            # if solved mark is highlighted the question is really solved
            assert 'highlighted' in question.solved_questions_filter

    @pytest.mark.nondestructive
    def test_questions_sorts_correctly_by_filter_equal_to_unanswered(self, base_url, selenium):
        """
           Goes to the /questions page,
           Verifies the sort filter=unanswered works
        """
        expected_sorted_text = "Unanswered"

        questions_page = QuestionsPage(base_url, selenium).open()
        questions_page.click_all_products()
        questions_page.click_all_questions_tab()

        questions_page.click_sort_by_unanswered_questions()
        # if there are no questions in the list then skip the test
        if not questions_page.are_questions_present:
            pytest.skip("No questions present for filter=%s" % expected_sorted_text)

        for question in questions_page.questions:
            assert 0 == question.number_of_replies

    def test_that_questions_problem_count_increments(self, base_url, selenium):
        """Checks if the 'I have this problem too' counter increments"""

        # Can't +1 your own question so will do it logged out
        questions_page = QuestionsPage(base_url, selenium).open()
        questions_page.click_all_products()

        view_question_page = questions_page.click_any_question(1)

        initial_count = view_question_page.problem_count
        view_question_page.click_problem_too_button()
        view_question_page.refresh()
        post_click_count = view_question_page.problem_count

        assert initial_count + 1 == post_click_count

    def test_contributor_flow_to_support_forum_post(self, base_url, selenium, variables):
        """
            Shows a contributor can start on the home page and move
            all the way to answering a question in the forum.
        """
        # 1. Start on the home page
        # 2. Log in
        # 3. Use the contributor bar to go to the forums.
        #    The questions page should list 20 posts.
        # 3.1 go to the question page
        user = variables['users']['default']
        questions_page = QuestionsPage(base_url, selenium).open()
        questions_page.sign_in(user['username'], user['password'])

        questions_page.click_all_products()
        # 3.2 ensure the size of the list is 20
        assert questions_page.questions_count > 0, 'There is not at least one question displayed.'

        # 4. Click on a question. (URL is in the forum of /questions/[some number])
        # 4.1 pick up an arbitrary question and click
        # 4.2 check if it landed on an intended forum page
        question = questions_page.questions[randrange(questions_page.questions_count)]
        forum_page = question.click_question_link()

        # 5. Go to the thread
        # 6. Scroll to the bottom and click into the text field
        # 7. Type reply
        # 7.1 reply the post
        reply = "reply"
        forum_page.post_reply(reply)
        # 7.2 check if posting a reply finishes without an error
        assert forum_page.is_reply_text_present(user['username'], reply), \
            u'reply with "%s" text posted by %s is not present' % (
                reply, user['username'])
