from nose.tools import eq_

from kitsune.postcrash.models import Signature
from kitsune.sumo.tests import TestCase
from kitsune.wiki.tests import document


class SignatureTests(TestCase):
    def test_get_absolute_url(self):
        doc = document(slug='foo-bar')
        doc.save()
        sig = Signature(signature='baz', document=doc)
        eq_('/kb/foo-bar', sig.get_absolute_url())
