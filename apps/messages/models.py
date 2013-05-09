from datetime import datetime

from django.contrib.auth.models import User
from django.db import models

from jinja2 import Markup

from sumo.models import ModelBase
from sumo.helpers import wiki_to_html


class InboxMessage(ModelBase):
    """A message in a user's private message inbox."""
    to = models.ForeignKey(User, related_name='inbox')
    sender = models.ForeignKey(User, null=True, blank=True)
    message = models.TextField()
    created = models.DateTimeField(default=datetime.now, db_index=True)
    read = models.BooleanField(default=False, db_index=True)
    replied = models.BooleanField(default=False)

    unread = property(lambda self: not self.read)

    def __unicode__(self):
        s = self.message[0:30]
        return u'to:%s from:%s %s' % (self.to, self.sender, s)

    @property
    def content_parsed(self):
        return Markup(wiki_to_html(self.message))


class OutboxMessage(ModelBase):
    sender = models.ForeignKey(User, related_name='outbox')
    to = models.ManyToManyField(User)
    message = models.TextField()
    created = models.DateTimeField(default=datetime.now, db_index=True)

    def __unicode__(self):
        to = u', '.join([u.username for u in self.to.all()])
        return u'from:%s to:%s %s' % (self.sender, to, self.message[0:30])

    @property
    def content_parsed(self):
        return Markup(wiki_to_html(self.message))
