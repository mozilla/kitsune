# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from pages.desktop.knowledge_base_new_article import KnowledgeBaseNewArticle
from pages.desktop.questions_page import AskNewQuestionsPage
from pages.desktop.questions_page import QuestionsPage
from pages.desktop.refine_search_page import RefineSearchPage
from pages.desktop.search_page import SearchPage
from pages.desktop.support_home_page import SupportHomePage
from mocks.mock_article import MockArticle


class TestLoginLogout:

    @pytest.mark.nondestructive
    def test_login(self, base_url, selenium, variables):
        user = variables['users']['default']
        page = SupportHomePage(base_url, selenium).open()
        page.sign_in(user['username'], user['password'])
        assert page.header.is_user_logged_in, 'User not shown to be logged in'

    # logging out of the following pages keeps user on the same pages

    @pytest.mark.native
    @pytest.mark.nondestructive
    @pytest.mark.parametrize('page_object', [
        SupportHomePage,
        AskNewQuestionsPage,
        QuestionsPage,
        SearchPage,
        RefineSearchPage,
    ])
    def test_logout_from_pages(self, base_url, selenium, variables, page_object):
        user = variables['users']['default']
        page = page_object(base_url, selenium).open()
        page.sign_in(user['username'], user['password'])
        assert page.header.is_user_logged_in, 'User not shown to be logged in'

        # sign out
        page.sign_out()
        assert page.canonical_url in selenium.current_url
        assert page.header.is_user_logged_out

    @pytest.mark.native
    def test_logout_from_new_kb_article_page(self, base_url, selenium, variables):
        user = variables['users']['default']
        page = KnowledgeBaseNewArticle(base_url, selenium).open(
            user['username'], user['password'])
        assert page.header.is_user_logged_in, 'User not shown to be logged in'

        # sign out
        login_page = page.sign_out()
        assert login_page.canonical_url in selenium.current_url
        assert login_page.header.is_user_logged_out

    @pytest.mark.native
    def test_logout_from_edit_kb_article_page(self, base_url, selenium, variables):
        user = variables['users']['default']
        kb_new_article = KnowledgeBaseNewArticle(base_url, selenium).open(
            user['username'], user['password'])

        # create a new article
        mock_article = MockArticle()
        kb_new_article.set_article(mock_article)
        kb_new_article.submit_article()
        kb_article_history = kb_new_article.set_article_comment_box(mock_article['comment'])

        kb_edit_article = kb_article_history.navigation.click_edit_article()

        # sign out
        login_page = kb_edit_article.sign_out()
        assert login_page.canonical_url in selenium.current_url
        assert login_page.header.is_user_logged_out

    @pytest.mark.native
    def test_logout_from_translate_kb_article_page(self, base_url, selenium, variables):
        user = variables['users']['default']
        kb_new_article = KnowledgeBaseNewArticle(base_url, selenium).open(
            user['username'], user['password'])

        # create a new article
        mock_article = MockArticle()
        kb_new_article.set_article(mock_article)
        kb_new_article.submit_article()
        kb_article_history = kb_new_article.set_article_comment_box(mock_article['comment'])

        kb_translate_pg = kb_article_history.navigation.click_translate_article()
        kb_translate_pg.click_translate_language('Deutsch (de)')

        # sign out
        login_page = kb_translate_pg.sign_out()
        login_page.url_kwargs['locale'] = 'de'
        assert login_page.canonical_url in selenium.current_url
        assert login_page.header.is_user_logged_out
