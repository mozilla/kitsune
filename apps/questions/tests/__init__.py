from datetime import datetime

from django.conf import settings
from django.template.defaultfilters import slugify

from nose.tools import eq_

from questions.models import Question, QuestionVote, Answer, AnswerVote
from sumo.tests import LocalizingClient, TestCase, with_save
from users.tests import user


class TestCaseBase(TestCase):
    """Base TestCase for the Questions app test cases."""

    fixtures = ['users.json', 'questions.json']
    client_class = LocalizingClient

    def setUp(self):
        super(TestCaseBase, self).setUp()
        q = Question.objects.get(pk=1)
        q.last_answer_id = 1
        q.save()

        # create a new cache key for top contributors to avoid conflict
        # TODO: May be able to go away once we flush memcache between tests.
        self.orig_tc_cache_key = settings.TOP_CONTRIBUTORS_CACHE_KEY
        settings.TOP_CONTRIBUTORS_CACHE_KEY += slugify(datetime.now())

    def tearDown(self):
        super(TestCaseBase, self).tearDown()
        settings.TOP_CONTRIBUTORS_CACHE_KEY = self.orig_tc_cache_key


class TaggingTestCaseBase(TestCaseBase):
    """Base testcase with additional setup for testing tagging"""

    fixtures = TestCaseBase.fixtures + ['taggit.json']


def tags_eq(tagged_object, tag_names):
    """Assert that the names of the tags on tagged_object are tag_names."""
    eq_(sorted([t.name for t in tagged_object.tags.all()]),
        sorted(tag_names))


@with_save
def question(**kwargs):
    defaults = dict(title=str(datetime.now()),
                    content='',
                    created=datetime.now(),
                    num_answers=0,
                    is_locked=0)
    defaults.update(kwargs)
    if 'creator' not in kwargs and 'creator_id' not in kwargs:
        defaults['creator'] = user(save=True)
    return Question(**defaults)


@with_save
def questionvote(**kwargs):
    defaults = dict(created=datetime.now())
    defaults.update(kwargs)
    if 'question' not in kwargs and 'queation_id' not in kwargs:
        defaults['question'] = question(save=True)
    if 'creator' not in kwargs and 'creator_id' not in kwargs:
        defaults['creator'] = user(save=True)
    return QuestionVote(**defaults)


@with_save
def answer(**kwargs):
    defaults = dict(created=datetime.now(), content='')
    defaults.update(kwargs)
    if 'question' not in kwargs and 'question_id' not in kwargs:
        defaults['question'] = question(save=True)
    if 'creator' not in kwargs and 'creator_id' not in kwargs:
        defaults['creator'] = user(save=True)
    return Answer(**defaults)


@with_save
def answervote(**kwargs):
    defaults = dict(created=datetime.now(), helpful=False)
    defaults.update(kwargs)
    if 'creator' not in kwargs and 'creator_id' not in kwargs:
        defaults['creator'] = user(save=True)
    return AnswerVote(**defaults)
