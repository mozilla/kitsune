# Pruned and mnodified version of django-badger/badger/models.py
# https://github.com/mozilla/django-badger/blob/master/badger/models.py

import re

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.urls import reverse

from kitsune.kbadge.signals import badge_will_be_awarded, badge_was_awarded


IMG_MAX_SIZE = getattr(settings, "BADGER_IMG_MAX_SIZE", (256, 256))

MK_UPLOAD_TMPL = "%(base)s/%(h1)s/%(h2)s/%(hash)s_%(field_fn)s_%(now)s_%(rand)04d.%(ext)s"

DEFAULT_HTTP_PROTOCOL = getattr(settings, "DEFAULT_HTTP_PROTOCOL", "http")


def _document_django_model(cls):
    """Adds meta fields to the docstring for better autodoccing"""
    fields = cls._meta.fields
    doc = cls.__doc__

    if not doc.endswith("\n\n"):
        doc = doc + "\n\n"

    for f in fields:
        doc = doc + "    :arg {0}:\n".format(f.name)

    cls.__doc__ = doc
    return cls


# Taken from http://stackoverflow.com/a/4019144
def slugify(txt):
    """A custom version of slugify that retains non-ascii characters. The
    purpose of this function in the application is to make URLs more readable
    in a browser, so there are some added heuristics to retain as much of the
    title meaning as possible while excluding characters that are troublesome
    to read in URLs. For example, question marks will be seen in the browser
    URL as %3F and are thereful unreadable. Although non-ascii characters will
    also be hex-encoded in the raw URL, most browsers will display them as
    human-readable glyphs in the address bar -- those should be kept in the
    slug."""
    # remove trailing whitespace
    txt = txt.strip()
    # remove spaces before and after dashes
    txt = re.sub(r"\s*-\s*", "-", txt, re.UNICODE)
    # replace remaining spaces with dashes
    txt = re.sub(r"[\s/]", "-", txt, re.UNICODE)
    # replace colons between numbers with dashes
    txt = re.sub(r"(\d):(\d)", r"\1-\2", txt, re.UNICODE)
    # replace double quotes with single quotes
    txt = re.sub('"', "'", txt, re.UNICODE)
    # remove some characters altogether
    txt = re.sub(r"[?,:!@#~`+=$%^&\\*()\[\]{}<>]", "", txt, re.UNICODE)
    return txt


def get_permissions_for(self, user):
    """Mixin method to collect permissions for a model instance"""
    pre = "allows_"
    pre_len = len(pre)
    methods = (m for m in dir(self) if m.startswith(pre))
    perms = dict((m[pre_len:], getattr(self, m)(user)) for m in methods)
    return perms


class SearchManagerMixin(object):
    """Quick & dirty manager mixin for search"""

    # See: http://www.julienphalip.com/blog/2008/08/16/adding-search-django-site-snap/
    def _normalize_query(
        self,
        query_string,
        findterms=re.compile(r'"([^"]+)"|(\S+)').findall,
        normspace=re.compile(r"\s{2,}").sub,
    ):
        """
        Splits the query string in invidual keywords, getting rid of unecessary spaces
        and grouping quoted words together.
        Example::

            foo._normalize_query('  some random  words "with   quotes  " and   spaces')
            ['some', 'random', 'words', 'with quotes', 'and', 'spaces']

        """
        return [normspace(" ", (t[0] or t[1]).strip()) for t in findterms(query_string)]

    # See: http://www.julienphalip.com/blog/2008/08/16/adding-search-django-site-snap/
    def _get_query(self, query_string, search_fields):
        """
        Returns a query, that is a combination of Q objects. That
        combination aims to search keywords within a model by testing
        the given search fields.

        """
        query = None  # Query to search for every search term
        terms = self._normalize_query(query_string)
        for term in terms:
            or_query = None  # Query to search for a given term in each field
            for field_name in search_fields:
                q = Q(**{"%s__icontains" % field_name: term})
                if or_query is None:
                    or_query = q
                else:
                    or_query = or_query | q
            if query is None:
                query = or_query
            else:
                query = query & or_query
        return query

    def search(self, query_string, sort="title"):
        """Quick and dirty keyword search on submissions"""
        # TODO: Someday, replace this with something like Sphinx or another real
        # search engine
        strip_qs = query_string.strip()
        if not strip_qs:
            return self.all_sorted(sort).order_by("-modified")
        else:
            query = self._get_query(strip_qs, self.search_fields)
            return self.all_sorted(sort).filter(query).order_by("-modified")

    def all_sorted(self, sort=None):
        """Apply to .all() one of the sort orders supported for views"""
        queryset = self.all()
        if sort == "title":
            return queryset.order_by("title")
        else:
            return queryset.order_by("-created")


class BadgeException(Exception):
    """General Badger model exception"""


class BadgeException(BadgeException):
    """Badge model exception"""


class BadgeAwardNotAllowedException(BadgeException):
    """Attempt to award a badge not allowed."""


class BadgeAlreadyAwardedException(BadgeException):
    """Attempt to award a unique badge twice."""


class BadgeDeferredAwardManagementNotAllowedException(BadgeException):
    """Attempt to manage deferred awards not allowed."""


class BadgeManager(models.Manager, SearchManagerMixin):
    """Manager for Badge model objects"""

    search_fields = (
        "title",
        "slug",
        "description",
    )

    def allows_add_by(self, user):
        if user.is_anonymous:
            return False
        if getattr(settings, "BADGER_ALLOW_ADD_BY_ANYONE", False):
            return True
        if user.has_perm("badger.add_badge"):
            return True
        return False

    def allows_grant_by(self, user):
        if user.is_anonymous:
            return False
        if user.has_perm("badger.grant_deferredaward"):
            return True
        return False


@_document_django_model
class Badge(models.Model):
    """Representation of a badge"""

    objects = BadgeManager()

    title = models.CharField(
        max_length=255, blank=False, unique=True, help_text="Short, descriptive title"
    )
    slug = models.SlugField(
        blank=False, unique=True, help_text="Very short name, for use in URLs and links",
    )
    description = models.TextField(
        blank=True, help_text="Longer description of the badge and its criteria"
    )
    image = models.ImageField(
        blank=True,
        null=True,
        upload_to=settings.BADGE_IMAGE_PATH,
        help_text="Must be square. Recommended 256x256.",
    )
    # TODO: Rename? Eventually we'll want a globally-unique badge. That is, one
    # unique award for one person for the whole site.
    unique = models.BooleanField(
        default=True, help_text=("Should awards of this badge be limited to one-per-person?"),
    )

    creator = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, blank=False)
    modified = models.DateTimeField(auto_now=True, blank=False)

    class Meta:
        db_table = "badger_badge"
        unique_together = ("title", "slug")
        ordering = ["-modified", "-created"]

    get_permissions_for = get_permissions_for

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("kbadge.badge_detail", args=(self.slug,))

    def get_upload_meta(self):
        return ("badge", self.slug)

    def save(self, **kwargs):
        """Save the submission, updating slug and screenshot thumbnails"""
        if not self.slug:
            self.slug = slugify(self.title)

        super(Badge, self).save(**kwargs)

    def delete(self, **kwargs):
        """Make sure deletes cascade to awards"""
        self.award_set.all().delete()
        super(Badge, self).delete(**kwargs)

    def allows_detail_by(self, user):
        # TODO: Need some logic here, someday.
        return True

    def allows_edit_by(self, user):
        if user.is_anonymous:
            return False
        if user.has_perm("badger.change_badge"):
            return True
        if user == self.creator:
            return True
        return False

    def allows_delete_by(self, user):
        if user.is_anonymous:
            return False
        if user.has_perm("badger.change_badge"):
            return True
        if user == self.creator:
            return True
        return False

    def allows_award_to(self, user):
        """Is award_to() allowed for this user?"""
        if user is None:
            return True
        if user.is_anonymous:
            return False
        if user.is_staff or user.is_superuser:
            return True
        if user == self.creator:
            return True

        # TODO: List of delegates for whom awarding is allowed

        return False

    def award_to(
        self, awardee=None, email=None, awarder=None, description="", raise_already_awarded=False,
    ):
        """Award this badge to the awardee on the awarder's behalf"""
        # If no awarder given, assume this is on the badge creator's behalf.
        if not awarder:
            awarder = self.creator

        if not self.allows_award_to(awarder):
            raise BadgeAwardNotAllowedException()

        # If we have an email, but no awardee, try looking up the user.
        if email and not awardee:
            qs = User.objects.filter(email=email)

            if qs:
                awardee = qs.latest("date_joined")

        if self.unique and self.is_awarded_to(awardee):
            if raise_already_awarded:
                raise BadgeAlreadyAwardedException()
            else:
                return Award.objects.filter(user=awardee, badge=self)[0]

        return Award.objects.create(
            user=awardee, badge=self, creator=awarder, description=description
        )

    def is_awarded_to(self, user):
        """Has this badge been awarded to the user?"""
        return Award.objects.filter(user=user, badge=self).count() > 0


class AwardManager(models.Manager):
    def get_query_set(self):
        return super(AwardManager, self).get_query_set().exclude(hidden=True)


@_document_django_model
class Award(models.Model):
    """Representation of a badge awarded to a user"""

    admin_objects = models.Manager()
    objects = AwardManager()

    description = models.TextField(
        blank=True, help_text="Explanation and evidence for the badge award"
    )
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    image = models.ImageField(blank=True, null=True, upload_to=settings.BADGE_IMAGE_PATH)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="award_user")
    creator = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="award_creator", blank=True, null=True
    )
    hidden = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True, blank=False)
    modified = models.DateTimeField(auto_now=True, blank=False)

    get_permissions_for = get_permissions_for

    class Meta:
        db_table = "badger_award"
        ordering = ["-modified", "-created"]

    def __str__(self):
        by = self.creator and (" by %s" % self.creator) or ""
        return "Award of %s to %s%s" % (self.badge, self.user, by)

    def get_absolute_url(self):
        return reverse("kbadge.award_detail", args=(self.badge.slug, self.pk))

    def get_upload_meta(self):
        u = self.user.username
        return ("award/%s/%s/%s" % (u[0], u[1], u), self.badge.slug)

    def allows_detail_by(self, user):
        # TODO: Need some logic here, someday.
        return True

    def allows_delete_by(self, user):
        if user.is_anonymous:
            return False
        if user == self.user:
            return True
        if user == self.creator:
            return True
        if user.has_perm("badger.change_award"):
            return True
        return False

    def save(self, *args, **kwargs):

        # Signals and some bits of logic only happen on a new award.
        is_new = not self.pk

        if is_new:
            # Bail if this is an attempt to double-award a unique badge
            if self.badge.unique and self.badge.is_awarded_to(self.user):
                raise BadgeAlreadyAwardedException()

            # Only fire will-be-awarded signal on a new award.
            badge_will_be_awarded.send(sender=self.__class__, award=self)

        super(Award, self).save(*args, **kwargs)

        if is_new:
            # Only fire was-awarded signal on a new award.
            # TODO: we might not need this as there are no more notifications
            badge_was_awarded.send(sender=self.__class__, award=self)

    def delete(self):
        super(Award, self).delete()
