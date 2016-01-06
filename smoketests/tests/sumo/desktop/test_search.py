#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from unittestzero import Assert
import pytest
from pages.desktop.page_provider import PageProvider
from pages.desktop.search_page import SearchPage


class TestSearch:

    forum_search_term = "Firefox crash"

    @pytest.mark.nondestructive
    def test_no_query_adv_forum_search(self, mozwebqa, variables):
        if mozwebqa.base_url in ['https://support-dev.allizom.org',
                                 'https://support.mozilla.org']:
            pytest.skip('Search results are not guaranteed to exist on %s' % mozwebqa.base_url)

        refine_search_pg = PageProvider(mozwebqa).refine_search_page()

        # do test
        refine_search_pg.click_support_questions_tab()
        username = variables['users']['default']['username']
        refine_search_pg.type_in_asked_by_box(username)
        refine_search_pg.click_search_button_support()

        Assert.true(refine_search_pg.search_result_count > 0, "No search results not found")

    @pytest.mark.nondestructive
    def test_user_flow_to_forum_post(self, mozwebqa):

        if mozwebqa.base_url == 'https://support-dev.allizom.org':
            pytest.skip('Search results are not guaranteed to exist on support-dev.allizom.org')

        # 1. start on the home page
        PageProvider(mozwebqa).home_page()

        # 2. type "Firefox crashed"
        # 3. hit Enter
        search_pg = SearchPage(mozwebqa)
        search_pg.do_search_on_search_query(self.forum_search_term + "ed")

        # 4. In the results list there are two types of results:
        #    Forum and KB. Click on a forum result.
        #    (Url is in the forum of /questions/[some number])
        # 5. A complete forum thread should be displayed.
        Assert.true(search_pg.is_result_present, "result page is not present.")
        result_thread_title = search_pg.result_question_text()
        Assert.contains(self.forum_search_term, result_thread_title)
        is_reached_right_page = search_pg.click_question_link(self.forum_search_term)
        Assert.true(is_reached_right_page, "a form thread page is not displayed.")
