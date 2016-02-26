# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from pages.mobile.home import Home


class TestMobileLoginLogout:

    @pytest.mark.nondestructive
    def test_login(self, base_url, selenium, variables):
        user = variables['users']['default']
        home_page = Home(base_url, selenium).open()
        home_page.log_in(user['username'], user['password'])

        assert home_page.is_user_logged_in, 'User not shown to be logged in'

    @pytest.mark.nondestructive
    def test_logout(self, base_url, selenium, variables):
        user = variables['users']['default']
        home_page = Home(base_url, selenium).open()
        home_page.log_in(user['username'], user['password'])

        assert home_page.is_user_logged_in, 'User is not shown to be logged in'

        # sign out
        home_page.log_out()
        home_page.is_the_current_page
        assert not home_page.is_user_logged_in
