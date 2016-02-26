# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from selenium.webdriver.common.by import By
from pages.desktop.base import Base


class SearchPage(Base):
    """
    'Search for Firefox Help' page
    """

    URL_TEMPLATE = '{locale}/search'

    _page_title = 'Search | Mozilla Support'
    _search_query_locator = (By.CSS_SELECTOR, 'input.searchbox')
    _search_box_locator = (By.CSS_SELECTOR, 'input.searchbox')
    _search_button = (By.CSS_SELECTOR, 'button[type="submit"]')
    _search_support_button_locator = (By.CSS_SELECTOR, '.btn-important')
    _refine_search_link = (By.CSS_SELECTOR, 'a[href *= "a=2"]')
    _next_page_link = (By.LINK_TEXT, 'Next')
    _result_div = (By.CSS_SELECTOR, 'div.result')
    _results_list_locator = (By.CSS_SELECTOR, 'div.search-results div[class*="result"]')
    _result_question_locator = (By.CSS_SELECTOR, '#search-results h3 a')

    def do_search_on_search_query(self, search_query):
        self.selenium.find_element(*self._search_query_locator).send_keys(search_query)
        self.selenium.find_element(*self._search_button).click()

    def do_search_on_search_box(self, search_term):
        self.selenium.find_element(*self._search_box_locator).send_keys(search_term)
        self.selenium.find_element(*self._search_support_button_locator).click()

    @property
    def is_result_present(self):
        return self.is_element_present(*self._result_div)

    @property
    def are_ten_results_present(self):
        return len(self.selenium.find_elements(*self._results_list_locator)) == 10

    @property
    def get_result_text(self):
        return self.selenium.find_element(*self._result_div).text

    def result_question_text(self):
        return self.selenium.find_element(*self._result_question_locator).text

    def click_refine_search_link(self, refine_search_page_obj):
        self.selenium.find_element(*self._refine_search_link).click()
        refine_search_page_obj.is_the_current_page

    def click_next_page_link(self):
        self.selenium.find_element(*self._next_page_link).click()

    def click_question_link(self, link_title):
        # click the link to one of the forum threads
        self.selenium.find_element(*self._result_question_locator).click()
        # check if the opened page contains the given page title
        # 1.get all the window handles
        window_handles = self.selenium.window_handles
        isReachedRightPage = False
        # 2.search for the handle of the window containing the given title
        for h_window in window_handles:
            # 3. switch to one of the handles
            self.selenium.switch_to_window(h_window)
            self.selenium.implicitly_wait(1)
            title_h_window = self.selenium.title
            if (link_title in title_h_window):
                # a handle of the window containing it is found
                isReachedRightPage = True
                break
        # 4. notify if such a page has been found
        return isReachedRightPage
