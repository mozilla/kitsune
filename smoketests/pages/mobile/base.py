#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from selenium.webdriver.common.by import By

from pages.page import Page


class Base(Page):

    _body_locator = (By.TAG_NAME, 'body')
    _menu_items_locator = (By.CSS_SELECTOR, 'nav a')
    _menu_button_locator = (By.ID, 'menu-button')
    _mobile_header_locator = (By.CSS_SELECTOR, 'header.slide-on-exposed')

    @property
    def is_menu_exposed(self):
        return 'exposed' in self.selenium.find_element(*self._body_locator).get_attribute('class')

    @property
    def menu_items(self):
        return [self.MenuItem(self.testsetup, element)
                for element in self.selenium.find_elements(*self._menu_items_locator)]

    @property
    def is_mobile_view_displayed(self):
        return self.selenium.find_element(*self._mobile_header_locator).is_displayed()

    def click_menu(self):
        self.selenium.find_element(*self._menu_button_locator).click()

    def close_menu(self):
        assert self.is_menu_exposed, 'Menu is already closed'
        self.click_menu()

    def open_menu(self):
        assert not self.is_menu_exposed, 'Menu is already open'
        self.click_menu()

    class MenuItem(Page):

        def __init__(self, testsetup, element):
            Page.__init__(self, testsetup)
            self._root_element = element

        @property
        def name(self):
            return self._root_element.text

        def click(self):
            return self._root_element.click()
