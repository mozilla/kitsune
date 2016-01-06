#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


from unittestzero import Assert
from pages.desktop.page_provider import PageProvider


class TestNewUserRegistration:

    def test_that_thank_you_page_is_displayed_after_successful_registration(self, mozwebqa):
        """
           Register a new user using random username.
           Verify registration by checking the page title
        """
        register_pg = PageProvider(mozwebqa).new_user_registration_page()
        register_pg.register_new_user()

        registration_text = register_pg.successful_registration_message
        Assert.contains('Thank you for registering!', registration_text)

        actual_page_title = register_pg.page_title
        expected_page_title = register_pg._page_title_after_registration
        Assert.contains(expected_page_title, actual_page_title)
