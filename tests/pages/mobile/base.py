# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from pages.page import Page


class Base(Page):

    URL_TEMPLATE = '{locale}'

    _body_locator = (By.TAG_NAME, 'body')
    _menu_items_locator = (By.CSS_SELECTOR, 'nav a')
    _menu_button_locator = (By.ID, 'menu-button')
    _mobile_header_locator = (By.CSS_SELECTOR, 'header.slide-on-exposed')
    _search_bar_locator = (By.ID, 'search-bar')
    _username_box_locator = (By.ID, 'id_username')
    _password_box_locator = (By.ID, 'id_password')
    _log_in_button_locator = (By.CSS_SELECTOR, "button[data-name='login']")
    _log_in_menu_locator = (By.CSS_SELECTOR, '.scrollable > a:nth-child(9)')
    _login_error_locator = (By.CSS_SELECTOR, 'ul.errorlist > li')
    _log_out_menu_locator = (By.CSS_SELECTOR, '.sign-out')

    def __init__(self, base_url, selenium, locale='en-US', **url_kwargs):
        url_kwargs['locale'] = locale
        super(Base, self).__init__(base_url, selenium, **url_kwargs)

    @property
    def is_menu_exposed(self):
        return 'exposed' in self.selenium.find_element(*self._body_locator).get_attribute('class')

    @property
    def menu_items(self):
        return [self.MenuItem(self.base_url, self.selenium, element)
                for element in self.selenium.find_elements(*self._menu_items_locator)]

    @property
    def is_mobile_view_displayed(self):
        return self.selenium.find_element(*self._mobile_header_locator).is_displayed()

    @property
    def is_user_logged_in(self):
        return self.is_element_present(*self._log_out_menu_locator)

    def click_menu(self):
        self.selenium.find_element(*self._menu_button_locator).click()

    def close_menu(self):
        assert self.is_element_visible(*self._search_bar_locator), 'Menu is already closed'
        self.click_menu()
        WebDriverWait(self.selenium, self.timeout).until(
            lambda s: not self.is_element_visible(*self._search_bar_locator))

    def log_in(self, username, password):
        self.open_menu()
        self.selenium.find_element(*self._log_in_menu_locator).click()
        self.selenium.find_element(*self._username_box_locator).send_keys(username)
        self.selenium.find_element(*self._password_box_locator).send_keys(password)
        self.selenium.find_element(*self._log_in_button_locator).click()

        if not self.is_user_logged_in:
            error = self.selenium.find_element(*self._login_error_locator).text
            error = "login failed for %s\n" % username + error
            raise AssertionError(error)

    def log_out(self):
        self.open_menu()
        self.selenium.find_element(*self._log_out_menu_locator).click()
        WebDriverWait(self.selenium, self.timeout).until(
            lambda s: not self.is_element_visible(*self._search_bar_locator))

    def open_menu(self):
        assert not self.is_element_visible(*self._search_bar_locator), 'Menu is already open'
        self.click_menu()
        WebDriverWait(self.selenium, self.timeout).until(
            lambda s: self.is_element_visible(*self._search_bar_locator))

    class MenuItem(Page):

        def __init__(self, base_url, selenium, element):
            Page.__init__(self, base_url, selenium)
            self._root_element = element

        @property
        def name(self):
            return self._root_element.text

        def click(self):
            return self._root_element.click()
