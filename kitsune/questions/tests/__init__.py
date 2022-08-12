from datetime import datetime

import factory

from kitsune.questions.models import Answer, AnswerVote, Question, QuestionLocale, QuestionVote
from kitsune.sumo.tests import FuzzyUnicode, LocalizingClient, TestCase
from kitsune.users.tests import UserFactory


class TestCaseBase(TestCase):
    """Base TestCase for the Questions app test cases."""

    client_class = LocalizingClient


def tags_eq(tagged_object, tag_names):
    """Assert that the names of the tags on tagged_object are tag_names."""
    TestCase().assertEqual(sorted([t.name for t in tagged_object.tags.all()]), sorted(tag_names))


class QuestionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Question

    title = FuzzyUnicode()
    content = FuzzyUnicode()
    creator = factory.SubFactory(UserFactory)

    @factory.post_generation
    def metadata(q, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing
            return

        if extracted is not None:
            q.add_metadata(**extracted)

    @factory.post_generation
    def tags(q, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing
            return

        if extracted is not None:
            for tag in extracted:
                q.tags.add(tag)


class QuestionVoteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = QuestionVote

    created = factory.LazyAttribute(lambda o: datetime.now())
    question = factory.SubFactory(QuestionFactory)
    creator = factory.SubFactory(UserFactory)


class QuestionLocaleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = QuestionLocale

    @factory.post_generation
    def products(obj, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing
            return

        if extracted is not None:
            for product in extracted:
                obj.products.add(product)


class AnswerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Answer

    content = FuzzyUnicode()
    created = factory.LazyAttribute(lambda a: datetime.now())
    creator = factory.SubFactory(UserFactory)
    question = factory.SubFactory(QuestionFactory)


class SolutionAnswerFactory(AnswerFactory):
    @factory.post_generation
    def set_question_solution(obj, create, extracted, **kwargs):
        obj.question.solution = obj
        obj.save()


class AnswerVoteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AnswerVote

    created = factory.LazyAttribute(lambda a: datetime.now())
    helpful = factory.fuzzy.FuzzyChoice([True, False])
    creator = factory.SubFactory(UserFactory)
    answer = factory.SubFactory(AnswerFactory)
