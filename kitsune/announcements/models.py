from collections.abc import Iterable
from datetime import datetime
from typing import Self

from django.contrib.auth.models import Group, User
from django.db import models
from django.db.models import Q, QuerySet
from django.db.models.functions import Now
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
    platforms = models.ManyToManyField("products.Platform", related_name="announcements", blank=True)
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
    def get_site_wide(cls, platform_slugs: Iterable[str] | None = None):
        """Returns announcements that are visible to everyone (no group/locale restrictions)."""
        return cls._visible_query(platforms=platform_slugs).filter(groups__isnull=True, locale__isnull=True)

    @classmethod
    def get_for_groups(cls, group_ids: Iterable[int], platform_slugs: Iterable[str] | None = None) -> QuerySet[Self]:
        """Returns visible announcements for the given group ids and platform slugs.

        If an announcement has no groups, it's considered site-wide and will be included.
        If an announcement has any groups, it will only be included if one of those groups
        is in the provided group_ids.
        """
        return cls._visible_query(platforms=platform_slugs, groups=group_ids)

    @classmethod
    def get_for_locale_name(cls, locale_name):
        """Returns visible announcements for a given locale name."""
        return cls._visible_query(locale__locale=locale_name)

    @classmethod
    def _visible_query(cls, **query_kwargs):
        """Return visible announcements given query parameters."""
        query = Announcement.objects.filter(
            # Show if interval is specified and current or show_until is None
            Q(show_after__range=(datetime.min, Now()))
            & (Q(show_until__range=(Now(), datetime.max)) | Q(show_until__isnull=True))
        )

        # Handle platform filtering
        platforms = query_kwargs.pop('platforms', None)
        groups = query_kwargs.pop('groups', None)

        if platforms and 'web' not in platforms:
            has_web_announcements = query.filter(platforms__slug='web').exists()
            if not has_web_announcements:
                query = query.filter(
                    Q(platforms__isnull=True) |
                    Q(platforms__slug__in=platforms)
                )

        if groups:
            query = query.filter(Q(groups__isnull=True) | Q(groups__id__in=groups))
        else:
            query = query.filter(groups__isnull=True)

        if query_kwargs:
            query = query.filter(**query_kwargs)

        return query.distinct()


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
