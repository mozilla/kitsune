from django.db import models

from kitsune.sumo.models import ModelBase
from kitsune.wiki.models import Document


class Signature(ModelBase):
    signature = models.CharField(max_length=255, db_index=True, unique=True)
    document = models.ForeignKey(Document)

    def __unicode__(self):
        return u'<%s> %s' % (self.signature, self.document.title)

    def get_absolute_url(self):
        doc = self.document.get_absolute_url().lstrip('/')
        _, _, url = doc.partition('/')
        return u'/' + url
