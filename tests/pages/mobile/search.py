# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from selenium.webdriver.common.by import By

from pages.mobile.base import Base
from pages.page import Page


class Search(Base):

    _page_title = 'Search | Mozilla Support'
    _results_locator = (By.CSS_SELECTOR, 'ol.search-results li')

    @property
    def results(self):
        return [self.SearchResult(self.base_url, self.selenium, element)
                for element in self.selenium.find_elements(*self._results_locator)]

    class SearchResult(Page):
        def __init__(self, base_url, selenium, element):
            Page.__init__(self, base_url, selenium)
            self._root_element = element

        def click(self):
            self._root_element.click()
            from pages.mobile.article import Article
            return Article(self.base_url, self.selenium)
