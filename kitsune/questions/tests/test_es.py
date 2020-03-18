from datetime import datetime, timedelta

from nose.tools import eq_
from pyquery import PyQuery as pq

from kitsune.products.tests import ProductFactory
from kitsune.questions.models import QuestionMappingType, AnswerMetricsMappingType
from kitsune.questions.tests import (
    QuestionFactory,
    AnswerFactory,
    AnswerVoteFactory,
    QuestionVoteFactory,
)
from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.sumo.tests import LocalizingClient
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.models import Profile
from kitsune.users.tests import UserFactory


class QuestionUpdateTests(ElasticTestCase):
    def test_added(self):
        search = QuestionMappingType.search()

        # Create a question--that adds one document to the index.
        q = QuestionFactory(title=u"Does this test work?")
        self.refresh()
        eq_(search.count(), 1)
        eq_(search.query(question_title__match="test").count(), 1)

        # No answer exist, so none should be searchable.
        eq_(search.query(question_answer_content__match="only").count(), 0)

        # Create an answer for the question. It should be searchable now.
        AnswerFactory(content=u"There's only one way to find out!", question=q)
        self.refresh()
        eq_(search.query(question_answer_content__match="only").count(), 1)

        # Make sure that there's only one question document in the index--creating an answer
        # should have updated the existing one.
        eq_(search.count(), 1)

    def test_question_no_answers_deleted(self):
        search = QuestionMappingType.search()

        q = QuestionFactory(title=u"Does this work?")
        self.refresh()
        eq_(search.query(question_title__match="work").count(), 1)

        q.delete()
        self.refresh()
        eq_(search.query(question_title__match="work").count(), 0)

    def test_question_one_answer_deleted(self):
        search = QuestionMappingType.search()

        q = QuestionFactory(title=u"are model makers the new pink?")
        a = AnswerFactory(content=u"yes.", question=q)
        self.refresh()

        # Question and its answers are a single document--so the index count should be only 1.
        eq_(search.query(question_title__match="pink").count(), 1)

        # After deleting the answer, the question document should remain.
        a.delete()
        self.refresh()
        eq_(search.query(question_title__match="pink").count(), 1)

        # Delete the question and it should be removed from the index.
        q.delete()
        self.refresh()
        eq_(search.query(question_title__match="pink").count(), 0)

    def test_question_questionvote(self):
        search = QuestionMappingType.search()

        # Create a question and verify it doesn't show up in a
        # query for num_votes__gt=0.
        q = QuestionFactory(title=u"model makers will inherit the earth")
        self.refresh()
        eq_(search.filter(question_num_votes__gt=0).count(), 0)

        # Add a QuestionVote--it should show up now.
        QuestionVoteFactory(question=q)
        self.refresh()
        eq_(search.filter(question_num_votes__gt=0).count(), 1)

    def test_questions_tags(self):
        """Make sure that adding tags to a Question causes it to
        refresh the index.

        """
        tag = u"hiphop"
        eq_(QuestionMappingType.search().filter(question_tag=tag).count(), 0)
        q = QuestionFactory()
        self.refresh()
        eq_(QuestionMappingType.search().filter(question_tag=tag).count(), 0)
        q.tags.add(tag)
        self.refresh()
        eq_(QuestionMappingType.search().filter(question_tag=tag).count(), 1)
        q.tags.remove(tag)
        self.refresh()
        eq_(QuestionMappingType.search().filter(question_tag=tag).count(), 0)

    def test_question_is_unindexed_on_creator_delete(self):
        search = QuestionMappingType.search()

        q = QuestionFactory(title=u"Does this work?")
        self.refresh()
        eq_(search.query(question_title__match="work").count(), 1)

        q.creator.delete()
        self.refresh()
        eq_(search.query(question_title__match="work").count(), 0)

    def test_question_is_reindexed_on_username_change(self):
        search = QuestionMappingType.search()

        u = UserFactory(username="dexter")

        QuestionFactory(creator=u, title=u"Hello")
        AnswerFactory(creator=u, content=u"I love you")
        self.refresh()
        eq_(
            search.query(question_title__match="hello")[0]["question_creator"],
            u"dexter",
        )
        query = search.query(question_answer_content__match="love")
        eq_(query[0]["question_answer_creator"], [u"dexter"])

        # Change the username and verify the index.
        u.username = "walter"
        u.save()
        self.refresh()
        eq_(
            search.query(question_title__match="hello")[0]["question_creator"],
            u"walter",
        )
        query = search.query(question_answer_content__match="love")
        eq_(query[0]["question_answer_creator"], [u"walter"])

    def test_question_spam_is_unindexed(self):
        search = QuestionMappingType.search()

        q = QuestionFactory(title=u"I am spam")
        self.refresh()
        eq_(search.query(question_title__match="spam").count(), 1)

        q.is_spam = True
        q.save()
        self.refresh()
        eq_(search.query(question_title__match="spam").count(), 0)

    def test_answer_spam_is_unindexed(self):
        search = QuestionMappingType.search()

        a = AnswerFactory(content=u"I am spam")
        self.refresh()
        eq_(search.query(question_answer_content__match="spam").count(), 1)

        a.is_spam = True
        a.save()
        self.refresh()
        eq_(search.query(question_answer_content__match="spam").count(), 0)


class QuestionSearchTests(ElasticTestCase):
    """Tests about searching for questions"""

    def test_case_insensitive_search(self):
        """Ensure the default searcher is case insensitive."""
        q = QuestionFactory(title="lolrus", content="I am the lolrus.")
        AnswerVoteFactory(answer__question=q)
        self.refresh()
        # This is an AND operation
        result = QuestionMappingType.search().query(
            question_title__match="LOLRUS", question_content__match="LOLRUS"
        )
        assert result.count() > 0


class AnswerMetricsTests(ElasticTestCase):
    def test_add_and_delete(self):
        """Adding an answer should add it to the index.

        Deleting should delete it.
        """
        a = AnswerFactory()
        self.refresh()
        eq_(AnswerMetricsMappingType.search().count(), 1)

        a.delete()
        self.refresh()
        eq_(AnswerMetricsMappingType.search().count(), 0)

    def test_data_in_index(self):
        """Verify the data we are indexing."""
        p = ProductFactory()
        q = QuestionFactory(locale="pt-BR", product=p)
        a = AnswerFactory(question=q)

        self.refresh()

        eq_(AnswerMetricsMappingType.search().count(), 1)
        data = AnswerMetricsMappingType.search()[0]
        eq_(data["locale"], q.locale)
        eq_(data["product"], [p.slug])
        eq_(data["creator_id"], a.creator_id)
        eq_(data["is_solution"], False)
        eq_(data["by_asker"], False)

        # Mark as solution and verify
        q.solution = a
        q.save()

        self.refresh()
        data = AnswerMetricsMappingType.search()[0]
        eq_(data["is_solution"], True)

        # Make the answer creator to be the question creator and verify.
        a.creator = q.creator
        a.save()

        self.refresh()
        data = AnswerMetricsMappingType.search()[0]
        eq_(data["by_asker"], True)


class SupportForumTopContributorsTests(ElasticTestCase):
    client_class = LocalizingClient

    def test_top_contributors(self):
        # There should be no top contributors since there are no answers.
        response = self.client.get(reverse("questions.list", args=["all"]))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(0, len(doc("#top-contributors ol li")))

        # Add an answer, we now have a top conributor.
        a = AnswerFactory()
        self.refresh()
        response = self.client.get(reverse("questions.list", args=["all"]))
        eq_(200, response.status_code)
        doc = pq(response.content)
        lis = doc("#top-contributors ol li")
        eq_(1, len(lis))
        eq_(Profile.objects.get(user=a.creator).display_name, lis[0].text)

        # Make answer 91 days old. There should no be top contributors.
        a.created = datetime.now() - timedelta(days=91)
        a.save()
        self.refresh()
        response = self.client.get(reverse("questions.list", args=["all"]))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(0, len(doc("#top-contributors ol li")))
