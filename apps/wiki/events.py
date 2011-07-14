import difflib
import logging

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMessage
from django.template import Context, loader

from bleach import clean
from tidings.events import InstanceEvent, Event, EventUnion
from tower import ugettext as _
from wikimarkup.parser import ALLOWED_TAGS, ALLOWED_ATTRIBUTES

from sumo.urlresolvers import reverse
from users.models import Profile
from wiki.models import Document


log = logging.getLogger('k.wiki.events')


def context_dict(revision):
    """Return a dict that fills in the blanks in KB notification templates."""
    document = revision.document
    if revision.document.current_revision is not None:
        fromfile = u'[%s] %s #%s' % (revision.document.locale,
                                     revision.document.title,
                                     revision.document.current_revision.id)
        tofile = u'[%s] %s #%s' % (revision.document.locale,
                                   revision.document.title,
                                   revision.id)

        diff = clean(u''.join(difflib.unified_diff(
                                 revision.document.current_revision.\
                                    content.splitlines(1),
                                 revision.content.splitlines(1),
                                 fromfile=fromfile, tofile=tofile)),
                    ALLOWED_TAGS, ALLOWED_ATTRIBUTES)
    else:
        diff = ''  # No based_on, so diff wouldn't make sense.

    return {
        'document_title': document.title,
        'creator': revision.creator,
        'host': Site.objects.get_current().domain,
        'diff': diff,
        'fulltext': clean(revision.content, ALLOWED_TAGS, ALLOWED_ATTRIBUTES)}


def notification_mails(revision, subject, template, url, users_and_watches):
    """Return EmailMessages in the KB's standard notification mail format."""
    document = revision.document
    subject = subject.format(title=document.title, creator=revision.creator,
                             locale=document.locale)
    t = loader.get_template(template)
    c = context_dict(revision)
    mail = EmailMessage(subject, '', settings.TIDINGS_FROM_ADDRESS)

    for u, w in users_and_watches:
        c['watch'] = w[0]  # TODO: Expose all watches.
        c['url'] = url
        mail.to = [u.email]
        mail.body = t.render(Context(c))
        yield mail


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
        subject = _(u'{title} was edited by {creator}')
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
    # Our event_type suffices to limit our scope, so we don't bother setting
    # content_type.
    event_type = 'reviewable wiki in locale'

    def _mails(self, users_and_watches):
        revision = self.revision
        document = revision.document
        log.debug('Sending ready for review email for revision (id=%s)' %
                  revision.id)
        subject = _(u'{title} is ready for review ({creator})')
        url = reverse('wiki.review_revision',
                      locale=document.locale,
                      args=[document.slug,
                      revision.id])
        return notification_mails(revision, subject,
                                  'wiki/email/ready_for_review.ltxt', url,
                                  users_and_watches)


class ReadyRevisionEvent(_RevisionConstructor, Event):
    """Event fed to a union when a (en-US) revision becomes ready for l10n

    Note that no diff is sent, only a fulltext of the revision.

    """
    event_type = 'ready wiki'

    def _mails(self, users_and_watches):
        """Send readiness mails.

        """
        revision = self.revision
        document = revision.document
        revision.is_ready_for_localization
        log.debug('Sending ready notifications for revision (id=%s)' %
                  revision.id)
        ready_subject = _(
            u'{title} has a revision ready for localization').format(
                title=document.title,
                creator=revision.creator,
                locale=document.locale)

        ready_template = loader.get_template(
                                'wiki/email/ready_for_l10n_existing.ltxt')

        c = context_dict(revision)
        for user, watches in users_and_watches:
            c['watch'] = watches[0]  # TODO: Expose all watches.

            try:
                profile = user.profile
            except Profile.DoesNotExist:
                locale = settings.WIKI_DEFAULT_LANGUAGE
            else:
                locale = profile.locale
            c['url'] = reverse('wiki.translate',
                               locale=locale,
                               args=[document.slug])
            yield EmailMessage(ready_subject,
                               ready_template.render(Context(c)),
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
        ready_subject, approved_subject = [s.format(
            title=document.title,
            reviewer=revision.reviewer.username,
            locale=document.locale) for s in
                [_(u'{title} has a revision ready for localization'),
                 _(u'{title} ({locale}) has a new approved revision '
                    '({reviewer})')]]
        ready_template = loader.get_template('wiki/email/ready_for_l10n.ltxt')
        approved_template = loader.get_template('wiki/email/approved.ltxt')
        approved_url = reverse('wiki.document',
                               locale=document.locale,
                               args=[document.slug])
        c = context_dict(revision)
        for user, watches in users_and_watches:
            c['watch'] = watches[0]  # TODO: Expose all watches.
            if (is_ready and
                ReadyRevisionEvent.event_type in
                    (w.event_type for w in watches)):
                # We should send a "ready" mail.
                try:
                    profile = user.profile
                except Profile.DoesNotExist:
                    locale = settings.WIKI_DEFAULT_LANGUAGE
                else:
                    locale = profile.locale
                c['url'] = reverse('wiki.translate',
                                   locale=locale,
                                   args=[document.slug])
                yield EmailMessage(ready_subject,
                                   ready_template.render(Context(c)),
                                   settings.TIDINGS_FROM_ADDRESS,
                                   [user.email])
            else:
                # Send an "approved" mail:
                c['url'] = approved_url
                yield EmailMessage(approved_subject,
                                   approved_template.render(Context(c)),
                                   settings.TIDINGS_FROM_ADDRESS,
                                   [user.email])
