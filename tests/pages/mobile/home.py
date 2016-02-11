# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from selenium.webdriver.common.by import By

from pages.mobile.base import Base


class Home(Base):

    _page_title = 'Products | Mozilla Support'

    _header_locator = (By.CSS_SELECTOR, 'header h1')
    _search_box_locator = (By.CSS_SELECTOR, '#search input')

    @property
    def header_text(self):
        return self.selenium.find_element(*self._header_locator).text

    def search_for(self, search_term):
        self.open_menu()
        search_box = self.selenium.find_element(*self._search_box_locator)
        search_box.send_keys(search_term)
        search_box.submit()

        from pages.mobile.search import Search
        return Search(self.base_url, self.selenium)
