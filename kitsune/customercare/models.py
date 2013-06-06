from datetime import datetime
import json

from django.contrib.auth.models import User
from django.db import models

from kitsune.sumo.models import ModelBase


class Tweet(ModelBase):
    """An entry on twitter."""
    tweet_id = models.BigIntegerField(primary_key=True)
    raw_json = models.TextField()
    # This is different from our usual locale, so not using LocaleField.
    locale = models.CharField(max_length=20, db_index=True)
    created = models.DateTimeField(default=datetime.now, db_index=True)
    reply_to = models.ForeignKey('self', null=True, related_name='replies')
    hidden = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ('-tweet_id',)

    @classmethod
    def latest(cls):
        """Return the most recent tweet.

        Raise Tweet.DoesNotExist if there are None.

        This is like Tweet.objects.latest(), except it sorts by tweet_id rather
        than a date column.

        """
        return cls.objects.order_by('-tweet_id')[0:1].get()

    def __unicode__(self):
        tweet = json.loads(self.raw_json)
        return tweet['text']


class Reply(ModelBase):
    """A reply from an AoA contributor.

    The Tweet table gets truncated regularly so we can't use it for metrics.
    This model is to keep track of contributor counts and such.
    """
    user = models.ForeignKey(User, null=True, blank=True, related_name='tweet_replies')
    twitter_username = models.CharField(max_length=20)
    tweet_id = models.BigIntegerField()
    raw_json = models.TextField()
    locale = models.CharField(max_length=20)
    created = models.DateTimeField(default=datetime.now, db_index=True)
    reply_to_tweet_id = models.BigIntegerField()

    def __unicode__(self):
        tweet = json.loads(self.raw_json)
        return u'@{u}: {t}'.format(u=self.twitter_username, t=tweet['text'])
