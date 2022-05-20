from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.db import connections, models, router

from .utils import import_from_setting, reverse

ModelBase = import_from_setting("TIDINGS_MODEL_BASE", models.Model)


def multi_raw(query, params, models, model_to_fields):
    """Scoop multiple model instances out of the DB at once, given a query that
    returns all fields of each.

    Return an iterable of sequences of model instances parallel to the
    ``models`` sequence of classes. For example::

        [(<User such-and-such>, <Watch such-and-such>), ...]

    """
    cursor = connections[router.db_for_read(models[0])].cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()

    for row in rows:
        row_iter = iter(row)
        yield [
            model_class(**dict((a, next(row_iter)) for a in model_to_fields[model_class]))
            for model_class in models
        ]


class Watch(ModelBase):
    """The registration of a user's interest in a certain event

    At minimum, specifies an event_type and thereby an
    :class:`~tidings.events.Event` subclass. May also specify a content type
    and/or object ID and, indirectly, any number of
    :class:`WatchFilters <WatchFilter>`.

    """

    #: Key used by an Event to find watches it manages:
    event_type = models.CharField(max_length=30, db_index=True)

    #: Optional reference to a content type:
    content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(db_index=True, null=True)
    content_object = GenericForeignKey("content_type", "object_id")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE
    )

    #: Email stored only in the case of anonymous users:
    email = models.EmailField(db_index=True, null=True, blank=True)

    #: Secret for activating anonymous watch email addresses.
    secret = models.CharField(max_length=10, null=True, blank=True)
    #: Active watches receive notifications, inactive watches don't.
    is_active = models.BooleanField(default=False, db_index=True)

    def __str__(self):
        # TODO: Trace event_type back to find the Event subclass, and ask it
        # how to describe me in English.
        rest = self.content_object or self.content_type or self.object_id
        return "id=%s, type=%s, content_object=%s" % (
            self.pk,
            self.event_type,
            str(rest),
        )

    def activate(self):
        """Enable this watch so it actually fires.

        Return ``self`` to support method chaining.

        """
        self.is_active = True
        return self

    def unsubscribe_url(self):
        """Return the absolute URL to visit to delete me."""
        server_relative = "%s?s=%s" % (
            reverse("tidings.unsubscribe", args=[self.pk]),
            self.secret,
        )
        return "https://%s%s" % (Site.objects.get_current().domain, server_relative)


class WatchFilter(ModelBase):
    """Additional key/value pairs that pare down the scope of a watch"""

    watch = models.ForeignKey(Watch, related_name="filters", on_delete=models.CASCADE)
    name = models.CharField(max_length=20)

    #: Either an int or the hash of an item in a reasonably small set, which is
    #: indicated by the name field. See comments by
    #: :func:`~tidings.utils.hash_to_unsigned()` for more on what is reasonably
    #: small.
    value = models.PositiveIntegerField()

    class Meta(object):
        # There's no particular reason we couldn't allow multiple values for
        # one name to be ORed together, but the API needs a little work
        # (accepting lists passed to notify()) to support that.
        #
        # This ordering makes the index usable for lookups by name.
        unique_together = ("name", "watch")

    def __str__(self):
        return "WatchFilter %s: %s=%s" % (self.pk, self.name, self.value)


class NotificationsMixin(models.Model):
    """Mixin for notifications models that adds watches as a generic relation.

    So we get cascading deletes for free, yay!

    """

    watches = GenericRelation(Watch)

    class Meta(object):
        abstract = True


class EmailUser(AnonymousUser):
    """An anonymous user identified only by email address.

    This is based on Django's AnonymousUser, so you can use the
    ``is_authenticated`` property to tell that this is an anonymous user.
    """

    def __init__(self, email=""):
        self.email = email

    def __str__(self):
        return "Anonymous user <%s>" % self.email

    __repr__ = AnonymousUser.__str__

    def __eq__(self, other):
        return self.email == other.email

    def __ne__(self, other):
        return self.email != other.email

    def __hash__(self):
        return hash(self.email)
