# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import re
import time
from urlparse import urljoin

from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementNotVisibleException

http_regex = re.compile('https?://((\w+\.)+\w+\.\w+)')


class Page(object):

    URL_TEMPLATE = None

    def __init__(self, base_url, selenium, timeout=10, **url_kwargs):
        self.base_url = base_url
        self.selenium = selenium
        self.timeout = timeout
        self.url_kwargs = url_kwargs
        self.wait = WebDriverWait(self.selenium, self.timeout)

    @property
    def canonical_url(self):
        if self.URL_TEMPLATE is not None:
            return urljoin(self.base_url,
                           self.URL_TEMPLATE.format(**self.url_kwargs))
        return self.base_url

    def open(self):
        self.selenium.get(self.canonical_url)
        self.wait_for_page_to_load()
        return self

    def wait_for_page_to_load(self):
        self.wait.until(lambda s: self.canonical_url in s.current_url)
        return self

    @property
    def is_the_current_page(self):
        if self._page_title:
            assert self._page_title == self.page_title

    @property
    def url_current_page(self):
        return(self.selenium.current_url)

    @property
    def page_title(self):
        WebDriverWait(self.selenium, self.timeout).until(lambda s: s.title)
        return self.selenium.title

    def refresh(self):
        self.selenium.refresh()

    def is_element_present(self, *locator):
        self.selenium.implicitly_wait(0)
        try:
            self.selenium.find_element(*locator)
            return True
        except NoSuchElementException:
            # this will return a snapshot, which takes time.
            return False
        finally:
            # set back to where you once belonged
            self.selenium.implicitly_wait(10)

    def is_element_visible(self, *locator):
        try:
            return self.selenium.find_element(*locator).is_displayed()
        except (NoSuchElementException, ElementNotVisibleException):
            # this will return a snapshot, which takes time.
            return False

    def wait_for_element_present(self, *locator):
        count = 0
        while not self.is_element_present(*locator):
            time.sleep(1)
            count += 1
            if count == self.timeout:
                raise Exception(*locator + ' has not loaded')

    def wait_for_element_visible(self, *locator):
        count = 0
        while not self.is_element_visible(*locator):
            time.sleep(1)
            count += 1
            if count == self.timeout:
                raise Exception(*locator + " is not visible")

    def wait_for_ajax(self):
        count = 0
        while count < self.timeout:
            time.sleep(1)
            count += 1
            if self.selenium.execute_script("return jQuery.active == 0"):
                return
        raise Exception("Wait for AJAX timed out after %s seconds" % count)
