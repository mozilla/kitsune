from datetime import datetime, timedelta
import logging
import re
import time

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db import models, connection
from django.db.models.signals import post_save

from product_details import product_details
from statsd import statsd
from taggit.models import Tag, TaggedItem
import waffle

from activity.models import ActionMixin
from flagit.models import FlaggedObject
from karma.manager import KarmaManager
import questions as constants
from questions.karma_actions import (AnswerAction, FirstAnswerAction,
                                     SolutionAction)
from questions.question_config import products
from questions.tasks import (update_question_votes, update_answer_pages,
                             log_answer)
from search import searcher
from search.models import SearchMixin, register_for_indexing
from search.utils import crc32
from sumo.helpers import urlparams
from sumo.models import ModelBase
from sumo.parser import wiki_to_html
from sumo.redis_utils import RedisError
from sumo.urlresolvers import reverse
from tags.models import BigVocabTaggableMixin
from tags.utils import add_existing_tag
from upload.models import ImageAttachment


log = logging.getLogger('k.questions')


CACHE_TIMEOUT = 10800  # 3 hours


class Question(ModelBase, BigVocabTaggableMixin, SearchMixin):
    """A support question."""
    title = models.CharField(max_length=255)
    creator = models.ForeignKey(User, related_name='questions')
    content = models.TextField()

    created = models.DateTimeField(default=datetime.now, db_index=True)
    updated = models.DateTimeField(default=datetime.now, db_index=True)
    updated_by = models.ForeignKey(User, null=True,
                                   related_name='questions_updated')
    last_answer = models.ForeignKey('Answer', related_name='last_reply_in',
                                    null=True)
    num_answers = models.IntegerField(default=0, db_index=True)
    solution = models.ForeignKey('Answer', related_name='solution_for',
                                 null=True)
    is_locked = models.BooleanField(default=False)
    num_votes_past_week = models.PositiveIntegerField(default=0, db_index=True)

    images = generic.GenericRelation(ImageAttachment)
    flags = generic.GenericRelation(FlaggedObject)

    html_cache_key = u'question:html:%s'
    tags_cache_key = u'question:tags:%s'
    contributors_cache_key = u'question:contributors:%s'

    class Meta:
        ordering = ['-updated']
        permissions = (
                ('tag_question',
                 'Can add tags to and remove tags from questions'),
                ('change_solution',
                 'Can change/remove the solution to a question'),
            )

    class SphinxMeta(object):
        index = 'questions'
        filter_mapping = {
            'tag': crc32,
            'question_creator': crc32,
            'answer_creator': crc32}
        id_field = 'question_id'

    def __unicode__(self):
        return self.title

    @property
    def content_parsed(self):
        return _content_parsed(self)

    def clear_cached_html(self):
        cache.delete(self.html_cache_key % self.id)

    def clear_cached_tags(self):
        cache.delete(self.tags_cache_key % self.id)

    def clear_cached_contributors(self):
        cache.delete(self.contributors_cache_key % self.id)

    def save(self, no_update=False, *args, **kwargs):
        """Override save method to take care of updated."""
        new = not self.id

        if not new:
            self.clear_cached_html()
            if not no_update:
                self.updated = datetime.now()

        super(Question, self).save(*args, **kwargs)

        if new:
            # Avoid circular import, events.py imports Question
            from questions.events import QuestionReplyEvent
            # Authors should automatically watch their own questions.
            QuestionReplyEvent.notify(self.creator, self)

    def add_metadata(self, **kwargs):
        """Add (save to db) the passed in metadata.

        Usage:
        question = Question.objects.get(pk=1)
        question.add_metadata(ff_version='3.6.3', os='Linux')

        """
        for key, value in kwargs.items():
            QuestionMetaData.objects.create(question=self, name=key,
                                            value=value)
        self._metadata = None

    def clear_mutable_metadata(self):
        """Clear the mutable metadata.

        This excludes immutable fields: user agent, product, and category.

        """
        self.metadata_set.exclude(name__in=['useragent', 'product',
                                            'category']).delete()
        self._metadata = None

    @property
    def metadata(self):
        """Dictionary access to metadata

        Caches the full metadata dict after first call.

        """
        if not hasattr(self, '_metadata') or self._metadata is None:
            self._metadata = dict((m.name, m.value) for
                                  m in self.metadata_set.all())
        return self._metadata

    @property
    def product(self):
        """Return the product this question is about or an empty mapping if
        unknown."""
        md = self.metadata
        if 'product' in md:
            return products.get(md['product'], {})
        return {}

    @property
    def category(self):
        """Return the category this question refers to or an empty mapping if
        unknown."""
        md = self.metadata
        if self.product and 'category' in md:
            return self.product['categories'].get(md['category'], {})
        return {}

    def auto_tag(self):
        """Apply tags to myself that are implied by my metadata.

        You don't need to call save on the question after this.

        """
        to_add = self.product.get('tags', []) + self.category.get('tags', [])

        version = self.metadata.get('ff_version', '')
        dev_releases = product_details.firefox_history_development_releases
        if version in dev_releases or \
           version in product_details.firefox_history_stability_releases or \
           version in product_details.firefox_history_major_releases:
            to_add.append('Firefox %s' % version)
            tenths = _tenths_version(version)
            if tenths:
                to_add.append('Firefox %s' % tenths)
        elif _has_beta(version, dev_releases):
            to_add.append('Firefox %s' % version)
            to_add.append('beta')

        self.tags.add(*to_add)

        # Add a tag for the OS if it already exists as a tag:
        os = self.metadata.get('os')
        if os:
            try:
                add_existing_tag(os, self.tags)
            except Tag.DoesNotExist:
                pass

    def get_absolute_url(self):
        # Note: If this function changes, we need to change it in
        # extract_document, too.
        return reverse('questions.answers',
                       kwargs={'question_id': self.id})

    @property
    def num_votes(self):
        """Get the number of votes for this question."""
        if not hasattr(self, '_num_votes'):
            n = QuestionVote.objects.filter(question=self).count()
            self._num_votes = n
        return self._num_votes

    def sync_num_votes_past_week(self):
        """Get the number of votes for this question in the past week."""
        last_week = datetime.now().date() - timedelta(days=7)
        n = QuestionVote.objects.filter(question=self,
                                        created__gte=last_week).count()
        self.num_votes_past_week = n
        return n

    def has_voted(self, request):
        """Did the user already vote?"""
        if request.user.is_authenticated():
            qs = QuestionVote.objects.filter(question=self,
                                             creator=request.user)
        elif request.anonymous.has_id:
            anon_id = request.anonymous.anonymous_id
            qs = QuestionVote.objects.filter(question=self,
                                             anonymous_id=anon_id)
        else:
            return False

        return qs.exists()

    @property
    def helpful_replies(self):
        """Return answers that have been voted as helpful."""
        cursor = connection.cursor()
        cursor.execute('SELECT votes.answer_id, '
                       'SUM(IF(votes.helpful=1,1,-1)) AS score '
                       'FROM questions_answervote AS votes '
                       'JOIN questions_answer AS ans '
                       'ON ans.id=votes.answer_id '
                       'AND ans.question_id=%s '
                       'GROUP BY votes.answer_id '
                       'HAVING score > 0 '
                       'ORDER BY score DESC LIMIT 2', [self.id])

        helpful_ids = [row[0] for row in cursor.fetchall()]

        # Exclude the solution if it is set
        if self.solution and self.solution.id in helpful_ids:
            helpful_ids.remove(self.solution.id)

        if len(helpful_ids) > 0:
            return self.answers.filter(id__in=helpful_ids)
        else:
            return []

    def is_contributor(self, user):
        """Did the passed in user contribute to this question?"""
        if user.is_authenticated():
            return user.id in self.contributors

        return False

    @property
    def contributors(self):
        """The contributors to the question."""
        cache_key = self.contributors_cache_key % self.id
        contributors = cache.get(cache_key)
        if contributors is None:
            contributors = self.answers.all().values_list('creator_id',
                                                          flat=True)
            contributors = list(contributors)
            contributors.append(self.creator_id)
            cache.add(cache_key, contributors, CACHE_TIMEOUT)
        return contributors

    @property
    def is_solved(self):
        return not not self.solution_id

    @property
    def my_tags(self):
        """A caching wrapper around self.tags.all()."""
        cache_key = self.tags_cache_key % self.id
        tags = cache.get(cache_key)
        if tags is None:
            tags = self.tags.all()
            cache.add(cache_key, tags, CACHE_TIMEOUT)
        return tags

    @classmethod
    def get_query_fields(cls):
        return ['question_title__text',
                'question_content__text',
                'question_answer_content__text']

    @classmethod
    def get_mapping(cls):
        return {
            'id': {'type': 'long'},
            'model': {'type': 'string', 'index': 'not_analyzed'},
            'url': {'type': 'string', 'index': 'not_analyzed'},
            'indexed_on': {'type': 'integer'},
            'created': {'type': 'integer'},
            'updated': {'type': 'integer'},

            'question_title': {'type': 'string', 'analyzer': 'snowball'},
            'question_content':
                {'type': 'string', 'analyzer': 'snowball',
                # TODO: Stored because originally, this is the
                # only field we were excerpting on. Standardize
                # one way or the other.
                 'store': 'yes', 'term_vector': 'with_positions_offsets'},
            'question_answer_content':
                {'type': 'string', 'analyzer': 'snowball'},
            'question_num_answers': {'type': 'integer'},
            'question_is_solved': {'type': 'boolean'},
            'question_is_locked': {'type': 'boolean'},
            'question_has_answers': {'type': 'boolean'},
            'question_has_helpful': {'type': 'boolean'},
            'question_creator': {'type': 'string', 'index': 'not_analyzed'},
            'question_answer_creator':
                {'type': 'string', 'index': 'not_analyzed'},
            'question_num_votes': {'type': 'integer'},
            'question_num_votes_past_week': {'type': 'integer'},
            'question_answer_votes': {'type': 'integer'},
            'question_tag': {'type': 'string', 'index': 'not_analyzed'}}

    @classmethod
    def extract_document(cls, obj_id):
        """Extracts indexable attributes from a Question and its answers."""

        # Note: Need to keep this in sync with
        # tasks.update_question_vote_chunk.
        obj = cls.uncached.values(
            'id', 'title', 'content', 'num_answers', 'solution_id',
            'is_locked', 'created', 'updated', 'num_votes_past_week',
            'creator__username').get(pk=obj_id)

        d = {}
        d['id'] = obj['id']
        d['model'] = cls.get_model_name()

        # We do this because get_absolute_url is an instance method
        # and we don't want to create an instance because it's a DB
        # hit and expensive. So we do it by hand. get_absolute_url
        # doesn't change much, so this is probably ok.
        d['url'] = reverse('questions.answers',
                           kwargs={'question_id': obj['id']})

        d['indexed_on'] = int(time.time())

        # TODO: Sphinx stores created and updated as seconds since the
        # epoch, so we convert them to that format here so that the
        # search view works correctly. When we ditch Sphinx, we should
        # see if it's faster to filter on ints or whether we should
        # switch them to dates.
        d['created'] = int(time.mktime(obj['created'].timetuple()))
        d['updated'] = int(time.mktime(obj['updated'].timetuple()))

        d['question_title'] = obj['title']
        d['question_content'] = obj['content']
        d['question_num_answers'] = obj['num_answers']
        d['question_is_solved'] = bool(obj['solution_id'])
        d['question_is_locked'] = obj['is_locked']
        d['question_has_answers'] = bool(obj['num_answers'])

        d['question_creator'] = obj['creator__username']
        d['question_num_votes'] = (QuestionVote.objects
                          .filter(question=obj['id'])
                          .count())
        d['question_num_votes_past_week'] = obj['num_votes_past_week']

        d['question_tag'] = list(TaggedItem.tags_for(
            Question, Question(pk=obj_id)).values_list('name', flat=True))

        answer_values = list(Answer.objects
                                   .filter(question=obj_id)
                                   .values_list('content',
                                                'creator__username'))

        d['question_answer_content'] = [a[0] for a in answer_values]
        d['question_answer_creator'] = list(set(a[1] for a in answer_values))

        if not answer_values:
            d['question_has_helpful'] = False
        else:
            d['question_has_helpful'] = Answer.objects.filter(
                question=obj_id).filter(votes__helpful=True).exists()

        return d

    @classmethod
    def search(cls):
        s = super(Question, cls).search()
        return (s.query_fields('question_title__text',
                               'question_content__text',
                               'question_answer_content__text'))

    @classmethod
    def recent_asked_count(cls):
        """Returns the number of questions asked in the last 72 hours."""
        start = datetime.now() - timedelta(hours=72)
        qs = cls.objects.filter(created__gt=start, creator__is_active=True)
        return qs.count()

    @classmethod
    def recent_unanswered_count(cls):
        """Returns the number of questions that have not been answered in the
        last 72 hours
        """
        start = datetime.now() - timedelta(hours=72)
        qs = cls.objects.filter(
            num_answers=0, created__gt=start, is_locked=False,
            creator__is_active=1)
        return qs.count()


register_for_indexing(Question, 'questions')
register_for_indexing(
    TaggedItem,
    'questions',
    instance_to_indexee=(
        lambda i: i.content_object if isinstance(i.content_object, Question)
                  else None))


class QuestionMetaData(ModelBase):
    """Metadata associated with a support question."""
    question = models.ForeignKey('Question', related_name='metadata_set')
    name = models.SlugField(db_index=True)
    value = models.TextField()

    class Meta:
        unique_together = ('question', 'name')

    def __unicode__(self):
        return u'%s: %s' % (self.name, self.value[:50])


class Answer(ActionMixin, ModelBase):
    """An answer to a support question."""
    question = models.ForeignKey('Question', related_name='answers')
    creator = models.ForeignKey(User, related_name='answers')
    created = models.DateTimeField(default=datetime.now, db_index=True)
    content = models.TextField()
    updated = models.DateTimeField(default=datetime.now, db_index=True)
    updated_by = models.ForeignKey(User, null=True,
                                   related_name='answers_updated')
    upvotes = models.IntegerField(default=0, db_index=True)
    page = models.IntegerField(default=1)

    images = generic.GenericRelation(ImageAttachment)
    flags = generic.GenericRelation(FlaggedObject)

    html_cache_key = u'answer:html:%s'

    class Meta:
        ordering = ['created']

    def __unicode__(self):
        return u'%s: %s' % (self.question.title, self.content[:50])

    @property
    def content_parsed(self):
        return _content_parsed(self)

    def clear_cached_html(self):
        cache.delete(self.html_cache_key % self.id)

    def save(self, no_update=False, no_notify=False, *args, **kwargs):
        """
        Override save method to update question info and take care of
        updated.
        """

        new = self.id is None

        if new:
            page = self.question.num_answers / constants.ANSWERS_PER_PAGE + 1
            self.page = page
        else:
            self.updated = datetime.now()
            self.clear_cached_html()

        super(Answer, self).save(*args, **kwargs)

        if new:
            # Occasionally, num_answers seems to get out of sync with the
            # actual number of answers. This changes it to pull from
            # uncached on the off chance that fixes it. Plus if we enable
            # caching of counts, this will continue to work.
            self.question.num_answers = Answer.uncached.filter(
                question=self.question).count()
            self.question.last_answer = self
            self.question.save(no_update)
            self.question.clear_cached_contributors()

            if not no_notify:
                # Avoid circular import: events.py imports Question.
                from questions.events import QuestionReplyEvent
                QuestionReplyEvent(self).fire(exclude=self.creator)

    def delete(self, *args, **kwargs):
        """Override delete method to update parent question info."""
        question = Question.uncached.get(pk=self.question.id)
        if question.last_answer == self:
            answers = question.answers.all().order_by('-created')
            try:
                question.last_answer = answers[1]
            except IndexError:
                # The question has only one answer
                question.last_answer = None
        if question.solution == self:
            question.solution = None

            # Delete karma solution action.
            SolutionAction(user=self.creator, day=self.created).delete()

        # Delete karma answer action and first answer action if it was first.
        AnswerAction(user=self.creator, day=self.created).delete()
        if self.id == question.answers.all().order_by('created')[0].id:
            FirstAnswerAction(user=self.creator, day=self.created).delete()

        question.num_answers = question.answers.count() - 1
        question.save()
        question.clear_cached_contributors()

        super(Answer, self).delete(*args, **kwargs)

        update_answer_pages.delay(question)

    def get_helpful_answer_url(self):
        url = reverse('questions.answer_vote',
                      kwargs={'question_id': self.question_id,
                              'answer_id': self.id})
        return '%s?%s' % (url, 'helpful')

    def get_solution_url(self, watch):
        url = reverse('questions.solve',
                      kwargs={'question_id': self.question_id,
                              'answer_id': self.id})
        return urlparams(url, watch=watch.secret)

    def get_absolute_url(self):
        query = {}
        if self.page > 1:
            query = {'page': self.page}

        url = reverse('questions.answers',
                      kwargs={'question_id': self.question_id})
        return urlparams(url, hash='answer-%s' % self.id, **query)

    @property
    def num_votes(self):
        """Get the total number of votes for this answer."""
        return AnswerVote.objects.filter(answer=self).count()

    @property
    def creator_num_answers(self):
        # If karma is enabled, try to use the karma backend (redis) to get
        # the number of answers. Fallback to database.
        if waffle.switch_is_active('karma'):
            try:
                count = KarmaManager().count(
                    user=self.creator, type=AnswerAction.action_type)
                if count != None:
                    return count
            except RedisError as e:
                statsd.incr('redis.errror')
                log.error('Redis connection error: %s' % e)

        return Answer.objects.filter(creator=self.creator).count()

    @property
    def creator_num_solutions(self):
        # If karma is enabled, try to use the karma backend (redis) to get
        # the number of solutions. Fallback to database.
        if waffle.switch_is_active('karma'):
            try:
                count = KarmaManager().count(
                    user=self.creator, type=SolutionAction.action_type)
                if count != None:
                    return count
            except RedisError as e:
                statsd.incr('redis.errror')
                log.error('Redis connection error: %s' % e)

        return Question.objects.filter(
            solution__in=Answer.objects.filter(creator=self.creator)).count()

    @property
    def creator_num_points(self):
        try:
            return KarmaManager().count(self.creator, type='points')
        except RedisError as e:
            statsd.incr('redis.errror')
            log.error('Redis connection error: %s' % e)

    @property
    def num_helpful_votes(self):
        """Get the number of helpful votes for this answer."""
        return AnswerVote.objects.filter(answer=self, helpful=True).count()

    def has_voted(self, request):
        """Did the user already vote for this answer?"""
        if request.user.is_authenticated():
            qs = AnswerVote.objects.filter(answer=self,
                                           creator=request.user)
        elif request.anonymous.has_id:
            anon_id = request.anonymous.anonymous_id
            qs = AnswerVote.objects.filter(answer=self,
                                           anonymous_id=anon_id)
        else:
            return False

        return qs.exists()

    @classmethod
    def last_activity_for(cls, user):
        """Returns the datetime of the user's last answer."""
        try:
            return (Answer.objects.filter(creator=user)
                                  .order_by('-created')
                                  .values_list('created', flat=True)[0])
        except IndexError:
            return None


def answer_connector(sender, instance, created, **kw):
    if created:
        log_answer.delay(instance)

post_save.connect(answer_connector, sender=Answer,
                  dispatch_uid='question_answer_activity')


register_for_indexing(Answer,
                      'questions',
                      instance_to_indexee=lambda a: a.question)


class QuestionVote(ModelBase):
    """I have this problem too.
    Keeps track of users that have problem over time."""
    question = models.ForeignKey('Question', related_name='votes')
    created = models.DateTimeField(default=datetime.now, db_index=True)
    creator = models.ForeignKey(User, related_name='question_votes',
                                null=True)
    anonymous_id = models.CharField(max_length=40, db_index=True)

    def add_metadata(self, key, value):
        VoteMetadata.objects.create(vote=self, key=key, value=value)


register_for_indexing(
    QuestionVote, 'questions', instance_to_indexee=lambda v: v.question)


class AnswerVote(ModelBase):
    """Helpful or Not Helpful vote on Answer."""
    answer = models.ForeignKey('Answer', related_name='votes')
    helpful = models.BooleanField(default=False)
    created = models.DateTimeField(default=datetime.now, db_index=True)
    creator = models.ForeignKey(User, related_name='answer_votes',
                                null=True)
    anonymous_id = models.CharField(max_length=40, db_index=True)

    def add_metadata(self, key, value):
        VoteMetadata.objects.create(vote=self, key=key, value=value)


# TODO: We only need to update the helpful bit.  It's possible
# we could ignore all AnswerVotes that aren't helpful and if
# they're marked as helpful, then update the index.  Look into
# this.
register_for_indexing(
    AnswerVote, 'questions', instance_to_indexee=lambda v: v.answer.question)


class VoteMetadata(ModelBase):
    """Metadata for question and answer votes."""
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    vote = generic.GenericForeignKey()
    key = models.CharField(max_length=40, db_index=True)
    value = models.CharField(max_length=1000)


def send_vote_update_task(**kwargs):
    if kwargs.get('created'):
        q = kwargs.get('instance').question
        update_question_votes.delay(q.id)

post_save.connect(send_vote_update_task, sender=QuestionVote)


_tenths_version_pattern = re.compile(r'(\d+\.\d+).*')


def _tenths_version(full_version):
    """Return the major and minor version numbers from a full version string.

    Don't return bugfix version, beta status, or anything futher. If there is
    no major or minor version in the string, return ''.

    """
    match = _tenths_version_pattern.match(full_version)
    if match:
        return match.group(1)
    return ''


def _has_beta(version, dev_releases):
    """Returns True if the version has a beta release.

    For example, if:
        dev_releases={...u'4.0rc2': u'2011-03-18',
                      u'5.0b1': u'2011-05-20',
                      u'5.0b2': u'2011-05-20',
                      u'5.0b3': u'2011-06-01'}
    and you pass '5.0', it return True since there are 5.0 betas in the
    dev_releases dict. If you pass '6.0', it returns False.
    """
    return version in [re.search('(\d+\.)+\d+', s).group(0)
                       for s in dev_releases.keys()]


def _content_parsed(obj):
    cache_key = obj.html_cache_key % obj.id
    html = cache.get(cache_key)
    if html is None:
        html = wiki_to_html(obj.content)
        cache.add(cache_key, html, CACHE_TIMEOUT)
    return html


# NOTE: This only affects Sphinx search--it's not used in ES search.
def question_searcher(request):
    """Return a question searcher with default parameters."""
    return (searcher(request)(Question)
                .query_fields('title__text',
                              'question_content__text',
                              'answer_content__text')
                .weight(title=4, question_content=3, answer_content=3)
                .group_by('question_id', '-@group')  # nop in elasticutils
                .highlight(before_match='<b>',
                           after_match='</b>',
                           limit=settings.SEARCH_SUMMARY_LENGTH))
