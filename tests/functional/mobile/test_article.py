# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from pages.mobile.home import Home


class TestArticle:

    def test_that_checks_the_vote_of_an_article(self, base_url, selenium):
        home = Home(base_url, selenium).open()

        article_page = home.search_for('firefox').results[0].click()
        assert '| Mozilla Support' in article_page.page_title
        assert 'Was this article helpful?' == article_page.helpful_header_text

        article_page.click_helpful_button()
        article_page.wait_for_vote_message_text(u'Glad to hear it \u2014 thanks for the feedback!')
