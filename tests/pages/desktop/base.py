# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from pages.page import Page


class Base(Page):

    URL_TEMPLATE = '{locale}'

    def __init__(self, base_url, selenium, locale='en-US', **url_kwargs):
        url_kwargs['locale'] = locale
        super(Base, self).__init__(base_url, selenium, **url_kwargs)

    def wait_for_page_to_load(self):
        super(Base, self).wait_for_page_to_load()
        self.header.dismiss_staging_site_warning_if_present()
        return self

    def click_card_grid(self, locator):
        ActionChains(self.selenium).move_to_element(
            self.selenium.find_element(*locator)).click().perform()
        self.selenium.implicitly_wait(10)
        return self.selenium.title

    @property
    def footer(self):
        return self.FooterRegion(self.base_url, self.selenium)

    @property
    def header(self):
        return self.HeaderRegion(self.base_url, self.selenium)

    def sign_in(self, username, password):
        login = self.header.click_login()
        login.log_in(username, password)

    def sign_out(self):
        self.header.click_logout()
        from pages.desktop.login_page import LoginPage
        return LoginPage(self.base_url, self.selenium)

    def switch_to_mobile_view(self):
        self.footer.click_switch_to_mobile_view()

    def format_page_title(self, *title_segments):
        '''
            Create a page title by adding separators between title segments
            and ending with the base segment
            Usage:
                format_page_title('Forum')            returns 'Forum | Mozilla Support'
                format_page_title('Create New', 'KB') returns 'Create New | KB | Mozilla Support'
                format_page_title('', 'Forum')        returns ' | Forum | Mozilla Support'
                format_page_title()                   returns 'Mozilla Support'
        '''
        separator = ' | '
        page_title = 'Mozilla Support'
        segment_list = list(title_segments)
        segment_list.reverse()
        for title in segment_list:
            page_title = title + separator + page_title
        return page_title

    class FooterRegion(Page):

        _switch_to_mobile_view_locator = (By.CSS_SELECTOR, 'footer a[href*="mobile=1"]')

        def click_switch_to_mobile_view(self):
            self.selenium.find_element(*self._switch_to_mobile_view_locator).click()

    class HeaderRegion(Page):

        # Not LoggedIn
        _login_locator = (By.CSS_SELECTOR, 'a.sign-in')
        _register_locator = (By.CSS_SELECTOR, 'a.register')

        # LoggedIn
        _account_controller_locator = (By.CSS_SELECTOR, '.user')
        _account_dropdown_locator = (By.CSS_SELECTOR, 'li.dropdown a.user')
        _logout_locator = (By.CSS_SELECTOR, 'li.dropdown > ul > li > a.sign-out')

        # Staging site warning
        _staging_site_warning_close_button_locator = (
            By.CSS_SELECTOR, '#stage-banner > div.close-button')

        def click_login(self):
            self.selenium.find_element(*self._login_locator).click()
            from pages.desktop.login_page import LoginPage
            return LoginPage(self.base_url, self.selenium)

        def click_logout(self):
            self.dismiss_staging_site_warning_if_present()
            ActionChains(self.selenium).move_to_element(
                self.selenium.find_element(*self._account_dropdown_locator)
            ).move_to_element(
                self.selenium.find_element(*self._logout_locator)
            ).click().perform()

        def dismiss_staging_site_warning_if_present(self):
            if self.is_element_present(*self._staging_site_warning_close_button_locator):
                if self.is_element_visible(*self._staging_site_warning_close_button_locator):
                    self.selenium.find_element(
                        *self._staging_site_warning_close_button_locator).click()

        @property
        def is_user_logged_in(self):
            return self.is_element_visible(*self._account_controller_locator)

        @property
        def is_user_logged_out(self):
            return self.is_element_visible(*self._login_locator)

        @property
        def login_user_name(self):
            return self.selenium.find_element(*self._account_controller_locator).text
