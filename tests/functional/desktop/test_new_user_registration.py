# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from pages.desktop.register_page import RegisterPage


class TestNewUserRegistration:

    def test_that_thank_you_page_is_displayed_after_registration(self, base_url, selenium):
        """
           Register a new user using random username.
           Verify registration by checking the page title
        """
        page = RegisterPage(base_url, selenium).open()
        page.register_new_user()

        registration_text = page.successful_registration_message
        assert 'Thank you for registering!' in registration_text

        actual_page_title = page.page_title
        expected_page_title = page._page_title_after_registration
        assert expected_page_title in actual_page_title
