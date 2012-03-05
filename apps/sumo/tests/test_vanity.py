from nose.tools import eq_

from sumo.tests import TestCase


class TestVanityURLs(TestCase):
    """We're just asserting that these vanity URLs go somewhere."""

    def test_windows7(self):
        response = self.client.get('/en-US/windows7-support', follow=False)
        eq_(302, response.status_code)
        assert 'home' in response['location']

    def test_contribute(self):
        response = self.client.get('/en-US/contribute', follow=False)
        eq_(302, response.status_code)
        assert 'superheroes-wanted' in response['location']
