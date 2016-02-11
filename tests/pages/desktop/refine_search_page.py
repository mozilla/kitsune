# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from selenium.webdriver.common.by import By
from pages.desktop.base import Base


class RefineSearchPage(Base):
    """
       'Advanced Search' page.
    """

    URL_TEMPLATE = '{locale}/search/advanced?a=2'

    _page_title = 'Advanced Search | Mozilla Support'
    _post_tags_box = (By.CSS_SELECTOR, 'input[name="q_tags"]')
    _thread_search_box = (By.ID, 'discussion_q')
    _search_button_kb = (
        By.CSS_SELECTOR, 'input[name="w"][value="1"]+div.submit-search > input[type="submit"]')
    _search_button_support = (By.CSS_SELECTOR, '#support > div.submit-search > button')
    _search_button_disc = (
        By.CSS_SELECTOR, 'input[name="w"][value="4"]+div.submit-search > input[type="submit"]')
    _kb_tab = (By.CSS_SELECTOR, 'div#search-tabs > ul > li:nth-child(1) > a')
    _support_questions_tab = (By.CSS_SELECTOR, 'div#search-tabs > ul > li:nth-child(2) > a')
    _forums_tab = (By.CSS_SELECTOR, 'div#search-tabs > ul > li:nth-child(3) > a')
    _asked_by_box = (By.CSS_SELECTOR, 'input[name="asked_by"]')
    _search_results_list = (By.CSS_SELECTOR, 'div.result.question')

    def click_support_questions_tab(self):
        self.selenium.find_element(*self._support_questions_tab).click()

    def type_in_asked_by_box(self, text):
        self.selenium.find_element(*self._asked_by_box).send_keys(text)

    def click_search_button_support(self):
        self.selenium.find_element(*self._search_button_support).click()

    def do_search_on_knowledge_base(self, search_query, search_page_obj):
        self.selenium.find_element(*self._kb_tab).click()
        self.selenium.find_element(*self.article_search_box).send_keys(search_query)
        self.selenium.find_element(*self._search_button_kb).click()
        search_page_obj.is_the_current_page

    def do_search_on_support_questions(self, search_query, search_page_obj):
        self.selenium.find_element(*self._support_questions_tab).click()
        self.selenium.find_element(*self.post_search_box).send_keys(search_query)
        self.selenium.find_element(*self._search_button_support).click()
        search_page_obj.is_the_current_page

    def do_search_tags_on_support_questions(self, search_query, search_page_obj):
        self.selenium.find_element(*self._support_questions_tab).click()
        self.selenium.find_element(*self._post_tags_box).send_keys(search_query)
        self.selenium.find_element(*self._search_button_support).click()
        search_page_obj.is_the_current_page

    def do_search_on_discussion_forums(self, search_query, search_page_obj):
        self.selenium.find_element(*self._forums_tab).click()
        self.selenium.find_element(*self._thread_search_box).send_keys(search_query)
        self.selenium.find_element(*self._search_button_disc).click()
        search_page_obj.is_the_current_page

    @property
    def search_result_count(self):
        return len(self.selenium.find_elements(*self._search_results_list))
