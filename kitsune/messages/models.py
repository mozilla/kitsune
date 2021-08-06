from datetime import datetime

from django.contrib.auth.models import User
from django.db import models

from kitsune.sumo.models import ModelBase, utf8mb3TextField


class InboxMessage(ModelBase):
    """A message in a user's private message inbox."""

    to = models.ForeignKey(User, on_delete=models.CASCADE, related_name="inbox")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    message = utf8mb3TextField(html=True)
    created = models.DateTimeField(default=datetime.now, db_index=True)
    read = models.BooleanField(default=False, db_index=True)
    replied = models.BooleanField(default=False)

    unread = property(lambda self: not self.read)

    def __str__(self):
        s = self.message[0:30]
        return "to:%s from:%s %s" % (self.to, self.sender, s)

    @property
    def content_parsed(self):
        from kitsune.sumo.templatetags.jinja_helpers import wiki_to_html

        return wiki_to_html(self.message)

    class Meta:
        db_table = "messages_inboxmessage"


class OutboxMessage(ModelBase):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="outbox")
    to = models.ManyToManyField(User)
    message = utf8mb3TextField(html=True)
    created = models.DateTimeField(default=datetime.now, db_index=True)

    def __str__(self):
        to = ", ".join([u.username for u in self.to.all()])
        return "from:%s to:%s %s" % (self.sender, to, self.message[0:30])

    @property
    def content_parsed(self):
        from kitsune.sumo.templatetags.jinja_helpers import wiki_to_html

        return wiki_to_html(self.message)

    class Meta:
        db_table = "messages_outboxmessage"
