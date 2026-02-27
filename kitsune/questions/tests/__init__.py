import factory
from django.utils import timezone

from kitsune.questions.models import (
    AAQConfig,
    Answer,
    AnswerVote,
    Question,
    QuestionLocale,
    QuestionVote,
)
from kitsune.sumo.tests import FuzzyUnicode, TestCase
from kitsune.users.tests import UserFactory


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
    def metadata(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing
            return

        if extracted is not None:
            self.add_metadata(**extracted)

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing
            return

        if extracted is not None:
            for tag in extracted:
                self.tags.add(tag)


class QuestionVoteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = QuestionVote

    created = factory.LazyAttribute(lambda o: timezone.now())
    question = factory.SubFactory(QuestionFactory)
    creator = factory.SubFactory(UserFactory)


class QuestionLocaleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = QuestionLocale


class AAQConfigFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AAQConfig

    title = FuzzyUnicode()

    @factory.post_generation
    def enabled_locales(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing
            return

        if extracted is not None:
            for locale in extracted:
                self.enabled_locales.add(locale)

    @factory.post_generation
    def associated_tags(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing
            return

        if extracted is not None:
            for tag in extracted:
                self.associated_tags.add(tag)


class AnswerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Answer

    content = FuzzyUnicode()
    created = factory.LazyAttribute(lambda a: timezone.now())
    creator = factory.SubFactory(UserFactory)
    question = factory.SubFactory(QuestionFactory)


class SolutionAnswerFactory(AnswerFactory):
    @factory.post_generation
    def set_question_solution(self, create, extracted, **kwargs):
        self.question.solution = self
        self.save()


class AnswerVoteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AnswerVote

    created = factory.LazyAttribute(lambda a: timezone.now())
    helpful = factory.fuzzy.FuzzyChoice([True, False])
    creator = factory.SubFactory(UserFactory)
    answer = factory.SubFactory(AnswerFactory)
