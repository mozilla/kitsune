# -*- coding: utf-8 -*-
from django.core import mail

from nose.tools import eq_

from kitsune.sumo.tests import post
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import add_permission, UserFactory
from kitsune.products.tests import ProductFactory
from kitsune.wiki.config import (
    SIGNIFICANCES, MAJOR_SIGNIFICANCE, MEDIUM_SIGNIFICANCE, TYPO_SIGNIFICANCE)
from kitsune.wiki.events import (
    ReadyRevisionEvent, ApproveRevisionInLocaleEvent)
from kitsune.wiki.models import Revision
from kitsune.wiki.tests import (
    DocumentFactory, RevisionFactory, ApprovedRevisionFactory, TestCaseBase)


def _assert_ready_mail(mail):
    assert 'ready for localization' in mail.subject


def _assert_approved_mail(mail):
    assert 'new approved revision' in mail.subject


def _assert_creator_mail(mail):
    assert mail.subject.startswith('Your revision has been approved')


def _set_up_ready_watcher():
    """Make a user who watches for revision readiness."""
    ready_watcher = UserFactory(email='ready@example.com')
    ReadyRevisionEvent.notify(ready_watcher)
    return ready_watcher


class ReviewTests(TestCaseBase):
    """Tests for notifications sent during revision review"""

    def setUp(self):
        """Have a user watch for revision approval. Log in."""
        self.approved_watcher = UserFactory(email='approved@example.com')
        ApproveRevisionInLocaleEvent.notify(self.approved_watcher,
                                            locale='en-US')
        approver = UserFactory()
        add_permission(approver, Revision, 'review_revision')
        add_permission(approver, Revision, 'mark_ready_for_l10n')
        self.client.login(username=approver.username, password='testpass')

    def _review_revision(self, is_approved=True, is_ready=False, significance=SIGNIFICANCES[0][0],
                         r=None, comment=None, **kwargs):
        """Make a revision, and approve or reject it through the view."""
        if not r:
            r = RevisionFactory(
                is_approved=False,
                is_ready_for_localization=False,
                significance=significance,
                **kwargs)

        # Figure out POST data:
        data = {'comment': 'đSome comment'}
        if is_approved:
            data['approve'] = 'Approve Revision'
            data['significance'] = significance
            if is_ready:
                data['is_ready_for_localization'] = 'on'
            if comment:
                data['comment'] = comment
        else:
            data['reject'] = 'Reject Revision'

        url = reverse('wiki.review_revision', locale=r.document.locale,
                      args=[r.document.slug, r.id])
        response = self.client.post(url, data)

        eq_(302, response.status_code)

    def test_ready(self):
        """Show that a ready(-and-approved) rev mails Ready watchers a Ready
        notification and Approved watchers an Approved one."""
        _set_up_ready_watcher()
        self._review_revision(is_ready=True, significance=MEDIUM_SIGNIFICANCE)
        # 1 mail to each watcher, 1 to the creator, and one to the reviewer
        eq_(4, len(mail.outbox))
        _assert_ready_mail(mail.outbox[0])
        _assert_approved_mail(mail.outbox[1])
        _assert_creator_mail(mail.outbox[2])

    def test_product_specific_ready(self):
        """Verify product-specific ready for review notifications."""
        # Add an all products in 'es' watcher and a Firefox OS in 'es'
        # watcher.
        ApproveRevisionInLocaleEvent.notify(UserFactory(), locale='es')
        ApproveRevisionInLocaleEvent.notify(
            UserFactory(), product='firefox-os', locale='es')

        # Create an 'es' document for Firefox
        parent = DocumentFactory()
        doc = DocumentFactory(parent=parent, locale='es')
        parent.products.add(ProductFactory(slug='firefox'))

        # Review a revision. There should be 3 new emails:
        # 1 to the creator, 1 to the reviewer and 1 to the 'es' watcher.
        self._review_revision(
            document=doc, is_ready=True, significance=MEDIUM_SIGNIFICANCE)
        eq_(3, len(mail.outbox))
        _assert_approved_mail(mail.outbox[0])
        _assert_creator_mail(mail.outbox[1])

        # Add firefox-os to the document's products and review a new revision.
        # There should be 4 new emails now (the same 3 from before plus one
        # for the firefox-os watcher).
        parent.products.add(ProductFactory(slug='firefox-os'))
        self._review_revision(
            document=doc, is_ready=True, significance=MEDIUM_SIGNIFICANCE)
        eq_(7, len(mail.outbox))
        _assert_approved_mail(mail.outbox[3])
        _assert_approved_mail(mail.outbox[4])
        _assert_creator_mail(mail.outbox[5])

        # Add a Firefox watcher. This time there should be 5 new emails.
        ApproveRevisionInLocaleEvent.notify(
            UserFactory(), product='firefox', locale='es')
        self._review_revision(
            document=doc, is_ready=True, significance=MEDIUM_SIGNIFICANCE)
        eq_(12, len(mail.outbox))

    def test_typo_significance_ignore(self):
        # Create the first approved revision for the document. This one will
        # always have MAJOR_SIGNIFICANCE.
        r = RevisionFactory(is_approved=True)

        # Then, set up a watcher and create a TYPO_SIGNIFICANCE revision.
        _set_up_ready_watcher()
        self._review_revision(is_ready=True, document=r.document,
                              significance=TYPO_SIGNIFICANCE)
        # This is the same as test_ready, except we miss 1 mail, that is the
        # localization mail.
        eq_(3, len(mail.outbox))

    def test_approved(self):
        """Show that an approved rev mails Ready watchers nothing and Approved
        watchers an Approved notification."""
        _set_up_ready_watcher()
        self._review_revision(is_ready=False)
        # 1 mail to Approved watcher, 1 to creator, 1 for reviewer
        eq_(3, len(mail.outbox))
        assert 'new approved revision' in mail.outbox[0].subject
        assert 'Your revision has been approved' in mail.outbox[1].subject

    def test_based_on_approved(self):
        u1 = UserFactory()
        r1 = RevisionFactory(is_approved=False, creator=u1, is_ready_for_localization=False)
        u2 = UserFactory()
        r2 = RevisionFactory(
            document=r1.document,
            based_on=r1,
            is_approved=False,
            creator=u2,
            is_ready_for_localization=False)
        eq_(0, len(mail.outbox))
        self._review_revision(r=r2)
        # 1 mail for each watcher, 1 for creator, and one for reviewer.
        eq_(4, len(mail.outbox))
        assert 'has a new approved revision' in mail.outbox[0].subject
        assert 'Your revision has been approved' in mail.outbox[1].subject
        assert 'Your revision has been approved' in mail.outbox[2].subject
        assert 'A revision you contributed to has' in mail.outbox[3].subject

    def test_neither(self):
        """Show that neither an Approved nor a Ready mail is sent if a rev is
        rejected."""
        _set_up_ready_watcher()
        self._review_revision(is_approved=False)
        eq_(2, len(mail.outbox))  # 1 mail to creator, one to the reviewer.
        assert mail.outbox[0].subject.startswith(
            'Your revision has been reviewed')

    def test_user_watching_both(self):
        """If a single person is watching ready and approved revisions and a
        revision becomes ready, send only the readiness email, not the approval
        one."""
        # Have the Approved watcher watch Ready as well:
        ReadyRevisionEvent.notify(self.approved_watcher)

        self._review_revision(is_ready=True, significance=MEDIUM_SIGNIFICANCE)
        # 1 mail to watcher, 1 to creator, 1 to reviewer
        eq_(3, len(mail.outbox))
        _assert_ready_mail(mail.outbox[0])
        _assert_creator_mail(mail.outbox[1])

    def test_new_lines_in_review_message(self):
        """Test that newlines in a review message are properly displayed."""
        _set_up_ready_watcher()
        self._review_revision(comment='foo\n\nbar\nbaz')
        msg = mail.outbox[1].alternatives[0][0]
        assert 'foo</p>' in msg
        assert 'bar<br>baz</p>' in msg

    def test_first_approved_revision_has_major_significance(self):
        """The 1st approved revision of a document has MAJOR_SIGNIFICANCE."""
        self._review_revision(significance=MEDIUM_SIGNIFICANCE)
        r = Revision.objects.get()

        # Even though MEDIUM_SIGNIFICANCE was POSTed, the revision will be set
        # to MAJOR_SIGNIFICANCE.
        eq_(MAJOR_SIGNIFICANCE, r.significance)


class ReadyForL10nTests(TestCaseBase):
    """Tests for notifications sent during ready for l10n"""

    def setUp(self):
        """Have a user watch for revision approval. Log in."""
        self.ready_watcher = UserFactory(email='approved@example.com')
        ReadyRevisionEvent.notify(self.ready_watcher)

        readyer = UserFactory()
        add_permission(readyer, Revision, 'mark_ready_for_l10n')
        self.client.login(username=readyer.username, password='testpass')

    def _mark_as_ready_revision(self, doc=None):
        """Make a revision, and approve or reject it through the view."""
        if doc is None:
            doc = DocumentFactory()

        r = ApprovedRevisionFactory(
            is_ready_for_localization=False,
            significance=MEDIUM_SIGNIFICANCE,
            document=doc)

        # Figure out POST data:
        data = {'comment': 'something'}

        response = post(self.client,
                        'wiki.mark_ready_for_l10n_revision',
                        data,
                        args=[r.document.slug, r.id])
        eq_(200, response.status_code)

    def test_ready(self):
        """Show that a ready(-and-approved) rev mails Ready watchers a Ready
        notification and Approved watchers an Approved one."""
        _set_up_ready_watcher()
        self._mark_as_ready_revision()
        eq_(2, len(mail.outbox))  # 1 mail to each watcher, none to marker
        _assert_ready_mail(mail.outbox[0])
        _assert_ready_mail(mail.outbox[1])

    def test_product_specific_ready(self):
        """Verify product-specific ready for l10n notifications."""
        # Add a Firefox OS watcher.
        ReadyRevisionEvent.notify(UserFactory(), product='firefox-os')

        # Create a document for Firefox
        doc = DocumentFactory()
        doc.products.add(ProductFactory(slug='firefox'))

        # Mark a revision a ready for L10n. There should be only one email
        # to the watcher created in setUp.
        self._mark_as_ready_revision(doc=doc)
        eq_(1, len(mail.outbox))
        _assert_ready_mail(mail.outbox[0])

        # Add firefox-os to the document's products. Mark as ready for l10n,
        # and there should be two new emails.
        doc.products.add(ProductFactory(slug='firefox-os'))
        self._mark_as_ready_revision(doc=doc)
        eq_(3, len(mail.outbox))
        _assert_ready_mail(mail.outbox[1])
        _assert_ready_mail(mail.outbox[2])

        # Add a Firefox watcher, mark as ready for l10n, and there should
        # be three new emails.
        ReadyRevisionEvent.notify(UserFactory(), product='firefox')
        self._mark_as_ready_revision(doc=doc)
        eq_(6, len(mail.outbox))
