#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from pages.page import Page


class PageProvider(Page):

    def _go_to_page(self, page_object):
        self.selenium.get(self.base_url + page_object._page_url)
        page_object.is_the_current_page
        return page_object

    def home_page(self):
        from pages.mobile.home import Home
        return self._go_to_page(Home(self.testsetup))
