from django.core import mail

from nose.tools import eq_

from sumo.tests import post
from users.tests import user
from wiki.events import ReadyRevisionEvent, ApproveRevisionInLocaleEvent
from wiki.models import SIGNIFICANCES
from wiki.tests import revision, TestCaseBase


def _assert_ready_mail(mail):
    assert 'ready for localization' in mail.subject


def _assert_approved_mail(mail):
    assert 'new approved revision' in mail.subject


def _assert_creator_mail(mail):
    assert mail.subject.startswith('Your revision has been approved')


def _set_up_ready_watcher():
    """Make a user who watches for revision readiness."""
    ready_watcher = user(email='ready@example.com', save=True)
    ReadyRevisionEvent.notify(ready_watcher)
    return ready_watcher


class ReviewTests(TestCaseBase):
    """Tests for notifications sent during revision review"""
    fixtures = ['users.json']

    def setUp(self):
        """Have a user watch for revision approval. Log in."""
        self.approved_watcher = user(email='approved@example.com', save=True)
        ApproveRevisionInLocaleEvent.notify(self.approved_watcher,
                                            locale='en-US')
        self.client.login(username='admin', password='testpass')

    def _review_revision(self, is_approved=True, is_ready=False):
        """Make a revision, and approve or reject it through the view."""
        r = revision(is_approved=False,
                     is_ready_for_localization=False,
                     save=True)

        # Figure out POST data:
        data = {'comment': ''}
        if is_approved:
            data['approve'] = 'Approve Revision'
            data['significance'] = SIGNIFICANCES[0][0]
            if is_ready:
                data['is_ready_for_localization'] = 'on'
        else:
            data['reject'] = 'Reject Revision'

        response = post(self.client,
                        'wiki.review_revision',
                        data,
                        args=[r.document.slug, r.id])
        eq_(200, response.status_code)

    def test_ready(self):
        """Show that a ready(-and-approved) rev mails Ready watchers a Ready
        notification and Approved watchers an Approved one."""
        _set_up_ready_watcher()
        self._review_revision(is_ready=True)
        eq_(3, len(mail.outbox))  # 1 mail to each watcher, + 1 to creator
        _assert_ready_mail(mail.outbox[0])
        _assert_approved_mail(mail.outbox[1])
        _assert_creator_mail(mail.outbox[2])

    def test_approved(self):
        """Show that an approved rev mails Ready watchers nothing and Approved
        watchers an Approved notification."""
        _set_up_ready_watcher()
        self._review_revision(is_ready=False)
        eq_(2, len(mail.outbox))  # 1 mail to Approved watcher, 1 to creator
        assert 'new approved revision' in mail.outbox[0].subject
        assert 'Your revision has been approved' in mail.outbox[1].subject

    def test_neither(self):
        """Show that neither an Approved nor a Ready mail is sent if a rev is
        rejected."""
        _set_up_ready_watcher()
        self._review_revision(is_approved=False)
        eq_(1, len(mail.outbox))  # 1 mail to creator
        assert mail.outbox[0].subject.startswith(
            'Your revision has been rejected')

    def test_user_watching_both(self):
        """If a single person is watching ready and approved revisions and a
        revision becomes ready, send only the readiness email, not the approval
        one."""
        # Have the Approved watcher watch Ready as well:
        ReadyRevisionEvent.notify(self.approved_watcher)

        self._review_revision(is_ready=True)
        eq_(2, len(mail.outbox))  # 1 mail to watcher, 1 to creator
        _assert_ready_mail(mail.outbox[0])
        _assert_creator_mail(mail.outbox[1])


class ReadyForL10nTests(TestCaseBase):
    """Tests for notifications sent during ready for l10n"""
    fixtures = ['users.json']

    def setUp(self):
        """Have a user watch for revision approval. Log in."""
        self.ready_watcher = user(email='approved@example.com', save=True)
        ReadyRevisionEvent.notify(self.ready_watcher)
        self.client.login(username='admin', password='testpass')

    def _mark_as_ready_revision(self):
        """Make a revision, and approve or reject it through the view."""
        r = revision(is_approved=True,
                     is_ready_for_localization=False,
                     save=True)

        # Figure out POST data:
        data = {}

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
