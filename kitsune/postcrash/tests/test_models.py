from nose.tools import eq_

from kitsune.postcrash.tests import SignatureFactory
from kitsune.sumo.tests import TestCase


class SignatureTests(TestCase):
    def test_get_absolute_url(self):
        sig = SignatureFactory(document__slug="foo-bar")
        eq_("/kb/foo-bar", sig.get_absolute_url())
