from collections.abc import Iterable
from datetime import datetime
from typing import Self

from django.contrib.auth.models import Group, User
from django.db import models
from django.db.models import Q, QuerySet
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from kitsune.sumo.models import ModelBase
from kitsune.sumo.templatetags.jinja_helpers import wiki_to_html
from kitsune.wiki.models import Locale


class Announcement(ModelBase):
    created = models.DateTimeField(default=datetime.now)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    show_after = models.DateTimeField(
        default=datetime.now,
        db_index=True,
        verbose_name="Start displaying",
        help_text=("When this announcement will start appearing. " "(US/Pacific)"),
    )
    show_until = models.DateTimeField(
        db_index=True,
        null=True,
        blank=True,
        verbose_name="Stop displaying",
        help_text=(
            "When this announcement will stop appearing. "
            "Leave blank for indefinite. (US/Pacific)"
        ),
    )
    content = models.TextField(
        max_length=10000,
        help_text=("Use wiki syntax or HTML. It will display similar to a document's content."),
    )
    groups = models.ManyToManyField(Group, related_name="announcements", blank=True, null=True)
    locale = models.ForeignKey(Locale, on_delete=models.CASCADE, null=True, blank=True)
    send_email = models.BooleanField(
        default=False,
        help_text=(
            "Send an email to all users in the groups. If no groups are selected, this is ignored."
        ),
    )

    def __str__(self):
        return f"{self.content[:50]}"

    def is_visible(self):
        now = datetime.now()
        if now > self.show_after and (not self.show_until or now < self.show_until):
            return True
        return False

    @property
    def content_parsed(self):
        return wiki_to_html(self.content.strip())

    @classmethod
    def get_site_wide(cls):
        return cls._visible_query(groups=None, locale=None)

    @classmethod
    def get_for_groups(cls, group_ids: Iterable[int]) -> QuerySet[Self]:
        """Returns visible announcements for the given group ids."""
        return cls._visible_query(groups__id__in=group_ids).distinct()

    @classmethod
    def get_for_locale_name(cls, locale_name):
        """Returns visible announcements for a given locale name."""
        return cls._visible_query(locale__locale=locale_name)

    @classmethod
    def _visible_query(cls, **query_kwargs):
        """Return visible announcements given a groups query."""
        return Announcement.objects.filter(
            # Show if interval is specified and current or show_until is None
            Q(show_after__lt=datetime.now())
            & (Q(show_until__gt=datetime.now()) | Q(show_until__isnull=True)),
            **query_kwargs,
        )


@receiver(m2m_changed, sender=Announcement.groups.through)
def connector(sender, **kw):
    if kw.get("action", "") == "post_add":
        instance = kw["instance"]
        if instance.send_email:
            from kitsune.announcements.tasks import send_group_email

            now = datetime.now()
            if instance.is_visible():
                send_group_email.delay(instance.pk)
            elif now < instance.show_after:
                send_group_email.delay(instance.pk, eta=instance.show_after)
