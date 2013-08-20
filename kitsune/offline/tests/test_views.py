import json

from nose import SkipTest
from nose.tools import eq_

from django.conf import settings

from kitsune.offline.cron import build_kb_bundles
from kitsune.products.tests import product, topic
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.redis_utils import RedisError, redis_client
from kitsune.wiki.models import Document
from kitsune.wiki.tests import document, revision


class OfflineViewTests(TestCase):

    def _create_bundle(self, prod, locale=settings.WIKI_DEFAULT_LANGUAGE):
        p = product(title=prod, save=True)
        t = topic(title='topic1', product=p, save=True)

        if locale == settings.WIKI_DEFAULT_LANGUAGE:
            parent = lambda i: None
        else:
            def parent(i):
                d = document(title='test {0} {1}'.format(locale, i),
                             locale=settings.WIKI_DEFAULT_LANGUAGE,
                             save=True)

                d.products.add(p)
                d.topics.add(t)
                d.save()

                revision(summary='test article {0}'.format(i),
                         document=d,
                         is_approved=True,
                         save=True)
                return d

        for i in xrange(5):
            d = document(title='test {0} {1}'.format(locale, i),
                         locale=locale, save=True)
            revision(summary='test article {0}'.format(i),
                     document=d,
                     is_approved=True,
                     save=True)

            d.products.add(p)
            d.topics.add(t)
            d.parent = parent(i)
            d.save()

        try:
            build_kb_bundles((prod, ))
        except RedisError:
            pass  # do nothing as we should gracefully fallback.

    def test_get_single_bundle(self):
        self._create_bundle('firefox', 'en-US')

        url = reverse('offline.get_bundle') + '?locale=en-US&product=firefox'
        resp = self.client.get(url, follow=True)
        data = json.loads(resp.content)

        assert 'locales' in data
        eq_(1, len(data['locales']))
        eq_([{u'slug': u'firefox', u'name': u'firefox'}],
            data['locales'][0]['products'])
        eq_('en-US', data['locales'][0]['key'])

        assert 'topics' in data
        eq_(1, len(data['topics']))
        eq_('en-US~firefox~topic1', data['topics'][0]['key'])
        eq_(5, len(data['topics'][0]['docs']))

        assert 'docs' in data
        eq_(5, len(data['docs']))

        assert 'indexes' in data

    def test_get_bundle_bad_request(self):
        url = reverse('offline.get_bundle')
        resp = self.client.get(url, follow=True)
        eq_(400, resp.status_code)
        data = json.loads(resp.content)
        eq_('bad request', data['error'])

    def test_get_bundle_not_found(self):
        url = reverse('offline.get_bundle') + '?locale=fr&product=redpanda'
        resp = self.client.get(url, follow=True)
        eq_(404, resp.status_code)
        data = json.loads(resp.content)
        eq_('not found', data['error'])

    def test_get_bundle_meta(self):
        self._create_bundle('firefox', 'en-US')
        url = (reverse('offline.bundle_meta') +
               '?locale=en-US&product=firefox')

        try:
            redis_client('default')
        except RedisError:
            raise SkipTest

        resp = self.client.get(url, follow=True)

        meta = json.loads(resp.content)
        hash1 = meta['hash']
        assert resp['Content-Type'] == 'application/json'

        assert len(hash1) == 40  # sha1 hexdigest should be 40 char long.

        doc = Document.objects.all()[0]  # getting one document should be okay.
        doc.title = 'some differnet title!'
        doc.save()

        # rebuild bundle as the version is different now.
        build_kb_bundles(('firefox', ))

        # test to see if the hash has changed.
        resp = self.client.get(url, follow=True)
        assert hash1 != json.loads(resp.content)['hash']

    def test_get_language(self):
        self._create_bundle('firefox', 'en-US')

        resp = self.client.get(reverse('offline.get_languages'))
        meta = json.loads(resp.content)

        assert {'id': 'en-US', 'name': 'English'} in meta['languages']
