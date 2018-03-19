# -*- coding: utf-8 -*-

import json

from django.conf import settings
from django.contrib.sites.models import Site
from django.test import Client

import mock
from nose.tools import eq_
from pyquery import PyQuery as pq

from kitsune.products.tests import ProductFactory
from kitsune.sumo.redis_utils import redis_client, RedisError
from kitsune.sumo.tests import SkipTest, TestCase, LocalizingClient, MobileTestCase, template_used
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import UserFactory, add_permission
from kitsune.wiki.config import (
    CATEGORIES, TEMPLATES_CATEGORY, TYPO_SIGNIFICANCE, MEDIUM_SIGNIFICANCE, MAJOR_SIGNIFICANCE,
    TEMPLATE_TITLE_PREFIX)
from kitsune.wiki.models import Document, HelpfulVoteMetadata, HelpfulVote, DraftRevision
from kitsune.wiki.tests import (
    HelpfulVoteFactory, new_document_data, RevisionFactory, TranslatedRevisionFactory,
    TemplateDocumentFactory, DocumentFactory, DraftRevisionFactory, ApprovedRevisionFactory,
    RedirectRevisionFactory)
from kitsune.wiki.views import (
    _document_lock_check, _document_lock_clear, _document_lock_steal)


class RedirectTests(TestCase):
    """Tests for the REDIRECT wiki directive"""

    def setUp(self):
        super(RedirectTests, self).setUp()
        ProductFactory()

    def test_redirect_suppression(self):
        """The document view shouldn't redirect when passed redirect=no."""
        rev = RedirectRevisionFactory()
        redirect = rev.document
        response = self.client.get(redirect.get_absolute_url() + '?redirect=no', follow=True)
        self.assertContains(response, 'REDIRECT ')


class LocaleRedirectTests(TestCase):
    """Tests for fallbacks to en-US and such for slug lookups."""
    # Some of these may fail or be invalid if your WIKI_DEFAULT_LANGUAGE is de.

    def setUp(self):
        super(LocaleRedirectTests, self).setUp()
        ProductFactory()

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
        en_doc = DocumentFactory(locale=en, slug='english-slug')
        de_doc = DocumentFactory(locale='de', parent=en_doc)
        RevisionFactory(document=de_doc, is_approved=True)
        return en_doc, de_doc


class LocalizationAnalyticsTests(TestCase):

    def setUp(self):
        super(LocalizationAnalyticsTests, self).setUp()
        ProductFactory()

    def test_not_fired(self):
        """Test that the Not Localized and Not Updated events don't fire
        when they are not appropriate."""
        trans = TranslatedRevisionFactory(is_approved=True)
        trans_doc = trans.document

        # Add a parent revision of TYPO significance. This shouldn't do
        # anything, since it isn't significant enough.
        ApprovedRevisionFactory(
            document=trans.document.parent,
            is_ready_for_localization=True,
            significance=TYPO_SIGNIFICANCE)

        url = reverse('wiki.document', args=[trans_doc.slug],
                      locale=trans_doc.locale)
        response = self.client.get(url, follow=True)
        eq_(200, response.status_code)

        doc = pq(response.content)
        assert '"Not Localized"' not in doc('body').attr('data-ga-push')
        assert '"Not Updated"' not in doc('body').attr('data-ga-push')

    def test_custom_event_majorly_out_of_date(self):
        """If a document's parent has major edits and the document has
        not been updated, it should fire a "Not Updated" GA event."""

        # Make a document, and a translation of it.
        trans = TranslatedRevisionFactory(is_approved=True)

        # Add a parent revision of MAJOR significance:
        ApprovedRevisionFactory(
            document=trans.document.parent,
            is_ready_for_localization=True,
            significance=MAJOR_SIGNIFICANCE)

        url = reverse('wiki.document', args=[trans.document.slug], locale=trans.document.locale)
        response = self.client.get(url, follow=True)
        eq_(200, response.status_code)

        doc = pq(response.content)
        assert '"Not Localized"' not in doc('body').attr('data-ga-push')
        assert '"Not Updated"' in doc('body').attr('data-ga-push')

    def test_custom_event_medium_out_of_date(self):
        """If a document's parent has medium edits and the document has
        not been updated, it should fire a "Not Updated" GA event."""

        # Make a document, and a translation of it.
        trans = TranslatedRevisionFactory(is_approved=True)

        # Add a parent revision of MEDIUM significance:
        ApprovedRevisionFactory(
            document=trans.document.parent,
            is_ready_for_localization=True,
            significance=MEDIUM_SIGNIFICANCE)

        url = reverse('wiki.document', args=[trans.document.slug], locale=trans.document.locale)
        response = self.client.get(url, follow=True)
        eq_(200, response.status_code)

        doc = pq(response.content)
        assert '"Not Localized"' not in doc('body').attr('data-ga-push')
        assert '"Not Updated"' in doc('body').attr('data-ga-push')

    def test_custom_event_not_translated(self):
        """If a document is requested in a locale it is not translated
        to, it should fire a "Not Localized" GA event."""
        # This will make a document and revision suitable for translation.
        r = RevisionFactory(is_approved=True, is_ready_for_localization=True)
        url = reverse('wiki.document', args=[r.document.slug], locale='fr')
        response = self.client.get(url)
        eq_(200, response.status_code)

        doc = pq(response.content)
        assert '"Not Localized"' in doc('body').attr('data-ga-push')
        assert '"Not Updated"' not in doc('body').attr('data-ga-push')

    def test_custom_event_while_fallback_locale(self):
        """If a document is shown in fallback locale because the document is not
        available in requested locale, it should fire a "Fallback Locale" GA event"""
        # A Approved revision ready for localization
        r = ApprovedRevisionFactory(is_ready_for_localization=True)
        # A document and revision in bn-BD locale
        trans = DocumentFactory(parent=r.document, locale='bn-BD')
        ApprovedRevisionFactory(document=trans, based_on=r)
        # Get the bn-IN locale version of the document
        url = reverse('wiki.document', args=[r.document.slug], locale='bn-IN')
        response = self.client.get(url)
        eq_(200, response.status_code)

        doc = pq(response.content)
        ga_data = r.document.slug + "/bn-IN" + "/bn-BD"
        assert ga_data in doc('body').attr('data-ga-push')
        assert '"Fallback Locale"' in doc('body').attr('data-ga-push')
        assert '"Not Localized"' not in doc('body').attr('data-ga-push')


class JsonViewTests(TestCase):
    def setUp(self):
        super(JsonViewTests, self).setUp()

        d = DocumentFactory(title='an article title', slug='article-title')
        RevisionFactory(document=d, is_approved=True)

    def test_json_view_by_title(self):
        """Verify checking for an article by title."""
        url = reverse('wiki.json', force_locale=True)
        resp = self.client.get(url, {'title': 'an article title'})
        eq_(200, resp.status_code)
        data = json.loads(resp.content)
        eq_('article-title', data['slug'])

    def test_json_view_by_slug(self):
        """Verify checking for an article by slug."""
        url = reverse('wiki.json', force_locale=True)
        resp = self.client.get(url, {'slug': 'article-title'})
        eq_(200, resp.status_code)
        data = json.loads(resp.content)
        eq_('an article title', data['title'])

    def test_json_view_404(self):
        """Searching for something that doesn't exist should 404."""
        url = reverse('wiki.json', force_locale=True)
        resp = self.client.get(url, {'title': 'an article title ok.'})
        eq_(404, resp.status_code)


class WhatLinksWhereTests(TestCase):
    def test_what_links_here(self):
        d1 = DocumentFactory(title='D1')
        RevisionFactory(document=d1, content='', is_approved=True)
        d2 = DocumentFactory(title='D2')
        RevisionFactory(document=d2, content='[[D1]]', is_approved=True)

        url = reverse('wiki.what_links_here', args=[d1.slug])
        resp = self.client.get(url, follow=True)
        eq_(200, resp.status_code)
        assert 'D2' in resp.content

    def test_what_links_here_locale_filtering(self):
        d1 = DocumentFactory(title='D1', locale='de')
        ApprovedRevisionFactory(document=d1, content='')
        d2 = DocumentFactory(title='D2', locale='fr')
        ApprovedRevisionFactory(document=d2, content='[[D1]]')

        url = reverse('wiki.what_links_here', args=[d1.slug], locale='de')
        resp = self.client.get(url, follow=True)
        eq_(200, resp.status_code)
        assert 'No other documents link to D1.' in resp.content


class DocumentEditingTests(TestCase):
    """Tests for the document-editing view"""

    client_class = LocalizingClient

    def setUp(self):
        super(DocumentEditingTests, self).setUp()
        self.u = UserFactory()
        add_permission(self.u, Document, 'change_document')
        self.client.login(username=self.u.username, password='testpass')

    def test_retitling(self):
        """When the title of an article is edited, a redirect is made."""
        # Not testing slug changes separately; the model tests cover those plus
        # slug+title changes. If title changes work in the view, the rest
        # should also.
        new_title = 'Some New Title'
        r = ApprovedRevisionFactory()
        d = r.document
        old_title = d.title
        data = new_document_data()
        data.update({'title': new_title, 'slug': d.slug, 'form': 'doc'})
        self.client.post(reverse('wiki.edit_document', args=[d.slug]), data)
        eq_(new_title, Document.objects.get(id=d.id).title)
        assert Document.objects.get(title=old_title).redirect_url()

    def test_retitling_accent(self):
        d = DocumentFactory(title='Umlaut test')
        RevisionFactory(document=d, is_approved=True)
        new_title = u'Ümlaut test'
        data = new_document_data()
        data.update({'title': new_title,
                     'slug': d.slug,
                     'form': 'doc'})
        self.client.post(reverse('wiki.edit_document', args=[d.slug]), data)
        eq_(new_title, Document.objects.get(id=d.id).title)

    def test_retitling_template(self):
        d = TemplateDocumentFactory()
        RevisionFactory(document=d)

        old_title = d.title
        new_title = 'Not a template'

        # First try and change the title without also changing the category. It should fail.
        data = new_document_data()
        data.update({
            'title': new_title,
            'category': d.category,
            'slug': d.slug,
            'form': 'doc'
        })
        url = reverse('wiki.edit_document', args=[d.slug])
        res = self.client.post(url, data, follow=True)
        eq_(Document.objects.get(id=d.id).title, old_title)
        # This message gets HTML encoded.
        assert ('Documents in the Template category must have titles that start with '
                '&#34;Template:&#34;.'
                in res.content)

        # Now try and change the title while also changing the category.
        data['category'] = CATEGORIES[0][0]
        url = reverse('wiki.edit_document', args=[d.slug])
        self.client.post(url, data, follow=True)
        eq_(Document.objects.get(id=d.id).title, new_title)

    def test_removing_template_category(self):
        d = TemplateDocumentFactory()
        RevisionFactory(document=d)
        eq_(d.category, TEMPLATES_CATEGORY)
        assert d.title.startswith(TEMPLATE_TITLE_PREFIX)

        # First try and change the category without also changing the title. It should fail.
        data = new_document_data()
        data.update({
            'title': d.title,
            'category': CATEGORIES[0][0],
            'slug': d.slug,
            'form': 'doc'
        })
        url = reverse('wiki.edit_document', args=[d.slug])
        res = self.client.post(url, data, follow=True)
        eq_(Document.objects.get(id=d.id).category, TEMPLATES_CATEGORY)
        # This message gets HTML encoded.
        assert ('Documents with titles that start with &#34;Template:&#34; must be in the '
                'templates category.' in res.content)

        # Now try and change the title while also changing the category.
        data['title'] = 'not a template'
        url = reverse('wiki.edit_document', args=[d.slug])
        self.client.post(url, data)
        eq_(Document.objects.get(id=d.id).category, CATEGORIES[0][0])

    def test_changing_products(self):
        """Changing products works as expected."""
        r = ApprovedRevisionFactory()
        d = r.document
        prod_desktop = ProductFactory(title=u'desktop')
        prod_mobile = ProductFactory(title=u'mobile')

        data = new_document_data()
        data.update({'products': [prod_desktop.id, prod_mobile.id],
                     'title': d.title,
                     'slug': d.slug,
                     'form': 'doc'})
        self.client.post(reverse('wiki.edit_document', args=[d.slug]), data)

        eq_(sorted(Document.objects.get(id=d.id).products
                   .values_list('id', flat=True)),
            sorted([prod.id for prod in [prod_desktop, prod_mobile]]))

        data.update({'products': [prod_desktop.id],
                     'form': 'doc'})
        self.client.post(reverse('wiki.edit_document', args=[data['slug']]),
                         data)
        eq_(sorted(Document.objects.get(id=d.id).products
                   .values_list('id', flat=True)),
            sorted([prod.id for prod in [prod_desktop]]))

    @mock.patch.object(Site.objects, 'get_current')
    def test_new_document_slugs(self, get_current):
        """Slugs cannot contain /. but can be urlencoded"""
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

        data['slug'] = '%2Atesttest'
        response = self.client.post(reverse('wiki.new_document'), data)
        self.assertContains(response, error)

        data['slug'] = '%20testtest'
        response = self.client.post(reverse('wiki.new_document'), data)
        self.assertContains(response, error)

        data['slug'] = 'valid'
        response = self.client.post(reverse('wiki.new_document'), data)
        self.assertRedirects(response, reverse('wiki.document_revisions',
                                               args=[data['slug']],
                                               locale='en-US'))

    def test_translate_with_parent_slug_while_trans_article_available(self):
        doc = DocumentFactory(locale=settings.WIKI_DEFAULT_LANGUAGE)
        r = RevisionFactory(document=doc)
        trans_doc = DocumentFactory(parent=doc, locale='bn-BD', slug='bn-BD_slug')
        RevisionFactory(document=trans_doc, based_on=r)
        url = reverse('wiki.edit_document', args=[doc.slug], locale=trans_doc.locale)
        response = self.client.get(url)
        eq_(response.status_code, 200)
        # Check translate article template is being used
        assert template_used(response, 'wiki/translate.html')
        content = pq(response.content)
        eq_(content('#id_title').val(), trans_doc.title)
        eq_(content('#id_slug').val(), trans_doc.slug)

    def test_translate_with_parent_slug_while_trans_article_not_available(self):
        doc = DocumentFactory(locale=settings.WIKI_DEFAULT_LANGUAGE)
        RevisionFactory(document=doc)
        url = reverse('wiki.edit_document', args=[doc.slug], locale='bn-BD')
        response = self.client.get(url)
        # Check redirect is happening
        eq_(response.status_code, 302)
        # get the redirected url
        response = self.client.get(url, follow=True)
        eq_(response.status_code, 200)
        # Check translate article template is being used
        assert template_used(response, 'wiki/translate.html')
        content = pq(response.content)
        # While first translation, the slug and title field is always blank.
        # So the value field should be None
        eq_(content('#id_title').val(), None)
        eq_(content('#id_slug').val(), None)

    def test_while_there_is_no_parent_slug(self):
        doc = DocumentFactory(locale=settings.WIKI_DEFAULT_LANGUAGE)
        invalid_slug = doc.slug + 'invalid_slug'
        url = reverse('wiki.edit_document', args=[invalid_slug], locale='bn-BD')
        response = self.client.get(url)
        eq_(response.status_code, 404)

    def test_localized_based_on(self):
        """Editing a localized article 'based on' an older revision of the
        localization is OK."""
        en_r = RevisionFactory()
        fr_d = DocumentFactory(parent=en_r.document, locale='fr')
        RevisionFactory(document=fr_d, based_on=en_r, is_approved=True)
        fr_r = RevisionFactory(document=fr_d, based_on=en_r, keywords="oui", summary="lipsum")
        url = reverse('wiki.new_revision_based_on', locale='fr', args=(fr_d.slug, fr_r.pk,))
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
        doc = RevisionFactory().document
        data = new_document_data()
        data.update({'needs_change': True,
                     'needs_change_comment': comment,
                     'form': 'doc'})

        # Verify that needs_change can't be set if the user doesn't have
        # the permission.
        self.client.post(reverse('wiki.edit_document', args=[doc.slug]), data)
        doc = Document.objects.get(pk=doc.pk)
        assert not doc.needs_change
        assert not doc.needs_change_comment

        # Give the user permission, now it should work.
        add_permission(self.u, Document, 'edit_needs_change')
        self.client.post(reverse('wiki.edit_document', args=[doc.slug]), data)
        doc = Document.objects.get(pk=doc.pk)
        assert doc.needs_change
        eq_(comment, doc.needs_change_comment)

        # Clear out needs_change.
        data.update({'needs_change': False,
                     'needs_change_comment': comment})
        self.client.post(reverse('wiki.edit_document', args=[doc.slug]), data)
        doc = Document.objects.get(pk=doc.pk)
        assert not doc.needs_change
        eq_('', doc.needs_change_comment)

    def test_draft_revision_view(self):
        """Test Draft Revision saving is working propoerly"""
        rev = ApprovedRevisionFactory()
        url = reverse('wiki.draft_revision', locale='bn-BD')
        data = {
            'content': 'Test Content bla bla bla',
            'keyword': 'something',
            'summary': 'some summary',
            'title': 'test title',
            'slug': 'test-slug',
            'based_on': rev.id
        }
        resp = self.client.post(url, data)
        eq_(201, resp.status_code)
        obj = DraftRevision.objects.get(creator=self.u, document=rev.document, locale='bn-BD')
        eq_(obj.content, data['content'])
        eq_(obj.based_on, rev)

    def test_draft_revision_many_times(self):
        """Test only one draft revision for a single translation and user"""
        rev = ApprovedRevisionFactory()
        url = reverse('wiki.draft_revision', locale='bn-BD')
        data = {
            'content': 'Test Content bla bla bla',
            'keyword': 'something',
            'summary': 'some summary',
            'title': 'test title',
            'slug': 'test-slug',
            'based_on': rev.id
        }
        # post 10 post request for draft
        for i in range(10):
            resp = self.client.post(url, data)
            eq_(201, resp.status_code)

        obj = DraftRevision.objects.filter(creator=self.u, document=rev.document, locale='bn-BD')
        # There should be only one draft revision
        eq_(1, obj.count())

    def test_draft_revision_restore_in_translation_page(self):
        """Check Draft Revision is restored when a user click on the Restore Button"""
        # Create a draft revision
        draft = DraftRevisionFactory(creator=self.u)
        doc = draft.document
        # Now send a get request to the page for restoring the draft
        trans_url = reverse('wiki.translate', locale=draft.locale, args=[doc.slug])
        draft_request = {'restore': 'Restore'}
        restore_draft_resp = self.client.get(trans_url, draft_request)
        eq_(200, restore_draft_resp.status_code)
        # Check if the title of the translate page contains the title of draft revision
        trans_page = pq(restore_draft_resp.content)
        eq_(draft.content, trans_page('#id_content').text())

    def test_discard_draft_revision(self):
        """Check Draft Revision is discarded

        If a user clicks on Discard button in the translation page, the draft revision
        should be deleted"""
        draft = DraftRevisionFactory(creator=self.u)
        doc = draft.document
        # Send a request to translate article page to discard the draft
        trans_url = reverse('wiki.translate', locale=draft.locale, args=[doc.slug])
        draft_request = {'discard': 'Discard'}
        restore_draft_resp = self.client.get(trans_url, draft_request)
        eq_(200, restore_draft_resp.status_code)
        # Check if the draft revision is in database
        draft = DraftRevision.objects.filter(id=draft.id)
        eq_(False, draft.exists())

    def test_draft_revision_discarded_when_submitting_revision(self):
        """Check draft revision is discarded when submitting a revision

        A user can have only one Draft revision for each translated document. The draft revision
        should be deleted automatically when the user submit any revision in the document."""
        draft = DraftRevisionFactory(creator=self.u)
        doc = draft.document
        locale = draft.locale
        trans_url = reverse('wiki.translate', locale=locale, args=[doc.slug])
        data = {
            'title': 'Un Test Articulo',
            'slug': 'un-test-articulo',
            'keywords': 'keyUno, keyDos, keyTres',
            'summary': 'lipsumo',
            'content': 'loremo ipsumo doloro sito ameto',
            'form': 'both'}
        self.client.post(trans_url, data)
        draft_revision = DraftRevision.objects.filter(id=draft.id)
        eq_(False, draft_revision.exists())


class AddRemoveContributorTests(TestCase):
    def setUp(self):
        super(AddRemoveContributorTests, self).setUp()
        self.user = UserFactory()
        self.contributor = UserFactory()
        add_permission(self.user, Document, 'change_document')
        self.client.login(username=self.user.username, password='testpass')
        self.revision = RevisionFactory()
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
        assert self.contributor not in self.document.contributors.all()


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

    def test_vote_on_template(self):
        """
        Throw helpful_vote a document that is a template and see if it 400s.
        """
        d = TemplateDocumentFactory()
        r = RevisionFactory(document=d)
        response = self.client.post(reverse('wiki.document_vote', args=['hi']),
                                    {'revision_id': r.id})
        eq_(400, response.status_code)

    def test_unhelpful_survey(self):
        """The unhelpful survey is stored as vote metadata"""
        vote = HelpfulVoteFactory()
        url = reverse('wiki.unhelpful_survey')
        data = {'vote_id': vote.id,
                'button': 'Submit',
                'confusing': 1,
                'too-long': 1,
                'comment': 'lorem ipsum dolor'}
        response = self.client.post(url, data)
        eq_(200, response.status_code)
        eq_('{"message": "Thanks for making us better!"}',
            response.content)

        vote_meta = vote.metadata.all()
        eq_(1, len(vote_meta))
        eq_('survey', vote_meta[0].key)

        survey = json.loads(vote_meta[0].value)
        eq_(3, len(survey.keys()))
        assert 'confusing' in survey
        assert 'too-long' in survey
        eq_('lorem ipsum dolor', survey['comment'])

        # Posting the survey again shouldn't add a new survey result.
        self.client.post(url, data)
        eq_(1, vote.metadata.filter(key='survey').count())

    def test_unhelpful_survey_on_helpful_vote(self):
        """Verify a survey doesn't get saved on helpful votes."""
        vote = HelpfulVoteFactory(helpful=True)
        url = reverse('wiki.unhelpful_survey')
        data = {'vote_id': vote.id,
                'button': 'Submit',
                'confusing': 1,
                'too-long': 1,
                'comment': 'lorem ipsum dolor'}
        self.client.post(url, data)
        eq_(0, vote.metadata.count())

    def test_unhelpful_truncation(self):
        """Give helpful_vote a survey that is too long.

        It should be truncated safely, instead of generating bad JSON.
        """
        vote = HelpfulVoteFactory()
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
        rev = RevisionFactory()
        url = reverse('wiki.document_vote', kwargs={
            'document_slug': rev.document.slug
        })
        self.client.post(url, {
            'revision_id': rev.id,
            'helpful': True,
            'source': 'test',
        })

        eq_(HelpfulVoteMetadata.objects.filter(key='source').count(), 1)

    def test_rate_limiting(self):
        """Verify only 10 votes are counted in a day."""
        for i in range(13):
            rev = RevisionFactory()
            url = reverse('wiki.document_vote', kwargs={
                'document_slug': rev.document.slug})
            self.client.post(url, {
                'revision_id': rev.id,
                'helpful': True})

        eq_(10, HelpfulVote.objects.count())


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
        u1 = UserFactory()
        u2 = UserFactory()

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
        doc = DocumentFactory()
        self._test_lock_helpers(doc)

    def test_lock_helpers_translation(self):
        doc_en = DocumentFactory()
        doc_de = DocumentFactory(parent=doc_en, locale='de')
        self._test_lock_helpers(doc_de)

    def _lock_workflow(self, doc, edit_url):
        """This is a big end to end feature test of document locking.

        This tests that when a user starts editing a page, it gets locked,
        users can steal locks, and that when a user submits the edit page, the
        lock is cleared.
        """
        def _login(user):
            self.client.login(username=user.username, password='testpass')

        def assert_is_locked(r):
            self.assertContains(r, 'id="unlock-button"')

        def assert_not_locked(r):
            self.assertNotContains(r, 'id="unlock-button"')

        u1 = UserFactory(password='testpass')
        u2 = UserFactory(password='testpass')

        # With u1, edit the document. No lock should be found.
        _login(u1)
        r = self.client.get(edit_url)
        # Now load it again, the page should not show as being locked
        # (since u1 has the lock)
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
        rev = ApprovedRevisionFactory()
        doc = rev.document
        url = reverse('wiki.edit_document', args=[doc.slug], locale='en-US')
        self._lock_workflow(doc, url)

    def test_trans_lock_workflow(self):
        """End to end test of locking on a translated document."""
        rev = ApprovedRevisionFactory()
        doc = rev.document
        u = UserFactory(password='testpass')

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
        edit_url = reverse('wiki.edit_document', locale='es',
                           args=[data['slug']])
        es_doc = Document.objects.get(slug=data['slug'])
        eq_(es_doc.locale, 'es')
        self._lock_workflow(es_doc, edit_url)


class MinimalViewTests(TestCase):

    def setUp(self):
        super(MinimalViewTests, self).setUp()
        rev = ApprovedRevisionFactory()
        self.doc = rev.document
        p = ProductFactory()
        self.doc.products.add(p)
        self.doc.save()

    def test_it_works(self):
        url = reverse('wiki.document', args=[self.doc.slug], locale='en-US')
        url += '?minimal=1&mobile=1'
        res = self.client.get(url)
        assert template_used(res, 'wiki/mobile/document-minimal.html')

    def test_only_if_mobile(self):
        url = reverse('wiki.document', args=[self.doc.slug], locale='en-US')
        url += '?minimal=1'
        res = self.client.get(url)
        assert template_used(res, 'wiki/document.html')

    def test_xframe_options(self):
        url = reverse('wiki.document', args=[self.doc.slug], locale='en-US')
        url += '?minimal=1&mobile=1'
        res = self.client.get(url)
        # If it is not set to "DENY", then it is allowed.
        eq_(res.get('X-Frame-Options', 'ALLOW').lower(), 'allow')

    def test_xframe_options_deny_not_minimal(self):
        url = reverse('wiki.document', args=[self.doc.slug], locale='en-US')
        res = self.client.get(url)
        eq_(res['X-Frame-Options'], 'DENY')

    def test_caching(self):
        """Test that the cached version of the page also allows framing."""
        url = reverse('wiki.document', args=[self.doc.slug], locale='en-US')
        url += '?minimal=1&mobile=1'
        res = self.client.get(url)
        eq_(res.get('X-Frame-Options', 'ALLOW').lower(), 'allow')
        # Now do it again. This one should hit the cache.
        res = self.client.get(url)
        eq_(res.get('X-Frame-Options', 'ALLOW').lower(), 'allow')


class MobileDocumentTests(MobileTestCase):

    def setUp(self):
        super(MobileDocumentTests, self).setUp()
        rev = ApprovedRevisionFactory()
        self.doc = rev.document
        p = ProductFactory()
        self.doc.products.add(p)
        self.doc.save()

    def test_it_works(self):
        url = reverse('wiki.document', args=[self.doc.slug], locale='en-US')
        res = self.client.get(url)
        eq_(res.status_code, 200)
        assert template_used(res, 'wiki/mobile/document.html')


class FallbackSystem(TestCase):
    """Check that fallback locales on article level are working correctly."""

    def setUp(self):
        super(FallbackSystem, self).setUp()
        ProductFactory()

    def create_documents(self, locale):
        """Create a document in English and a translated document for the locale"""
        en = settings.WIKI_DEFAULT_LANGUAGE
        en_content = 'This article is in English'
        trans_content = 'This article is translated into %slocale' % locale
        # Create an English article and a translation for the locale
        en_doc = DocumentFactory(locale=en)
        ApprovedRevisionFactory(document=en_doc, content=en_content,
                                is_ready_for_localization=True)
        trans_doc = DocumentFactory(parent=en_doc, locale=locale)
        # Create a new revision of the localized document
        trans_rev = ApprovedRevisionFactory(document=trans_doc, content=trans_content)
        # Make the created revision the current one for the localized document
        trans_doc.current_revision = trans_rev
        trans_doc.save()
        # Return both the English version and the localized version of the document
        return en_doc, trans_doc

    def get_data_from_translated_document(self, header, create_doc_locale, req_doc_locale):
        """Create documents and get provided locale document data"""
        # Create a client with provided ACCEPT_LANGUAGE header information
        client = Client(HTTP_ACCEPT_LANGUAGE=header)
        # Create an English and a localized version of the document, based on create_doc_locale
        en_doc, trans_doc = self.create_documents(create_doc_locale)
        # Get the data of the requested locale version of the document
        url = reverse('wiki.document', args=[en_doc.slug], locale=req_doc_locale)
        response = client.get(url, follow=True)
        eq_(200, response.status_code)
        doc = pq(response.content)
        doc_content = doc('#doc-content').text()
        return doc_content

    def test_header_locales_in_translated_list(self):
        """
        Test that the article is showing in the header locale

        Test cases when the document is not localized to locale requested by the user,
        but is localized to a locale mentioned in the ACCEPT_LANGUAGE header
        """
        # Define a client with es, fr, ja as locale choices in the ACCEPT_LANGUAGE header
        header = 'es,fr;q=0.7,ja;q=0.3,'
        # Create a document localized into fr
        # Attempt to resolve to the es version of the document with the client defined before
        doc_content = self.get_data_from_translated_document(header=header,
                                                             create_doc_locale='fr',
                                                             req_doc_locale='es')
        # Show the fr version of the document based on existing client header,
        # as it is not localized into es
        en_content = 'This article is in English'
        trans_content = 'This article is translated into fr'
        assert en_content not in doc_content
        assert trans_content in doc_content

    def test_header_locales_not_in_translated_list(self):
        """
        Test that the article is showing in the header locale, with the following conditions:

        * the article is not localized into the user-requested locale
        * the article is not localized to any of the locales listed in the ACCEPT_LANGUAGE header
        * there is a fallback locale defined for one of the locales listed in the the
          ACCEPT LANGUAGE header
           ** it is set in kitsune/settings.py

        Test that the fallback locale is used
        """

        # Define a client with de, an, ja as locale choices in the ACCEPT_LANGUAGE header
        header = 'de,an;q=0.7,ja;q=0.3,'
        # Create a document localized into es
        # Attempt to resolve to the de version of the document with the client defined before
        doc_content = self.get_data_from_translated_document(
            header=header, create_doc_locale='es', req_doc_locale='de')
        # Show the es version of the document based on the fallback locale for an set in
        # kitsune/settings.py, as it is not localized into de and there is no available
        # locale based on the client header
        en_content = 'This article is in English'
        trans_content = 'This article is translated into es'
        assert en_content not in doc_content
        assert trans_content in doc_content

    def test_en_in_accept_language_header(self):
        """If the first fallback locale does not exist and the second fallback locale is en-US,
        the second fallback locale should not be used"""
        # Define a client with fr, en-US, de as locale choices in the ACCEPT_LANGUAGE header
        header = 'fr,en-US;q=0.7,de;q=0.3,'
        # Create a document localized into de
        # Attempt to resolve to the es version of the document with the client defined before
        doc_content = self.get_data_from_translated_document(header=header,
                                                             create_doc_locale='de',
                                                             req_doc_locale='es')
        # Show the en-US version of the document based on existing client header,
        # as it is not localized into fr and de is behind en-US in header
        en_content = 'This article is in English'
        trans_content = 'This article is translated into de'
        assert en_content in doc_content
        assert trans_content not in doc_content

    def test_custom_locale_mapping(self):
        """
        Test that the article is showing according to defined locale fallback options
        (more than one), with the following conditions:

        * the article is not localized into the user-requested locale
        * the article is not localized into any of the locales listed in the ACCEPT_LANGUAGE header
        * None of the ACCEPT_LANGUAGE header locales has a defined fallback locale
        * the user-requested locale has more than one fallback locale defined and
          the requested article is localized into one of the defined fallback locales
            ** the fallback locale is set in kitsune/settings.py

        Test that the article is shown in the defined fallback locale
        """

        # Create a document localized into bn-BD. Attempt to resolve to the bn-IN version
        # of the document without defining locale options for the client

        # of the document. While we the client have no language choices.
        doc_content = self.get_data_from_translated_document(
            header=None, create_doc_locale='bn-BD', req_doc_locale='bn-IN')
        # Show the bn-BD version of the document based on the fallback locale,
        # as it is not localized into bn-IN and there is no available locale
        # from the ACCEPT_LANGUAGE header
        en_content = 'This article is in English'
        trans_content = 'This article is translated into bn-BD'
        assert en_content not in doc_content
        assert trans_content in doc_content

    def test_custom_locale_mapping_for_header_locale(self):
        """
        Test that defined locale fallbacks are used as header locales,
        with the following conditions:

        * the article is not localized into the user-requested locale
        * the article is not localized to any of the locales listed in the ACCEPT_LANGUAGE header
        * the header locales do not have a defined fallback locale OR the article is not localized
          into any of those defined fallback locales
        * the user-requested locale has a defined fallback locale, but the article is
          not localized into it
        * one of the locales listed in the ACCEPT_LANGUAGE headers has a defined fallback locale
          and the article is localized into that fallback locale

        Test that the defined fallback locale is used
        """

        # The user-requested locale has a defined custom wiki fallback locale,
        # but the article is not localized into that fallback locale

        # Define a client with ca, pt-PT, ja as locale choices in the ACCEPT_LANGUAGE header
        header = 'ca,bn-IN;q=0.7,ja;q=0.3,'
        # Create a document localized into pt-BR
        # Attempt to resolve to the ca version of the document with the client defined before
        doc_content = self.get_data_from_translated_document(
            header=header, create_doc_locale='bn-BD', req_doc_locale='ca')
        # Show the pt-BR version of the document based on existing custom wiki locale mapping
        # for pt-PT, as it is not localized into ca
        en_content = 'This article is in English'
        trans_content = 'This article is translated into bn-BD'
        assert en_content not in doc_content
        assert trans_content in doc_content

        # If the user-requested locale does not have a custom wiki fallback locale
        # Define a client with ca, bn-IN, ja as locale choices in the ACCEPT_LANGUAGE header
        header = 'ar,bn-IN;q=0.7,ja;q=0.3,'
        # Create a document localized into bn-BD
        # Attempt to resolve to the ar version of the document with the client defined before
        doc_content = self.get_data_from_translated_document(
            header=header, create_doc_locale='bn-BD', req_doc_locale='ar')
        # Show the article in bn-BD based on the custom wiki fallback locale mapping for bn-IN,
        # as it is localized neither into any of the locales listed in the
        # ACCEPT_LANGUAGE header, nor into ar
        en_content = 'This article is in English'
        trans_content = 'This article is translated into bn-BD'
        assert en_content not in doc_content
        assert trans_content in doc_content
