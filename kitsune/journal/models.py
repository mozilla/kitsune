from datetime import datetime

from django.db import models


RECORD_INFO = "info"
RECORD_ERROR = "error"


class RecordManager(models.Manager):
    def log(self, level, src, msg, **kwargs):
        msg = msg.format(**kwargs).encode("utf-8")
        return Record.objects.create(level=RECORD_INFO, src=src, msg=msg)

    def info(self, src, msg, **kwargs):
        self.log(RECORD_INFO, src, msg, **kwargs)

    def error(self, src, msg, **kwargs):
        self.log(RECORD_ERROR, src, msg, **kwargs)


class Record(models.Model):
    """Defines an audit record for something that happened in translations"""

    TYPE_CHOICES = [
        (RECORD_INFO, RECORD_INFO),
        (RECORD_ERROR, RECORD_ERROR),
    ]

    # The log level of this message (e.g. "info", "error", ...)
    level = models.CharField(choices=TYPE_CHOICES, max_length=20)

    # What component was running (e.g. "sumo.ratelimit", "questions.aaq")
    src = models.CharField(max_length=50)

    # The message details. (e.g. "user bob hit the ratelimit for questions.ask")
    msg = models.CharField(max_length=255)

    # When this log entry was created
    created = models.DateTimeField(default=datetime.now)

    objects = RecordManager()

    def __str__(self):
        return "<Record {self.src} {self.msg}>".format(self=self)
