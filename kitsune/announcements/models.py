from datetime import datetime

from django.contrib.auth.models import User, Group
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save

from kitsune.sumo.templatetags.jinja_helpers import wiki_to_html
from kitsune.sumo.models import ModelBase
from kitsune.wiki.models import Locale


class Announcement(ModelBase):
    created = models.DateTimeField(default=datetime.now)
    creator = models.ForeignKey(User)
    show_after = models.DateTimeField(
        default=datetime.now, db_index=True,
        verbose_name='Start displaying',
        help_text=('When this announcement will start appearing. '
                   '(US/Pacific)'))
    show_until = models.DateTimeField(
        db_index=True, null=True, blank=True,
        verbose_name='Stop displaying',
        help_text=('When this announcement will stop appearing. '
                   'Leave blank for indefinite. (US/Pacific)'))
    content = models.TextField(
        max_length=10000,
        help_text=("Use wiki syntax or HTML. It will display similar to a "
                   "document's content."))
    group = models.ForeignKey(Group, null=True, blank=True)
    locale = models.ForeignKey(Locale, null=True, blank=True)

    def __unicode__(self):
        excerpt = self.content[:50]
        if self.group:
            return u'[{group}] {excerpt}'.format(group=self.group,
                                                 excerpt=excerpt)
        return u'{excerpt}'.format(excerpt=excerpt)

    def is_visible(self):
        now = datetime.now()
        if now > self.show_after and (not self.show_until or
                                      now < self.show_until):
            return True
        return False

    @property
    def content_parsed(self):
        return wiki_to_html(self.content.strip())

    @classmethod
    def get_site_wide(cls):
        return cls._visible_query(group=None, locale=None)

    @classmethod
    def get_for_group_id(cls, group_id):
        """Returns visible announcements for a given group id."""
        return cls._visible_query(group__id=group_id)

    @classmethod
    def get_for_locale_name(cls, locale_name):
        """Returns visible announcements for a given locale name."""
        return cls._visible_query(locale__locale=locale_name)

    @classmethod
    def _visible_query(cls, **query_kwargs):
        """Return visible announcements given a group query."""
        return Announcement.objects.filter(
            # Show if interval is specified and current or show_until is None
            Q(show_after__lt=datetime.now()) &
            (Q(show_until__gt=datetime.now()) | Q(show_until__isnull=True)),
            **query_kwargs)


def connector(sender, instance, created, **kw):
    # Only email new announcements in a group. We don't want to email everyone.
    if created and instance.group:
        from kitsune.announcements.tasks import send_group_email
        now = datetime.now()
        if instance.is_visible():
            send_group_email.delay(instance.pk)
        elif now < instance.show_after:
            send_group_email.delay(instance.pk, eta=instance.show_after)

post_save.connect(connector, sender=Announcement,
                  dispatch_uid='email_announcement')
