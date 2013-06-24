import json

from nose.tools import eq_

from django.conf import settings

from kitsune.products.tests import product, topic
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
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
            rev = revision(summary='test article {0}'.format(i),
                           document=d,
                           is_approved=True,
                           save=True)

            d.products.add(p)
            d.topics.add(t)
            d.parent = parent(i)
            d.save()

    def test_get_single_bundle(self):
        self._create_bundle('firefox', 'en-US')

        url = reverse('offline.get_bundles') + '?locales=en-US&products=firefox'
        resp = self.client.get(url, follow=True)
        data = json.loads(resp.content)

        assert 'locales' in data
        eq_(1, len(data['locales']))
        eq_([{u'slug': u'firefox', u'name': u'firefox'}], data['locales'][0]['products'])
        eq_(['topic1'], data['locales'][0]['children'])
        eq_('en-US', data['locales'][0]['key'])

        assert 'topics' in data
        eq_(1, len(data['topics']))
        eq_('en-US~firefox~topic1', data['topics'][0]['key'])
        eq_(5, len(data['topics'][0]['docs']))

        assert 'docs' in data
        eq_(5, len(data['docs']))

        assert 'indexes' in data

    def test_get_multiple_bundles(self):
        self._create_bundle('firefox', 'en-US')
        self._create_bundle('mobile', 'fr')

        url = (reverse('offline.get_bundles') +
               '?locales=en-US&products=firefox&locales=fr&products=mobile')
        resp = self.client.get(url, follow=True)
        data = json.loads(resp.content)

        assert 'locales' in data
        eq_(2, len(data['locales']))

        assert 'topics' in data

        assert 'docs' in data

        # Note that _create_bundle with another language will create additional
        # docs for en-US. So this means that en-US will have 10 articles while
        # fr will have 5, making a total of 15.
        eq_(15, len(data['docs']))

        assert 'indexes' in data
