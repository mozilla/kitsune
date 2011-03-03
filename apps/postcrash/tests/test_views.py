from nose.tools import eq_

from postcrash.models import Signature
from sumo.helpers import urlparams
from sumo.tests import TestCase
from sumo.urlresolvers import reverse
from wiki.tests import document


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
        slug = 'foo'
        doc = document(slug=slug)
        doc.save()
        sig = Signature(signature=slug, document=doc)
        sig.save()
        url = urlparams(reverse('postcrash.api'), s=slug)
        response = self.client.get(url)
        eq_(200, response.status_code)
        eq_('https://example.com/kb/%s' % slug, response.content)
        eq_('text/plain', response['content-type'])
