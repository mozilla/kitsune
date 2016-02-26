# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from pages.desktop.base import Base
from selenium.webdriver.common.by import By


class LoginPage(Base):
    """
        Form for login.
    """

    URL_TEMPLATE = '{locale}/users/auth'

    _page_title = 'Log In | Mozilla Support'
    _username_box_locator = (By.ID, 'id_username')
    _password_box_locator = (By.ID, 'id_password')
    _log_in_button_locator = (By.CSS_SELECTOR, "button[data-name='login']")
    _login_error_locator = (By.CSS_SELECTOR, 'ul.errorlist > li')

    # if user is logged-in then you see these elements
    _logged_in_as_div_locator = (By.CSS_SELECTOR, 'div#mod-login_box > div')
    _logged_in_text = 'Logged in as'

    def log_in(self, username, password):
        self.selenium.find_element(*self._username_box_locator).send_keys(username)
        self.selenium.find_element(*self._password_box_locator).send_keys(password)
        self.selenium.find_element(*self._log_in_button_locator).click()

        if not self.header.is_user_logged_in:
            error = self.selenium.find_element(*self._login_error_locator).text
            error = "login failed for %s\n" % username + error
            raise AssertionError(error)
