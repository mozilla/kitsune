import json

from django.conf import settings
from django.contrib.sites.models import Site

import mock
from nose.tools import eq_
from nose import SkipTest
from pyquery import PyQuery as pq

from products.tests import product
from sumo.tests import TestCase, LocalizingClient
from sumo.urlresolvers import reverse
from users.tests import user, add_permission
from wiki.models import Document
from wiki.config import VersionMetadata
from wiki.tests import (doc_rev, document, helpful_vote, new_document_data,
                        revision)
from wiki.showfor import _version_groups
from wiki.views import (_document_lock_check, _document_lock_clear,
                        _document_lock_steal)
from wiki.models import HelpfulVoteMetadata

from sumo.redis_utils import redis_client, RedisError


class VersionGroupTests(TestCase):
    def test_version_groups(self):
        """Make sure we correctly set up browser/version mappings for the JS"""
        versions = [VersionMetadata(1, 'Firefox 4.0', 'Firefox 4.0', 'fx4',
                                    5.0, False, True),
                    VersionMetadata(2, 'Firefox 3.5-3.6', 'Firefox 3.5-3.6',
                                    'fx35', 4.0, False, False),
                    VersionMetadata(4, 'Firefox Mobile 1.1',
                                    'Firefox Mobile 1.1', 'm11', 2.0, False,
                                    True)]
        want = {'fx': [(4.0, '35'), (5.0, '4')],
                'm': [(2.0, '11')]}
        eq_(want, _version_groups(versions))


class RedirectTests(TestCase):
    """Tests for the REDIRECT wiki directive"""

    fixtures = ['users.json']

    def setUp(self):
        super(RedirectTests, self).setUp()
        product(save=True)

    def test_redirect_suppression(self):
        """The document view shouldn't redirect when passed redirect=no."""
        redirect, _ = doc_rev('REDIRECT [[http://smoo/]]')
        response = self.client.get(
                       redirect.get_absolute_url() + '?redirect=no',
                       follow=True)
        self.assertContains(response, 'REDIRECT ')


class LocaleRedirectTests(TestCase):
    """Tests for fallbacks to en-US and such for slug lookups."""
    # Some of these may fail or be invalid if your WIKI_DEFAULT_LANGUAGE is de.

    fixtures = ['users.json']

    def setUp(self):
        super(LocaleRedirectTests, self).setUp()
        product(save=True)

    def test_fallback_to_translation(self):
        """If a slug isn't found in the requested locale but is in the default
        locale and if there is a translation of that default-locale document to
        the requested locale, the translation should be served."""
        en_doc, de_doc = self._create_en_and_de_docs()
        response = self.client.get(reverse('wiki.document',
                                           args=[en_doc.slug],
                                           locale='de'),
                                   follow=True)
        self.assertRedirects(response, de_doc.get_absolute_url())

    def test_fallback_with_query_params(self):
        """The query parameters should be passed along to the redirect."""
        en_doc, de_doc = self._create_en_and_de_docs()
        url = reverse('wiki.document', args=[en_doc.slug], locale='de')
        response = self.client.get(url + '?x=y&x=z', follow=True)
        self.assertRedirects(response, de_doc.get_absolute_url() + '?x=y&x=z')

    def _create_en_and_de_docs(self):
        en = settings.WIKI_DEFAULT_LANGUAGE
        en_doc = document(locale=en, slug='english-slug')
        en_doc.save()
        de_doc = document(locale='de', parent=en_doc)
        de_doc.save()
        de_rev = revision(document=de_doc, is_approved=True)
        de_rev.save()
        return en_doc, de_doc


class ViewTests(TestCase):
    fixtures = ['users.json', 'search/documents.json']

    def test_json_view(self):
        url = reverse('wiki.json', force_locale=True)

        resp = self.client.get(url, {'title': 'an article title'})
        eq_(200, resp.status_code)
        data = json.loads(resp.content)
        eq_('article-title', data['slug'])

        resp = self.client.get(url, {'slug': 'article-title'})
        eq_(200, resp.status_code)
        data = json.loads(resp.content)
        eq_('an article title', data['title'])


class DocumentEditingTests(TestCase):
    """Tests for the document-editing view"""

    fixtures = ['users.json']
    client_class = LocalizingClient

    def setUp(self):
        super(DocumentEditingTests, self).setUp()
        u = user(save=True)
        add_permission(u, Document, 'change_document')
        self.client.login(username=u.username, password='testpass')

    def test_retitling(self):
        """When the title of an article is edited, a redirect is made."""
        # Not testing slug changes separately; the model tests cover those plus
        # slug+title changes. If title changes work in the view, the rest
        # should also.
        new_title = 'Some New Title'
        d, r = doc_rev()
        old_title = d.title
        data = new_document_data()
        data.update({'title': new_title,
                     'slug': d.slug,
                     'form': 'doc'})
        self.client.post(reverse('wiki.edit_document', args=[d.slug]), data)
        eq_(new_title, Document.uncached.get(slug=d.slug).title)
        assert Document.uncached.get(title=old_title).redirect_url()

    def test_changing_products(self):
        """Changing products works as expected."""
        d, r = doc_rev()
        prod_desktop = product(title=u'desktop', save=True)
        prod_mobile = product(title=u'mobile', save=True)

        data = new_document_data()
        data.update({'products': [prod_desktop.id, prod_mobile.id],
                     'title': d.title,
                     'slug': d.slug,
                     'form': 'doc'})
        self.client.post(reverse('wiki.edit_document', args=[d.slug]), data)

        eq_(sorted(Document.uncached.get(slug=d.slug).products.values_list(
                    'id', flat=True)),
            sorted([prod.id for prod in [prod_desktop, prod_mobile]]))

        data.update({'products': [prod_desktop.id],
                     'form': 'doc'})
        self.client.post(reverse('wiki.edit_document', args=[data['slug']]),
                         data)
        eq_(sorted(Document.uncached.get(slug=d.slug).products.values_list(
                    'id', flat=True)),
            sorted([prod.id for prod in [prod_desktop]]))

    @mock.patch.object(Site.objects, 'get_current')
    def test_invalid_slugs(self, get_current):
        """Slugs cannot contain /."""
        get_current.return_value.domain = 'testserver'
        data = new_document_data()
        error = 'The slug provided is not valid.'

        data['slug'] = 'inva/lid'
        response = self.client.post(reverse('wiki.new_document'), data)
        self.assertContains(response, error)

        data['slug'] = 'no-question-marks?'
        response = self.client.post(reverse('wiki.new_document'), data)
        self.assertContains(response, error)

        data['slug'] = 'no+plus'
        response = self.client.post(reverse('wiki.new_document'), data)
        self.assertContains(response, error)

        data['slug'] = 'valid'
        response = self.client.post(reverse('wiki.new_document'), data)
        self.assertRedirects(response, reverse('wiki.document_revisions',
                                               args=[data['slug']],
                                               locale='en-US'))

    def test_localized_based_on(self):
        """Editing a localized article 'based on' an older revision of the
        localization is OK."""
        en_r = revision(save=True)
        fr_d = document(parent=en_r.document, locale='fr', save=True)
        revision(document=fr_d, based_on=en_r, is_approved=True, save=True)
        fr_r = revision(document=fr_d, based_on=en_r, keywords="oui",
                        summary="lipsum", save=True)
        url = reverse('wiki.new_revision_based_on',
                      locale='fr', args=(fr_d.slug, fr_r.pk,))
        response = self.client.get(url)
        doc = pq(response.content)
        input = doc('#id_based_on')[0]
        eq_(int(input.value), en_r.pk)
        eq_(doc('#id_keywords')[0].attrib['value'], 'oui')
        eq_(doc('#id_summary').text(), 'lipsum')

    def test_needs_change(self):
        """Test setting and unsetting the needs change flag"""
        # Create a new document and edit it, setting needs_change.
        comment = 'Please update for Firefix.next'
        doc = revision(save=True).document
        data = new_document_data()
        data.update({'needs_change': True,
                     'needs_change_comment': comment,
                     'form': 'doc'})
        self.client.post(reverse('wiki.edit_document', args=[doc.slug]), data)
        doc = Document.uncached.get(pk=doc.pk)
        assert doc.needs_change
        eq_(comment, doc.needs_change_comment)

        # Clear out needs_change
        data.update({'needs_change': False,
                     'needs_change_comment': comment})
        self.client.post(reverse('wiki.edit_document', args=[doc.slug]), data)
        doc = Document.uncached.get(pk=doc.pk)
        assert not doc.needs_change
        eq_('', doc.needs_change_comment)


class AddRemoveContributorTests(TestCase):
    def setUp(self):
        super(AddRemoveContributorTests, self).setUp()
        self.user = user(save=True)
        self.contributor = user(save=True)
        add_permission(self.user, Document, 'change_document')
        self.client.login(username=self.user.username, password='testpass')
        self.revision = revision(save=True)
        self.document = self.revision.document

    def test_add_contributor(self):
        url = reverse('wiki.add_contributor', locale='en-US',
                      args=[self.document.slug])
        r = self.client.get(url)
        eq_(405, r.status_code)
        r = self.client.post(url, {'users': self.contributor.username})
        eq_(302, r.status_code)
        assert self.contributor in self.document.contributors.all()

    def test_remove_contributor(self):
        self.document.contributors.add(self.contributor)
        url = reverse('wiki.remove_contributor', locale='en-US',
                      args=[self.document.slug, self.contributor.id])
        r = self.client.get(url)
        eq_(200, r.status_code)
        r = self.client.post(url)
        eq_(302, r.status_code)
        assert not self.contributor in self.document.contributors.all()


class VoteTests(TestCase):
    client_class = LocalizingClient

    def test_helpful_vote_bad_id(self):
        """Throw helpful_vote a bad ID, and see if it crashes."""
        response = self.client.post(reverse('wiki.document_vote', args=['hi']),
                                    {'revision_id': 'x'})
        eq_(404, response.status_code)

    def test_helpful_vote_no_id(self):
        """Throw helpful_vote a POST without an ID and see if it 400s."""
        response = self.client.post(reverse('wiki.document_vote', args=['hi']),
                                    {})
        eq_(400, response.status_code)

    def test_unhelpful_survey(self):
        """The unhelpful survey is stored as vote metadata"""
        vote = helpful_vote(save=True)
        response = self.client.post(reverse('wiki.unhelpful_survey'),
                                    {'vote_id': vote.id,
                                     'button': 'Submit',
                                     'confusing': 1,
                                     'too-long': 1,
                                     'comment': 'lorem ipsum dolor'})
        eq_(200, response.status_code)
        eq_('{"message": "Thanks for making us better!"}',
            response.content)

        vote_meta = vote.metadata.all()[0]
        eq_('survey', vote_meta.key)

        survey = json.loads(vote_meta.value)
        eq_(3, len(survey.keys()))
        assert 'confusing' in survey
        assert 'too-long' in survey
        eq_('lorem ipsum dolor', survey['comment'])

    def test_unhelpful_truncation(self):
        """Give helpful_vote a survey that is too long.

        It should be truncated safely, instead of generating bad JSON.
        """
        vote = helpful_vote(save=True)
        too_long_comment = ('lorem ipsum' * 100) + 'bad data'
        self.client.post(reverse('wiki.unhelpful_survey'),
                         {'vote_id': vote.id,
                          'button': 'Submit',
                          'comment': too_long_comment})
        vote_meta = vote.metadata.all()[0]
        # Will fail if it is not proper json, ie: bad truncation happened.
        survey = json.loads(vote_meta.value)
        # Make sure the right value was truncated.
        assert 'bad data' not in survey['comment']

    def test_source(self):
        """Test that the source metadata field works."""
        rev = revision(save=True)
        url = reverse('wiki.document_vote', kwargs={
            'document_slug': rev.document.slug
            })
        self.client.post(url, {
                'revision_id': rev.id,
                'helpful': True,
                'source': 'test',
            })

        eq_(HelpfulVoteMetadata.objects.filter(key='source').count(), 1)


class TestDocumentLocking(TestCase):
    client_class = LocalizingClient

    def setUp(self):
        super(TestDocumentLocking, self).setUp()
        try:
            self.redis = redis_client('default')
            self.redis.flushdb()
        except RedisError:
            raise SkipTest

    def _test_lock_helpers(self, doc):
        u1 = user(save=True)
        u2 = user(save=True)

        # No one has the document locked yet.
        eq_(_document_lock_check(doc.id), None)
        # u1 should be able to lock the doc
        eq_(_document_lock_steal(doc.id, u1.username), True)
        eq_(_document_lock_check(doc.id), u1.username)
        # u2 should be able to steal the lock
        eq_(_document_lock_steal(doc.id, u2.username), True)
        eq_(_document_lock_check(doc.id), u2.username)
        # u1 can't release the lock, because u2 stole it
        eq_(_document_lock_clear(doc.id, u1.username), False)
        eq_(_document_lock_check(doc.id), u2.username)
        # u2 can release the lock
        eq_(_document_lock_clear(doc.id, u2.username), True)
        eq_(_document_lock_check(doc.id), None)

    def test_lock_helpers_doc(self):
        doc = document(save=True)
        self._test_lock_helpers(doc)

    def test_lock_helpers_translation(self):
        doc_en = document(save=True)
        doc_de = document(parent=doc_en, locale='de', save=True)
        self._test_lock_helpers(doc_de)

    def _lock_workflow(self, doc, edit_url):
        """This is a big end to end feature test of document locking.

        This tests that when a user starts editing a page, it gets locked,
        users can steal locks, and that when a user submits the edit page, the
        lock is cleared.
        """
        _login = lambda u: self.client.login(username=u.username, password='testpass')
        assert_is_locked = lambda r: self.assertContains(r, 'id="unlock-button"')
        assert_not_locked = lambda r: self.assertNotContains(r, 'id="unlock-button"')

        u1 = user(save=True, password='testpass')
        u2 = user(save=True, password='testpass')

        # With u1, edit the document. No lock should be found.
        _login(u1)
        r = self.client.get(edit_url)
        # Now load it again, the page should not show as being locked (since u1 has the lock)
        r = self.client.get(edit_url)
        assert_not_locked(r)

        # With u2, edit the document. It should be locked.
        _login(u2)
        r = self.client.get(edit_url)
        assert_is_locked(r)
        # Simulate stealing the lock by clicking the button.
        _document_lock_steal(doc.id, u2.username)
        r = self.client.get(edit_url)
        assert_not_locked(r)

        # Now u1 should see the page as locked.
        _login(u1)
        r = self.client.get(edit_url)
        assert_is_locked(r)

        # Now u2 submits the page, clearing the held lock.
        _login(u2)
        r = self.client.post(edit_url)

        data = new_document_data()
        data.update({'title': doc.title, 'slug': doc.slug, 'form': 'doc'})
        self.client.post(edit_url, data)

        # And u1 should not see a lock warning.
        _login(u1)
        r = self.client.get(edit_url)
        assert_not_locked(r)

    def test_doc_lock_workflow(self):
        """End to end test of locking on an english document."""
        doc, rev = doc_rev()
        url = reverse('wiki.edit_document', args=[doc.slug], locale='en-US')
        self._lock_workflow(doc, url)

    def test_trans_lock_workflow(self):
        """End to end test of locking on a translated document."""
        doc, _ = doc_rev()
        u = user(save=True, password='testpass')

        # Create a new translation of doc() using the translation view
        self.client.login(username=u.username, password='testpass')
        trans_url = reverse('wiki.translate', locale='es', args=[doc.slug])
        data = {
            'title': 'Un Test Articulo',
            'slug': 'un-test-articulo',
            'keywords': 'keyUno, keyDos, keyTres',
            'summary': 'lipsumo',
            'content': 'loremo ipsumo doloro sito ameto'}
        r = self.client.post(trans_url, data)
        eq_(r.status_code, 302)

        # Now run the test.
        edit_url = reverse('wiki.edit_document', locale='es', args=[data['slug']])
        es_doc = Document.objects.get(slug=data['slug'])
        eq_(es_doc.locale, 'es')
        self._lock_workflow(es_doc, edit_url)
