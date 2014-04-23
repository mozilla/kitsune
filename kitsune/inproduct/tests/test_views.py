from urlparse import urlparse

from django.contrib.sites.models import Site

import mock
import waffle
from nose.tools import eq_

from kitsune.inproduct.tests import redirect
from kitsune.sumo.tests import TestCase


class RedirectTestCase(TestCase):
    test_urls = (
        ('firefox/3.6.12/WINNT/en-US/', '/en-US/home'),
        ('mobile/4.0/Android/en-US/', '/en-US/products/mobile'),
        ('firefox/3.6.12/MACOSX/en-US', '/en-US/home'),
        ('firefox/3.6.12/WINNT/fr/', '/fr/home'),
        ('firefox/3.6.12/WINNT/fr-FR/', '/fr/home'),
        ('firefox-home/1.1/iPhone/en-US/', '/en-US/home'),
        ('firefox/4.0/Linux/en-US/prefs-applications',
            '/en-US/kb/Applications'),
        ('firefox/4.0/Linux/en-US/prefs-applications/',
            '/en-US/kb/Applications'),
        ('firefox/5.0/NONE/en-US/', '/en-US/does-not-exist'),
        ('mobile/4.0/MARTIAN/en-US/', 'http://martian.com'),
        ('mobile/4.0/martian/en-US/', 'http://martian.com'),
        ('firefox/4.0/Android/en-US/foo', 404),
        # Make sure Basque doesn't trigger the EU ballot logic.
        ('firefox/29.0/Darwin/eu/', '/eu/home'),
        ('firefox/29.0/Darwin/eu', '/eu/home'),
    )

    test_eu_urls = (
        ('firefox/3.6.12/WINNT/en-US/eu/', '/en-US/home'),
        ('mobile/4.0/Android/en-US/eu/', '/en-US/products/mobile'),
        ('firefox/3.6.12/MACOSX/en-US/eu', '/en-US/home'),
        ('firefox/3.6.12/WINNT/fr/eu/', '/fr/home'),
        ('firefox/3.6.12/WINNT/fr-FR/eu/', '/fr/home'),
        ('firefox-home/1.1/iPhone/en-US/eu/', '/en-US/home'),
        ('firefox/4.0/Linux/en-US/eu/prefs-applications',
            '/en-US/kb/Applications'),
        ('firefox/4.0/Linux/en-US/eu/prefs-applications/',
            '/en-US/kb/Applications'),
        ('firefox/5.0/NONE/en-US/eu/', '/en-US/does-not-exist'),
        ('mobile/4.0/MARTIAN/en-US/eu/', 'http://martian.com'),
        ('mobile/4.0/martian/en-US/eu/', 'http://martian.com'),
        ('firefox/4.0/Android/en-US/eu/foo', 404),
        # Basque is awesome.
        ('firefox/30.0/WINNT/eu/eu/', '/eu/home'),
        ('firefox/4.0/Linux/eu/eu/prefs-applications',
            '/eu/kb/Applications'),
    )

    def setUp(self):
        super(RedirectTestCase, self).setUp()

        # Create redirects to test with.
        redirect(target='kb/Applications', topic='prefs-applications',
                 save=True)
        redirect(target='home', save=True)
        redirect(product='mobile', target='/products/mobile', save=True)
        redirect(platform='iPhone', target='home', save=True)
        redirect(product='mobile', platform='Android', topic='foo',
                 target='home', save=True)
        redirect(version='5.0', target='does-not-exist', save=True)
        redirect(platform='martian', target='http://martian.com', save=True)

    def test_target(self):
        """Test that we can vary on any parameter and targets work."""
        self._targets(self.test_urls, 'as=u&utm_source=inproduct')

    def test_eu_target(self):
        """Test that all URLs work with the extra 'eu'."""
        self._targets(self.test_eu_urls, 'eu=1&as=u&utm_source=inproduct')

    def _targets(self, urls, querystring):
        for input, output in urls:
            response = self.client.get(u'/1/%s' % input, follow=True)
            if output == 404:
                eq_(404, response.status_code)
            elif output.startswith('http'):
                chain = [u[0] for u in response.redirect_chain]
                assert output in chain
            else:
                r = response.redirect_chain
                r.reverse()
                final = urlparse(r[0][0])
                eq_(output, final.path)
                eq_(querystring, final.query)

    @mock.patch.object(Site.objects, 'get_current')
    @mock.patch.object(waffle, 'sample_is_active')
    def test_switch_to_https(self, sample_is_active, get_current):
        """Verify we switch to https when sample is active."""
        get_current.return_value.domain = 'example.com'
        sample_is_active.return_value = True

        response = self.client.get(
            u'/1/firefox/4.0/Linux/en-US/prefs-applications')
        eq_(302, response.status_code)
        assert response['location'].startswith('https://example.com/')
