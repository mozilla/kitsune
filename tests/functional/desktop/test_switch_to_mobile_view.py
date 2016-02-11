# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from pages.desktop.support_home_page import SupportHomePage as DesktopHome
from pages.mobile.home import Home as MobileHome


class TestMobileSite:

    @pytest.mark.nondestructive
    def test_switch_to_mobile_view(self, base_url, selenium):
        desktop = DesktopHome(base_url, selenium).open()
        desktop.switch_to_mobile_view()
        mobile = MobileHome(base_url, selenium)
        assert mobile.is_mobile_view_displayed
