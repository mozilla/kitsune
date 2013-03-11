import difflib
import logging

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse as django_reverse
from django.template import Context, loader

from bleach import clean
from tidings.events import InstanceEvent, Event, EventUnion
from tower import ugettext as _
from tower import ugettext_lazy as _lazy
from wikimarkup.parser import ALLOWED_TAGS, ALLOWED_ATTRIBUTES

from sumo import email_utils
from sumo.urlresolvers import reverse
from users.models import Profile
from wiki.models import Document


log = logging.getLogger('k.wiki.events')


def context_dict(revision, ready_for_l10n=False, revision_approved=False):
    """Return a dict that fills in the blanks in KB notification templates."""
    document = revision.document
    diff = ''
    l10n = revision.document.revisions.filter(is_ready_for_localization=True)
    approved = revision.document.revisions.filter(is_approved=True)
    if ready_for_l10n and l10n.count() > 1:
        fromfile = u'[%s] %s #%s' % (revision.document.locale,
                                     revision.document.title,
                                     l10n.order_by('-created')[1].id)
        tofile = u'[%s] %s #%s' % (revision.document.locale,
                                   revision.document.title,
                                   revision.id)

        diff = clean(
            u''.join(
                difflib.unified_diff(
                    l10n.order_by('-created')[1].content.splitlines(1),
                    revision.content.splitlines(1),
                    fromfile=fromfile, tofile=tofile)
                ),
            ALLOWED_TAGS, ALLOWED_ATTRIBUTES)
    elif revision_approved and approved.count() > 1:
        doc = revision.document
        approved_rev = approved.order_by('-created')[1]

        fromfile = u'[%s] %s #%s' % (doc.locale, doc.title, approved_rev.id)
        tofile = u'[%s] %s #%s' % (doc.locale, doc.title, revision.id)

        diff = clean(
            u''.join(
                difflib.unified_diff(
                    approved_rev.content.splitlines(1),
                    revision.content.splitlines(1),
                    fromfile=fromfile, tofile=tofile)
                ),
            ALLOWED_TAGS, ALLOWED_ATTRIBUTES)
    elif revision.document.current_revision is not None:
        fromfile = u'[%s] %s #%s' % (revision.document.locale,
                                     revision.document.title,
                                     revision.document.current_revision.id)
        tofile = u'[%s] %s #%s' % (revision.document.locale,
                                   revision.document.title,
                                   revision.id)

        diff = clean(
            u''.join(
                difflib.unified_diff(
                    revision.document.current_revision.content.splitlines(1),
                    revision.content.splitlines(1),
                    fromfile=fromfile, tofile=tofile)
                ),
            ALLOWED_TAGS, ALLOWED_ATTRIBUTES)

    return {
        'document_title': document.title,
        'creator': revision.creator,
        'host': Site.objects.get_current().domain,
        'diff': diff,
        'summary': clean(revision.summary, ALLOWED_TAGS, ALLOWED_ATTRIBUTES),
        'fulltext': clean(revision.content, ALLOWED_TAGS, ALLOWED_ATTRIBUTES),
    }


def notification_mails(revision, subject, template, url, users_and_watches):
    """Return EmailMessages in the KB's standard notification mail format."""
    document = revision.document

    for u, w in users_and_watches:
        if hasattr(u, 'profile'):
            locale = u.profile.locale
        else:
            locale = document.locale

        with email_utils.uselocale(locale):
            c = context_dict(revision)
            # TODO: Expose all watches
            c['watch'] = w[0]
            c['url'] = url

            subject = subject.format(title=document.title,
                                     creator=revision.creator,
                                     locale=document.locale)
            msg = email_utils.render_email(template, c)

        yield EmailMessage(subject,
                           msg,
                           settings.TIDINGS_FROM_ADDRESS,
                           [u.email])


class EditDocumentEvent(InstanceEvent):
    """Event fired when a certain document is edited"""
    event_type = 'wiki edit document'
    content_type = Document

    def __init__(self, revision):
        super(EditDocumentEvent, self).__init__(revision.document)
        self.revision = revision

    def _mails(self, users_and_watches):
        document = self.revision.document
        log.debug('Sending edited notification email for document (id=%s)' %
                  document.id)

        subject = _lazy(u'{title} was edited by {creator}')
        url = reverse('wiki.document_revisions', locale=document.locale,
                      args=[document.slug])
        return notification_mails(self.revision, subject,
                                  'wiki/email/edited.ltxt', url,
                                  users_and_watches)


class _RevisionConstructor(object):
    """An event that receives a revision when constructed"""
    def __init__(self, revision):
        super(_RevisionConstructor, self).__init__()
        self.revision = revision


class _LocaleFilter(object):
    """An event that receives a revision when constructed and filters according
    to that revision's document's locale"""
    filters = set(['locale'])

    # notify(), stop_notifying(), and is_notifying() take...
    # (user_or_email, locale=some_locale)

    def _users_watching(self, **kwargs):
        return self._users_watching_by_filter(
            locale=self.revision.document.locale, **kwargs)


class ReviewableRevisionInLocaleEvent(_RevisionConstructor,
                                      _LocaleFilter,
                                      Event):
    """Event fired when any revision in a certain locale is ready for review"""
    # Our event_type suffices to limit our scope, so we don't bother
    # setting content_type.
    event_type = 'reviewable wiki in locale'

    def _mails(self, users_and_watches):
        revision = self.revision
        document = revision.document
        log.debug('Sending ready for review email for revision (id=%s)' %
                  revision.id)
        subject = _lazy(u'{title} is ready for review ({creator})')
        url = reverse('wiki.review_revision',
                      locale=document.locale,
                      args=[document.slug,
                      revision.id])
        return notification_mails(revision, subject,
                                  'wiki/email/ready_for_review.ltxt', url,
                                  users_and_watches)


class ReadyRevisionEvent(_RevisionConstructor, Event):
    """Event fed to a union when a (en-US) revision becomes ready for l10n
    """
    event_type = 'ready wiki'

    def _mails(self, users_and_watches):
        """Send readiness mails.

        """
        revision = self.revision
        document = revision.document
        log.debug('Sending ready notifications for revision (id=%s)' %
                  revision.id)

        for user, watches in users_and_watches:
            if hasattr(user, 'profile'):
                locale = user.profile.locale
            else:
                locale = document.locale

            with email_utils.uselocale(locale):
                subject = _(u'{title} has a revision ready for '
                            'localization').format(title=document.title)
                template = 'wiki/email/ready_for_l10n.ltxt'

                c = context_dict(revision, ready_for_l10n=True)
                # TODO: Expose all watches
                c['watch'] = watches[0]
                c['url'] = django_reverse('wiki.select_locale',
                                          args=[document.slug])

                msg = email_utils.render_email(template, c)

            yield EmailMessage(subject,
                               msg,
                               settings.TIDINGS_FROM_ADDRESS,
                               [user.email])


class ApproveRevisionInLocaleEvent(_RevisionConstructor, _LocaleFilter, Event):
    """Event fed to a union when any revision in a certain locale is approved

    Not intended to be fired individually

    """
    # No other content types have a concept of approval, so we don't bother
    # setting content_type.
    event_type = 'approved wiki in locale'


class ApprovedOrReadyUnion(EventUnion):
    """Event union fired when a revision is approved and also possibly ready

    Unioned events must have a `revision` attr.

    """
    def __init__(self, *args, **kwargs):
        super(ApprovedOrReadyUnion, self).__init__(*args, **kwargs)
        self._revision = self.events[0].revision

    def _mails(self, users_and_watches):
        """Send approval or readiness mails, as appropriate.

        If a given user is watching the Ready event and the revision
        is in fact ready, say so. Otherwise, just send the Approval
        email.

        """
        revision = self._revision
        document = revision.document
        is_ready = revision.is_ready_for_localization
        log.debug('Sending approved/ready notifications for revision (id=%s)' %
                  revision.id)

        for user, watches in users_and_watches:
            # Figure out the locale to use for l10n.
            if hasattr(user, 'profile'):
                locale = user.profile.locale
            else:
                locale = document.locale

            # Localize the subject and message with the appropriate
            # context.
            with email_utils.uselocale(locale):
                if (is_ready and
                    ReadyRevisionEvent.event_type in
                    (w.event_type for w in watches)):
                    c = context_dict(revision, ready_for_l10n=True)
                    # TODO: Expose all watches
                    c['watch'] = watches[0]
                    c['url'] = django_reverse('wiki.select_locale',
                                              args=[document.slug])

                    subject = _(u'{title} has a revision ready for '
                                'localization')
                    template = 'wiki/email/ready_for_l10n.ltxt'

                else:
                    c = context_dict(revision, revision_approved=True)
                    approved_url = reverse('wiki.document',
                                           locale=document.locale,
                                           args=[document.slug])

                    c['url'] = approved_url
                    # TODO: Expose all watches.
                    c['watch'] = watches[0]
                    c['reviewer'] = revision.reviewer.username

                    subject = _(u'{title} ({locale}) has a new approved '
                                'revision ({reviewer})')
                    template = 'wiki/email/approved.ltxt'

                subject = subject.format(
                    title=document.title,
                    reviewer=revision.reviewer.username,
                    locale=document.locale)
                msg = email_utils.render_email(template, c)

            yield EmailMessage(subject,
                               msg,
                               settings.TIDINGS_FROM_ADDRESS,
                               [user.email])
