# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


def pytest_configure(config):
    # set user agent override when running mobile tests in Firefox
    config.option.firefox_preferences.append((
        'general.useragent.override',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 8_4_1 like Mac OS X) '
        'AppleWebKit/600.1.4 (KHTML, like Gecko) GSA/8.0.57838 Mobile/12H321 '
        'Safari/600.1.4'))
