import json
import time
from datetime import datetime

from django.contrib.auth.models import User
from django.db import models

from kitsune.search.models import (
    SearchMappingType, SearchMixin, register_for_indexing,
    register_mapping_type)
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


class Reply(ModelBase, SearchMixin):
    """A reply from an AoA contributor.

    The Tweet table gets truncated regularly so we can't use it for metrics.
    This model is to keep track of contributor counts and such.
    """
    user = models.ForeignKey(User, null=True, blank=True,
                             related_name='tweet_replies')
    twitter_username = models.CharField(max_length=20)
    tweet_id = models.BigIntegerField()
    raw_json = models.TextField()
    locale = models.CharField(max_length=20)
    created = models.DateTimeField(default=datetime.now, db_index=True)
    reply_to_tweet_id = models.BigIntegerField()

    def __unicode__(self):
        tweet = json.loads(self.raw_json)
        return u'@{u}: {t}'.format(u=self.twitter_username, t=tweet['text'])

    @classmethod
    def get_mapping_type(cls):
        return ReplyMetricsMappingType


@register_mapping_type
class ReplyMetricsMappingType(SearchMappingType):
    @classmethod
    def get_model(cls):
        return Reply

    @classmethod
    def get_index_group(cls):
        return 'metrics'

    @classmethod
    def get_query_fields(cls):
        """Return the list of fields for query"""
        return []

    @classmethod
    def get_mapping(cls):
        return {
            'properties': {
                'id': {'type': 'long'},
                'model': {'type': 'string', 'index': 'not_analyzed'},
                'url': {'type': 'string', 'index': 'not_analyzed'},
                'indexed_on': {'type': 'integer'},
                'created': {'type': 'date'},

                'locale': {'type': 'string', 'index': 'not_analyzed'},
                'creator_id': {'type': 'long'},
            }
        }

    @classmethod
    def extract_document(cls, obj_id, obj=None):
        """Extracts indexable attributes from an Answer."""
        fields = ['id', 'created', 'user_id', 'locale']

        if obj is None:
            # Note: Need to keep this in sync with
            # tasks.update_question_vote_chunk.
            model = cls.get_model()
            obj = model.uncached.values(*fields).get(pk=obj_id)
        else:
            obj = dict([(field, getattr(obj, field))
                              for field in fields])

        d = {}
        d['id'] = obj['id']
        d['model'] = cls.get_mapping_type_name()

        d['indexed_on'] = int(time.time())

        d['created'] = obj['created']

        d['locale'] = obj['locale']
        d['creator_id'] = obj['user_id']

        return d


register_for_indexing('replies', Reply)

