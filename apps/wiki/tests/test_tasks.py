from copy import deepcopy
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core import mail
from django.core.cache import cache

import celery.conf
import mock
from nose.tools import eq_
from test_utils import RequestFactory
import waffle

from sumo.tests import TestCase
from wiki.models import (Document, HelpfulVote, HelpfulVoteOld)
from wiki.tasks import (migrate_helpfulvotes, 
                        send_reviewed_notification, rebuild_kb,
                        schedule_rebuild_kb, _rebuild_kb_chunk)
from wiki.tests import TestCaseBase, revision, document
from users.tests import user


REVIEWED_EMAIL_CONTENT = """Your revision has been reviewed.

admin has approved your revision to the document
%s.

Message from the reviewer:

%s

To view the history of this document, click the following
link, or paste it into your browser's location bar:

https://testserver/en-US/kb/%s/history"""


class RebuildTestCase(TestCase):
    fixtures = ['users.json', 'wiki/documents.json']
    rf = RequestFactory()
    ALWAYS_EAGER = celery.conf.ALWAYS_EAGER

    def setUp(self):
        self.old_settings = deepcopy(settings._wrapped.__dict__)
        celery.conf.ALWAYS_EAGER = True

    def tearDown(self):
        cache.delete(settings.WIKI_REBUILD_TOKEN)
        settings._wrapped.__dict__ = self.old_settings
        celery.conf.ALWAYS_EAGER = self.ALWAYS_EAGER

    @mock.patch.object(rebuild_kb, 'delay')
    @mock.patch.object(waffle, 'switch_is_active')
    def test_eager_queue(self, switch_is_active, delay):
        switch_is_active.return_value = True
        schedule_rebuild_kb()
        assert not cache.get(settings.WIKI_REBUILD_TOKEN)
        assert not delay.called

    @mock.patch.object(rebuild_kb, 'delay')
    @mock.patch.object(waffle, 'switch_is_active')
    def test_task_queue(self, switch_is_active, delay):
        switch_is_active.return_value = True
        celery.conf.ALWAYS_EAGER = False
        schedule_rebuild_kb()
        assert cache.get(settings.WIKI_REBUILD_TOKEN)
        assert delay.called

    @mock.patch.object(rebuild_kb, 'delay')
    @mock.patch.object(waffle, 'switch_is_active')
    def test_already_queued(self, switch_is_active, delay):
        switch_is_active.return_value = True
        cache.set(settings.WIKI_REBUILD_TOKEN, True)
        schedule_rebuild_kb()
        assert cache.get(settings.WIKI_REBUILD_TOKEN)
        assert not delay.called

    @mock.patch.object(rebuild_kb, 'delay')
    @mock.patch.object(cache, 'get')
    @mock.patch.object(waffle, 'switch_is_active')
    def test_dont_queue(self, switch_is_active, get, delay):
        switch_is_active.return_value = False
        schedule_rebuild_kb()
        assert not get.called
        assert not delay.called

    @mock.patch.object(_rebuild_kb_chunk, 'apply_async')
    def test_rebuild_chunk(self, apply_async):
        cache.set(settings.WIKI_REBUILD_TOKEN, True)
        rebuild_kb()
        assert not cache.get(settings.WIKI_REBUILD_TOKEN)
        data = set((1, 2, 4, 5))
        assert 'args' in apply_async.call_args[1]
        eq_(data, set(apply_async.call_args[1]['args'][0]))


class RedirectDeletionTests(TestCase):
    def test_delete_redirects(self):
        """Test that the rebuild deletes redirects that point to deleted
        documents."""
        # Change slug so redirect is created:
        d = revision(is_approved=True,
                     document=document(title='foo', slug='foo', save=True),
                     save=True).document
        slug = d.slug
        d.slug = slug + '-1'
        d.save()

        # Rebuild kb, and make sure redirect is still there:
        rebuild_kb()
        redirect = Document.objects.get(slug=slug)
        eq_(d.slug, redirect.redirect_document().slug)

        # Delete the document, and make sure redirect is gone:
        d.delete()
        rebuild_kb()
        eq_(0, Document.objects.filter(slug=slug).count())

    def test_external(self):
        """Make sure rebuild_kb doesn't delete redirects to external URLs."""
        doc_pk = revision(content='REDIRECT [http://www.example.com/]',
                          is_approved=True,
                          save=True).document.pk
        rebuild_kb()
        assert Document.uncached.filter(pk=doc_pk).exists()


class ReviewMailTestCase(TestCaseBase):
    """Test that the review mail gets sent."""
    fixtures = ['users.json']

    def _approve_and_send(self, revision, reviewer, message):
        revision.reviewer = reviewer
        revision.reviewed = datetime.now()
        revision.is_approved = True
        revision.save()
        send_reviewed_notification(revision, revision.document, message)

    @mock.patch.object(Site.objects, 'get_current')
    def test_reviewed_notification(self, get_current):
        get_current.return_value.domain = 'testserver'

        rev = revision()
        doc = rev.document
        msg = 'great work!'
        self._approve_and_send(rev, User.objects.get(username='admin'), msg)

        eq_(1, len(mail.outbox))
        eq_('Your revision has been approved: %s' % doc.title,
            mail.outbox[0].subject)
        eq_([rev.creator.email], mail.outbox[0].to)
        eq_(REVIEWED_EMAIL_CONTENT % (doc.title, msg, doc.slug),
            mail.outbox[0].body)

    @mock.patch.object(Site.objects, 'get_current')
    def test_reviewed_by_creator_no_notification(self, get_current):
        get_current.return_value.domain = 'testserver'

        rev = revision()
        msg = "great work!"
        self._approve_and_send(rev, rev.creator, msg)

        # Verify no email was sent
        eq_(0, len(mail.outbox))

    @mock.patch.object(Site.objects, 'get_current')
    def test_unicode_notifications(self, get_current):
        get_current.return_value.domain = 'testserver'

        rev = revision()
        doc = rev.document
        doc.title = u'Foo \xe8 incode'
        msg = 'foo'
        self._approve_and_send(rev, User.objects.get(username='admin'), msg)

        eq_(1, len(mail.outbox))
        eq_('Your revision has been approved: %s' % doc.title,
            mail.outbox[0].subject)


anon_id = '69beab04be927353c2f0046db2232643'
ua = '''Mozilla/5.0 (Windows; U; Windows NT 6.1;
    pt-BR; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12'''


class HelpfulMigrationTestCase(TestCase):

    @mock.patch.object(waffle, 'switch_is_active')
    def test_normal_migrate_anon(self, switch_is_active):
        switch_is_active.return_value = True
        rev = revision()
        rev.save()
        old = HelpfulVoteOld()
        old.document = rev.document
        old.helpful = 1
        old.anonymous_id = anon_id
        old.user_agent = ua
        old.save()
        migrate_helpfulvotes(0, 1000)
        new = HelpfulVote.objects.filter(revision=rev,
            helpful=1,
            anonymous_id=anon_id,
            user_agent=ua
            )
        assert new.exists()

        check_old = HelpfulVoteOld.objects.filter(id=old.id)
        assert check_old.exists()

    @mock.patch.object(waffle, 'switch_is_active')
    def test_normal_migrate_user(self, switch_is_active):
        switch_is_active.return_value = True
        rev = revision()
        rev.save()
        usr = user(save=True)

        old = HelpfulVoteOld()
        old.document = rev.document
        old.helpful = 1
        old.creator = usr
        old.user_agent = ua
        old.save()

        migrate_helpfulvotes(0, 1000)

        new = HelpfulVote.objects.filter(revision=rev,
            helpful=1,
            creator=usr,
            user_agent=ua
            )
        assert new.exists()

        check_old = HelpfulVoteOld.objects.filter(id=old.id)
        assert check_old.exists()
