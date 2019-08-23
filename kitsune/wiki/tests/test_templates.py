from datetime import datetime, timedelta
import json

from django.conf import settings
from django.contrib.sites.models import Site
from django.core import mail
from django.core.cache import cache

import mock
from nose.tools import eq_, nottest

from kitsune.products.tests import ProductFactory, TopicFactory
from kitsune.sumo.templatetags.jinja_helpers import urlparams
from kitsune.sumo.tests import post, get, attrs_eq, MobileTestCase, MinimalViewTestCase
from kitsune.sumo.tests import SumoPyQuery as pq, template_used
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import UserFactory, add_permission
from kitsune.wiki.events import (
    EditDocumentEvent, ReadyRevisionEvent, ReviewableRevisionInLocaleEvent,
    ApproveRevisionInLocaleEvent, get_diff_for)
from kitsune.wiki.models import (
    Document, Revision, HelpfulVote, HelpfulVoteMetadata)
from kitsune.wiki.config import (
    SIGNIFICANCES, MEDIUM_SIGNIFICANCE, ADMINISTRATION_CATEGORY, TROUBLESHOOTING_CATEGORY,
    CATEGORIES, CANNED_RESPONSES_CATEGORY, TEMPLATES_CATEGORY, TEMPLATE_TITLE_PREFIX)
from kitsune.wiki.tasks import send_reviewed_notification
from kitsune.wiki.tests import (
    TestCaseBase, DocumentFactory, DraftRevisionFactory, RevisionFactory, ApprovedRevisionFactory,
    RedirectRevisionFactory, TranslatedRevisionFactory, LocaleFactory, new_document_data)


READY_FOR_REVIEW_EMAIL_CONTENT = u"""\
%(user)s submitted a new revision to the document %(title)s.

Fixing all the typos!!!!!11!!!one!!!!

To review this revision, click the following link, or paste it into your \
browser's location bar:

https://testserver/en-US/kb/%(slug)s/review/%(new_id)s?utm_campaign=\
wiki-ready-review&utm_medium=email&utm_source=notification

--
Summary:
%(summary)s

--
Changes:
%(diff)s

--
Unsubscribe from these emails:
https://testserver/en-US/unsubscribe/%(watcher)s?s=%(secret)s"""


DOCUMENT_EDITED_EMAIL_CONTENT = u"""\
%(user)s created a new revision to the document %(title)s.

Fixing all the typos!!!!!11!!!one!!!!

To view this document's history, click the following link, or paste it \
into your browser's location bar:

https://testserver/en-US/kb/%(slug)s/history?utm_campaign=wiki-edit&\
utm_medium=email&utm_source=notification

--
Summary:
%(summary)s

--
Changes:
%(diff)s

--
Unsubscribe from these emails:
https://testserver/en-US/unsubscribe/%(watcher)s?s=%(secret)s"""


APPROVED_EMAIL_CONTENT = u"""\
%(reviewer)s has approved the revision to the document %(document_title)s.

To view the updated document, click the following link, or paste it into \
your browser's location bar:

https://testserver/en-US/kb/%(document_slug)s?utm_campaign=wiki-approved&\
utm_medium=email&utm_source=notification

--
Summary:
%(summary)s

--
Changes:
%(diff)s

--
Unsubscribe from these emails:
https://testserver/en-US/unsubscribe/%(watcher)s?s=%(secret)s"""


class DocumentTests(TestCaseBase):
    """Tests for the Document template"""

    def setUp(self):
        super(DocumentTests, self).setUp()
        ProductFactory()

    def test_document_view(self):
        """Load the document view page and verify the title and content."""
        r = ApprovedRevisionFactory(summary='search summary', content='Some text.')
        response = self.client.get(r.document.get_absolute_url())
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(r.document.title, doc('article h1.title').text())
        eq_(pq(r.document.html)('div').text(), doc('#doc-content div').text())
        # There's a canonical URL in the <head>.
        eq_(settings.CANONICAL_URL + r.document.get_absolute_url(),
            doc('link[rel=canonical]').attr('href'))
        # The summary is in <meta name="description"...
        eq_('search summary', doc('meta[name=description]').attr('content'))

    def test_english_document_no_approved_content(self):
        """Load an English document with no approved content."""
        r = RevisionFactory(content='Some text.', is_approved=False)
        response = self.client.get(r.document.get_absolute_url())
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(r.document.title, doc('article h1.title').text())
        eq_("This article doesn't have approved content yet.",
            doc('#doc-content').text())

    def test_translation_document_no_approved_content(self):
        """Load a non-English document with no approved content, with a parent
        with no approved content either."""
        r = RevisionFactory(content='Some text.', is_approved=False)
        d2 = DocumentFactory(parent=r.document, locale='fr', slug='french')
        RevisionFactory(document=d2, content='Moartext', is_approved=False)
        response = self.client.get(d2.get_absolute_url())
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(d2.title, doc('article h1.title').text())
        # Avoid depending on localization, assert just that there is only text
        # d.html would definitely have a <p> in it, at least.
        eq_(doc('#doc-content').html().strip(), doc('#doc-content').text())

    def test_document_fallback_with_translation(self):
        """The document template falls back to English if translation exists
        but it has no approved revisions."""
        r = ApprovedRevisionFactory(content='Test')
        d2 = DocumentFactory(parent=r.document, locale='fr', slug='french')
        RevisionFactory(document=d2, is_approved=False)
        url = reverse('wiki.document', args=[d2.slug], locale='fr')
        response = self.client.get(url)
        doc = pq(response.content)
        eq_(d2.title, doc('article h1.title').text())

        # Fallback message is shown.
        eq_(1, len(doc('#doc-pending-fallback')))
        # Removing this as it shows up in text(), and we don't want to depend
        # on its localization.
        doc('#doc-pending-fallback').remove()
        # Included content is English.
        eq_(pq(r.document.html).text(), doc('#doc-content').text())

    def test_document_fallback_with_translation_english_slug(self):
        """The document template falls back to English if translation exists
        but it has no approved revisions, while visiting the English slug."""
        r = ApprovedRevisionFactory(content='Test')
        d2 = DocumentFactory(parent=r.document, locale='fr', slug='french')
        RevisionFactory(document=d2, is_approved=False)
        url = reverse('wiki.document', args=[r.document.slug], locale='fr')
        response = self.client.get(url, follow=True)
        eq_('/fr/kb/french', response.redirect_chain[0][0])
        doc = pq(response.content)
        # Fallback message is shown.
        eq_(1, len(doc('#doc-pending-fallback')))
        # Removing this as it shows up in text(), and we don't want to depend
        # on its localization.
        doc('#doc-pending-fallback').remove()
        # Included content is English.
        eq_(pq(r.document.html).text(), doc('#doc-content').text())

    def test_document_fallback_no_translation(self):
        """The document template falls back to English if no translation exists."""
        r = ApprovedRevisionFactory(content='Some text.')
        url = reverse('wiki.document', args=[r.document.slug], locale='fr')
        response = self.client.get(url)
        doc = pq(response.content)
        eq_(r.document.title, doc('article h1.title').text())
        # Removing this as it shows up in text(), and we don't want to depend
        # on its localization.
        doc('#doc-pending-fallback').remove()
        # Included content is English.
        eq_(pq(r.document.html)('div').text(), doc('#doc-content div').text())

    def test_document_fallback_no_translation_not_ready_for_l10n(self):
        """Prompt to localize an article isn't shown when there is a pending localization."""
        # Creating a revision not ready for localization
        r = ApprovedRevisionFactory(content='Some text.', is_ready_for_localization=False)
        url = reverse('wiki.document', args=[r.document.slug], locale='de')
        response = self.client.get(url)
        doc = pq(response.content)
        # Fallback message is not shown.
        eq_(0, len(doc('#doc-pending-fallback')))

    def test_document_fallback_no_translation_ready_for_l10n(self):
        """Prompt to localize an article is shown when there are no pending localizations."""
        # Creating a revision ready for localization
        r = ApprovedRevisionFactory(content='Some text.', is_ready_for_localization=True)
        url = reverse('wiki.document', args=[r.document.slug], locale='de')
        response = self.client.get(url)
        doc = pq(response.content)
        # Fallback message is shown.
        eq_(1, len(doc('#doc-pending-fallback')))

    def test_redirect(self):
        """Make sure documents with REDIRECT directives redirect properly.

        Also check the backlink to the redirect page.

        """
        target = DocumentFactory()
        target_url = target.get_absolute_url()

        # Ordinarily, a document with no approved revisions cannot have HTML,
        # but we shove it in manually here as a shortcut:
        redirect = RedirectRevisionFactory(target=target).document
        redirect_url = redirect.get_absolute_url()
        response = self.client.get(redirect_url, follow=True)
        self.assertRedirects(
            response,
            urlparams(target_url, redirectlocale=redirect.locale, redirectslug=redirect.slug))
        self.assertContains(response, redirect_url + '?redirect=no')
        # There's a canonical URL in the <head>.
        doc = pq(response.content)
        eq_(settings.CANONICAL_URL + target_url, doc('link[rel=canonical]').attr('href'))

    def test_redirect_no_vote(self):
        """Make sure documents with REDIRECT directives have no vote form.
        """
        target = DocumentFactory()
        redirect = RedirectRevisionFactory(target=target).document
        redirect_url = redirect.get_absolute_url()
        response = self.client.get(redirect_url + '?redirect=no')
        doc = pq(response.content)
        assert not doc('.document-vote')

    def test_redirect_from_nonexistent(self):
        """The template shouldn't crash or print a backlink if the "from" page
        doesn't exist."""
        d = DocumentFactory()
        response = self.client.get(urlparams(d.get_absolute_url(),
                                             redirectlocale='en-US',
                                             redirectslug='nonexistent'))
        self.assertNotContains(response, 'Redirected from ')

    def test_watch_includes_csrf(self):
        """The watch/unwatch forms should include the csrf tag."""
        u = UserFactory()
        self.client.login(username=u.username, password='testpass')
        d = DocumentFactory()
        resp = self.client.get(d.get_absolute_url())
        doc = pq(resp.content)
        assert doc('#doc-watch input[type=hidden]')

    def test_non_localizable_translate_disabled(self):
        """Non localizable document doesn't show tab for 'Localize'."""
        u = UserFactory()
        self.client.login(username=u.username, password='testpass')
        d = DocumentFactory(is_localizable=True)
        resp = self.client.get(d.get_absolute_url())
        doc = pq(resp.content)
        assert 'Translate' in doc('#doc-tools li').text()

        # Make it non-localizable
        d.is_localizable = False
        d.save()
        resp = self.client.get(d.get_absolute_url())
        doc = pq(resp.content)
        assert 'Localize' not in doc('#doc-tools li').text()

    def test_obsolete_hide_edit(self):
        """Make sure Edit sidebar link is hidden for obsolete articles."""
        d = DocumentFactory(is_archived=True)
        r = self.client.get(d.get_absolute_url())
        doc = pq(r.content)
        assert not doc('#doc-tabs li.edit')

    def test_obsolete_no_vote(self):
        """No voting on is_archived documents."""
        d = DocumentFactory(is_archived=True)
        RevisionFactory(document=d, is_approved=True)
        response = self.client.get(d.get_absolute_url())
        eq_(200, response.status_code)
        doc = pq(response.content)
        assert not doc('.document-vote')

    def test_templates_noindex(self):
        """Document templates should have a noindex meta tag."""
        # Create a document and verify there is no robots:noindex
        d = DocumentFactory()
        r = ApprovedRevisionFactory(document=d)

        response = self.client.get(r.document.get_absolute_url())
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(0, len(doc('meta[name=robots]')))

        # Convert the document to a template and verify robots:noindex
        d.category = TEMPLATES_CATEGORY
        d.title = TEMPLATE_TITLE_PREFIX + d.title
        d.save()

        # This page is cached
        cache.clear()

        response = self.client.get(r.document.get_absolute_url())
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(doc('meta[name=robots]')[0].attrib['content'], 'noindex')

    def test_archived_noindex(self):
        """Archived documents should have a noindex meta tag."""
        # Create a document and verify there is no robots:noindex
        r = ApprovedRevisionFactory(content='Some text.')
        response = self.client.get(r.document.get_absolute_url())
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(0, len(doc('meta[name=robots]')))

        # Archive the document and verify robots:noindex
        d = r.document
        d.is_archived = True
        d.save()
        cache.clear()
        response = self.client.get(r.document.get_absolute_url())
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_('noindex', doc('meta[name=robots]')[0].attrib['content'])

    def test_administration_noindex(self):
        """Administration documents should have a noindex meta tag."""
        # Create a document and verify there is no robots:noindex
        r = ApprovedRevisionFactory(content='Some text.')
        response = self.client.get(r.document.get_absolute_url())
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(0, len(doc('meta[name=robots]')))

        # Archive the document and verify robots:noindex
        d = r.document
        d.category = ADMINISTRATION_CATEGORY
        d.save()
        cache.clear()
        response = self.client.get(r.document.get_absolute_url())
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_('noindex', doc('meta[name=robots]')[0].attrib['content'])

    def test_canned_responses_noindex(self):
        """Canned response documents should have a noindex meta tag."""
        # Create a document and verify there is no robots:noindex
        r = ApprovedRevisionFactory(content='Some text.')
        response = self.client.get(r.document.get_absolute_url())
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(0, len(doc('meta[name=robots]')))

        # Archive the document and verify robots:noindex
        d = r.document
        d.category = CANNED_RESPONSES_CATEGORY
        d.save()
        cache.clear()
        response = self.client.get(r.document.get_absolute_url())
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_('noindex', doc('meta[name=robots]')[0].attrib['content'])

    def test_links_follow(self):
        """Links in kb should not have rel=nofollow"""
        r = ApprovedRevisionFactory(content='Some link http://test.com')
        response = self.client.get(r.document.get_absolute_url())
        eq_(200, response.status_code)
        doc = pq(response.content)
        assert 'rel' not in doc('#doc-content a')[0].attrib

    def test_document_with_fallback_locale(self):
        """The document template falls back to fallback locale if there is
        custom wiki fallback mapping for the locale and the locale have no translation
        exists."""
        # Create an English document and a es translated document
        en_rev = ApprovedRevisionFactory(is_ready_for_localization=True)
        trans_doc = DocumentFactory(parent=en_rev.document, locale='es')
        trans_rev = ApprovedRevisionFactory(document=trans_doc)
        # Mark the created revision as the current revision for the document
        trans_doc.current_revision = trans_rev
        trans_doc.save()

        # Get the ca version of the document.
        # Resolve to the ca version
        # because ca has es set in FALLBACK_LOCALES in wiki/config.py
        url = reverse('wiki.document', args=[en_rev.document.slug], locale='ca')
        response = self.client.get(url)
        doc = pq(response.content)
        eq_(trans_doc.title, doc('article h1.title').text())

        # Display fallback message to the user.
        eq_(1, len(doc('#doc-pending-fallback')))
        # Check Translate article is showing in the side tools bar
        assert 'Translate Article' in doc('#editing-tools-sidebar').text()
        # Removing this as it shows up in text(), and we don't want to depend
        # on its localization.
        doc('#doc-pending-fallback').remove()
        # Check that content is available in es
        eq_(pq(trans_doc.html)('div').text(), doc('#doc-content div').text())

    def test_document_share_link_escape(self):
        """Ensure that the share link isn't escaped."""
        r = ApprovedRevisionFactory(
            content='Test',
            document__share_link='https://www.example.org',
        )
        response = self.client.get(r.document.get_absolute_url())
        doc = pq(response.content)
        eq_(doc('.wiki-doc .share-link a').attr('href'), 'https://www.example.org')


class MobileArticleTemplate(MobileTestCase):
    def setUp(self):
        super(MobileArticleTemplate, self).setUp()
        ProductFactory()

    def test_document_view(self):
        """Verify mobile template doesn't 500."""
        r = ApprovedRevisionFactory(content='Some text.')
        response = self.client.get(r.document.get_absolute_url())
        eq_(200, response.status_code)
        assert template_used(response, 'wiki/mobile/document.html')

    def test_document_share_link_escape(self):
        """Ensure that the share link isn't escaped."""
        r = ApprovedRevisionFactory(
            content='Test',
            document__share_link='https://www.example.org',
        )
        response = self.client.get(r.document.get_absolute_url())
        doc = pq(response.content)
        eq_(doc('#wiki-doc .share-link a').attr('href'), 'https://www.example.org')


class MinimalArticleTemplate(MinimalViewTestCase):
    def setUp(self):
        super(MinimalArticleTemplate, self).setUp()
        ProductFactory()

    def test_document_share_link_escape(self):
        """Ensure that the share link isn't escaped."""
        r = ApprovedRevisionFactory(
            content='Test',
            document__share_link='https://www.example.org',
        )
        response = self.client.get(self.get_minimal_url(r.document))
        doc = pq(response.content)
        eq_(doc('#wiki-doc .share-link a').attr('href'), 'https://www.example.org')


class RevisionTests(TestCaseBase):
    """Tests for the Revision template"""

    def setUp(self):
        super(RevisionTests, self).setUp()
        self.client.logout()

    def test_revision_view(self):
        """Load the revision view page and verify the title and content."""
        d = _create_document()
        r = d.current_revision
        r.created = datetime(2011, 1, 1)
        r.reviewed = datetime(2011, 1, 2)
        r.readied_for_localization = datetime(2011, 1, 3)
        r.save()
        url = reverse('wiki.revision', args=[d.slug, r.id])
        response = self.client.get(url)
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_('Revision id: %s' % r.id,
            doc('div.revision-info li').first().text())
        eq_(d.title, doc('h1.title').text())
        eq_(pq(r.content_parsed)('div').text(),
            doc('#doc-content div').text())
        eq_('Created:\n              Jan 1, 2011, 12:00:00 AM',
            doc('.revision-info li')[1].text_content().strip())
        eq_('Reviewed:\n                Jan 2, 2011, 12:00:00 AM',
            doc('.revision-info li')[5].text_content().strip())
        # is reviewed?
        eq_('Yes', doc('.revision-info li').eq(4).find('span').text())
        # is current revision?
        eq_('Yes', doc('.revision-info li').eq(8).find('span').text())

    @mock.patch.object(ReadyRevisionEvent, 'fire')
    def test_mark_as_ready_POST(self, fire):
        """HTTP POST to mark a revision as ready for l10n."""
        u = UserFactory()
        add_permission(u, Revision, 'mark_ready_for_l10n')
        self.client.login(username=u.username, password='testpass')

        r = ApprovedRevisionFactory(
            is_ready_for_localization=False,
            significance=MEDIUM_SIGNIFICANCE)

        url = reverse('wiki.mark_ready_for_l10n_revision',
                      args=[r.document.slug, r.id])
        response = self.client.post(url, data={},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        eq_(200, response.status_code)

        r2 = Revision.objects.get(pk=r.pk)

        assert fire.called
        assert r2.is_ready_for_localization
        assert r2.readied_for_localization
        eq_(r2.readied_for_localization_by, u)
        eq_(r2.document.latest_localizable_revision, r2)

    @mock.patch.object(ReadyRevisionEvent, 'fire')
    def test_mark_as_ready_GET(self, fire):
        """HTTP GET to mark a revision as ready for l10n must fail."""
        r = ApprovedRevisionFactory(is_ready_for_localization=False)

        u = UserFactory()
        add_permission(u, Revision, 'mark_ready_for_l10n')
        self.client.login(username=u.username, password='testpass')

        url = reverse('wiki.mark_ready_for_l10n_revision',
                      args=[r.document.slug, r.id])
        response = self.client.get(url, data={},
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        eq_(405, response.status_code)

        r2 = Revision.objects.get(pk=r.pk)

        assert not fire.called
        assert not r2.is_ready_for_localization

    @mock.patch.object(ReadyRevisionEvent, 'fire')
    def test_mark_as_ready_no_perm(self, fire):
        """Mark a revision as ready for l10n without perm must fail."""

        r = ApprovedRevisionFactory()

        u = UserFactory()
        self.client.login(username=u.username, password='testpass')

        url = reverse('wiki.mark_ready_for_l10n_revision',
                      args=[r.document.slug, r.id])
        response = self.client.post(url, data={},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        eq_(403, response.status_code)

        r2 = Revision.objects.get(pk=r.pk)

        assert not fire.called
        assert not r2.is_ready_for_localization

    @mock.patch.object(ReadyRevisionEvent, 'fire')
    def test_mark_as_ready_no_login(self, fire):
        """Mark a revision as ready for l10n without login must fail."""

        r = ApprovedRevisionFactory(is_ready_for_localization=False)

        url = reverse('wiki.mark_ready_for_l10n_revision',
                      args=[r.document.slug, r.id])
        response = self.client.post(url, data={},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        eq_(403, response.status_code)

        r2 = Revision.objects.get(pk=r.pk)

        assert not fire.called
        assert not r2.is_ready_for_localization

    @mock.patch.object(ReadyRevisionEvent, 'fire')
    def test_mark_as_ready_no_approval(self, fire):
        """Mark an unapproved revision as ready for l10n must fail."""

        r = RevisionFactory(is_approved=False, is_ready_for_localization=False)

        u = UserFactory()
        add_permission(u, Revision, 'mark_ready_for_l10n')
        self.client.login(username=u.username, password='testpass')

        url = reverse('wiki.mark_ready_for_l10n_revision',
                      args=[r.document.slug, r.id])
        response = self.client.post(url, data={},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        eq_(400, response.status_code)

        r2 = Revision.objects.get(pk=r.pk)

        assert not fire.called
        assert not r2.is_ready_for_localization


class NewDocumentTests(TestCaseBase):
    """Tests for the New Document template"""

    def setUp(self):
        super(NewDocumentTests, self).setUp()

        u = UserFactory()
        self.client.login(username=u.username, password='testpass')

    def test_new_document_GET_with_perm(self):
        """HTTP GET to new document URL renders the form."""
        self.client.login(username='admin', password='testpass')
        response = self.client.get(reverse('wiki.new_document'))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(1, len(doc('#document-form input[name="title"]')))

    def test_new_document_form_defaults(self):
        """Verify that new document form defaults are correct."""
        self.client.login(username='admin', password='testpass')
        response = self.client.get(reverse('wiki.new_document'))
        doc = pq(response.content)
        # TODO: Do we want to re-implement the initial product
        # checked? Maybe add a column to the table and use that to
        # figure out which are initial?
        # eq_(1, len(doc('input[name="products"][checked=checked]')))
        eq_(None, doc('input[name="tags"]').attr('required'))
        eq_('checked', doc('input#id_allow_discussion').attr('checked'))
        eq_(None, doc('input#id_allow_discussion').attr('required'))

    @mock.patch.object(ReviewableRevisionInLocaleEvent, 'fire')
    def test_new_document_POST(self, ready_fire):
        """HTTP POST to new document URL creates the document."""
        self.client.login(username='admin', password='testpass')
        data = new_document_data()
        response = self.client.post(reverse('wiki.new_document'), data,
                                    follow=True)
        d = Document.objects.get(title=data['title'])
        eq_([('/en-US/kb/%s/history' % d.slug, 302)],
            response.redirect_chain)
        eq_(settings.WIKI_DEFAULT_LANGUAGE, d.locale)
        eq_(data['category'], d.category)
        r = d.revisions.all()[0]
        eq_(data['keywords'], r.keywords)
        eq_(data['summary'], r.summary)
        eq_(data['content'], r.content)
        assert ready_fire.called

    @mock.patch.object(ReviewableRevisionInLocaleEvent, 'fire')
    @mock.patch.object(Site.objects, 'get_current')
    def test_new_document_other_locale(self, get_current, ready_fire):
        """Make sure we can create a document in a non-default locale."""
        get_current.return_value.domain = 'testserver'

        self.client.login(username='admin', password='testpass')
        data = new_document_data()
        doc_locale = 'es'
        self.client.post(reverse('wiki.new_document', locale=doc_locale),
                         data, follow=True)
        d = Document.objects.get(title=data['title'])
        eq_(doc_locale, d.locale)
        assert ready_fire.called

    def test_new_document_POST_empty_title(self):
        """Trigger required field validation for title."""
        self.client.login(username='admin', password='testpass')
        data = new_document_data()
        data['title'] = ''
        response = self.client.post(reverse('wiki.new_document'), data,
                                    follow=True)
        doc = pq(response.content)
        ul = doc('#document-form > ul.errorlist')
        eq_(1, len(ul))
        eq_('Please provide a title.', ul('li').text())

    def test_new_document_POST_empty_content(self):
        """Trigger required field validation for content."""
        self.client.login(username='admin', password='testpass')
        data = new_document_data()
        data['content'] = ''
        response = self.client.post(reverse('wiki.new_document'), data,
                                    follow=True)
        doc = pq(response.content)
        ul = doc('#document-form > ul.errorlist')
        eq_(1, len(ul))
        eq_('Please provide content.', ul('li').text())

    def test_new_document_POST_invalid_category(self):
        """Try to create a new document with an invalid category value."""
        self.client.login(username='admin', password='testpass')
        data = new_document_data()
        data['category'] = 963
        response = self.client.post(reverse('wiki.new_document'), data,
                                    follow=True)
        doc = pq(response.content)
        ul = doc('#document-form > ul.errorlist')
        eq_(1, len(ul))
        assert ('Select a valid choice. 963 is not one of the available '
                'choices.' in ul('li').text())

    def test_new_document_missing_category(self):
        """Test the DocumentForm's category validation.

        Submit the form without a category set, and it should complain, even
        though it's not a strictly required field (because it cannot be set for
        translations).

        """
        self.client.login(username='admin', password='testpass')
        data = new_document_data()
        del data['category']
        response = self.client.post(reverse('wiki.new_document'), data,
                                    follow=True)
        self.assertContains(response, 'Please choose a category.')

    def test_new_document_POST_invalid_product(self):
        """Try to create a new document with an invalid product."""
        self.client.login(username='admin', password='testpass')
        data = new_document_data()
        data['products'] = ['l337']
        response = self.client.post(reverse('wiki.new_document'), data,
                                    follow=True)
        doc = pq(response.content)
        ul = doc('#document-form > ul.errorlist')
        eq_(1, len(ul))
        eq_('Select a valid choice. l337 is not one of the available choices. '
            'Please select at least one product.',
            ul('li').text())

    def test_slug_collision_validation(self):
        """Trying to create document with existing locale/slug should
        show validation error."""
        d = _create_document()
        self.client.login(username='admin', password='testpass')
        data = new_document_data()
        data['slug'] = d.slug
        response = self.client.post(reverse('wiki.new_document'), data)
        eq_(200, response.status_code)
        doc = pq(response.content)
        ul = doc('#document-form > ul.errorlist')
        eq_(1, len(ul))
        eq_('Document with this Slug and Locale already exists.',
            ul('li').text())

    def test_title_collision_validation(self):
        """Trying to create document with existing locale/slug should
        show validation error."""
        d = _create_document()
        self.client.login(username='admin', password='testpass')
        data = new_document_data()
        data['title'] = d.title
        response = self.client.post(reverse('wiki.new_document'), data)
        eq_(200, response.status_code)
        doc = pq(response.content)
        ul = doc('#document-form > ul.errorlist')
        eq_(1, len(ul))
        eq_('Document with this Title and Locale already exists.',
            ul('li').text())

    @mock.patch.object(Site.objects, 'get_current')
    def test_slug_3_chars(self, get_current):
        """Make sure we can create a slug with only 3 characters."""
        get_current.return_value.domain = 'testserver'
        self.client.login(username='admin', password='testpass')
        data = new_document_data()
        data['slug'] = 'ask'
        response = self.client.post(reverse('wiki.new_document'), data)
        eq_(302, response.status_code)
        eq_('ask', Document.objects.order_by('-id')[0].slug)


class NewRevisionTests(TestCaseBase):
    """Tests for the New Revision template"""

    def setUp(self):
        super(NewRevisionTests, self).setUp()
        rev = ApprovedRevisionFactory(document__topics=[])
        self.d = rev.document

        self.user = UserFactory()
        self.client.login(username=self.user.username, password='testpass')

    def test_new_revision_GET_logged_out(self):
        """Creating a revision without being logged in redirects to login page.
        """
        self.client.logout()
        response = self.client.get(reverse('wiki.edit_document',
                                           args=[self.d.slug]))
        eq_(302, response.status_code)

    def test_new_revision_GET_with_perm(self):
        """HTTP GET to new revision URL renders the form."""
        response = self.client.get(reverse('wiki.edit_document',
                                           args=[self.d.slug]))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(1, len(doc('#revision-form textarea[name="content"]')))
        comment = doc('#id_comment')[0]
        assert 'value' not in comment.attrib
        eq_('255', comment.attrib['maxlength'])

    def test_new_revision_GET_based_on(self):
        """HTTP GET to new revision URL based on another revision.

        This case should render the form with the fields pre-populated
        with the based-on revision info.

        """
        r = Revision(document=self.d, keywords='ky1, kw2',
                     summary='the summary',
                     content='<div>The content here</div>',
                     creator_id=UserFactory().id)
        r.save()

        add_permission(self.user, Revision, 'edit_keywords')
        response = self.client.get(reverse('wiki.new_revision_based_on',
                                           args=[self.d.slug, r.id]))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(doc('#id_keywords')[0].value, r.keywords)
        eq_(doc('#id_summary')[0].value.strip(), r.summary)
        eq_(doc('#id_content')[0].value.strip(), r.content)

    @mock.patch.object(Site.objects, 'get_current')
    @mock.patch.object(settings._wrapped, 'TIDINGS_CONFIRM_ANONYMOUS_WATCHES',
                       False)
    def test_new_revision_POST_document_with_current(self, get_current):
        """HTTP POST to new revision URL creates the revision on a document.

        The document in this case already has a current_revision, therefore
        the document document fields are not editable.

        Also assert that the edited and reviewable notifications go out.

        """
        get_current.return_value.domain = 'testserver'

        # Sign up for notifications:
        edit_watch = EditDocumentEvent.notify('sam@example.com', self.d)
        edit_watch.activate().save()

        review_user = UserFactory(email='joe@example.com')
        add_permission(review_user, Revision, 'review_revision')
        reviewable_watch = ReviewableRevisionInLocaleEvent.notify(review_user, locale='en-US')
        reviewable_watch.activate().save()

        reviewable_watch_no_permission = ReviewableRevisionInLocaleEvent.notify(
            UserFactory(), locale='en-US')
        reviewable_watch_no_permission.activate().save()

        # Edit a document:
        response = self.client.post(
            reverse('wiki.edit_document', args=[self.d.slug]),
            {'summary': 'A brief summary', 'content': 'The article content',
             'keywords': 'keyword1 keyword2',
             'comment': 'Fixing all the typos!!!!!11!!!one!!!!',
             'based_on': self.d.current_revision.id, 'form': 'rev'})
        eq_(302, response.status_code)
        eq_(2, self.d.revisions.count())
        new_rev = self.d.revisions.order_by('-id')[0]
        eq_(self.d.current_revision, new_rev.based_on)

        if new_rev.based_on is not None:
            diff = get_diff_for(new_rev.based_on.document, new_rev.based_on, new_rev)
        else:
            diff = ''  # No based_on, so diff wouldn't make sense.

        # Assert notifications fired and have the expected content:
        eq_(2, len(mail.outbox))
        attrs_eq(
            mail.outbox[0],
            subject=u'%s is ready for review (%s)' % (
                self.d.title, new_rev.creator),
            body=READY_FOR_REVIEW_EMAIL_CONTENT % {
                'user': self.user.profile.name,
                'title': self.d.title,
                'slug': self.d.slug,
                'new_id': new_rev.id,
                'summary': new_rev.summary,
                'diff': diff,
                'watcher': reviewable_watch.pk,
                'secret': reviewable_watch.secret
            },
            to=['joe@example.com'])
        attrs_eq(
            mail.outbox[1],
            subject=u'%s was edited by %s' % (
                self.d.title, new_rev.creator),
            body=DOCUMENT_EDITED_EMAIL_CONTENT % {
                'user': self.user.profile.name,
                'title': self.d.title,
                'slug': self.d.slug,
                'watcher': edit_watch.pk,
                'secret': edit_watch.secret,
                'summary': new_rev.summary,
                'diff': diff,
            },
            to=['sam@example.com'])

    @mock.patch.object(ReviewableRevisionInLocaleEvent, 'fire')
    @mock.patch.object(EditDocumentEvent, 'fire')
    @mock.patch.object(Site.objects, 'get_current')
    def test_new_revision_POST_document_without_current(
            self, get_current, edited_fire, ready_fire):
        """HTTP POST to new revision URL creates the revision on a document.

        The document in this case doesn't have a current_revision, therefore
        the document fields are open for editing.

        """
        get_current.return_value.domain = 'testserver'

        self.d.current_revision = None
        self.d.save()
        data = new_document_data()
        data['form'] = 'rev'
        response = self.client.post(reverse('wiki.edit_document',
                                    args=[self.d.slug]), data)
        eq_(302, response.status_code)
        eq_(2, self.d.revisions.count())

        new_rev = self.d.revisions.order_by('-id')[0]
        # There are no approved revisions, so it's based_on nothing:
        eq_(None, new_rev.based_on)
        assert edited_fire.called
        assert ready_fire.called

    def test_edit_document_POST_removes_old_tags(self):
        """Changing the tags on a document removes the old tags from
        that document."""
        self.d.current_revision = None
        self.d.save()
        topics = [TopicFactory(), TopicFactory(), TopicFactory()]
        self.d.topics.add(*topics)
        eq_(self.d.topics.count(), len(topics))
        new_topics = [topics[0], TopicFactory()]
        data = new_document_data(t.id for t in new_topics)
        data['form'] = 'doc'
        self.client.post(reverse('wiki.edit_document', args=[self.d.slug]), data)
        topic_ids = self.d.topics.values_list('id', flat=True)
        eq_(2, len(topic_ids))
        assert new_topics[0].id in topic_ids
        assert new_topics[1].id in topic_ids

    @mock.patch.object(Site.objects, 'get_current')
    def test_new_form_maintains_based_on_rev(self, get_current):
        """Revision.based_on should be the rev that was current when the Edit
        button was clicked, even if other revisions happen while the user is
        editing."""
        get_current.return_value.domain = 'testserver'
        _test_form_maintains_based_on_rev(
            self.client, self.d, 'wiki.edit_document',
            {'summary': 'Windy', 'content': 'gerbils', 'form': 'rev'},
            locale=None)

    def _test_new_revision_warning(self, doc):
        """When editing based on current revision, we should show a warning if
        there are newer unapproved revisions."""
        # Create a new revision that is at least 1 second newer than current
        created = datetime.now() + timedelta(seconds=1)
        r = RevisionFactory(document=doc, created=created)

        # Verify there is a warning box
        response = self.client.get(
            reverse('wiki.edit_document', locale=doc.locale, args=[doc.slug]))
        assert len(pq(response.content)('.user-messages .warning'))

        # Verify there is no warning box if editing the latest unreviewed
        response = self.client.get(
            reverse('wiki.new_revision_based_on', locale=doc.locale,
                    args=[doc.slug, r.id]))
        assert not len(pq(response.content)('div.warning-box'))

        # Create a newer unreviewed revision and now warning shows
        created = created + timedelta(seconds=1)
        RevisionFactory(document=doc, created=created)
        response = self.client.get(
            reverse('wiki.new_revision_based_on', locale=doc.locale,
                    args=[doc.slug, r.id]))
        assert len(pq(response.content)('.user-messages .warning'))

    def test_new_revision_warning(self,):
        """When editing based on current revision, we should show a warning if
        there are newer unapproved revisions."""
        self._test_new_revision_warning(self.d)

    def test_new_revision_warning_l10n(self,):
        """When translating based on current revision, we should show a
        warning if there are newer unapproved revisions."""
        # Make the en-US revision ready for l10n first
        r = self.d.current_revision
        r.is_ready_for_localization = True
        r.save()

        # Create the localization.
        l10n = DocumentFactory(parent=self.d, locale='es')
        r = RevisionFactory(document=l10n, is_approved=True)
        l10n.current_revision = r
        l10n.save()
        self._test_new_revision_warning(l10n)

    def test_keywords_require_permission(self):
        """Test keywords require permission."""
        doc = self.d
        old_rev = doc.current_revision

        u = UserFactory()
        self.client.login(username=u.username, password='testpass')

        # Edit the document:
        response = self.client.post(
            reverse('wiki.edit_document', args=[doc.slug]),
            {'summary': 'A brief summary', 'content': 'The article content',
             'keywords': 'keyword1 keyword2',
             'based_on': old_rev.id, 'form': 'rev'})
        eq_(302, response.status_code)

        # Keywords should remain the same as in old revision.
        new_rev = Revision.objects.filter(document=doc).order_by('-id')[0]
        eq_(old_rev.keywords, new_rev.keywords)

        # Grant the permission.
        add_permission(u, Revision, 'edit_keywords')

        # Edit the document:
        response = self.client.post(
            reverse('wiki.edit_document', args=[doc.slug]),
            {'summary': 'A brief summary', 'content': 'The article content',
             'keywords': 'keyword1 keyword2',
             'based_on': old_rev.id, 'form': 'rev'})
        eq_(302, response.status_code)

        # Keywords should be updated now
        new_rev = Revision.objects.filter(document=doc).order_by('-id')[0]
        eq_('keyword1 keyword2', new_rev.keywords)

    def test_draft_button(self):
        rev = ApprovedRevisionFactory(is_ready_for_localization=True,
                                      document__is_localizable=True)
        doc = rev.document
        # Check the Translation page has Save Draft Button
        trans_url = reverse('wiki.translate', locale='bn', args=[doc.slug])
        trans_resp = self.client.get(trans_url)
        eq_(200, trans_resp.status_code)
        trans_content = pq(trans_resp.content)
        eq_(0, len(trans_content('.user-messages li')))
        eq_(2, len(trans_content('.submit .btn-draft')))

    def test_restore_draft_revision(self):
        draft = DraftRevisionFactory(creator=self.user)
        trans_url = reverse('wiki.translate', locale=draft.locale, args=[draft.document.slug])
        trans_resp = self.client.get(trans_url)
        trans_content = pq(trans_resp.content)
        # Check user message is shown there
        eq_(1, len(trans_content('.user-messages li')))
        # Check there are two buttons for restore and discard
        eq_(2, len(trans_content('.user-messages .info form .btn')))
        # Restore with the draft data
        draft_request = {'restore': 'Restore'}
        trans_resp = self.client.get(trans_url, draft_request)
        trans_content = pq(trans_resp.content)
        # No user message is shown there
        eq_(0, len(trans_content('.user-messages li')))
        # Check title, slug, keywords, content etc are restored
        eq_(draft.title, trans_content('#id_title').val())
        eq_(draft.slug, trans_content('#id_slug').val())
        eq_(draft.keywords, trans_content('#id_keywords').val())
        eq_(draft.summary, trans_content('#id_summary').text())
        eq_(draft.content, trans_content('#id_content').text())
        eq_(draft.based_on.id, int(trans_content('#id_based_on').val()))

    @nottest
    def test_restore_draft_revision_with_older_based_on(self):
        """Test restoring a draft which is based on an old based on"""
        draft = DraftRevisionFactory(creator=self.user)
        rev1 = draft.based_on
        doc = draft.document
        # Create another revision in the parent doc
        rev2 = ApprovedRevisionFactory(document=doc, is_ready_for_localization=True)
        # Check this rev2 revision content is the translation page
        trans_url = reverse('wiki.translate', locale=draft.locale, args=[doc.slug])
        trans_resp = self.client.get(trans_url)
        trans_content = pq(trans_resp.content)
        eq_(rev2.content, trans_content('.content textarea').text())
        # Now Restore the draft which is based on the past revision
        draft_request = {'restore': 'Restore'}
        cache.clear()
        trans_resp = self.client.get(trans_url, draft_request)
        trans_content = pq(trans_resp.content)
        eq_(rev1.content, trans_content('.content textarea').text())
        # As the old based on draft is restored, the latest revision content should not be there
        assert rev2.content != trans_content('.content textarea').text()

    def test_draft_restoring_works_while_updating_translation(self):
        trans_rev = TranslatedRevisionFactory()
        trans = trans_rev.document
        doc = trans.parent
        user = trans_rev.creator
        doc.allows(user, 'create_revision')
        self.client.login(username=user.username, password='testpass')
        # Create a draft revision
        # As the user will not see the title and slug, it should be blank
        draft = DraftRevisionFactory(
            document=doc, creator=user, locale=trans.locale,
            based_on=trans_rev.based_on, title='', slug='')
        # Now Restore the draft
        draft_request = {'restore': 'Restore'}
        trans_url = reverse('wiki.translate', locale=trans.locale, args=[doc.slug])
        trans_resp = self.client.get(trans_url, draft_request)
        trans_content = pq(trans_resp.content)
        # Check the data is restored
        eq_(draft.keywords, trans_content('#id_keywords').val())
        eq_(draft.summary, trans_content('#id_summary').text())
        eq_(draft.content, trans_content('#id_content').text())
        eq_(draft.based_on.id, int(trans_content('#id_based_on').val()))

    def test_warning_showing_while_new_revision(self):
        """Check warning is being showed if another updated revision"""
        # Create a translation
        rev = TranslatedRevisionFactory()
        trans = rev.document
        doc = trans.parent
        # Create a draft revision
        draft = DraftRevisionFactory(
            creator=self.user, locale=trans.locale, document=doc, based_on=rev.based_on)
        # Create another revision in the english document
        rev2 = ApprovedRevisionFactory(document=doc, is_ready_for_localization=True)
        # Create a revision in translated article which is based on the later revision
        RevisionFactory(based_on=rev2, document=trans)
        # Now restore the draft
        draft_request = {'restore': 'Restore'}
        trans_url = reverse('wiki.translate', locale=draft.locale, args=[doc.slug])
        trans_resp = self.client.get(trans_url, draft_request)
        trans_content = pq(trans_resp.content)
        # Check there is a warning message
        eq_(1, len(trans_content('.user-messages li.draft-warning')))


class HistoryTests(TestCaseBase):
    """Test the history listing of a document."""

    def setUp(self):
        super(HistoryTests, self).setUp()
        self.client.login(username='admin', password='testpass')

    def test_history_noindex(self):
        """Document history should have a noindex meta tag."""
        # Create a document and verify there is no robots:noindex
        r = ApprovedRevisionFactory(content='Some text.')
        response = get(self.client, 'wiki.document_revisions',
                       args=[r.document.slug])
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_('noindex, nofollow', doc('meta[name=robots]')[0].attrib['content'])

    def test_history_category_appears(self):
        """Document history should have a category on page"""
        category = CATEGORIES[1]
        r = ApprovedRevisionFactory(content='Some text.', document__category=category[0])
        response = get(self.client, 'wiki.document_revisions', args=[r.document.slug])
        eq_(200, response.status_code)
        self.assertContains(response, category[1])

    def test_translation_history_with_english_slug(self):
        """Request in en-US slug but translated locale should redirect to translation history"""
        doc = DocumentFactory(locale=settings.WIKI_DEFAULT_LANGUAGE)
        trans = DocumentFactory(parent=doc, locale='bn', slug='bn_trans_slug')
        ApprovedRevisionFactory(document=trans)
        # Get the page with the en-US slug
        url = reverse('wiki.document_revisions', args=[doc.slug], locale=trans.locale)
        response = self.client.get(url)
        # Check redirection happens
        eq_(302, response.status_code)
        url = '/bn/kb/bn_trans_slug/history'
        eq_(url, response['Location'])

    def test_translation_history_with_english_slug_while_no_trans(self):
        """Request in en-US slug but untranslated locale should raise 404"""
        doc = DocumentFactory(locale=settings.WIKI_DEFAULT_LANGUAGE)
        url = reverse('wiki.document_revisions', args=[doc.slug], locale='bn')
        response = self.client.get(url)
        # Check raises 404 error
        eq_(404, response.status_code)


class DocumentEditTests(TestCaseBase):
    """Test the editing of document level fields."""

    def setUp(self):
        super(DocumentEditTests, self).setUp()
        self.d = _create_document()

        u = UserFactory()
        add_permission(u, Document, 'change_document')
        self.client.login(username=u.username, password='testpass')

    def test_can_save_document_with_translations(self):
        """Make sure we can save a document with translations."""
        # Create a translation
        _create_document(title='Document Prueba', parent=self.d,
                         locale='es')
        # Make sure is_localizable hidden field is rendered
        response = get(self.client, 'wiki.edit_document', args=[self.d.slug])
        eq_(200, response.status_code)
        doc = pq(response.content)
        is_localizable = doc('input[name="is_localizable"]')
        eq_(1, len(is_localizable))
        eq_('True', is_localizable[0].attrib['value'])
        # And make sure we can update the document
        data = new_document_data()
        new_title = 'A brand new title'
        data.update(title=new_title)
        data.update(form='doc')
        data.update(is_localizable='True')
        response = post(self.client, 'wiki.edit_document', data,
                        args=[self.d.slug])
        eq_(200, response.status_code)
        doc = Document.objects.get(pk=self.d.pk)
        eq_(new_title, doc.title)

    def test_change_slug_case(self):
        """Changing the case of some letters in the slug should work."""
        data = new_document_data()
        new_slug = 'Test-Document'
        data.update(slug=new_slug)
        data.update(form='doc')
        response = post(self.client, 'wiki.edit_document', data,
                        args=[self.d.slug])
        eq_(200, response.status_code)
        doc = Document.objects.get(pk=self.d.pk)
        eq_(new_slug, doc.slug)

    def test_change_title_case(self):
        """Changing the case of some letters in the title should work."""
        data = new_document_data()
        new_title = 'TeST DoCuMent'
        data.update(title=new_title)
        data.update(form='doc')
        response = post(self.client, 'wiki.edit_document', data,
                        args=[self.d.slug])
        eq_(200, response.status_code)
        doc = Document.objects.get(pk=self.d.pk)
        eq_(new_title, doc.title)

    def test_archive_permission_off(self):
        """Shouldn't be able to change is_archive bit without permission."""
        u = UserFactory()
        add_permission(u, Document, 'change_document')
        self.client.login(username=u.username, password='testpass')
        data = new_document_data()
        # Try to set is_archived, even though we shouldn't have permission to:
        data.update(form='doc', is_archived='on')
        response = post(self.client, 'wiki.edit_document', data,
                        args=[self.d.slug])
        eq_(200, response.status_code)
        doc = Document.objects.get(pk=self.d.pk)
        assert not doc.is_archived

    # TODO: Factor with test_archive_permission_off.
    def test_archive_permission_on(self):
        """Shouldn't be able to change is_archive bit without permission."""
        u = UserFactory()
        add_permission(u, Document, 'change_document')
        add_permission(u, Document, 'archive_document')
        self.client.login(username=u.username, password='testpass')
        data = new_document_data()
        data.update(form='doc', is_archived='on')
        response = post(self.client, 'wiki.edit_document', data,
                        args=[self.d.slug])
        eq_(200, response.status_code)
        doc = Document.objects.get(pk=self.d.pk)
        assert doc.is_archived

    @mock.patch.object(EditDocumentEvent, 'notify')
    def test_watch_article_from_edit_page(self, notify_on_edit):
        """Make sure we can watch the article when submitting an edit."""
        data = new_document_data()
        data['form'] = 'rev'
        data['notify-future-changes'] = 'Yes'
        response = post(self.client, 'wiki.edit_document',
                        data, args=[self.d.slug])
        eq_(200, response.status_code)
        assert notify_on_edit.called

    @mock.patch.object(EditDocumentEvent, 'notify')
    def test_not_watch_article_from_edit_page(self, notify_on_edit):
        """Make sure editing an article does not cause a watch."""
        data = new_document_data()
        data['form'] = 'rev'
        response = post(self.client, 'wiki.edit_document',
                        data, args=[self.d.slug])
        eq_(200, response.status_code)
        assert not notify_on_edit.called


class DocumentListTests(TestCaseBase):
    """Tests for the All and Category template"""

    def setUp(self):
        super(DocumentListTests, self).setUp()
        self.locale = settings.WIKI_DEFAULT_LANGUAGE
        self.doc = _create_document(locale=self.locale)
        _create_document(locale=self.locale, title='Another one')

        # Create a document in different locale to make sure it doesn't show
        _create_document(parent=self.doc, locale='es')

    def test_category_list(self):
        """Verify the category documents list view."""
        response = self.client.get(reverse('wiki.category',
                                   args=[self.doc.category]))
        doc = pq(response.content)
        cat = self.doc.category
        eq_(Document.objects.filter(category=cat, locale=self.locale).count(),
            len(doc('#document-list ul.documents li')))

    def test_all_list(self):
        """Verify the all documents list view."""
        response = self.client.get(reverse('wiki.all_documents'))
        doc = pq(response.content)
        eq_(Document.objects.filter(locale=self.locale).count(),
            len(doc('#document-list ul.documents li')))


class DocumentRevisionsTests(TestCaseBase):
    """Tests for the Document Revisions template"""

    def test_document_revisions_list(self):
        """Verify the document revisions list view."""
        creator = UserFactory()
        d = DocumentFactory()
        ApprovedRevisionFactory(document=d)
        RevisionFactory(
            summary="a tweak",
            content='lorem ipsum dolor',
            keywords='kw1 kw2',
            document=d,
            reviewed=None,
            creator=creator)
        r2 = RevisionFactory(
            summary="another tweak",
            content='lorem dimsum dolor',
            keywords='kw1 kw2',
            document=d,
            reviewed=None,
            creator=creator)
        response = self.client.get(reverse('wiki.document_revisions', args=[d.slug]))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(4, len(doc('#revision-list li')))
        # Verify there is no Review link
        eq_(0, len(doc('#revision-list div.status a')))
        eq_('Unreviewed', doc('#revision-list li:not(.header) div.status').first().text())

        # Log in as user with permission to review
        reviewer = UserFactory()
        add_permission(reviewer, Revision, 'review_revision')
        self.client.login(username=reviewer.username, password='testpass')
        response = self.client.get(reverse('wiki.document_revisions', args=[d.slug]))
        eq_(200, response.status_code)
        doc = pq(response.content)

        # Verify there are Review links now
        eq_(2, len(doc('#revision-list div.status a')))
        eq_('Review', doc('#revision-list li:not(.header) div.status').first().text())

        # Verify edit revision link
        eq_('/en-US/kb/{slug}/edit/{rev_id}'.format(slug=d.slug, rev_id=r2.id),
            doc('#revision-list div.edit a')[0].attrib['href'])

    def test_revisions_ready_for_l10n(self):
        """Verify that the ready for l10n icon is only present on en-US."""
        d = _create_document()
        user = UserFactory()
        r1 = RevisionFactory(
            summary="a tweak",
            content='lorem ipsum dolor',
            keywords='kw1 kw2',
            document=d,
            creator=user)

        d2 = _create_document(locale='es')
        RevisionFactory(
            summary="a tweak",
            content='lorem ipsum dolor',
            keywords='kw1 kw2',
            document=d2,
            creator=user)

        response = self.client.get(reverse('wiki.document_revisions',
                                   args=[r1.document.slug]))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(1, len(doc('#revision-list li.header div.l10n')))

        response = self.client.get(reverse('wiki.document_revisions',
                                   args=[d2.slug], locale='es'))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(0, len(doc('#revision-list div.l10n-head')))


class ReviewRevisionTests(TestCaseBase):
    """Tests for Review Revisions and Translations"""

    def setUp(self):
        super(ReviewRevisionTests, self).setUp()
        self.document = _create_document()
        user_ = UserFactory()
        self.revision = Revision(summary="lipsum",
                                 content='<div>Lorem {for mac}Ipsum{/for} '
                                         'Dolor</div>',
                                 keywords='kw1 kw2', document=self.document,
                                 creator=user_)
        self.revision.save()

        self.user = UserFactory()
        add_permission(self.user, Revision, 'review_revision')
        add_permission(self.user, Document, 'edit_needs_change')
        self.client.login(username=self.user.username, password='testpass')

    def test_fancy_renderer(self):
        """Make sure it renders the whizzy new wiki syntax."""
        # The right branch of the template renders only when there's no current
        # revision.
        self.document.current_revision = None
        self.document.save()

        response = get(self.client, 'wiki.review_revision',
                       args=[self.document.slug, self.revision.id])

        # Does the {for} syntax seem to have rendered?
        assert pq(response.content)('span[class=for]')

    @mock.patch.object(send_reviewed_notification, 'delay')
    @mock.patch.object(Site.objects, 'get_current')
    @mock.patch.object(settings._wrapped, 'TIDINGS_CONFIRM_ANONYMOUS_WATCHES',
                       False)
    def test_approve_revision(self, get_current, reviewed_delay):
        """Verify revision approval with proper notifications."""

        # TODO: This isn't a great unit test. The problem here is that
        # the unit test code duplicates the code it's testing. So if
        # the code is bad, it'll be bad in both places and that's not
        # particularly helpful. Probably better to change the test so
        # that it sets up the data correctly, then compares the output
        # with hard-coded expected output.

        get_current.return_value.domain = 'testserver'

        # Subscribe to approvals:
        watch = ApproveRevisionInLocaleEvent.notify('joe@example.com', locale='en-US')
        watch.activate().save()

        # Subscribe the approver to approvals so we can assert (by counting the
        # mails) that he didn't get notified.
        ApproveRevisionInLocaleEvent.notify(self.user, locale='en-US').activate().save()

        # Approve something:
        significance = SIGNIFICANCES[0][0]
        response = post(self.client, 'wiki.review_revision',
                        {'approve': 'Approve Revision',
                         'significance': significance,
                         'comment': 'something',
                         'needs_change': True,
                         'needs_change_comment': 'comment'},
                        args=[self.document.slug, self.revision.id])

        eq_(200, response.status_code)
        r = Revision.objects.get(pk=self.revision.id)
        eq_(significance, r.significance)
        assert r.reviewed
        assert r.is_approved
        assert r.document.needs_change
        assert not r.is_ready_for_localization
        eq_('comment', r.document.needs_change_comment)

        # Verify that revision creator is now in contributors
        assert r.creator in self.document.contributors.all()

        # The "reviewed" mail should be sent to the creator, and the "approved"
        # mail should be sent to any subscribers:
        reviewed_delay.assert_called_with(r, r.document, 'something')

        if r.based_on is not None:
            old_rev = r.document.current_Revision
        else:
            old_rev = r.document.revisions.filter(is_approved=True).order_by('-created')[1]

        diff = get_diff_for(r.document, old_rev, r)

        expected_body = (APPROVED_EMAIL_CONTENT % {
            'reviewer': r.reviewer.profile.name,
            'document_title': self.document.title,
            'document_slug': self.document.slug,
            'watcher': watch.pk,
            'secret': watch.secret,
            'summary': old_rev.summary,
            'diff': diff,
            'content': r.content})

        eq_(1, len(mail.outbox))
        attrs_eq(mail.outbox[0],
                 subject=(u'{0} ({1}) has a new approved revision ({2})'
                          .format(self.document.title, self.document.locale, self.user.username)),
                 body=expected_body,
                 to=['joe@example.com'])

    def test_approve_and_ready_for_l10n_revision(self):
        """Verify revision approval with ready for l10n."""
        add_permission(self.user, Revision, 'mark_ready_for_l10n')
        # Approve something:
        significance = SIGNIFICANCES[1][0]
        response = post(self.client, 'wiki.review_revision',
                        {'approve': 'Approve Revision',
                         'significance': significance,
                         'comment': 'something',
                         'needs_change': True,
                         'needs_change_comment': 'comment',
                         'is_ready_for_localization': True},
                        args=[self.document.slug, self.revision.id])

        eq_(200, response.status_code)
        r = Revision.objects.get(pk=self.revision.id)
        assert r.is_ready_for_localization
        eq_(r.reviewer, r.readied_for_localization_by)
        eq_(r.reviewed, r.readied_for_localization)

    @mock.patch.object(send_reviewed_notification, 'delay')
    @mock.patch.object(Site.objects, 'get_current')
    def test_reject_revision(self, get_current, delay):
        """Verify revision rejection."""
        get_current.return_value.domain = 'testserver'

        comment = 'no good'
        response = post(self.client, 'wiki.review_revision',
                        {'reject': 'Reject Revision',
                         'comment': comment},
                        args=[self.document.slug, self.revision.id])
        eq_(200, response.status_code)
        r = Revision.objects.get(pk=self.revision.pk)
        assert r.reviewed
        assert not r.is_approved
        delay.assert_called_with(r, r.document, comment)

        # Verify that revision creator is not in contributors
        assert r.creator not in r.document.contributors.all()

    @mock.patch.object(send_reviewed_notification, 'delay')
    @mock.patch.object(Site.objects, 'get_current')
    def test_reject_with_needs_change(self, get_current, delay):
        """Verify needs_change bit isn't changed when rejecting."""
        get_current.return_value.domain = 'testserver'

        comment = 'no good'

        d = self.document
        d.needs_change = True
        d.needs_change_comment = comment
        d.save()

        response = post(self.client, 'wiki.review_revision',
                        {'reject': 'Reject Revision',
                         'comment': comment}, args=[d.slug, self.revision.id])
        eq_(200, response.status_code)
        r = Revision.objects.get(pk=self.revision.pk)
        assert r.reviewed
        assert not r.is_approved
        d = Document.objects.get(pk=d.pk)
        assert d.needs_change
        eq_(comment, d.needs_change_comment)

    def test_review_without_permission(self):
        """Make sure unauthorized users can't review revisions."""
        u = UserFactory()
        self.client.login(username=u.username, password='testpass')
        response = post(self.client, 'wiki.review_revision',
                        {'reject': 'Reject Revision'},
                        args=[self.document.slug, self.revision.id])
        eq_(403, response.status_code)

    def test_review_as_l10n_leader(self):
        """Reviewing a revision as an l10n leader should work."""
        u = UserFactory()
        l10n = LocaleFactory(locale='en-US')
        l10n.leaders.add(u)
        self.client.login(username=u.username, password='testpass')
        response = post(self.client, 'wiki.review_revision',
                        {'reject': 'Reject Revision'},
                        args=[self.document.slug, self.revision.id])
        eq_(200, response.status_code)

    def test_review_as_l10n_reviewer(self):
        """Reviewing a revision as an l10n reviewer should work."""
        u = UserFactory()
        l10n = LocaleFactory(locale='en-US')
        l10n.reviewers.add(u)
        self.client.login(username=u.username, password='testpass')
        response = post(self.client, 'wiki.review_revision',
                        {'reject': 'Reject Revision'},
                        args=[self.document.slug, self.revision.id])
        eq_(200, response.status_code)

    def test_review_logged_out(self):
        """Make sure logged out users can't review revisions."""
        self.client.logout()
        response = post(self.client, 'wiki.review_revision',
                        {'reject': 'Reject Revision'},
                        args=[self.document.slug, self.revision.id])
        redirect = response.redirect_chain[0]
        eq_(302, redirect[1])
        eq_('/{0}{1}?next=/en-US/kb/test-document/review/{2}'
            .format(settings.LANGUAGE_CODE, settings.LOGIN_URL,
                    str(self.revision.id)),
            redirect[0])

    @mock.patch.object(Site.objects, 'get_current')
    def test_review_translation(self, get_current):
        """Make sure it works for localizations as well."""
        get_current.return_value.domain = 'testserver'
        doc = self.document
        user = UserFactory()

        # Create the translated document based on the current revision
        doc_es = _create_document(locale='es', parent=doc)
        rev_es1 = doc_es.current_revision
        rev_es1.based_on = doc.current_revision
        rev_es1.save()

        # Add a new revision to the parent and set it as the current one
        rev = ApprovedRevisionFactory(
            summary="another tweak",
            content='lorem dimsum dolor',
            significance=SIGNIFICANCES[0][0],
            keywords='kw1 kw2',
            document=doc,
            creator=user,
            based_on=self.revision)
        rev.save()

        # Create a new translation based on the new current revision
        rev_es2 = RevisionFactory(
            summary="lipsum",
            content='<div>Lorem {for mac}Ipsum{/for} Dolor</div>',
            keywords='kw1 kw2', document=doc_es,
            creator=user,
            based_on=doc.current_revision)

        # Whew, now render the review page
        self.client.login(username='admin', password='testpass')
        url = reverse('wiki.review_revision', locale='es',
                      args=[doc_es.slug, rev_es2.id])
        response = self.client.get(url, follow=True)
        eq_(200, response.status_code)
        doc = pq(response.content)
        diff_heading = doc('div.revision-diff h3').text()
        assert str(rev_es1.based_on.id) in diff_heading
        assert str(rev.id) in diff_heading

        # And finally, approve the translation
        response = self.client.post(url, {'approve': 'Approve Translation',
                                          'comment': 'something'},
                                    follow=True)
        eq_(200, response.status_code)
        d = Document.objects.get(pk=doc_es.id)
        r = Revision.objects.get(pk=rev_es2.id)
        eq_(d.current_revision, r)
        assert r.reviewed
        assert r.is_approved

    def test_review_translation_of_unapproved_parent(self):
        """Translate unapproved English document a 2nd time.

        Reviewing a revision of a translation when the English document
        does not have a current revision should fall back to the latest
        English revision.

        """
        en_revision = RevisionFactory(is_approved=False)

        # Create the translated document based on the current revision
        es_document = DocumentFactory(locale='es', parent=en_revision.document)
        # Create first revision
        RevisionFactory(document=es_document, is_approved=True)
        es_revision = RevisionFactory(
            document=es_document,
            reviewed=None,
            is_approved=False,
            reviewer=None)

        # Now render the review page
        self.client.login(username='admin', password='testpass')
        url = reverse('wiki.review_revision',
                      args=[es_document.slug, es_revision.id])
        response = self.client.get(url, follow=True)
        eq_(200, response.status_code)
        doc = pq(response.content)
        # There's no 'Recent English Changes' <details> section
        eq_(3, len(doc('details')))
        eq_('Approved English version:',
            doc('#content-fields h3').eq(0).text())
        rev_message = doc('#content-fields p').eq(0).text()
        assert 'by %s' % en_revision.creator.username in rev_message

    def test_review_translation_of_rejected_parent(self):
        """Translate rejected English document a 2nd time.

        Reviewing a revision of a translation when the English document
        has only rejected revisions should show a message.

        """
        user = UserFactory()
        en_revision = RevisionFactory(is_approved=False, reviewer=user, reviewed=datetime.now())

        # Create the translated document based on the current revision
        es_document = DocumentFactory(locale='es', parent=en_revision.document)
        # Create first revision
        RevisionFactory(document=es_document, is_approved=True)
        es_revision = RevisionFactory(
            document=es_document,
            reviewed=None,
            is_approved=False,
            reviewer=None)

        # Now render the review page
        self.client.login(username='admin', password='testpass')
        url = reverse('wiki.review_revision',
                      args=[es_document.slug, es_revision.id])
        response = self.client.get(url, follow=True)
        eq_(200, response.status_code)
        doc = pq(response.content)
        # There's no 'Recent English Changes' <details> section
        eq_(3, len(doc('details')))
        eq_('The English version has no approved content to show.',
            doc('details .warning-box').text())

    def test_default_significance(self):
        """Verify the default significance is MEDIUM_SIGNIFICANCE."""
        response = get(self.client, 'wiki.review_revision',
                       args=[self.document.slug, self.revision.id])
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(MEDIUM_SIGNIFICANCE,
            int(doc('input[name=significance][checked]')[0].attrib['value']))

    def test_self_approve_without_revision_contributors(self):
        """Verify review page when self approving and no other contributors.

        Textarea for approve/defer message should not be included in the page.
        """
        rev = RevisionFactory(is_approved=False)
        u = rev.creator
        add_permission(u, Revision, 'review_revision')
        self.client.login(username=u.username, password='testpass')

        response = get(self.client, 'wiki.review_revision',
                       args=[rev.document.slug, rev.id])
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(0, len(doc('textarea[name="comment"]')))

    def test_self_approve_with_revision_contributors(self):
        """Verify review page when self approving and other contributors.

        Textarea for approve/defer message should be included in the page.
        """
        rev1 = RevisionFactory(is_approved=False)
        rev2 = RevisionFactory(is_approved=False, document=rev1.document)
        u = rev2.creator
        add_permission(u, Revision, 'review_revision')
        self.client.login(username=u.username, password='testpass')

        response = get(self.client, 'wiki.review_revision',
                       args=[rev2.document.slug, rev2.id])
        eq_(200, response.status_code)

        doc = pq(response.content)
        eq_(2, len(doc('textarea[name="comment"]')))
        label = doc('div.message label').text()
        assert rev1.creator.username in label
        assert u.username not in label

    def test_review_past_revision(self):
        """Verify that its not possible to review a revision older than the current revision"""
        r1 = RevisionFactory(is_approved=False)
        r2 = RevisionFactory(document=r1.document, is_approved=True)
        r1.document.current_revision = r2
        r1.document.save()
        u = UserFactory()
        add_permission(u, Revision, 'review_revision')
        self.client.login(username=u.username, password='testpass')

        # Get the data of the document
        response = get(self.client, 'wiki.review_revision',
                       args=[r1.document.slug, r1.id])
        eq_(200, response.status_code)
        message1 = 'A newer revision has already been reviewed.'
        message2 = ('This revision is outdated, but there is a new revision available. '
                    'Please review the latest revision.')

        # While there is no unapproved revision after the current revision.
        doc = pq(response.content)
        doc_content = doc('#review-revision').text()
        assert message1 in doc_content
        assert message2 not in doc_content
        # While there is Unapproved revision after the Current Revision
        RevisionFactory(document=r1.document, is_approved=False)
        response = get(self.client, 'wiki.review_revision',
                       args=[r1.document.slug, r1.id])
        doc = pq(response.content)
        doc_content = doc('#review-revision').text()
        assert message1 not in doc_content
        assert message2 in doc_content

    def test_revision_comments(self):
        """Verify that reviewing revision comment and past revision comments are showing"""
        d = self.document
        # Create 7 Revisions in the Document
        revs = [RevisionFactory(document=d, is_approved=False, comment="test-{0}".format(i))
                for i in range(7)]
        # Create a user with Review permission and login with the user
        u = UserFactory()
        add_permission(u, Revision, 'review_revision')
        self.client.login(username=u.username, password='testpass')

        # Review the latest revision and Get the data of the document
        response = get(self.client, 'wiki.review_revision',
                       args=[d.slug, revs[6].id])
        eq_(200, response.status_code)

        # Check there is comment of the revision that is being reviewed
        doc = pq(response.content)
        doc_content = doc('#review-revision').text()
        assert revs[6].comment in doc_content

        # Check that the Plural message is shown when there are multiple revision comments
        subject = doc('.unreviewed-revision').text()
        message = 'Unreviewed Revisions:'
        assert message in subject

        # Check *Revision Comment* text is in <label> to to be bolded
        text = doc('ul.revision-comment li label')[0].text_content()
        eq_('Revision Comment:', text)

        # Check whether past revisions Comments are there
        # As the comments are reversed means that the latest ones comment will be at 1st
        # the 2nd latest ones comment will be at second and like that.
        # So the revs[5] comment will be at first and revs[1] comment will be at last
        revision_comment = doc('ul.revision-comment li')
        assert revs[5].comment in revision_comment[0].text_content()
        assert revs[4].comment in revision_comment[1].text_content()
        assert revs[3].comment in revision_comment[2].text_content()
        assert revs[2].comment in revision_comment[3].text_content()
        assert revs[1].comment in revision_comment[4].text_content()
        # Verify that there is highest 5 revision comments. The 6th revision comment is not there
        assert revs[0].comment not in revision_comment.text()

        # Check that there is no comment of the revisions which is older than Current Revision
        # Also there is no comment of Current Revision
        revs[4].reviewed = datetime.now()
        revs[4].is_approved = True
        revs[4].save()
        d.current_revision = revs[4]
        d.save()
        response = get(self.client, 'wiki.review_revision',
                       args=[d.slug, revs[6].id])
        doc = pq(response.content)
        revision_comment = doc('ul.revision-comment li').text()
        assert revs[5].comment in revision_comment
        assert revs[4].comment not in revision_comment
        assert revs[3].comment not in revision_comment
        assert revs[2].comment not in revision_comment
        assert revs[1].comment not in revision_comment
        assert revs[0].comment not in revision_comment

        # Check that the Singular message is shown when there is single revision comment
        subject = doc('.unreviewed-revision').text()
        message = 'Unreviewed Revision:'
        assert message in subject


class CompareRevisionTests(TestCaseBase):
    """Tests for Review Revisions"""

    def setUp(self):
        super(CompareRevisionTests, self).setUp()
        self.document = _create_document()
        self.revision1 = self.document.current_revision
        u = UserFactory()
        self.revision2 = Revision(summary="lipsum",
                                  content='<div>Lorem Ipsum Dolor</div>',
                                  keywords='kw1 kw2',
                                  document=self.document, creator=u)
        self.revision2.save()

        u = UserFactory()
        self.client.login(username=u.username, password='testpass')

    def test_compare_revisions(self):
        """Compare two revisions"""
        url = reverse('wiki.compare_revisions', args=[self.document.slug])
        query = {'from': self.revision1.id, 'to': self.revision2.id}
        url = urlparams(url, **query)
        response = self.client.get(url)
        eq_(200, response.status_code)

    def test_compare_revisions_invalid_to_int(self):
        """Provide invalid 'to' int for revision ids."""
        url = reverse('wiki.compare_revisions', args=[self.document.slug])
        query = {'from': '', 'to': 'invalid'}
        url = urlparams(url, **query)
        response = self.client.get(url)
        eq_(404, response.status_code)

    def test_compare_revisions_invalid_from_int(self):
        """Provide invalid 'from' int for revision ids."""
        url = reverse('wiki.compare_revisions', args=[self.document.slug])
        query = {'from': 'invalid', 'to': ''}
        url = urlparams(url, **query)
        response = self.client.get(url)
        eq_(404, response.status_code)

    def test_compare_revisions_missing_query_param(self):
        """Try to compare two revisions, with a missing query string param."""
        url = reverse('wiki.compare_revisions', args=[self.document.slug])
        query = {'from': self.revision1.id}
        url = urlparams(url, **query)
        response = self.client.get(url)
        eq_(404, response.status_code)

        url = reverse('wiki.compare_revisions', args=[self.document.slug])
        query = {'to': self.revision1.id}
        url = urlparams(url, **query)
        response = self.client.get(url)
        eq_(404, response.status_code)


class TranslateTests(TestCaseBase):
    """Tests for the Translate page"""

    def setUp(self):
        super(TranslateTests, self).setUp()
        self.d = _create_document()

        self.user = UserFactory()
        self.client.login(username=self.user.username, password='testpass')

    def test_translate_GET_logged_out(self):
        """Try to create a translation while logged out."""
        self.client.logout()
        url = reverse('wiki.translate', locale='es', args=[self.d.slug])
        response = self.client.get(url)
        eq_(302, response.status_code)

    def test_translate_GET_with_perm(self):
        """HTTP GET to translate URL renders the form."""
        url = reverse('wiki.translate', locale='es', args=[self.d.slug])
        response = self.client.get(url)
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(1, len(doc('form textarea[name="content"]')))
        assert 'value' not in doc('#id_comment')[0].attrib
        eq_('checked', doc('#id_allow_discussion')[0].attrib['checked'])

    def test_translate_disallow(self):
        """HTTP GET to translate URL returns 400 when not localizable."""
        self.d.is_localizable = False
        self.d.save()
        url = reverse('wiki.translate', locale='es', args=[self.d.slug])
        response = self.client.get(url)
        eq_(400, response.status_code)

    def test_invalid_document_form(self):
        """Make sure we handle invalid document form without a 500."""
        url = reverse('wiki.translate', locale='es', args=[self.d.slug])
        data = _translation_data()
        data['slug'] = ''  # Invalid slug
        response = self.client.post(url, data)
        eq_(200, response.status_code)

    def test_invalid_revision_form(self):
        """When creating a new translation, an invalid revision form shouldn't
        result in a new Document being created."""
        url = reverse('wiki.translate', locale='es', args=[self.d.slug])
        data = _translation_data()
        data['content'] = ''  # Content is required
        response = self.client.post(url, data)
        eq_(200, response.status_code)
        eq_(0, self.d.translations.count())

    @mock.patch.object(ReviewableRevisionInLocaleEvent, 'fire')
    @mock.patch.object(EditDocumentEvent, 'fire')
    @mock.patch.object(Site.objects, 'get_current')
    def test_first_translation_to_locale(self, get_current, edited_fire,
                                         ready_fire):
        """Create the first translation of a doc to new locale."""
        get_current.return_value.domain = 'testserver'

        url = reverse('wiki.translate', locale='es', args=[self.d.slug])
        data = _translation_data()
        response = self.client.post(url, data)
        eq_(302, response.status_code)
        new_doc = Document.objects.get(slug=data['slug'])
        eq_('es', new_doc.locale)
        eq_(data['title'], new_doc.title)
        eq_(self.d, new_doc.parent)
        rev = new_doc.revisions.all()[0]
        eq_(data['keywords'], rev.keywords)
        eq_(data['summary'], rev.summary)
        eq_(data['content'], rev.content)
        assert edited_fire.called
        assert ready_fire.called

    def _create_and_approve_first_translation(self):
        """Returns the revision."""
        # First create the first one with test above
        self.test_first_translation_to_locale()
        # Approve the translation
        rev_es = Revision.objects.filter(document__locale='es')[0]
        rev_es.is_approved = True
        rev_es.save()
        return rev_es

    @mock.patch.object(ReviewableRevisionInLocaleEvent, 'fire')
    @mock.patch.object(EditDocumentEvent, 'fire')
    def test_another_translation_to_locale(self, edited_fire,
                                           ready_fire):
        """Create the second translation of a doc."""
        rev_es = self._create_and_approve_first_translation()

        # Create and approve a new en-US revision
        rev_enUS = Revision(summary="lipsum",
                            content='lorem ipsum dolor sit amet new',
                            significance=SIGNIFICANCES[0][0],
                            keywords='kw1 kw2',
                            document=self.d,
                            creator_id=UserFactory().id,
                            is_ready_for_localization=True,
                            is_approved=True)
        rev_enUS.save()

        # Verify the form renders with correct content
        url = reverse('wiki.translate', locale='es', args=[self.d.slug])
        response = self.client.get(url)
        doc = pq(response.content)
        eq_(rev_es.content, doc('#id_content').text())
        eq_(rev_enUS.content, doc('#content-fields textarea[readonly]').text())
        eq_(2, len(doc('.recent-revisions li')))

        # Post the translation and verify
        data = _translation_data()
        data['content'] = 'loremo ipsumo doloro sito ameto nuevo'
        response = self.client.post(url, data)
        eq_(302, response.status_code)
        eq_('/es/kb/un-test-articulo/history',
            response['location'])
        doc = Document.objects.get(slug=data['slug'])
        rev = doc.revisions.filter(content=data['content'])[0]
        eq_(data['keywords'], rev.keywords)
        eq_(data['summary'], rev.summary)
        eq_(data['content'], rev.content)
        assert not rev.is_approved
        assert edited_fire.called
        assert ready_fire.called

    @mock.patch.object(Site.objects, 'get_current')
    def test_translate_form_maintains_based_on_rev(self, get_current):
        """Revision.based_on should be the rev that was current when the
        Translate button was clicked, even if other revisions happen while the
        user is editing."""
        get_current.return_value.domain = 'testserver'
        _test_form_maintains_based_on_rev(self.client, self.d,
                                          'wiki.translate',
                                          _translation_data(), locale='es')

    def test_translate_update_doc_only(self):
        """Submitting the document form should update document. No new
        revisions should be created."""
        add_permission(self.user, Document, 'change_document')
        rev_es = self._create_and_approve_first_translation()
        url = reverse('wiki.translate', locale='es', args=[self.d.slug])
        data = _translation_data()
        new_title = 'Un nuevo titulo'
        data['title'] = new_title
        data['form'] = 'doc'
        response = self.client.post(url, data)
        eq_(302, response.status_code)
        eq_('/es/kb/un-test-articulo/edit?opendescription=1',
            response['location'])
        revisions = rev_es.document.revisions.all()
        eq_(1, revisions.count())  # No new revisions
        d = Document.objects.get(id=rev_es.document.id)
        eq_(new_title, d.title)  # Title is updated

    def test_translate_update_rev_only(self):
        """Submitting the revision form should create a new revision.
        No document fields should be updated."""
        rev_es = self._create_and_approve_first_translation()
        orig_title = rev_es.document.title
        url = reverse('wiki.translate', locale='es', args=[self.d.slug])
        data = _translation_data()
        new_title = 'Un nuevo titulo'
        data['title'] = new_title
        data['form'] = 'rev'
        response = self.client.post(url, data)
        eq_(302, response.status_code)
        eq_('/es/kb/un-test-articulo/history', response['location'])
        revisions = rev_es.document.revisions.all()
        eq_(2, revisions.count())  # New revision is created
        d = Document.objects.get(id=rev_es.document.id)
        eq_(orig_title, d.title)  # Title isn't updated

    def test_translate_form_content_fallback(self):
        """If there are existing but unapproved translations, prefill
        content with latest."""
        self.test_first_translation_to_locale()
        url = reverse('wiki.translate', locale='es', args=[self.d.slug])
        response = self.client.get(url)
        doc = pq(response.content)
        document = Document.objects.filter(locale='es')[0]
        existing_rev = document.revisions.all()[0]
        eq_(existing_rev.content, doc('#id_content').text())

    def test_translate_based_on(self):
        """Test translating based on a non-current revision."""
        # Create the base revision
        base_rev = self._create_and_approve_first_translation()
        # Create a new current revision
        r = ApprovedRevisionFactory(document=base_rev.document)
        d = Document.objects.get(pk=base_rev.document.id)
        eq_(r, base_rev.document.current_revision)

        url = reverse('wiki.new_revision_based_on', locale='es',
                      args=[d.slug, base_rev.id])
        response = self.client.get(url)
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(doc('#id_content')[0].value.strip(), base_rev.content)

    def test_translate_rejected_parent(self):
        """Translate view of rejected English document shows warning."""
        user = UserFactory()
        en_revision = RevisionFactory(is_approved=False, reviewer=user, reviewed=datetime.now())

        url = reverse('wiki.translate', locale='es', args=[en_revision.document.slug])
        response = self.client.get(url)
        doc = pq(response.content)
        assert doc('.user-messages .warning').text()

    def test_skip_unready_when_first_translation(self):
        """Never offer an unready-for-localization revision as initial
        translation source text."""
        # Create an English document all ready to translate:
        en_doc = DocumentFactory(is_localizable=True)
        ApprovedRevisionFactory(
            document=en_doc,
            is_ready_for_localization=True,
            content='I am the ready!')
        ApprovedRevisionFactory(document=en_doc, is_ready_for_localization=False)

        url = reverse('wiki.translate', locale='de', args=[en_doc.slug])
        response = self.client.get(url)
        self.assertContains(response, 'I am the ready!')

    def test_skip_unready_when_not_first_translation(self):
        """Never offer an unready-for-localization revision as diff text when
        bringing an already translated article up to date."""
        # Create an initial translated revision so the version of the template
        # with the English-to-English diff shows up:
        initial_rev = TranslatedRevisionFactory(is_approved=True)
        doc = initial_rev.document
        en_doc = doc.parent
        ready = ApprovedRevisionFactory(document=en_doc, is_ready_for_localization=True)
        ApprovedRevisionFactory(document=en_doc, is_ready_for_localization=False)

        url = reverse('wiki.translate', locale=doc.locale, args=[en_doc.slug])
        response = self.client.get(url)
        eq_(200, response.status_code)
        # Get the link to the rev on the right side of the diff:
        to_link = pq(response.content)('.revision-diff h3 a')[1].attrib['href']
        assert to_link.endswith('/%s' % ready.pk)

    def test_translate_no_update_based_on(self):
        """Test translating based on a non-current revision."""
        # Set up the base es revision
        base_es_rev = self._create_and_approve_first_translation()
        es_doc = base_es_rev.document
        enUS_doc = es_doc.parent
        base_es_rev.based_on = enUS_doc.current_revision
        base_es_rev.save()

        # Create a new current revision on the parent document.
        r = ApprovedRevisionFactory(document=es_doc.parent, is_ready_for_localization=True)

        url = reverse('wiki.edit_document', locale='es', args=[es_doc.slug])
        data = _translation_data()
        data['form'] = 'rev'
        data['based_on'] = enUS_doc.current_revision_id

        # Passing no-update will create a new revision based on the same one
        # as the older revision.
        data['no-update'] = 'Yes'
        self.client.post(url, data)
        new_es_rev = es_doc.revisions.order_by('-id')[0]
        eq_(base_es_rev.based_on_id, new_es_rev.based_on_id)

        # Not passing no-update will create a new revision based on the latest
        # approved and ready for l10n en-US revision.
        del data['no-update']
        self.client.post(url, data)
        new_es_rev = es_doc.revisions.order_by('-id')[0]
        eq_(r.id, new_es_rev.based_on_id)

    def test_show_translations_page(self):
        en = settings.WIKI_DEFAULT_LANGUAGE
        en_doc = DocumentFactory(locale=en, slug='english-slug')
        DocumentFactory(locale='de', parent=en_doc)

        url = reverse('wiki.show_translations',
                      locale=settings.WIKI_DEFAULT_LANGUAGE,
                      args=[en_doc.slug])
        r = self.client.get(url)
        doc = pq(r.content)
        translated_locales = doc(".translated_locale")
        eq_(translated_locales.length, 2)
        eq_("English (en-US)", doc(".translated_locale").first().text())
        eq_("Deutsch (de)", doc(".translated_locale:eq(1)").text())

    def test_keywords_dont_require_permission(self):
        """Test keywords don't require permission when translating."""
        old_rev = self._create_and_approve_first_translation()
        doc = old_rev.document

        u = UserFactory()
        self.client.login(username=u.username, password='testpass')

        # Edit the document:
        response = self.client.post(
            reverse('wiki.edit_document', args=[doc.slug], locale=doc.locale),
            {'summary': 'A brief summary', 'content': 'The article content',
             'keywords': 'keyword1 keyword2',
             'based_on': doc.parent.current_revision_id, 'form': 'rev'})
        eq_(302, response.status_code)

        # Keywords should be updated
        new_rev = Revision.objects.filter(document=doc).order_by('-id')[0]
        eq_('keyword1 keyword2', new_rev.keywords)


def _test_form_maintains_based_on_rev(client, doc, view, post_data,
                                      locale=None):
    """Confirm that the based_on value set in the revision created by an edit
    or translate form is the current_revision of the document as of when the
    form was first loaded, even if other revisions have been approved in the
    meantime."""
    response = client.get(reverse(view, locale=locale, args=[doc.slug]))
    orig_rev = doc.current_revision
    eq_(orig_rev.id,
        int(pq(response.content)('input[name=based_on]').attr('value')))

    # While Fred is editing the above, Martha approves a new rev:
    ApprovedRevisionFactory(document=doc)

    # Then Fred saves his edit:
    post_data_copy = {'based_on': orig_rev.id}
    post_data_copy.update(post_data)  # Don't mutate arg.
    response = client.post(reverse(view, locale=locale, args=[doc.slug]),
                           data=post_data_copy)
    eq_(302, response.status_code)
    fred_rev = Revision.objects.all().order_by('-id')[0]
    eq_(orig_rev, fred_rev.based_on)


class DocumentWatchTests(TestCaseBase):
    """Tests for un/subscribing to document edit notifications."""

    def setUp(self):
        super(DocumentWatchTests, self).setUp()
        self.document = _create_document()
        ProductFactory()

        self.user = UserFactory()
        self.client.login(username=self.user.username, password='testpass')

    def test_watch_GET_405(self):
        """Watch document with HTTP GET results in 405."""
        response = get(self.client, 'wiki.document_watch',
                       args=[self.document.slug])
        eq_(405, response.status_code)

    def test_unwatch_GET_405(self):
        """Unwatch document with HTTP GET results in 405."""
        response = get(self.client, 'wiki.document_unwatch',
                       args=[self.document.slug])
        eq_(405, response.status_code)

    def test_watch_unwatch(self):
        """Watch and unwatch a document."""
        # Subscribe
        response = post(self.client, 'wiki.document_watch',
                        args=[self.document.slug])
        eq_(200, response.status_code)
        assert EditDocumentEvent.is_notifying(self.user, self.document), (
            'Watch was not created')
        # Unsubscribe
        response = post(self.client, 'wiki.document_unwatch',
                        args=[self.document.slug])
        eq_(200, response.status_code)
        assert not EditDocumentEvent.is_notifying(self.user, self.document), (
            'Watch was not destroyed')


class LocaleWatchTests(TestCaseBase):
    """Tests for un/subscribing to a locale's ready for review emails."""

    def setUp(self):
        super(LocaleWatchTests, self).setUp()

        self.user = UserFactory()
        self.client.login(username=self.user, password='testpass')

    def test_watch_GET_405(self):
        """Watch document with HTTP GET results in 405."""
        response = get(self.client, 'wiki.locale_watch')
        eq_(405, response.status_code)

    def test_unwatch_GET_405(self):
        """Unwatch document with HTTP GET results in 405."""
        response = get(self.client, 'wiki.locale_unwatch')
        eq_(405, response.status_code)

    def test_watch_and_unwatch_by_locale(self):
        """Watch and unwatch a locale."""
        # Subscribe
        response = post(self.client, 'wiki.locale_watch')
        eq_(200, response.status_code)
        assert ReviewableRevisionInLocaleEvent.is_notifying(self.user,
                                                            locale='en-US')

        # Unsubscribe
        response = post(self.client, 'wiki.locale_unwatch')
        eq_(200, response.status_code)
        assert not ReviewableRevisionInLocaleEvent.is_notifying(self.user,
                                                                locale='en-US')

    def test_watch_and_unwatch_by_locale_and_product(self):
        # Subscribe
        response = post(self.client, 'wiki.locale_watch', args=['firefox-os'])
        eq_(200, response.status_code)
        assert ReviewableRevisionInLocaleEvent.is_notifying(
            self.user, locale='en-US', product='firefox-os')

        # Unsubscribe
        response = post(self.client, 'wiki.locale_unwatch',
                        args=['firefox-os'])
        eq_(200, response.status_code)
        assert not ReviewableRevisionInLocaleEvent.is_notifying(
            self.user, locale='en-US', product='firefox-os')


class ArticlePreviewTests(TestCaseBase):
    """Tests for preview view and template."""

    def setUp(self):
        super(ArticlePreviewTests, self).setUp()

        u = UserFactory()
        self.client.login(username=u.username, password='testpass')

    def test_preview_GET_405(self):
        """Preview with HTTP GET results in 405."""
        response = get(self.client, 'wiki.preview')
        eq_(405, response.status_code)

    def test_preview(self):
        """Preview the wiki syntax content."""
        d = _create_document()
        response = post(self.client, 'wiki.preview', {
            'content': '=Test Content=',
            'slug': d.slug,
            'locale': d.locale,
        })
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_('Test Content', doc('#doc-content h1').text())

    def test_preview_locale(self):
        """Preview the wiki syntax content."""
        # Create a test document and translation.
        d = _create_document()
        _create_document(title='Prueba', parent=d, locale='es')
        # Preview content that links to it and verify link is in locale.
        url = reverse('wiki.preview', locale='es')
        response = self.client.post(url, {
            'content': '[[Test Document]]',
            'slug': d.slug,
            'locale': d.locale,
        })
        eq_(200, response.status_code)
        doc = pq(response.content)
        link = doc('#doc-content a')
        eq_('Prueba', link.text())
        eq_('/es/kb/prueba', link[0].attrib['href'])


class HelpfulVoteTests(TestCaseBase):

    def setUp(self):
        super(HelpfulVoteTests, self).setUp()

        self.document = _create_document()
        ProductFactory()

    def test_vote_yes(self):
        """Test voting helpful."""
        r = self.document.current_revision
        user_ = UserFactory()
        referrer = 'http://google.com/?q=test'
        query = 'test'
        self.client.login(username=user_.username, password='testpass')
        response = post(self.client, 'wiki.document_vote',
                        {'helpful': 'Yes', 'revision_id': r.id,
                         'referrer': referrer, 'query': query},
                        args=[self.document.slug])
        eq_(200, response.status_code)
        votes = HelpfulVote.objects.filter(revision=r, creator=user_)
        eq_(1, votes.count())
        assert votes[0].helpful
        metadata = HelpfulVoteMetadata.objects.values_list('key', 'value')
        eq_(2, len(metadata))
        metadata_dict = dict((k, v) for (k, v) in metadata)
        eq_(referrer, metadata_dict['referrer'])
        eq_(query, metadata_dict['query'])

    def test_vote_no(self):
        """Test voting not helpful."""
        r = self.document.current_revision
        user_ = UserFactory()
        referrer = 'inproduct'
        query = ''
        self.client.login(username=user_.username, password='testpass')
        response = post(self.client, 'wiki.document_vote',
                        {'not-helpful': 'No', 'revision_id': r.id,
                         'referrer': referrer, 'query': query},
                        args=[self.document.slug])
        eq_(200, response.status_code)
        votes = HelpfulVote.objects.filter(revision=r, creator=user_)
        eq_(1, votes.count())
        assert not votes[0].helpful
        metadata = HelpfulVoteMetadata.objects.values_list('key', 'value')
        eq_(1, len(metadata))
        metadata_dict = dict((k, v) for (k, v) in metadata)
        eq_(referrer, metadata_dict['referrer'])

    def test_vote_anonymous(self):
        """Test that voting works for anonymous user."""
        r = self.document.current_revision
        referrer = 'search'
        query = 'cookies'
        response = post(self.client, 'wiki.document_vote',
                        {'helpful': 'Yes', 'revision_id': r.id,
                         'referrer': referrer, 'query': query},
                        args=[self.document.slug])
        eq_(200, response.status_code)
        votes = HelpfulVote.objects.filter(revision=r, creator=None)
        votes = votes.exclude(anonymous_id=None)
        eq_(1, votes.count())
        assert votes[0].helpful
        metadata = HelpfulVoteMetadata.objects.values_list('key', 'value')
        eq_(2, len(metadata))
        metadata_dict = dict((k, v) for (k, v) in metadata)
        eq_(referrer, metadata_dict['referrer'])
        eq_(query, metadata_dict['query'])

    def test_vote_ajax(self):
        """Test voting via ajax."""
        r = self.document.current_revision
        referrer = ''
        query = ''
        url = reverse('wiki.document_vote', args=[self.document.slug])
        response = self.client.post(
            url, data={'helpful': 'Yes', 'revision_id': r.id,
                       'referrer': referrer, 'query': query},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(200, response.status_code)
        eq_('{"message": "Glad to hear it &mdash; thanks for the feedback!"}',
            response.content)
        votes = HelpfulVote.objects.filter(revision=r, creator=None)
        votes = votes.exclude(anonymous_id=None)
        eq_(1, votes.count())
        assert votes[0].helpful
        metadata = HelpfulVoteMetadata.objects.values_list('key', 'value')
        eq_(0, len(metadata))

    def test_helpfulvotes_graph_async_yes(self):
        r = self.document.current_revision
        response = post(self.client, 'wiki.document_vote',
                        {'helpful': 'Yes', 'revision_id': r.id},
                        args=[self.document.slug])
        eq_(200, response.status_code)

        resp = get(self.client, 'wiki.get_helpful_votes_async',
                   args=[r.document.slug])
        eq_(200, resp.status_code)
        data = json.loads(resp.content)

        eq_(1, len(data['datums']))
        assert 'yes' in data['datums'][0]
        assert 'no' in data['datums'][0]

    def test_helpfulvotes_graph_async_no(self):
        r = self.document.current_revision
        response = post(self.client, 'wiki.document_vote',
                        {'helpful': 'No', 'revision_id': r.id},
                        args=[self.document.slug])
        eq_(200, response.status_code)

        resp = get(self.client, 'wiki.get_helpful_votes_async',
                   args=[r.document.slug])
        eq_(200, resp.status_code)
        data = json.loads(resp.content)

        eq_(1, len(data['datums']))
        assert 'yes' in data['datums'][0]
        assert 'no' in data['datums'][0]

    def test_helpfulvotes_graph_async_no_votes(self):
        r = self.document.current_revision

        resp = get(self.client, 'wiki.get_helpful_votes_async',
                   args=[r.document.slug])
        eq_(200, resp.status_code)
        data = json.loads(resp.content)
        eq_(0, len(data['datums']))


class SelectLocaleTests(TestCaseBase):
    """Test the locale selection page"""

    def setUp(self):
        super(SelectLocaleTests, self).setUp()
        self.d = _create_document()

        u = UserFactory()
        self.client.login(username=u.username, password='testpass')

    def test_page_renders_locales(self):
        """Load the page and verify it contains all the locales for l10n."""
        response = get(self.client, 'wiki.select_locale', args=[self.d.slug])
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(len(settings.LANGUAGE_CHOICES),  # All Locals including ' en-US'.
            len(doc('#select-locale ul.locales li')))


class RevisionDeleteTestCase(TestCaseBase):
    def test_delete_revision_without_permissions(self):
        """Deleting a revision without permissions sends 403."""
        u = UserFactory()
        doc = DocumentFactory()
        rev = ApprovedRevisionFactory(document=doc)
        self.client.login(username=u.username, password='testpass')
        response = get(self.client, 'wiki.delete_revision', args=[doc.slug, rev.id])
        eq_(403, response.status_code)

        response = post(self.client, 'wiki.delete_revision', args=[doc.slug, rev.id])
        eq_(403, response.status_code)

    def test_delete_revision_logged_out(self):
        """Deleting a revision while logged out redirects to login."""
        doc = DocumentFactory()
        rev = RevisionFactory(document=doc)
        response = get(self.client, 'wiki.delete_revision', args=[doc.slug, rev.id])
        redirect = response.redirect_chain[0]
        eq_(302, redirect[1])
        eq_('/%s%s?next=/en-US/kb/%s/revision/%s/delete' %
            (settings.LANGUAGE_CODE, settings.LOGIN_URL, doc.slug, rev.id),
            redirect[0])

        response = post(self.client, 'wiki.delete_revision', args=[doc.slug, rev.id])
        redirect = response.redirect_chain[0]
        eq_(302, redirect[1])
        eq_('/%s%s?next=/en-US/kb/%s/revision/%s/delete' %
            (settings.LANGUAGE_CODE, settings.LOGIN_URL, doc.slug, rev.id),
            redirect[0])

    def _test_delete_revision_with_permission(self):
        doc = DocumentFactory()
        rev1 = ApprovedRevisionFactory(document=doc)
        rev2 = ApprovedRevisionFactory(document=doc)
        response = get(self.client, 'wiki.delete_revision', args=[doc.slug, rev2.id])
        eq_(200, response.status_code)
        response = post(self.client, 'wiki.delete_revision', args=[doc.slug, rev2.id])
        eq_(200, response.status_code)
        assert not Revision.objects.filter(pk=rev2.id).exists()
        assert Revision.objects.filter(pk=rev1.id).exists()

    def test_delete_revision_with_permission(self):
        """Deleting a revision with permissions should work."""
        u = UserFactory()
        add_permission(u, Revision, 'delete_revision')
        self.client.login(username=u.username, password='testpass')
        self._test_delete_revision_with_permission()

    def test_delete_revision_as_l10n_leader(self):
        """Deleting a revision as l10n leader should work."""
        u = UserFactory()
        l10n = LocaleFactory(locale='en-US')
        l10n.leaders.add(u)
        self.client.login(username=u.username, password='testpass')
        self._test_delete_revision_with_permission()

    def test_delete_revision_as_l10n_reviewer(self):
        """Deleting a revision as l10n reviewer should work."""
        u = UserFactory()
        l10n = LocaleFactory(locale='en-US')
        l10n.reviewers.add(u)
        self.client.login(username=u.username, password='testpass')
        self._test_delete_revision_with_permission()

    def test_delete_current_revision(self):
        """Deleting the current_revision of a document should update
        the current_revision to previous version."""
        doc = DocumentFactory()
        rev1 = ApprovedRevisionFactory(document=doc)
        rev2 = ApprovedRevisionFactory(document=doc)

        u = UserFactory()
        add_permission(u, Revision, 'delete_revision')
        self.client.login(username=u.username, password='testpass')
        eq_(rev2, doc.current_revision)

        res = post(self.client, 'wiki.delete_revision', args=[doc.slug, rev2.id])
        eq_(res.status_code, 200)
        doc = Document.objects.get(pk=doc.pk)
        eq_(rev1, doc.current_revision)

    def test_delete_only_revision(self):
        """If there is only one revision, it can't be deleted."""
        u = UserFactory()
        add_permission(u, Revision, 'delete_revision')
        self.client.login(username=u.username, password='testpass')

        # Create document with only 1 revision
        doc = DocumentFactory()
        rev = RevisionFactory(document=doc)

        # Confirm page should show the message
        response = get(self.client, 'wiki.delete_revision',
                       args=[doc.slug, rev.id])
        eq_(200, response.status_code)
        eq_('Unable to delete only revision of the document',
            pq(response.content)('h1.title').text())

        # POST should return bad request and revision should still exist
        response = post(self.client, 'wiki.delete_revision',
                        args=[doc.slug, rev.id])
        eq_(400, response.status_code)
        Revision.objects.get(id=rev.id)


class ApprovedWatchTests(TestCaseBase):
    """Tests for un/subscribing to revision approvals."""

    def setUp(self):
        super(ApprovedWatchTests, self).setUp()

        self.user = UserFactory()
        self.client.login(username=self.user.username, password='testpass')

    def test_watch_GET_405(self):
        """Watch with HTTP GET results in 405."""
        response = get(self.client, 'wiki.approved_watch')
        eq_(405, response.status_code)

    def test_unwatch_GET_405(self):
        """Unwatch with HTTP GET results in 405."""
        response = get(self.client, 'wiki.approved_unwatch')
        eq_(405, response.status_code)

    def test_watch_unwatch(self):
        """Watch and unwatch a document."""
        locale = 'es'

        # Subscribe
        response = post(self.client, 'wiki.approved_watch', locale=locale)
        eq_(200, response.status_code)
        assert ApproveRevisionInLocaleEvent.is_notifying(
            self.user, locale=locale)

        # Unsubscribe
        response = post(self.client, 'wiki.approved_unwatch', locale=locale)
        eq_(200, response.status_code)
        assert not ApproveRevisionInLocaleEvent.is_notifying(
            self.user, locale=locale)


class DocumentDeleteTestCase(TestCaseBase):
    """Tests for document delete."""
    def setUp(self):
        super(DocumentDeleteTestCase, self).setUp()
        self.document = DocumentFactory()
        self.user = UserFactory(username='testuser')

    def test_delete_document_without_permissions(self):
        """Deleting a document without permissions sends 403."""
        self.client.login(username='testuser', password='testpass')
        response = get(self.client, 'wiki.document_delete',
                       args=[self.document.slug])
        eq_(403, response.status_code)

        response = post(self.client, 'wiki.document_delete',
                        args=[self.document.slug])
        eq_(403, response.status_code)

    def test_delete_document_logged_out(self):
        """Deleting a document while logged out redirects to login."""
        response = get(self.client, 'wiki.document_delete',
                       args=[self.document.slug])
        redirect = response.redirect_chain[0]
        eq_(302, redirect[1])
        eq_('/%s%s?next=/en-US/kb/%s/delete' %
            (settings.LANGUAGE_CODE, settings.LOGIN_URL,
             self.document.slug),
            redirect[0])

        response = post(self.client, 'wiki.document_delete',
                        args=[self.document.slug])
        redirect = response.redirect_chain[0]
        eq_(302, redirect[1])
        eq_('/%s%s?next=/en-US/kb/%s/delete' %
            (settings.LANGUAGE_CODE, settings.LOGIN_URL,
             self.document.slug),
            redirect[0])

    def test_document_as_l10n_leader(self):
        """Deleting a document as l10n leader should work."""
        l10n = LocaleFactory(locale='en-US')
        l10n.leaders.add(self.user)
        self._test_delete_document_with_permission()

    def test_document_as_l10n_reviewer(self):
        """Deleting a document as l10n leader should NOT work."""
        l10n = LocaleFactory(locale='en-US')
        l10n.reviewers.add(self.user)
        self.test_delete_document_without_permissions()

    def _test_delete_document_with_permission(self):
        self.client.login(username='testuser', password='testpass')
        response = get(self.client, 'wiki.document_delete',
                       args=[self.document.slug])
        eq_(200, response.status_code)

        response = post(self.client, 'wiki.document_delete',
                        args=[self.document.slug])
        eq_(0, Document.objects.filter(pk=self.document.id).count())

    def test_revision_with_permission(self):
        """Deleting a document with delete_document permission should work."""
        add_permission(self.user, Document, 'delete_document')
        self._test_delete_document_with_permission()


class RecentRevisionsTest(TestCaseBase):

    def setUp(self):
        self.u1 = UserFactory()
        self.u2 = UserFactory()

        eq_(Document.objects.count(), 0)

        _create_document(title='1', rev_kwargs={'creator': self.u1})
        _create_document(title='2', rev_kwargs={
            'creator': self.u1,
            'created': datetime(2013, 3, 1, 0, 0, 0, 0),
        })
        _create_document(
            title='3', locale='de', rev_kwargs={'creator': self.u2})
        _create_document(
            title='4', locale='fr', rev_kwargs={'creator': self.u2})
        _create_document(
            title='5', locale='fr', rev_kwargs={'creator': self.u2})

        self.url = reverse('wiki.revisions')

    def test_basic(self):
        res = self.client.get(self.url)
        eq_(res.status_code, 200)

        doc = pq(res.content)
        eq_(len(doc('#revisions-fragment ul li:not(.header)')), 5)

    def test_locale_filtering(self):
        url = urlparams(self.url, locale='fr')
        res = self.client.get(url)
        eq_(res.status_code, 200)

        doc = pq(res.content)
        eq_(len(doc('#revisions-fragment ul li:not(.header)')), 2)

        url = urlparams(self.url, locale='de')
        res = self.client.get(url)
        eq_(res.status_code, 200)

        doc = pq(res.content)
        eq_(len(doc('#revisions-fragment ul li:not(.header)')), 1)

    def test_bad_locale(self):
        """A bad locale should not filter anything."""
        url = urlparams(self.url, locale='asdf')
        res = self.client.get(url)
        eq_(res.status_code, 200)

        doc = pq(res.content)
        eq_(len(doc('#revisions-fragment ul li:not(.header)')), 5)

    def test_user_filtering(self):
        url = urlparams(self.url, users=self.u1.username)
        res = self.client.get(url)
        eq_(res.status_code, 200)

        doc = pq(res.content)
        eq_(len(doc('#revisions-fragment ul li:not(.header)')), 2)

    def test_date_filtering(self):
        url = urlparams(self.url, start='2013-03-02')
        res = self.client.get(url)
        eq_(res.status_code, 200)

        doc = pq(res.content)
        eq_(len(doc('#revisions-fragment ul li:not(.header)')), 4)

        url = urlparams(self.url, end='2013-03-02')
        res = self.client.get(url)
        eq_(res.status_code, 200)

        doc = pq(res.content)
        eq_(len(doc('#revisions-fragment ul li:not(.header)')), 1)


# TODO: This should be a factory subclass
def _create_document(title='Test Document', parent=None, locale=settings.WIKI_DEFAULT_LANGUAGE,
                     doc_kwargs={}, rev_kwargs={}):
    d = DocumentFactory(
        title=title,
        html='<div>Lorem Ipsum</div>',
        category=TROUBLESHOOTING_CATEGORY,
        locale=locale,
        parent=parent,
        is_localizable=True,
        **doc_kwargs)
    d.save()
    r = ApprovedRevisionFactory(
        document=d,
        keywords='key1, key2',
        summary='lipsum',
        content='<div>Lorem Ipsum</div>',
        significance=SIGNIFICANCES[0][0],
        is_ready_for_localization=True,
        comment="Good job!",
        **rev_kwargs)
    r.created = r.created - timedelta(days=10)
    r.save()
    return d


def _translation_data():
    return {
        'title': 'Un Test Articulo', 'slug': 'un-test-articulo',
        'keywords': 'keyUno, keyDos, keyTres',
        'summary': 'lipsumo',
        'content': 'loremo ipsumo doloro sito ameto'}
