# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
import requests
import urllib


@pytest.mark.nondestructive
class TestRedirects:

    _user_agent_firefox = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:13.0) ' \
        'Gecko/20100101 Firefox/13.0.1'

    def _check_redirect(self, base_url, start_url, user_agent=_user_agent_firefox, locale='en-US'):
        if 'support.mozilla.org' not in base_url:
            pytest.skip("Skipped per dev instructions on continuous deployment. "
                        "To be run only on Prod")

        start_url = base_url + start_url

        headers = {'user-agent': user_agent,
                   'accept-language': locale}
        return requests.get(start_url, headers=headers)

    @pytest.mark.parametrize(('input', 'expected'), [
        ('/1/firefox/4.0/WINNT/en-US/firefox-help/',
         '/en-US/products/firefox?as=u&utm_source=inproduct'),
        ('/1/firefox/4.0/WINNT/en-US/firefox-f1/',
         '/en-US/products/firefox?as=u&utm_source=inproduct'),
        ('/1/firefox/4.0/WINNT/en-US/firefox-osxkey/',
         '/en-US/products/firefox?as=u&utm_source=inproduct'),
        ('/1/firefox/4.0/Darwin/en-US/firefox-help/',
         '/en-US/products/firefox?as=u&utm_source=inproduct'),
        ('/1/firefox/4.0/Darwin/en-US/firefox-f1/',
         '/en-US/products/firefox?as=u&utm_source=inproduct'),
        ('/1/firefox/4.0/Darwin/en-US/firefox-osxkey/',
         '/en-US/products/firefox?as=u&utm_source=inproduct'),
        ('/1/firefox/4.0/Linux/en-US/firefox-help/',
         '/en-US/products/firefox?as=u&utm_source=inproduct'),
        ('/1/firefox/4.0/Linux/en-US/firefox-f1/',
         '/en-US/products/firefox?as=u&utm_source=inproduct'),
        ('/1/firefox/4.0/Linux/en-US/firefox-osxkey/',
         '/en-US/products/firefox?as=u&utm_source=inproduct'),
    ])
    def test_browser_redirect_to_sumo(self, base_url, input, expected):
        expected_url = base_url + expected
        r = self._check_redirect(base_url, input)
        assert expected_url == urllib.unquote(r.url)
        assert requests.codes.ok == r.status_code

    @pytest.mark.parametrize(('input'), [
        ('/1/firefox/4.0/WINNT/en-US/prefs-main/'),
        ('/1/firefox/4.0/Darwin/en-US/prefs-main/'),
        ('/1/firefox/4.0/Linux/en-US/prefs-main/'),
        ('/1/firefox/4.0/WINNT/en-US/prefs-clear-private-data/'),
        ('/1/firefox/4.0/Darwin/en-US/prefs-clear-private-data/'),
        ('/1/firefox/4.0/Linux/en-US/prefs-clear-private-data/'),
        ('/1/firefox/4.0/WINNT/en-US/prefs-fonts-and-colors/')])
    def test_kb_redirects_status_ok(self, base_url, input):
        r = self._check_redirect(base_url, input)
        assert requests.codes.ok == r.status_code

    @pytest.mark.parametrize(('input', 'expected'), [
        ('/1/mobile/4.0/android/en-US/firefox-help',
         '/en-US/products/mobile/popular-articles-android?as=u&utm_source=inproduct'),
        ('/1/mobile/4.0/iphone/en-US/firefox-help',
         '/en-US/products/mobile/popular-articles-android?as=u&utm_source=inproduct'),
        ('/1/mobile/4.0/nokia/en-US/firefox-help',
         '/en-US/products/mobile/popular-articles-android?as=u&utm_source=inproduct')])
    def test_old_mobile_redirects(self, base_url, input, expected):
        expected_url = base_url + expected
        r = self._check_redirect(base_url, input)
        assert expected_url == urllib.unquote(r.url)
        assert requests.codes.ok == r.status_code

    @pytest.mark.parametrize(('input'), [
        ('/1/firefox-home/4.0/iPhone/en-US'),
        ('/1/firefox-home/4.0/iPhone/en-US/log-in')])
    def test_iphone_kb_redirects_status_ok(self, base_url, input):
        r = self._check_redirect(base_url, input)
        assert requests.codes.ok == r.status_code
