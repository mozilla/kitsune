#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from pages.mobile.page_provider import PageProvider


class TestSearch:

    @pytest.mark.nondestructive
    def test_that_positive_search_returns_results(self, mozwebqa):
        home = PageProvider(mozwebqa).home_page()

        search_page = home.search_for('firefox')
        assert len(search_page.results) > 0, 'No search results found'

    @pytest.mark.nondestructive
    def test_that_negative_search_does_not_return_results(self, mozwebqa):
        home = PageProvider(mozwebqa).home_page()

        search_page = home.search_for('frfx')
        assert 0 == len(search_page.results), 'Search results found but none expected'
