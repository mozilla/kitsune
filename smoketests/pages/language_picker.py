# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from selenium.webdriver.common.by import By

from pages.base import Page


class LanguagePickerPage(Page):
    _page_title = 'Switch language | Mozilla Support'
    _url = '/locales'

    def switch_to_language(self, lang):
        from pages.index import IndexPage

        self.selenium.find_element(By.CSS_SELECTOR, 'a[lang="' + lang + '"]').click()
        index_pg = IndexPage(self.testsetup)
        return index_pg
