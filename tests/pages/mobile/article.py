# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from pages.mobile.base import Base


class Article(Base):

    _helpful_button_locator = (By.NAME, 'helpful')
    _helpful_header_text_locator = (By.CSS_SELECTOR, 'div.vote-bar header')
    _vote_message_text_locator = (By.CSS_SELECTOR, 'div.vote-bar p')

    @property
    def helpful_header_text(self):
        return self.selenium.find_element(*self._helpful_header_text_locator).text

    def wait_for_vote_message_text(self, text):
        WebDriverWait(self.selenium, self.timeout).until(
            lambda s: s.find_element(*self._vote_message_text_locator).text == text)

    def click_helpful_button(self):
        self.selenium.find_element(*self._helpful_button_locator).click()
