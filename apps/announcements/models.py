from datetime import datetime

from django.contrib.auth.models import User, Group
from django.db import models
from django.db.models import Q

from tower import ugettext as _

from sumo.models import ModelBase
from wiki.parser import wiki_to_html


class Announcement(ModelBase):
    created = models.DateTimeField(default=datetime.now)
    creator = models.ForeignKey(User)
    show_after = models.DateTimeField(
        default=datetime.now, db_index=True,
        verbose_name=_(u'Start displaying'),
        help_text=_(u'When this announcement will start appearing. '
                    '(US/Pacific)'))
    show_until = models.DateTimeField(
        db_index=True, null=True, blank=True,
        verbose_name=_(u'Stop displaying'),
        help_text=_(u'When this announcement will stop appearing. '
                    'Leave blank for indefinite. (US/Pacific)'))
    content = models.TextField(
        max_length=10000,
        help_text=_(u"Use wiki syntax or HTML. It will display similar to a "
                    "document's content."))
    group = models.ForeignKey(Group, null=True, blank=True)

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
        return cls._group_query_filter(Q(group=None))

    @classmethod
    def get_for_group_name(cls, group_name):
        """Returns visible announcements for a given group name, or in no group
        if none is provided."""
        group_q = Q(group=Group.objects.get(name=group_name))
        return cls._group_query_filter(group_q)

    @classmethod
    def get_for_groups(cls, groups=None):
        """Returns visible announcements for a given (query)set of groups."""
        return cls._group_query_filter(Q(group__in=groups or []))

    @classmethod
    def _group_query_filter(cls, group_query):
        """Return visible announcements given a group query."""
        return Announcement.objects.filter(
            # Show if interval is specified and current or show_until is None
            Q(show_after__lt=datetime.now()) &
            (Q(show_until__gt=datetime.now()) | Q(show_until__isnull=True)),
            group_query)
