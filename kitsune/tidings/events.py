import random
from smtplib import SMTPException

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.db import models
from django.db.models import Q

from kitsune.tidings.models import EmailUser, Watch, WatchFilter, multi_raw
from kitsune.tidings.tasks import send_emails
from kitsune.tidings.utils import collate, hash_to_unsigned


class ActivationRequestFailed(Exception):
    """Raised when activation request fails, e.g. if email could not be sent"""

    def __init__(self, msgs):
        self.msgs = msgs


def _unique_by_email(users_and_watches):
    """Given a sequence of (User/EmailUser, [Watch, ...]) pairs
    clustered by email address (which is never ''), yield from each
    cluster a single pair like this::

      (User/EmailUser, [Watch, Watch, ...]).

    The User/Email is that of...
    (1) the first incoming pair where the User has an email and is not
        anonymous, or, if there isn't such a user...
    (2) the first pair.

    The list of Watches consists of all those found in the cluster.

    Compares email addresses case-insensitively.

    """

    def ensure_user_has_email(user, cluster_email):
        """Make sure the user in the user-watch pair has an email address.

        The caller guarantees us an email from either the user or the watch. If
        the passed-in user has no email, we return an EmailUser instead having
        the email address from the watch.

        """
        # Some of these cases shouldn't happen, but we're tolerant.
        if not getattr(user, "email", ""):
            user = EmailUser(cluster_email)
        return user

    # TODO: Do this instead with clever SQL that somehow returns just the
    # best row for each email.

    cluster_email = ""  # email of current cluster
    favorite_user = None  # best user in cluster so far
    watches = []  # all watches in cluster
    for u, w in users_and_watches:
        # w always has at least 1 Watch. All the emails are the same.
        row_email = u.email or w[0].email
        if cluster_email.lower() != row_email.lower():
            # Starting a new cluster.
            if cluster_email != "":
                # Ship the favorites from the previous cluster:
                yield (ensure_user_has_email(favorite_user, cluster_email), watches)
            favorite_user, watches = u, []
            cluster_email = row_email
        elif (
            (not favorite_user.email or not u.is_authenticated) and u.email and u.is_authenticated
        ):
            favorite_user = u
        watches.extend(w)
    if favorite_user is not None:
        yield ensure_user_has_email(favorite_user, cluster_email), watches


class Event(object):
    """Abstract base class for events

    An :class:`Event` represents, simply, something that occurs. A
    :class:`~tidings.models.Watch` is a record of someone's interest in a
    certain type of :class:`Event`, distinguished by ``Event.event_type``.

    Fire an Event (``SomeEvent.fire()``) from the code that causes the
    interesting event to occur. Fire it any time the event *might* have
    occurred. The Event will determine whether conditions are right to actually
    send notifications; don't succumb to the temptation to do these tests
    outside the Event, because you'll end up repeating yourself if the event is
    ever fired from more than one place.

    :class:`Event` subclasses can optionally represent a more limited scope of
    interest by populating the ``Watch.content_type`` field and/or adding
    related :class:`~tidings.models.WatchFilter` rows holding name/value pairs,
    the meaning of which is up to each individual subclass. NULL values are
    considered wildcards.
    """

    # event_type = 'hamster modified'  # key for the event_type column
    content_type: models.Model | None = None  # or, for example, Hamster

    #: Possible filter keys, for validation only. For example:
    #: ``set(['color', 'flavor'])``
    filters: set[str] = set()

    def fire(self, exclude=None, delay=True):
        """
        Notify everyone watching the event, either synchronously or asynchronously,
        excluding the users provided by "exclude", which must be a sequence of user
        objects if provided.
        """
        if delay:
            event_info = self.serialize()
            if exclude:
                exclude_user_ids = [user.id for user in exclude]
            else:
                exclude_user_ids = None
            send_emails.delay(event_info, exclude_user_ids=exclude_user_ids)
        else:
            self.send_emails(exclude=exclude)

    def send_emails(self, exclude=None):
        """
        Notify everyone watching the event (build and send emails).

        We are explicit about sending notifications; we don't just key off
        creation signals, because the receiver of a ``post_save`` signal has no
        idea what just changed, so it doesn't know which notifications to send.
        Also, we could easily send mail accidentally: for instance, during
        tests. If we want implicit event firing, we can always register a
        signal handler that calls :meth:`fire()`.

        :arg exclude: A sequence of users or None. If a sequence of users is
          passed in, each of those users will not be notified, though anonymous
          notifications having the same email address may still be sent.
        """
        connection = mail.get_connection(fail_silently=True)
        # Warning: fail_silently swallows errors thrown by the generators, too.
        connection.open()
        for m in self._mails(self._users_watching(exclude=exclude)):
            connection.send_messages([m])

    def serialize(self):
        """
        Serialize this event into a JSON-friendly dictionary. Subclasses must
        implement this method if they want to fire events asynchronously via
        the "send_emails" Celery task. Here's an example:

        def serialize(self):
            return {
                "event": {
                    "module": "kitsune.wiki.events"
                    "class": "ReadyRevisionEvent"
                },
                "instance": {
                    "module": "kitsune.wiki.models",
                    "class": "Revision",
                    "id": self.revision.id
                }
            }

        where the "event" is always required, but the "instance" only if it's
        needed to construct the event.
        """
        raise NotImplementedError

    @classmethod
    def _validate_filters(cls, filters):
        """Raise a TypeError if ``filters`` contains any keys inappropriate to
        this event class."""
        for k in iter(filters.keys()):
            if k not in cls.filters:
                # Mirror "unexpected keyword argument" message:
                raise TypeError("%s got an unsupported filter type '%s'" % (cls.__name__, k))

    def _users_watching_by_filter(self, object_id=None, exclude=None, **filters):
        """Return an iterable of (``User``/:class:`~tidings.models.EmailUser`,
        [:class:`~tidings.models.Watch` objects]) tuples watching the event.

        Of multiple Users/EmailUsers having the same email address, only one is
        returned. Users are favored over EmailUsers so we are sure to be able
        to, for example, include a link to a user profile in the mail.

        The list of :class:`~tidings.models.Watch` objects includes both
        those tied to the given User (if there is a registered user)
        and to any anonymous Watch having the same email address. This
        allows you to include all relevant unsubscribe URLs in a mail,
        for example. It also lets you make decisions in the
        :meth:`~tidings.events.EventUnion._mails()` method of
        :class:`~tidings.events.EventUnion` based on the kinds of
        watches found.

        "Watching the event" means having a Watch whose ``event_type`` is
        ``self.event_type``, whose ``content_type`` is ``self.content_type`` or
        ``NULL``, whose ``object_id`` is ``object_id`` or ``NULL``, and whose
        WatchFilter rows match as follows: each name/value pair given in
        ``filters`` must be matched by a related WatchFilter, or there must be
        no related WatchFilter having that name. If you find yourself wanting
        the lack of a particularly named WatchFilter to scuttle the match, use
        a different event_type instead.

        :arg exclude: A sequence of users or None. If a sequence of users is
          passed in, each of those users will not be notified, though anonymous
          notifications having the same email address may still be sent.

        """
        # I don't think we can use the ORM here, as there's no way to get a
        # second condition (name=whatever) into a left join. However, if we
        # were willing to have 2 subqueries run for every watch row--select
        # {are there any filters with name=x?} and select {is there a filter
        # with name=x and value=y?}--we could do it with extra(). Then we could
        # have EventUnion simply | the QuerySets together, which would avoid
        # having to merge in Python.

        def filter_conditions():
            """Return joins, WHERE conditions, and params to bind to them in
            order to check a notification against all the given filters."""
            # Not a one-liner. You're welcome. :-)
            self._validate_filters(filters)
            joins, wheres, join_params, where_params = [], [], [], []
            for n, (k, v) in enumerate(iter(filters.items())):
                joins.append(
                    "LEFT JOIN tidings_watchfilter f{n} "
                    "ON f{n}.watch_id=w.id "
                    "AND f{n}.name=%s".format(n=n)
                )
                join_params.append(k)
                wheres.append("(f{n}.value=%s " "OR f{n}.value IS NULL)".format(n=n))
                where_params.append(hash_to_unsigned(v))
            return joins, wheres, join_params + where_params

        # Apply watchfilter constraints:
        joins, wheres, params = filter_conditions()

        # Start off with event_type, which is always a constraint. These go in
        # the `wheres` list to guarantee that the AND after the {wheres}
        # substitution in the query is okay.
        wheres.append("w.event_type=%s")
        params.append(self.event_type)

        # Constrain on other 1-to-1 attributes:
        if self.content_type:
            wheres.append("(w.content_type_id IS NULL " "OR w.content_type_id=%s)")
            params.append(ContentType.objects.get_for_model(self.content_type).id)
        if object_id:
            wheres.append("(w.object_id IS NULL OR w.object_id=%s)")
            params.append(object_id)
        if exclude:
            # Don't try excluding unsaved Users:1
            if not all(e.id for e in exclude):
                raise ValueError("Can't exclude an unsaved User.")

            wheres.append("(u.id IS NULL OR u.id NOT IN (%s))" % ", ".join("%s" for e in exclude))
            params.extend(e.id for e in exclude)

        def get_fields(model):
            if hasattr(model._meta, "_fields"):
                # For django versions < 1.6
                return model._meta._fields()
            else:
                # For django versions >= 1.6
                return model._meta.fields

        User = get_user_model()
        model_to_fields = dict(
            (m, [f.get_attname() for f in get_fields(m)]) for m in [User, Watch]
        )
        query_fields = ["u.{0}".format(field) for field in model_to_fields[User]]
        query_fields.extend(["w.{0}".format(field) for field in model_to_fields[Watch]])

        query = (
            "SELECT {fields} "
            "FROM tidings_watch w "
            "LEFT JOIN {user_table} u ON u.id=w.user_id {joins} "
            "WHERE {wheres} "
            "AND (length(w.email)>0 OR length(u.email)>0) "
            "AND w.is_active "
            "ORDER BY u.email DESC, w.email DESC"
        ).format(
            fields=", ".join(query_fields),
            joins=" ".join(joins),
            wheres=" AND ".join(wheres),
            user_table=User._meta.db_table,
        )
        # IIRC, the DESC ordering was something to do with the placement of
        # NULLs. Track this down and explain it.

        # Put watch in a list just for consistency. Once the pairs go through
        # _unique_by_email, watches will be in a list, and EventUnion uses the
        # same function to union already-list-enclosed pairs from individual
        # events.
        return _unique_by_email(
            (u, [w]) for u, w in multi_raw(query, params, [User, Watch], model_to_fields)
        )

    @classmethod
    def _watches_belonging_to_user(cls, user_or_email, object_id=None, **filters):
        """Return a QuerySet of watches having the given user or email, having
        (only) the given filters, and having the event_type and content_type
        attrs of the class.

        Matched Watches may be either confirmed and unconfirmed. They may
        include duplicates if the get-then-create race condition in
        :meth:`notify()` allowed them to be created.

        If you pass an email, it will be matched against only the email
        addresses of anonymous watches. At the moment, the only integration
        point planned between anonymous and registered watches is the claiming
        of anonymous watches of the same email address on user registration
        confirmation.

        If you pass the AnonymousUser, this will return an empty QuerySet.

        """
        # If we have trouble distinguishing subsets and such, we could store a
        # number_of_filters on the Watch.
        cls._validate_filters(filters)

        if isinstance(user_or_email, str):
            user_condition = Q(email=user_or_email)
        elif user_or_email.is_authenticated:
            user_condition = Q(user=user_or_email)
        else:
            return Watch.objects.none()

        # Filter by stuff in the Watch row:
        watches = (
            getattr(Watch, "uncached", Watch.objects)
            .filter(
                user_condition,
                Q(content_type=ContentType.objects.get_for_model(cls.content_type))
                if cls.content_type
                else Q(),
                Q(object_id=object_id) if object_id else Q(),
                event_type=cls.event_type,
            )
            .extra(
                where=[
                    "(SELECT count(*) FROM tidings_watchfilter WHERE "
                    "tidings_watchfilter.watch_id="
                    "tidings_watch.id)=%s"
                ],
                params=[len(filters)],
            )
        )
        # Optimization: If the subselect ends up being slow, store the number
        # of filters in each Watch row or try a GROUP BY.

        # Apply 1-to-many filters:
        for k, v in iter(filters.items()):
            watches = watches.filter(filters__name=k, filters__value=hash_to_unsigned(v))

        return watches

    @classmethod
    # Funny arg name to reserve use of nice ones for filters
    def is_notifying(cls, user_or_email_, object_id=None, **filters):
        """Return whether the user/email is watching this event (either
        active or inactive watches), conditional on meeting the criteria in
        ``filters``.

        Count only watches that match the given filters exactly--not ones which
        match merely a superset of them. This lets callers distinguish between
        watches which overlap in scope. Equivalently, this lets callers check
        whether :meth:`notify()` has been called with these arguments.

        Implementations in subclasses may take different arguments--for
        example, to assume certain filters--though most will probably just use
        this. However, subclasses should clearly document what filters they
        supports and the meaning of each.

        Passing this an ``AnonymousUser`` always returns ``False``. This means
        you can always pass it ``request.user`` in a view and get a sensible
        response.

        """
        return cls._watches_belonging_to_user(
            user_or_email_, object_id=object_id, **filters
        ).exists()

    @classmethod
    def notify(cls, user_or_email_, object_id=None, **filters):
        """Start notifying the given user or email address when this event
        occurs and meets the criteria given in ``filters``.

        Return the created (or the existing matching) Watch so you can call
        :meth:`~tidings.models.Watch.activate()` on it if you're so inclined.

        Implementations in subclasses may take different arguments; see the
        docstring of :meth:`is_notifying()`.

        Send an activation email if an anonymous watch is created and
        :data:`~django.conf.settings.TIDINGS_CONFIRM_ANONYMOUS_WATCHES` is
        ``True``. If the activation request fails, raise a
        ActivationRequestFailed exception.

        Calling :meth:`notify()` twice for an anonymous user will send the
        email each time.

        """
        # A test-for-existence-then-create race condition exists here, but it
        # doesn't matter: de-duplication on fire() and deletion of all matches
        # on stop_notifying() nullify its effects.
        try:
            # Pick 1 if >1 are returned:
            watch = cls._watches_belonging_to_user(user_or_email_, object_id=object_id, **filters)[
                0:1
            ].get()
        except Watch.DoesNotExist:
            create_kwargs = {}
            if cls.content_type:
                create_kwargs["content_type"] = ContentType.objects.get_for_model(cls.content_type)
            create_kwargs["email" if isinstance(user_or_email_, str) else "user"] = user_or_email_
            # Letters that can't be mistaken for other letters or numbers in
            # most fonts, in case people try to type these:
            distinguishable_letters = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRTUVWXYZ"
            secret = "".join(random.choice(distinguishable_letters) for x in range(10))
            # Registered users don't need to confirm, but anonymous users do.
            is_active = "user" in create_kwargs or not settings.TIDINGS_CONFIRM_ANONYMOUS_WATCHES
            if object_id:
                create_kwargs["object_id"] = object_id
            watch = Watch.objects.create(
                secret=secret, is_active=is_active, event_type=cls.event_type, **create_kwargs
            )
            for k, v in iter(filters.items()):
                WatchFilter.objects.create(watch=watch, name=k, value=hash_to_unsigned(v))
        # Send email for inactive watches.
        if not watch.is_active:
            email = watch.user.email if watch.user else watch.email
            message = cls._activation_email(watch, email)
            try:
                message.send()
            except SMTPException as e:
                watch.delete()
                raise ActivationRequestFailed(e.recipients)
        return watch

    @classmethod
    def stop_notifying(cls, user_or_email_, **filters):
        """Delete all watches matching the exact user/email and filters.

        Delete both active and inactive watches. If duplicate watches
        exist due to the get-then-create race condition, delete them all.

        Implementations in subclasses may take different arguments; see the
        docstring of :meth:`is_notifying()`.

        """
        cls._watches_belonging_to_user(user_or_email_, **filters).delete()

    # TODO: If GenericForeignKeys don't give us cascading deletes, make a
    # stop_notifying_all(**filters) or something. It should delete any watch of
    # the class's event_type and content_type and having filters matching each
    # of **filters. Even if there are additional filters on a watch, that watch
    # should still be deleted so we can delete, for example, any watch that
    # references a certain Question instance. To do that, factor such that you
    # can effectively call _watches_belonging_to_user() without it calling
    # extra().

    # Subclasses should implement the following:

    def _mails(self, users_and_watches):
        """Return an iterable yielding an EmailMessage to send to each user.

        :arg users_and_watches: an iterable of (User or EmailUser, [Watches])
            pairs where the first element is the user to send to and the second
            is a list of watches (usually just one) that indicated the
            user's interest in this event

        :meth:`~tidings.utils.emails_with_users_and_watches()` can come in
        handy for generating mails from Django templates.

        """
        # Did this instead of mail() because a common case might be sending the
        # same mail to many users. mail() would make it difficult to avoid
        # redoing the templating every time.
        raise NotImplementedError

    def _users_watching(self, **kwargs):
        """Return an iterable of Users and EmailUsers watching this event
        and the Watches that map them to it.

        Each yielded item is a tuple: (User or EmailUser, [list of Watches]).

        Default implementation returns users watching this object's event_type
        and, if defined, content_type.

        """
        return self._users_watching_by_filter(**kwargs)

    @classmethod
    def _activation_email(cls, watch, email):
        """Return an EmailMessage to send to anonymous watchers.

        They are expected to follow the activation URL sent in the email to
        activate their watch, so you should include at least that.

        """
        # TODO: basic implementation.
        return mail.EmailMessage("TODO", "Activate!", settings.TIDINGS_FROM_ADDRESS, [email])

    @classmethod
    def _activation_url(cls, watch):
        """Return a URL pointing to a view which :meth:`activates
        <tidings.models.Watch.activate()>` a watch.

        TODO: provide generic implementation of this before liberating.
        Generic implementation could involve a setting to the default
        ``reverse()`` path, e.g. ``'tidings.activate_watch'``.

        """
        raise NotImplementedError

    @classmethod
    def description_of_watch(cls, watch):
        """Return a description of the Watch which can be used in emails.

        For example, "changes to English articles"

        """
        raise NotImplementedError


class EventUnion(Event):
    """Fireable conglomeration of multiple events

    Use this when you want to send a single mail to each person watching any of
    several events. For example, this sends only 1 mail to a given user, even
    if he was being notified of all 3 events::

        EventUnion(SomeEvent(), OtherEvent(), ThirdEvent()).fire()

    """

    # Calls some private methods on events, but this and Event are good
    # friends.

    def __init__(self, *events):
        """:arg events: the events of which to take the union"""
        super(EventUnion, self).__init__()
        self.events = events

    def _mails(self, users_and_watches):
        """Default implementation calls the
        :meth:`~tidings.events.Event._mails()` of my first event but may
        pass it any of my events as ``self``.

        Use this default implementation when the content of each event's mail
        template is essentially the same, e.g. "This new post was made.
        Enjoy.". When the receipt of a second mail from the second event would
        add no value, this is a fine choice. If the second event's email would
        add value, you should probably fire both events independently and let
        both mails be delivered. Or, if you would like to send a single mail
        with a custom template for a batch of events, just subclass
        :class:`EventUnion` and override this method.

        """
        return self.events[0]._mails(users_and_watches)

    def _users_watching(self, **kwargs):
        # Get a sorted iterable of user-watches pairs:
        def email_key(pair):
            user, watch = pair
            return user.email.lower()

        users_and_watches = collate(
            *[e._users_watching(**kwargs) for e in self.events], key=email_key, reverse=True
        )

        # Pick the best User out of each cluster of identical email addresses:
        return _unique_by_email(users_and_watches)


class InstanceEvent(Event):
    """Abstract superclass for watching a specific instance of a Model.

    Subclasses must specify an ``event_type`` and should specify a
    ``content_type``.
    """

    def __init__(self, instance, *args, **kwargs):
        """Initialize an InstanceEvent

        :arg instance: the instance someone would have to be watching in
          order to be notified when this event is fired.
        """
        super(InstanceEvent, self).__init__(*args, **kwargs)
        self.instance = instance

    @classmethod
    def notify(cls, user_or_email, instance):
        """Create, save, and return a watch which fires when something
        happens to ``instance``."""
        return super(InstanceEvent, cls).notify(user_or_email, object_id=instance.pk)

    @classmethod
    def stop_notifying(cls, user_or_email, instance):
        """Delete the watch created by notify."""
        super(InstanceEvent, cls).stop_notifying(user_or_email, object_id=instance.pk)

    @classmethod
    def is_notifying(cls, user_or_email, instance):
        """Check if the watch created by notify exists."""
        return super(InstanceEvent, cls).is_notifying(user_or_email, object_id=instance.pk)

    def _users_watching(self, **kwargs):
        """Return users watching this instance."""
        return self._users_watching_by_filter(object_id=self.instance.pk, **kwargs)
