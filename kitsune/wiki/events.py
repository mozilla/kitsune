import difflib
import logging

from bleach import clean
from django.conf import settings
from django.contrib.sites.models import Site
from django.urls import reverse as django_reverse
from django.utils.translation import gettext_lazy as _lazy
from django.utils.translation import gettext as _
from wikimarkup.parser import ALLOWED_ATTRIBUTES, ALLOWED_TAGS

from kitsune.sumo import email_utils
from kitsune.sumo.templatetags.jinja_helpers import add_utm
from kitsune.sumo.urlresolvers import reverse
from kitsune.tidings.events import Event, EventUnion, InstanceEvent
from kitsune.tidings.utils import hash_to_unsigned
from kitsune.wiki.models import Document

log = logging.getLogger("k.wiki.events")


def get_diff_for(doc, old_rev, new_rev):
    fromfile = "[%s] %s #%s" % (doc.locale, doc.title, old_rev.id)
    tofile = "[%s] %s #%s" % (doc.locale, doc.title, new_rev.id)

    # Get diff
    diff_parts = difflib.unified_diff(
        old_rev.content.splitlines(1),
        new_rev.content.splitlines(1),
        fromfile=fromfile,
        tofile=tofile,
    )

    # Join diff parts
    # XXX this is super goofy
    acc = ""
    for d in diff_parts:
        if isinstance(d, str):
            acc = acc + d
        else:
            acc = acc + d.decode("utf8")

    # Clean output
    return clean(acc, ALLOWED_TAGS, ALLOWED_ATTRIBUTES)


def context_dict(revision, ready_for_l10n=False, revision_approved=False):
    """Return a dict that fills in the blanks in KB notification templates."""
    diff = ""
    l10n = revision.document.revisions.filter(is_ready_for_localization=True)
    approved = revision.document.revisions.filter(is_approved=True)

    if ready_for_l10n and l10n.count() > 1:
        old_rev = l10n.order_by("-created")[1]
        diff = get_diff_for(revision.document, old_rev, revision)
    elif revision_approved and approved.count() > 1:
        old_rev = approved.order_by("-created")[1]
        diff = get_diff_for(revision.document, old_rev, revision)
    elif revision.document.current_revision is not None:
        old_rev = revision.document.current_revision
        diff = get_diff_for(revision.document, old_rev, revision)

    return {
        "document_title": revision.document.title,
        "creator": revision.creator,
        "host": Site.objects.get_current().domain,
        "diff": diff,
        "summary": clean(revision.summary, ALLOWED_TAGS, ALLOWED_ATTRIBUTES),
        "fulltext": clean(revision.content, ALLOWED_TAGS, ALLOWED_ATTRIBUTES),
    }


def filter_by_unrestricted(document, users_and_watches):
    """
    Given a document and an iterable of users and their watches, returns
    a generator yielding only the users that are allowed to view the document.
    """
    for user, watches in users_and_watches:
        if document.is_unrestricted_for(user):
            yield (user, watches)


class EditDocumentEvent(InstanceEvent):
    """Event fired when a certain document is edited"""

    event_type = "wiki edit document"
    content_type = Document

    def __init__(self, revision):
        super(EditDocumentEvent, self).__init__(revision.document)
        self.revision = revision

    def _users_watching(self, **kwargs):
        users_and_watches = super()._users_watching(**kwargs)
        return filter_by_unrestricted(self.instance, users_and_watches)

    def _mails(self, users_and_watches):
        revision = self.revision
        document = revision.document
        log.debug("Sending edited notification email for document (id=%s)" % document.id)

        subject = _lazy("{title} was edited by {creator}")
        url = reverse("wiki.document_revisions", locale=document.locale, args=[document.slug])

        context = context_dict(revision)
        context["revisions_url"] = add_utm(url, "wiki-edit")
        context["locale"] = document.locale
        context["title"] = document.title
        context["creator"] = revision.creator
        context["comment"] = revision.comment

        return email_utils.emails_with_users_and_watches(
            subject=subject,
            text_template="wiki/email/edited.ltxt",
            html_template="wiki/email/edited.html",
            context_vars=context,
            users_and_watches=users_and_watches,
            default_locale=document.locale,
        )

    def serialize(self):
        """
        Serialize this event into a JSON-friendly dictionary.
        """
        return {
            "event": {"module": "kitsune.wiki.events", "class": "EditDocumentEvent"},
            "instance": {
                "module": "kitsune.wiki.models",
                "class": "Revision",
                "id": self.revision.id,
            },
        }


class _RevisionConstructor:
    """An event that receives a revision when constructed"""

    def __init__(self, revision):
        super().__init__()
        self.revision = revision


class _BaseProductFilter:
    """A base class for product filters.

    It adds a _filter_by_product method that filters down a list of
    (user, watches) to only the users watching the products for the
    revision.
    """

    def _filter_by_product(self, all_watchers):
        products = self.revision.document.get_products()
        product_hashes = [hash_to_unsigned(s.slug) for s in products]

        watchers_and_watches = []

        # Weed out the users that have a product filter that isn't one of the
        # document's products.
        for user, watches in all_watchers:
            for watch in watches:
                # Get the product filters for the watch, if any.
                prods = watch.filters.filter(name="product").values_list("value", flat=True)

                # If there are no product filters, they are watching them all.
                if len(prods) == 0:
                    watchers_and_watches.append((user, watches))
                    break

                # Otherwise, check if they are watching any of the document's
                # products.
                for prod in prods:
                    if prod in product_hashes:
                        watchers_and_watches.append((user, watches))
                        break

        return watchers_and_watches


class _ProductFilter(_BaseProductFilter):
    """
    An event filter for events constructed with a revision, that filters
    by restricted visibility and the products of the revision's document.
    """

    filters = {"product"}

    # notify(), stop_notifying(), and is_notifying() take...
    # (user_or_email, product=optional_product)

    def _users_watching(self, **kwargs):
        # Get the users watching any or all products.
        users_and_watches = self._users_watching_by_filter(**kwargs)

        # Weed out restricted users.
        users_and_watches = filter_by_unrestricted(
            self.revision.document,
            users_and_watches,
        )

        # Weed out the users that have a product filter that isn't one of the
        # document's products.
        return self._filter_by_product(users_and_watches)


class _LocaleAndProductFilter(_BaseProductFilter):
    """
    An event filter for events constructed with a revision, that filters
    by restricted visibility, the locale, and the products of the revision's
    document.
    """

    filters = {"locale", "product"}

    # notify(), stop_notifying(), and is_notifying() take...
    # (user_or_email, locale=some_locale, product=optional_product)

    def _users_watching(self, **kwargs):
        locale = self.revision.document.locale

        # Get the users just subscribed to the locale (any and all products).
        users_and_watches = self._users_watching_by_filter(locale=locale, **kwargs)

        # Weed out restricted users.
        users_and_watches = filter_by_unrestricted(
            self.revision.document,
            users_and_watches,
        )

        # Weed out the users that have a product filter that isn't one of the
        # document's products.
        return self._filter_by_product(users_and_watches)


class ReviewableRevisionInLocaleEvent(_RevisionConstructor, _LocaleAndProductFilter, Event):
    """Event fired when any revision in a certain locale is ready for review"""

    # Our event_type suffices to limit our scope, so we don't bother
    # setting content_type.
    event_type = "reviewable wiki in locale"

    def _mails(self, users_and_watches):
        revision = self.revision
        document = revision.document
        log.debug("Sending ready for review email for revision (id=%s)" % revision.id)
        subject = _lazy("{title} is ready for review ({creator})")
        url = reverse(
            "wiki.review_revision",
            locale=document.locale,
            args=[document.slug, revision.id],
        )

        context = context_dict(revision)
        context["revision_url"] = add_utm(url, "wiki-ready-review")
        context["locale"] = document.locale
        context["title"] = document.title
        context["creator"] = revision.creator
        context["comment"] = revision.comment

        users = []
        for u, w in users_and_watches:
            if document.allows(u, "review_revision"):
                users.append((u, w))

        return email_utils.emails_with_users_and_watches(
            subject=subject,
            text_template="wiki/email/ready_for_review.ltxt",
            html_template="wiki/email/ready_for_review.html",
            context_vars=context,
            users_and_watches=users,
            default_locale=document.locale,
        )

    def serialize(self):
        """
        Serialize this event into a JSON-friendly dictionary.
        """
        return {
            "event": {"module": "kitsune.wiki.events", "class": "ReviewableRevisionInLocaleEvent"},
            "instance": {
                "module": "kitsune.wiki.models",
                "class": "Revision",
                "id": self.revision.id,
            },
        }


class ReadyRevisionEvent(_RevisionConstructor, _ProductFilter, Event):
    """Event fired when a revision becomes ready for l10n."""

    event_type = "ready wiki"

    def _mails(self, users_and_watches):
        """Send readiness mails."""
        revision = self.revision
        document = revision.document
        log.debug("Sending ready notifications for revision (id=%s)" % revision.id)

        subject = _lazy("{title} has a revision ready for localization")

        url = django_reverse("wiki.translate", args=[document.slug])

        context = context_dict(revision, ready_for_l10n=True)
        context["l10n_url"] = add_utm(url, "wiki-ready-l10n")
        context["title"] = document.title

        return email_utils.emails_with_users_and_watches(
            subject=subject,
            text_template="wiki/email/ready_for_l10n.ltxt",
            html_template="wiki/email/ready_for_l10n.html",
            context_vars=context,
            users_and_watches=users_and_watches,
            default_locale=document.locale,
        )

    def serialize(self):
        """
        Serialize this event into a JSON-friendly dictionary.
        """
        return {
            "event": {"module": "kitsune.wiki.events", "class": "ReadyRevisionEvent"},
            "instance": {
                "module": "kitsune.wiki.models",
                "class": "Revision",
                "id": self.revision.id,
            },
        }


class ApproveRevisionInLocaleEvent(_RevisionConstructor, _LocaleAndProductFilter, Event):
    """Event fed to a union when any revision in a certain locale is approved

    Not intended to be fired individually

    """

    # No other content types have a concept of approval, so we don't bother
    # setting content_type.
    event_type = "approved wiki in locale"

    def serialize(self):
        """
        Serialize this event into a JSON-friendly dictionary.
        """
        return {
            "event": {"module": "kitsune.wiki.events", "class": "ApproveRevisionInLocaleEvent"},
            "instance": {
                "module": "kitsune.wiki.models",
                "class": "Revision",
                "id": self.revision.id,
            },
        }


class ApprovedOrReadyUnion(EventUnion):
    """
    Event union fired when a revision is approved and also possibly ready for localization.
    """

    def __init__(self, revision):
        self.revision = revision
        events = [ApproveRevisionInLocaleEvent(revision)]
        if revision.is_ready_for_localization:
            events.append(ReadyRevisionEvent(revision))
        super(ApprovedOrReadyUnion, self).__init__(*events)

    def _mails(self, users_and_watches):
        """Send approval or readiness mails, as appropriate.

        If a given user is watching the Ready event and the revision
        is in fact ready, say so. Otherwise, just send the Approval
        email.

        """
        revision = self.revision
        document = revision.document
        is_ready = revision.is_ready_for_localization
        log.debug("Sending approved/ready notifications for revision (id=%s)" % revision.id)

        # Localize the subject and message with the appropriate
        # context. If there is an error, fall back to English.
        @email_utils.safe_translation
        def _make_mail(locale, user, watches):
            if is_ready and ReadyRevisionEvent.event_type in (w.event_type for w in watches):
                c = context_dict(revision, ready_for_l10n=True)
                # TODO: Expose all watches
                c["watch"] = watches[0]

                url = reverse("wiki.translate", args=[document.slug], locale=locale)
                c["l10n_url"] = add_utm(url, "wiki-ready-l10n")

                subject = _("{title} has a revision ready for localization")
                text_template = "wiki/email/ready_for_l10n.ltxt"
                html_template = "wiki/email/ready_for_l10n.html"

            else:
                c = context_dict(revision, revision_approved=True)
                approved_url = reverse(
                    "wiki.document", locale=document.locale, args=[document.slug]
                )

                c["document_url"] = add_utm(approved_url, "wiki-approved")
                # TODO: Expose all watches.
                c["watch"] = watches[0]
                c["reviewer"] = revision.reviewer

                subject = _("{title} ({locale}) has a new approved revision ({reviewer})")
                text_template = "wiki/email/approved.ltxt"
                html_template = "wiki/email/approved.html"

            subject = subject.format(
                title=document.title,
                reviewer=revision.reviewer.username,
                locale=document.locale,
            )

            mail = email_utils.make_mail(
                subject=subject,
                text_template=text_template,
                html_template=html_template,
                context_vars=c,
                from_email=settings.TIDINGS_FROM_ADDRESS,
                to_email=user.email,
            )

            return mail

        for user, watches in users_and_watches:
            # Figure out the locale to use for l10n.
            if hasattr(user, "profile"):
                locale = user.profile.locale
            else:
                locale = document.locale

            yield _make_mail(locale, user, watches)

    def serialize(self):
        """
        Serialize this event into a JSON-friendly dictionary.
        """
        return {
            "event": {"module": "kitsune.wiki.events", "class": "ApprovedOrReadyUnion"},
            "instance": {
                "module": "kitsune.wiki.models",
                "class": "Revision",
                "id": self.revision.id,
            },
        }
