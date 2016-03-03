from nose.tools import eq_

from kitsune.postcrash.tests import SignatureFactory
from kitsune.sumo.templatetags.jinja_helpers import urlparams
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse


class ApiTests(TestCase):
    def test_no_signature(self):
        response = self.client.get(reverse('postcrash.api'))
        eq_(400, response.status_code)
        eq_('', response.content)
        eq_('text/plain', response['content-type'])

    def test_unknown_signature(self):
        url = urlparams(reverse('postcrash.api'), s='foo')
        response = self.client.get(url)
        eq_(404, response.status_code)
        eq_('', response.content)
        eq_('text/plain', response['content-type'])

    def test_known_signature(self):
        sig = SignatureFactory()
        url = urlparams(reverse('postcrash.api'), s=sig.signature)
        response = self.client.get(url)
        eq_(200, response.status_code)
        eq_('https://example.com/kb/%s' % sig.document.slug, response.content)
        eq_('text/plain', response['content-type'])
