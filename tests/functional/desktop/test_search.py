# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from pages.desktop.refine_search_page import RefineSearchPage
from pages.desktop.search_page import SearchPage
from pages.desktop.support_home_page import SupportHomePage


class TestSearch:

    forum_search_term = "Firefox crash"

    @pytest.mark.nondestructive
    def test_no_query_adv_forum_search(self, base_url, selenium, variables):
        if base_url in ['https://support-dev.allizom.org',
                        'https://support.mozilla.org']:
            pytest.skip('Search results are not guaranteed to exist on %s' % base_url)

        refine_search_pg = RefineSearchPage(base_url, selenium).open()

        # do test
        refine_search_pg.click_support_questions_tab()
        username = variables['users']['default']['username']
        refine_search_pg.type_in_asked_by_box(username)
        refine_search_pg.click_search_button_support()

        assert refine_search_pg.search_result_count > 0, "No search results not found"

    @pytest.mark.nondestructive
    def test_user_flow_to_forum_post(self, base_url, selenium):

        if base_url == 'https://support-dev.allizom.org':
            pytest.skip('Search results are not guaranteed to exist on support-dev.allizom.org')

        # 1. start on the home page
        SupportHomePage(base_url, selenium).open()

        # 2. type "Firefox crashed"
        # 3. hit Enter
        search_pg = SearchPage(base_url, selenium).open()
        # FIXME: This is searching from the search page instead of the home page.
        search_pg.do_search_on_search_query(self.forum_search_term + "ed")

        # 4. In the results list there are two types of results:
        #    Forum and KB. Click on a forum result.
        #    (Url is in the forum of /questions/[some number])
        # 5. A complete forum thread should be displayed.
        assert search_pg.is_result_present, "result page is not present."
        result_thread_title = search_pg.result_question_text()
        assert self.forum_search_term in result_thread_title
        is_reached_right_page = search_pg.click_question_link(self.forum_search_term)
        assert is_reached_right_page, "a form thread page is not displayed."
