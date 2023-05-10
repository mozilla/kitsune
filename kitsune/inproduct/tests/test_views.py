from unittest import mock
from urllib.parse import urlparse

import waffle
from django.contrib.sites.models import Site

from kitsune.inproduct.tests import RedirectFactory
from kitsune.sumo.tests import TestCase


class RedirectTestCase(TestCase):
    test_urls = (
        ("firefox/3.6.12/WINNT/en-US/", "/en-US/"),
        ("mobile/4.0/Android/en-US/", "/en-US/products/mobile"),
        ("firefox/3.6.12/MACOSX/en-US", "/en-US/"),
        ("firefox/3.6.12/WINNT/fr/", "/fr/"),
        ("firefox/3.6.12/WINNT/fr-FR/", "/fr/"),
        ("firefox-home/1.1/iPhone/en-US/", "/en-US/"),
        ("firefox/4.0/Linux/en-US/prefs-applications", "/en-US/kb/Applications"),
        ("firefox/4.0/Linux/en-US/prefs-applications/", "/en-US/kb/Applications"),
        ("firefox/5.0/NONE/en-US/", "/en-US/does-not-exist"),
        ("firefox/4.0/Android/en-US/foo", 404),
        # Make sure Basque doesn't trigger the EU ballot logic.
        ("firefox/29.0/Darwin/eu/", "/eu/"),
        ("firefox/29.0/Darwin/eu", "/eu/"),
        ("mobile/105.1.0/Android/iw/foo", "/he/"),
        ("mobile/105.1.0/Android/iw-IL/foo", "/he/"),
        ("mobile/105.1.0/Android/in/foo", "/id/"),
        ("mobile/105.1.0/Android/co/foo", "/en-US/"),
        ("mobile/105.1.0/Android/ia/foo", "/en-US/"),
        ("mobile/105.1.0/Android/su/foo", "/en-US/"),
    )

    test_eu_urls = (
        ("firefox/3.6.12/WINNT/en-US/eu/", "/en-US/"),
        ("mobile/4.0/Android/en-US/eu/", "/en-US/products/mobile"),
        ("firefox/3.6.12/MACOSX/en-US/eu", "/en-US/"),
        ("firefox/3.6.12/WINNT/fr/eu/", "/fr/"),
        ("firefox/3.6.12/WINNT/fr-FR/eu/", "/fr/"),
        ("firefox-home/1.1/iPhone/en-US/eu/", "/en-US/"),
        ("firefox/4.0/Linux/en-US/eu/prefs-applications", "/en-US/kb/Applications"),
        ("firefox/4.0/Linux/en-US/eu/prefs-applications/", "/en-US/kb/Applications"),
        ("firefox/5.0/NONE/en-US/eu/", "/en-US/does-not-exist"),
        ("firefox/4.0/Android/en-US/eu/foo", 404),
        # Basque is awesome.
        ("firefox/30.0/WINNT/eu/eu/", "/eu/"),
        ("firefox/4.0/Linux/eu/eu/prefs-applications", "/eu/kb/Applications"),
    )

    def setUp(self):
        super(RedirectTestCase, self).setUp()

        # Create redirects to test with.
        RedirectFactory(target="kb/Applications", topic="prefs-applications")
        RedirectFactory(target="")
        RedirectFactory(product="mobile", target="products/mobile")
        RedirectFactory(platform="iPhone", target="")
        RedirectFactory(product="mobile", platform="Android", topic="foo", target="")
        RedirectFactory(version="5.0", target="does-not-exist")
        RedirectFactory(platform="martian", target="https://martian.com")
        RedirectFactory(product="firefox", topic="learn", target="kb/learn?utm_source=yada")
        RedirectFactory(
            product="monitor",
            topic="share",
            target="kb/share?utm_content=firefox-share&utm_source=blue",
        )

    def test_target(self):
        """Test that we can vary on any parameter and targets work."""
        self._targets(self.test_urls, "as=u&utm_source=inproduct")

    def test_eu_target(self):
        """Test that all URLs work with the extra 'eu'."""
        self._targets(self.test_eu_urls, "as=u&utm_source=inproduct&eu=1")

    def test_external_target(self):
        tests = (
            ("mobile/4.0/MARTIAN/en-US/", "https://martian.com"),
            ("mobile/4.0/MARTIAN/en-US/eu/", "https://martian.com"),
        )
        self._targets(tests, "")

    def test_with_incoming_params(self):
        """Test that incoming query parameters are preserved."""

        tests = (
            ("firefox/112/Linux/en-US/learn", "/en-US/kb/learn", "utm_source=yada&as=u"),
            (
                "firefox/112/Linux/en-US/learn?utm_source=firefox",
                "/en-US/kb/learn",
                "utm_source=firefox&as=u",
            ),
            (
                "firefox/112/Linux/en-US/learn?utm_content=learn&utm_source=firefox",
                "/en-US/kb/learn",
                "utm_source=firefox&utm_content=learn&as=u",
            ),
            (
                "firefox/112/Linux/en-US/learn?utm_content=learn",
                "/en-US/kb/learn",
                "utm_source=yada&utm_content=learn&as=u",
            ),
            (
                "monitor/112/Linux/en-US/share",
                "/en-US/kb/share",
                "utm_content=firefox-share&utm_source=blue&as=u",
            ),
            (
                "monitor/112/Linux/en-US/eu/share",
                "/en-US/kb/share",
                "utm_content=firefox-share&utm_source=blue&as=u&eu=1",
            ),
            (
                "mobile/4.0/martian/en-US?utm_source=aliens",
                "https://martian.com",
                "utm_source=aliens",
            ),
        )

        for ipl, expected_path, expected_qs in tests:
            self._targets([(ipl, expected_path)], expected_qs)

    def _targets(self, urls, querystring):
        for input, output in urls:
            with self.subTest(input):
                response = self.client.get(f"/1/{input}", follow=True)
                if output == 404:
                    self.assertEqual(404, response.status_code)
                elif output.startswith("http"):
                    # Since we're redirecting to an external domain, just check the first one.
                    url, status_code = response.redirect_chain[0]
                    self.assertEqual(302, status_code)
                    self.assertEqual(url, output + (f"?{querystring}" if querystring else ""))
                else:
                    # The first redirect should be a 302.
                    self.assertEqual(302, response.redirect_chain[0][1])
                    # Let's check the final redirect against what we expected.
                    final = urlparse(response.redirect_chain[-1][0])
                    self.assertEqual(output, final.path)
                    self.assertEqual(querystring, final.query)

    @mock.patch.object(Site.objects, "get_current")
    @mock.patch.object(waffle, "sample_is_active")
    def test_switch_to_https(self, sample_is_active, get_current):
        """Verify we switch to https when sample is active."""
        get_current.return_value.domain = "example.com"
        sample_is_active.return_value = True

        response = self.client.get("/1/firefox/4.0/Linux/en-US/prefs-applications")
        self.assertEqual(302, response.status_code)
        assert response["location"].startswith("https://example.com/")
