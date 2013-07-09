from datetime import datetime

from nose.tools import eq_

from kitsune.questions.models import (
    Question, QuestionVote, Answer, AnswerVote)
from kitsune.sumo.tests import LocalizingClient, TestCase, with_save
from kitsune.users.tests import user, profile


class TestCaseBase(TestCase):
    """Base TestCase for the Questions app test cases."""
    client_class = LocalizingClient


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
        defaults['creator'] = profile().user
    return Question(**defaults)


@with_save
def questionvote(**kwargs):
    defaults = dict(created=datetime.now())
    defaults.update(kwargs)
    if 'question' not in kwargs and 'queation_id' not in kwargs:
        defaults['question'] = question(save=True)
    if 'creator' not in kwargs and 'creator_id' not in kwargs:
        defaults['creator'] = profile().user
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
