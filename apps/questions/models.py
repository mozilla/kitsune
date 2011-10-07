from datetime import datetime, timedelta
import re

from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db import models
from django.db.models.signals import post_save

from product_details import product_details
from redis.exceptions import ConnectionError
from taggit.models import Tag
import waffle

from activity.models import ActionMixin
from flagit.models import FlaggedObject
from karma.actions import KarmaAction
import questions as constants
from questions.karma_actions import AnswerAction, SolutionAction
from questions.question_config import products
from questions.tasks import (update_question_votes, update_answer_pages,
                             log_answer)
from sumo.helpers import urlparams
from sumo.models import ModelBase
from sumo.parser import wiki_to_html
from sumo.urlresolvers import reverse
from tags.models import BigVocabTaggableMixin
from tags.utils import add_existing_tag
from upload.models import ImageAttachment

from search.utils import crc32


class Question(ModelBase, BigVocabTaggableMixin):
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
        weights = {'title': 4, 'question_content': 3, 'answer_content': 3}
        group_by = ('question_id', '-@group')
        filter_mapping = {
            'title': crc32,
            'question_content': crc32,
            'answer_content': crc32}

    def __unicode__(self):
        return self.title

    @property
    def content_parsed(self):
        cache_key = self.html_cache_key % self.id
        html = cache.get(cache_key)
        if html is None:
            html = wiki_to_html(self.content)
            cache.add(cache_key, html)
        return html

    def clear_cached_properties(self):
        cache.delete(self.html_cache_key % self.id)

    def save(self, no_update=False, *args, **kwargs):
        """Override save method to take care of updated."""
        new = not self.id

        if not new:
            self.clear_cached_properties()
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
        votes = AnswerVote.objects.filter(answer__question=self, helpful=True)
        helpful_ids = list(votes.values_list('answer', flat=True).distinct())
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
            qs = self.answers.filter(creator=user)
            if self.creator == user or qs.count() > 0:
                return True

        return False

    @property
    def is_solved(self):
        return Answer.objects.filter(pk=self.solution_id).exists()


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
        cache_key = self.html_cache_key % self.id
        html = cache.get(cache_key)
        if not html:
            html = wiki_to_html(self.content)
            cache.add(cache_key, html)
        return html

    def clear_cached_properties(self):
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
            self.clear_cached_properties()

        super(Answer, self).save(*args, **kwargs)

        if new:
            self.question.num_answers = self.question.answers.count()
            self.question.last_answer = self
            self.question.save(no_update)

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

        question.num_answers = question.answers.count() - 1
        question.save()

        super(Answer, self).delete(*args, **kwargs)

        update_answer_pages.delay(question)

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
                return KarmaAction.objects.total_count(
                    AnswerAction, self.creator)
            except ConnectionError:
                pass
        return Answer.objects.filter(creator=self.creator).count()

    @property
    def creator_num_solutions(self):
        # If karma is enabled, try to use the karma backend (redis) to get
        # the number of solutions. Fallback to database.
        if waffle.switch_is_active('karma'):
            try:
                return KarmaAction.objects.total_count(
                    SolutionAction, self.creator)
            except ConnectionError:
                pass
        return Question.objects.filter(
            solution__in=Answer.objects.filter(creator=self.creator)).count()

    @property
    def creator_num_points(self):
        try:
            return KarmaAction.objects.total_points(self.creator)
        except ConnectionError:
            return None

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


def answer_connector(sender, instance, created, **kw):
    if created:
        log_answer.delay(instance)

post_save.connect(answer_connector, sender=Answer,
                  dispatch_uid='question_answer_activity')


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
        update_question_votes.delay(q)

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
