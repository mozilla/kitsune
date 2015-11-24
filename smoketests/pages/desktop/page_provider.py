#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


class PageProvider():
    ''' internal methods '''

    def __init__(self, testsetup):
        self.testsetup = testsetup
        self.base_url = testsetup.base_url
        self.selenium = testsetup.selenium

    def _set_window_size(self):
        # SUMO requires a minimum window width
        # to display elements that we are checking
        if self.selenium.get_window_size()['width'] < 1920:
            self.selenium.set_window_size(1920, 1080)

    def _go_to_page(self, page_object, username=None, password=None):
        self._set_window_size()
        self.selenium.get(self.base_url + page_object._page_url)
        page_object.is_the_current_page
        if all((username, password)):
            page_object.sign_in(username, password)
        page_object.header.dismiss_staging_site_warning_if_present()
        return page_object

    def _go_to_page_with_login_redirect(self, page_object, username, password):
        self._set_window_size()
        from pages.desktop.login_page import LoginPage
        self.selenium.get(self.base_url + page_object._page_url)
        login_page = LoginPage(self.testsetup)
        login_page.log_in(username, password)
        page_object.is_the_current_page
        page_object.header.dismiss_staging_site_warning_if_present()
        return page_object

    ''' pages for which login is forbidden '''

    def new_user_registration_page(self):
        from pages.desktop.register_page import RegisterPage
        return self._go_to_page(RegisterPage(self.testsetup))

    ''' pages for which login is optional '''

    def home_page(self, username=None, password=None):
        from pages.desktop.support_home_page import SupportHomePage
        return self._go_to_page(SupportHomePage(self.testsetup), username, password)

    def new_question_page(self, username=None, password=None):
        from pages.desktop.questions_page import AskNewQuestionsPage
        return self._go_to_page(AskNewQuestionsPage(self.testsetup), username, password)

    def questions_page(self, username=None, password=None):
        from pages.desktop.questions_page import QuestionsPage
        return self._go_to_page(QuestionsPage(self.testsetup), username, password)

    def refine_search_page(self, username=None, password=None):
        from pages.desktop.refine_search_page import RefineSearchPage
        return self._go_to_page(RefineSearchPage(self.testsetup), username, password)

    def search_page(self, username=None, password=None):
        from pages.desktop.search_page import SearchPage
        return self._go_to_page(SearchPage(self.testsetup), username, password)

    ''' pages for which login is required '''

    def new_kb_article_page(self, username, password):
        from pages.desktop.knowledge_base_new_article import KnowledgeBaseNewArticle
        return self._go_to_page_with_login_redirect(KnowledgeBaseNewArticle(self.testsetup), username, password)
