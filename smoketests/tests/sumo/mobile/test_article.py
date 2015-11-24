#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


from pages.mobile.page_provider import PageProvider


class TestArticle:

    def test_that_checks_the_vote_of_an_article(self, mozwebqa):
        home = PageProvider(mozwebqa).home_page()

        article_page = home.search_for('firefox').results[0].click()
        assert '| Mozilla Support' in article_page.page_title
        assert 'Was this article helpful?' == article_page.helpful_header_text

        article_page.click_helpful_button()
        article_page.wait_for_vote_message_text(u'Glad to hear it \u2014 thanks for the feedback!')
