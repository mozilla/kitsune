#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from selenium.webdriver.common.by import By

from pages.mobile.base import Base
from pages.page import Page


class Search(Base):

    _results_locator = (By.CSS_SELECTOR, 'ol.search-results li')

    def __init__(self, testsetup):
        Base.__init__(self, testsetup)
        self._page_title = 'Search | Mozilla Support'

    @property
    def results(self):
        return [self.SearchResult(self.testsetup, element)
                for element in self.selenium.find_elements(*self._results_locator)]

    class SearchResult(Page):
        def __init__(self, testsetup, element):
            Page.__init__(self, testsetup)
            self._root_element = element

        def click(self):
            self._root_element.click()
            from pages.mobile.article import Article
            return Article(self.testsetup)
