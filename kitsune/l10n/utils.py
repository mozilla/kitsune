from datetime import timedelta
from functools import partial, wraps

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import connection
from django_celery_beat.models import IntervalSchedule, PeriodicTask

from kitsune.users.models import Profile


def text_to_duration(text):
    """
    Returns a timedelta object from a simple, readable string format. For
    example, it would parse "3 days" into timedelta(days=3). The text must
    be expressed as a positive integer and one of the following units of
    measurement: "days", "hours", or "minutes". If the integer is zero, the
    units can be skipped. For example, "3 days" or "2 hours" or "1 minutes"
    or "0". The integer and units must be separated by whitespace. Invalid
    text will raise an instance of ValidationError.
    """
    parts = text.split()
    validation_error = ValidationError(
        (
            "Must be expressed as a positive integer and one of the following "
            'units of measurement: "days", "hours", or "minutes". If the integer '
            'is zero, the units can be skipped. For example, "3 days" or "2 hours" '
            'or "1 minutes" or "0").'
        )
    )

    if not parts:
        raise validation_error

    try:
        num = int(parts[0])
    except ValueError:
        raise validation_error
    else:
        if num < 0:
            raise validation_error

    if num == 0:
        return timedelta(0)

    if not ((len(parts) == 2) and ((units := parts[1]) in ("days", "hours", "minutes"))):
        raise validation_error

    return timedelta(**{units: num})


def duration_to_text(duration):
    """
    A simpler, more readable version of Django's function that converts a timedelta
    instance into a string. It only cares about days, hours, and minutes.
    """
    days = duration.days
    minutes = duration.seconds // 60
    hours = minutes // 60
    minutes %= 60

    if minutes:
        return f"{(days * 24 * 60) + (hours * 60) + minutes} minutes"

    if hours:
        return f"{(days * 24) + hours} hours"

    if days:
        return f"{days} days"

    return "0"


def get_l10n_bot():
    """
    Returns the User instance that is the SUMO L10n Bot.
    """
    user, created = get_user_model().objects.get_or_create(
        username="sumo-l10n-bot", defaults=dict(email="sumodev@mozilla.com")
    )
    if created:
        Profile.objects.create(user=user, name="SUMO Localization Bot")
    return user


def manage_heartbeat(heartbeat_period):
    """
    Creates, updates, or deletes the "L10n Heartbeat" periodic task.
    """
    name = "L10n Heartbeat"

    if heartbeat_period == timedelta(0):
        # Delete the periodic task.
        PeriodicTask.objects.filter(name=name).delete()
        return

    num, units = duration_to_text(heartbeat_period).split()

    # Get or create an interval schedule.
    interval, created_interval = IntervalSchedule.objects.get_or_create(
        every=int(num), period=units
    )

    heartbeat, created_heartbeat = PeriodicTask.objects.get_or_create(
        name=name,
        defaults=dict(
            interval=interval,
            task="kitsune.l10n.tasks.handle_wiki_localization",
        ),
    )

    # Has the interval changed?
    if (not created_heartbeat) and (
        created_interval or (str(heartbeat.interval) != str(interval))
    ):
        # Update the heartbeat with the new interval.
        heartbeat.interval = interval
        heartbeat.save()


def build_message(
    mt_config,
    creations_awaiting_review,
    creations_already_approved,
    rejections,
    pre_review_approvals,
    post_rejection_approvals,
):
    """
    Builds a message given the machine translation URL's that have been automatically
    created, rejected, approved after the review grace period, and approved after the
    post-review grace period.
    """
    msgs = []

    if creations_awaiting_review:
        msgs.append(
            (
                "The following machine translations were automatically created "
                "and are awaiting review:\n"
            )
        )
        msgs.extend(f"{url}\n" for url in creations_awaiting_review)

    if creations_already_approved:
        msgs.append(
            (
                "The following machine translations were automatically created and also "
                "immediately approved because the locale team has not been active within "
                f"the last {duration_to_text(mt_config.locale_team_inactivity_grace_period)}:\n"
            )
        )
        msgs.extend(f"{url}\n" for url in creations_already_approved)

    if pre_review_approvals or post_rejection_approvals:
        if pre_review_approvals:
            msgs.append(
                (
                    "The following machine translations were automatically approved "
                    "because they were not reviewed within the grace period of "
                    f"{duration_to_text(mt_config.review_grace_period)}:\n"
                )
            )
            msgs.extend(f"{url}\n" for url in pre_review_approvals)

        if post_rejection_approvals:
            msgs.append(
                (
                    "The following machine translations are copies of machine "
                    "translations that were reviewed and rejected, but because "
                    "alternate translations were not approved within the post-"
                    "review grace period of "
                    f"{duration_to_text(mt_config.post_review_grace_period)}, "
                    "these copies were automatically created and approved:\n"
                )
            )
            msgs.extend(f"{url}\n" for url in post_rejection_approvals)

    if rejections:
        msgs.append(
            (
                "The following machine translations were automatically "
                "rejected because they were out-of-date or superseded "
                "by an alternate revision:\n"
            )
        )
        msgs.extend(f"{url}\n" for url in rejections)

    return "\n\n".join(msgs)


def run_with_pg_lock(func=None, lock_key=None, default=None):
    """
    Decorator that only runs the decorated function if it can acquire the
    Postgres advisory lock specified by the given "lock_key". It does not
    block if the lock can't be acquired, so in that case the execution of
    the decorated function is skipped and the given default value is
    returned.
    """

    if not func:
        return partial(run_with_pg_lock, lock_key=lock_key, default=default)

    if not lock_key:
        lock_key = 9876543210

    def run_sql(sql, *args):
        with connection.cursor() as cursor:
            cursor.execute(sql, args)
            return cursor.fetchone()[0]

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Attempt to acquire the advisory lock without blocking. Immediately
        # returns false if the lock is already taken.
        lock_acquired = run_sql("SELECT pg_try_advisory_lock(%s);", lock_key)

        if not lock_acquired:
            return default

        try:
            return func(*args, **kwargs)
        finally:
            # Release the advisory lock.
            run_sql("SELECT pg_advisory_unlock(%s);", lock_key)

    return wrapper
