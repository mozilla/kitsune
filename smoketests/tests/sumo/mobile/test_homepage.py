#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from pages.mobile.page_provider import PageProvider


class TestHome:

    @pytest.mark.nondestructive
    def test_the_expandable_header_menu(self, mozwebqa):
        expected_menu_items = [u'Home',
                               u'Ask a question',
                               u'Support Forum',
                               u'Help other users',
                               u'Switch to desktop site',
                               u'Sign in',
                               u'Switch language']
        home = PageProvider(mozwebqa).home_page()
        home.open_menu()
        assert home.is_menu_exposed, 'Menu is not open'

        menu_names = [menu.name for menu in home.menu_items]
        assert expected_menu_items == menu_names

        home.close_menu()
        assert not home.is_menu_exposed, 'Menu is not closed'

    @pytest.mark.nondestructive
    def test_the_header_text(self, mozwebqa):
        home = PageProvider(mozwebqa).home_page()
        home.is_the_current_page

        assert 'Products' == home.header_text
