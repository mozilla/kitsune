# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from selenium.webdriver.common.by import By

from pages.base import Page
from pages.language_picker import LanguagePickerPage


class IndexPage(Page):
    _page_title = 'Mozilla Support'
    _url = '/'

    _locale_picker = (By.CSS_SELECTOR, '.locale-picker')

    @property
    def current_language(self):
        return self.selenium.find_element(*self._locale_picker).text

    def go_to_picker_page(self):
        self.selenium.find_element(*self._locale_picker).click()
        picker_pg = LanguagePickerPage(self.testsetup)
        return picker_pg
