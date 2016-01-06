# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from pages.index import IndexPage


class TestIndex:
    @pytest.mark.nondestructive
    def test_english_to_spanish(self, mozwebqa):
        index_pg = IndexPage(mozwebqa)

        index_pg.go_to_page()

        # Assert we're looking at English
        assert index_pg.current_language.lower() == 'english'

        # Go to picker page
        picker_pg = index_pg.go_to_picker_page()

        # Switch to Spanish
        picker_pg.switch_to_language('es')

        # Assert we're looking at Spansih
        assert index_pg.current_page_url.endswith('/es/')
        assert index_pg.current_language.lower() == u'español'
