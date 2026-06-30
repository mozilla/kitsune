import json
from datetime import timedelta
from unittest import mock

import actstream.actions
from actstream.models import Follow
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.exceptions import APIException
from rest_framework.test import APIClient

from kitsune.products.models import ProductSupportConfig
from kitsune.products.tests import ProductFactory, ProductSupportConfigFactory, TopicFactory
from kitsune.questions import api
from kitsune.questions.models import Answer, Question
from kitsune.questions.tests import (
    AAQConfigFactory,
    AnswerFactory,
    AnswerVoteFactory,
    QuestionFactory,
    QuestionVoteFactory,
    tags_eq,
)
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.tags.tests import TagFactory
from kitsune.users.models import Profile
from kitsune.users.templatetags.jinja_helpers import profile_avatar
from kitsune.users.tests import UserFactory, add_permission


class TestQuestionSerializerDeserialization(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.product = ProductFactory()
        self.topic = TopicFactory(products=[self.product])
        self.request = mock.Mock()
        self.request.user = self.user
        self.context = {
            "request": self.request,
        }
        self.data = {
            "creator": self.user.profile,
            "title": "How do I test programs?",
            "content": "Help, I don't know what to do.",
            "product": self.product.slug,
            "topic": self.topic.slug,
        }

    def test_it_works(self):
        serializer = api.QuestionSerializer(context=self.context, data=self.data)
        serializer.is_valid(raise_exception=True)

    def test_automatic_creator(self):
        del self.data["creator"]
        serializer = api.QuestionSerializer(context=self.context, data=self.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        self.assertEqual(obj.creator, self.user)

    def test_product_required(self):
        del self.data["product"]
        serializer = api.QuestionSerializer(context=self.context, data=self.data)
        assert not serializer.is_valid()
        self.assertEqual(
            serializer.errors,
            {
                "product": ["This field is required."],
                "topic": ["A product must be specified to select a topic."],
            },
        )

    def test_topic_required(self):
        del self.data["topic"]
        serializer = api.QuestionSerializer(context=self.context, data=self.data)
        assert not serializer.is_valid()
        self.assertEqual(
            serializer.errors,
            {
                "topic": ["This field is required."],
            },
        )

    def test_topic_disambiguation(self):
        # First make another product, and a colliding topic.
        # It has the same slug, but a different product.
        new_product = ProductFactory()
        TopicFactory(products=[new_product], slug=self.topic.slug)
        serializer = api.QuestionSerializer(context=self.context, data=self.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        self.assertEqual(obj.topic, self.topic)

    def test_solution_is_readonly(self):
        q = QuestionFactory()
        a = AnswerFactory(question=q)
        self.data["solution"] = a.id
        serializer = api.QuestionSerializer(context=self.context, data=self.data, instance=q)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        self.assertEqual(q.solution, None)


class TestQuestionSerializerSerialization(TestCase):
    def setUp(self):
        self.asker = UserFactory()
        self.helper1 = UserFactory()
        self.helper2 = UserFactory()
        self.question = QuestionFactory(creator=self.asker)

    def _names(self, *users):
        return sorted(
            (
                {
                    "username": u.username,
                    "display_name": Profile.objects.get(user=u).name,
                    "avatar": profile_avatar(u),
                }
                for u in users
            ),
            key=lambda d: d["username"],
        )

    def _answer(self, user):
        return AnswerFactory(question=self.question, creator=user)

    def test_no_votes(self):
        serializer = api.QuestionSerializer(instance=self.question)
        self.assertEqual(serializer.data["num_votes"], 0)

    def test_with_votes(self):
        QuestionVoteFactory(question=self.question)
        QuestionVoteFactory(question=self.question)
        QuestionVoteFactory()
        serializer = api.QuestionSerializer(instance=self.question)
        self.assertEqual(serializer.data["num_votes"], 2)

    def test_just_asker(self):
        serializer = api.QuestionSerializer(instance=self.question)
        self.assertEqual(serializer.data["involved"], self._names(self.asker))

    def test_one_answer(self):
        self._answer(self.helper1)

        serializer = api.QuestionSerializer(instance=self.question)
        self.assertEqual(
            sorted(serializer.data["involved"], key=lambda d: d["username"]),
            self._names(self.asker, self.helper1),
        )

    def test_asker_and_response(self):
        self._answer(self.helper1)
        self._answer(self.asker)

        serializer = api.QuestionSerializer(instance=self.question)
        self.assertEqual(
            sorted(serializer.data["involved"], key=lambda d: d["username"]),
            self._names(self.asker, self.helper1),
        )

    def test_asker_and_two_answers(self):
        self._answer(self.helper1)
        self._answer(self.asker)
        self._answer(self.helper2)

        serializer = api.QuestionSerializer(instance=self.question)
        self.assertEqual(
            sorted(serializer.data["involved"], key=lambda d: d["username"]),
            self._names(self.asker, self.helper1, self.helper2),
        )

    def test_solution_is_id(self):
        a = self._answer(self.helper1)
        self.question.solution = a
        self.question.save()

        serializer = api.QuestionSerializer(instance=self.question)
        self.assertEqual(serializer.data["solution"], a.id)

    def test_creator_is_object(self):
        serializer = api.QuestionSerializer(instance=self.question)
        self.assertEqual(
            serializer.data["creator"],
            {
                "username": self.question.creator.username,
                "display_name": Profile.objects.get(user=self.question.creator).display_name,
                "avatar": profile_avatar(self.question.creator),
            },
        )

    def test_creator_without_profile_serializes_as_none(self):
        """Regression test for #7591.

        Serializing a Question is a read-only operation, so a creator who
        has no Profile must serialize as None rather than triggering a
        write (``get_or_create``) during serialization.
        """
        self.question.creator.profile.delete()
        profiles_before = Profile.objects.count()

        # Re-fetch so the serializer reads the creator's profile state from the
        # database, not the stale Profile left cached on the in-memory instance
        # by the delete above. This mirrors how the viewset loads a question
        # fresh on each request.
        question = Question.objects.get(pk=self.question.pk)
        serializer = api.QuestionSerializer(instance=question)

        self.assertIsNone(serializer.data["creator"])
        # Serialization must not create a Profile for the profile-less creator.
        self.assertEqual(Profile.objects.count(), profiles_before)

    def test_system_account_creator_serializes_as_none(self):
        """A system account creator must serialize as None, matching
        RegularProfileManager (which the reverse profile accessor bypasses)."""
        profile = self.question.creator.profile
        profile.account_type = Profile.AccountType.SYSTEM
        profile.save()

        question = Question.objects.get(pk=self.question.pk)
        serializer = api.QuestionSerializer(instance=question)

        self.assertIsNone(serializer.data["creator"])

    def test_system_account_excluded_from_involved(self):
        """A system account that answered must not appear in involved users."""
        bot = UserFactory()
        bot.profile.account_type = Profile.AccountType.SYSTEM
        bot.profile.save()
        self._answer(self.helper1)
        self._answer(bot)

        question = Question.objects.get(pk=self.question.pk)
        serializer = api.QuestionSerializer(instance=question)

        usernames = {profile["username"] for profile in serializer.data["involved"]}
        self.assertIn(self.helper1.username, usernames)
        self.assertNotIn(bot.username, usernames)

    def test_with_tags(self):
        self.question.tags.add("tag1")
        self.question.tags.add("tag2")
        serializer = api.QuestionSerializer(instance=self.question)
        self.assertEqual(
            serializer.data["tags"],
            [
                {"name": "tag1", "slug": "tag1"},
                {"name": "tag2", "slug": "tag2"},
            ],
        )


class TestQuestionViewSet(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create(self):
        u = UserFactory()
        p = ProductFactory()
        t = TopicFactory(products=[p])
        self.client.force_authenticate(user=u)
        data = {
            "title": "How do I start Firefox?",
            "content": "Seriously, what do I do?",
            "product": p.slug,
            "topic": t.slug,
        }
        self.assertEqual(Question.objects.count(), 0)
        res = self.client.post(reverse("question-list"), data)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Question.objects.count(), 1)
        q = Question.objects.all()[0]
        self.assertEqual(q.title, data["title"])
        self.assertEqual(q.content, data["content"])
        self.assertEqual(q.content_parsed, res.data["content"])

    def test_delete_permissions(self):
        u1 = UserFactory()
        u2 = UserFactory()
        q = QuestionFactory(creator=u1)

        # Anonymous user can't delete
        self.client.force_authenticate(user=None)
        res = self.client.delete(reverse("question-detail", args=[q.id]))
        self.assertEqual(res.status_code, 401)  # Unauthorized

        # Non-owner can't delete
        self.client.force_authenticate(user=u2)
        res = self.client.delete(reverse("question-detail", args=[q.id]))
        self.assertEqual(res.status_code, 403)  # Forbidden

        # Owner can delete
        self.client.force_authenticate(user=u1)
        res = self.client.delete(reverse("question-detail", args=[q.id]))
        self.assertEqual(res.status_code, 204)  # No content

    def test_solve(self):
        q = QuestionFactory()
        a = AnswerFactory(question=q)

        self.client.force_authenticate(user=q.creator)
        res = self.client.post(reverse("question-solve", args=[q.id]), data={"answer": a.id})
        self.assertEqual(res.status_code, 204)
        q = Question.objects.get(id=q.id)
        self.assertEqual(q.solution, a)

    def test_filter_is_taken_true(self):
        q1 = QuestionFactory()
        q2 = QuestionFactory()
        q2.take(q1.creator)

        url = reverse("question-list") + "?is_taken=1"
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(res.data["results"][0]["id"], q2.id)

    def test_filter_is_taken_false(self):
        q1 = QuestionFactory()
        q2 = QuestionFactory()
        q2.take(q1.creator)

        url = reverse("question-list") + "?is_taken=0"
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(res.data["results"][0]["id"], q1.id)

    def test_filter_is_taken_expired(self):
        q = QuestionFactory()
        # "take" the question, but with an expired timer.
        q.taken_by = UserFactory()
        q.taken_until = timezone.now() - timedelta(seconds=60)

        url = reverse("question-list") + "?is_taken=1"
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 0)

    def test_filter_taken_by_username(self):
        q1 = QuestionFactory()
        q2 = QuestionFactory()
        q2.take(q1.creator)

        url = reverse("question-list") + "?taken_by=" + q1.creator.username
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(res.data["results"][0]["id"], q2.id)

    def test_helpful(self):
        q = QuestionFactory()
        u = UserFactory()
        self.client.force_authenticate(user=u)
        res = self.client.post(reverse("question-helpful", args=[q.id]))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, {"num_votes": 1})
        self.assertEqual(Question.objects.get(id=q.id).num_votes, 1)

    def test_helpful_rate_limit(self):
        u = UserFactory()
        self.client.force_authenticate(user=u)

        # The first ten votes by this user today should be fine.
        for _ in range(10):
            q = QuestionFactory()
            res = self.client.post(reverse("question-helpful", args=[q.id]))
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.data, {"num_votes": 1})
            self.assertEqual(Question.objects.get(id=q.id).num_votes, 1)

        # The eleventh vote by this user today should trigger the rate limit.
        q = QuestionFactory()
        res = self.client.post(reverse("question-helpful", args=[q.id]))
        self.assertEqual(res.status_code, 429)
        # The vote count should not have changed.
        self.assertEqual(Question.objects.get(id=q.id).num_votes, 0)

    def test_helpful_double_vote(self):
        q = QuestionFactory()
        u = UserFactory()
        QuestionVoteFactory(question=q, creator=u)
        self.client.force_authenticate(user=u)
        res = self.client.post(reverse("question-helpful", args=[q.id]))
        self.assertEqual(res.status_code, 409)
        # It's 1, not 0, because one was created above. The failure cause is
        # if the number of votes is 2, one from above and one from the api call.
        self.assertEqual(Question.objects.get(id=q.id).num_votes, 1)

    def test_helpful_question_not_editable(self):
        q = QuestionFactory(is_locked=True)
        u = UserFactory()
        self.client.force_authenticate(user=u)
        res = self.client.post(reverse("question-helpful", args=[q.id]))
        self.assertEqual(res.status_code, 403)
        self.assertEqual(Question.objects.get(id=q.id).num_votes, 0)

    def test_ordering(self):
        q1 = QuestionFactory()
        q2 = QuestionFactory()
        q3 = QuestionFactory()
        AnswerFactory(question=q1)
        AnswerFactory(question=q2)

        res = self.client.get(reverse("question-list"))
        self.assertEqual(res.data["results"][0]["id"], q3.id)
        self.assertEqual(res.data["results"][1]["id"], q2.id)
        self.assertEqual(res.data["results"][2]["id"], q1.id)

        res = self.client.get(reverse("question-list") + "?ordering=id")
        self.assertEqual(res.data["results"][0]["id"], q1.id)
        self.assertEqual(res.data["results"][1]["id"], q2.id)
        self.assertEqual(res.data["results"][2]["id"], q3.id)

        res = self.client.get(reverse("question-list") + "?ordering=-last_answer")
        self.assertEqual(res.data["results"][0]["id"], q2.id)
        self.assertEqual(res.data["results"][1]["id"], q1.id)
        self.assertEqual(res.data["results"][2]["id"], q3.id)

        res = self.client.get(reverse("question-list") + "?ordering=last_answer")
        self.assertEqual(res.data["results"][0]["id"], q1.id)
        self.assertEqual(res.data["results"][1]["id"], q2.id)
        self.assertEqual(res.data["results"][2]["id"], q3.id)

    def test_list_ordering_by_updated_does_not_write_profiles(self):
        """Regression test for #7591.

        ``GET /api/2/question/?ordering=updated&updated__gt=`` is a
        read-only request and must never create Profile rows. Accounts
        without a Profile (common for old or imported users) previously
        triggered a per-row ``Profile.objects.get_or_create`` write while
        serializing the question's creator and involved users -- an N+1
        write-on-read that intermittently timed out (HTTP 500) on large,
        ordered result sets.
        """
        asker = UserFactory()
        answerer = UserFactory()
        question = QuestionFactory(creator=asker)
        AnswerFactory(question=question, creator=answerer)

        # Simulate accounts that have no Profile.
        Profile.objects.all().delete()
        self.assertEqual(Profile.objects.count(), 0)

        url = reverse("question-list") + "?ordering=updated&updated__gt=2000-01-01T00:00:00"
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 1)
        # The GET must not have created any Profile rows.
        self.assertEqual(Profile.objects.count(), 0)

    def test_serializing_more_involved_users_does_not_add_queries(self):
        """Regression test for #7591.

        Serializing a question's involved users must not run one query per
        answer author. With answers__creator__profile prefetched on the
        viewset, the query count is constant no matter how many distinct
        users answered -- this removes the N+1 read that, alongside the
        get_or_create write fixed in #7592, produced the intermittent HTTP
        500 on large result sets.
        """

        def query_count_for(num_answers):
            question = QuestionFactory()
            for _ in range(num_answers):
                AnswerFactory(question=question, creator=UserFactory())
            url = reverse("question-detail", args=[question.id])
            with CaptureQueriesContext(connection) as ctx:
                res = self.client.get(url)
            self.assertEqual(res.status_code, 200)
            # Sanity: the creator plus every distinct answerer is serialized.
            self.assertEqual(len(res.data["involved"]), num_answers + 1)
            return len(ctx.captured_queries)

        self.assertEqual(
            query_count_for(num_answers=1),
            query_count_for(num_answers=5),
            "Serializing more answer authors should not add queries; the "
            "involved profile lookup has regressed into an N+1.",
        )

    def test_list_query_count_is_fixed_for_populated_questions(self):
        """Regression test for #7591.

        Locks the query count for a representative page of fully-populated
        questions. Every related object the serializer reads -- creator,
        updated_by, taken_by, solution.creator, product, topic, answer
        authors, metadata and tags -- is select_related/prefetch_related on
        the viewset, so dropping any one of them reintroduces a per-row query
        and changes this count. Several questions (rather than one) are needed
        for the prefetched relations to show their savings.

        The expected count is fixed for this dataset, not invariant to page
        size: it includes one num_votes count-query per question, a separate
        per-row read not addressed here. Bump it if the serializer's related
        reads legitimately change.
        """
        product = ProductFactory()
        topic = TopicFactory(products=[product])
        for _ in range(3):
            question = QuestionFactory(
                creator=UserFactory(),
                product=product,
                topic=topic,
                metadata={"useragent": "Firefox"},
                tags=["tag1", "tag2"],
            )
            solution = AnswerFactory(question=question, creator=UserFactory())
            AnswerFactory(question=question, creator=UserFactory())
            question.solution = solution
            question.updated_by = UserFactory()
            question.taken_by = UserFactory()
            question.taken_until = timezone.now() + timedelta(days=1)
            question.save()

        url = reverse("question-list")
        with self.assertNumQueries(10):
            res = self.client.get(url)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 3)

    def test_filter_product_with_slug(self):
        p1 = ProductFactory()
        p2 = ProductFactory()
        q1 = QuestionFactory(product=p1)
        QuestionFactory(product=p2)

        querystring = "?product={}".format(p1.slug)
        res = self.client.get(reverse("question-list") + querystring)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["id"], q1.id)

    def test_filter_creator_with_username(self):
        q1 = QuestionFactory()
        QuestionFactory()

        querystring = "?creator={}".format(q1.creator.username)
        res = self.client.get(reverse("question-list") + querystring)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["id"], q1.id)

    def test_filter_involved(self):
        q1 = QuestionFactory()
        a1 = AnswerFactory(question=q1)
        q2 = QuestionFactory(creator=a1.creator)

        querystring = "?involved={}".format(q1.creator.username)
        res = self.client.get(reverse("question-list") + querystring)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["id"], q1.id)

        querystring = "?involved={}".format(q2.creator.username)
        res = self.client.get(reverse("question-list") + querystring)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data["results"]), 2)
        # The API has a default sort, so ordering will be consistent.
        self.assertEqual(res.data["results"][0]["id"], q2.id)
        self.assertEqual(res.data["results"][1]["id"], q1.id)

    def test_is_taken(self):
        q = QuestionFactory()
        u = UserFactory()
        q.take(u)
        url = reverse("question-detail", args=[q.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["taken_by"]["username"], u.username)

    def test_take(self):
        q = QuestionFactory()
        u = UserFactory()
        self.client.force_authenticate(user=u)
        res = self.client.post(reverse("question-take", args=[q.id]))
        self.assertEqual(res.status_code, 204)
        q = Question.objects.get(id=q.id)
        self.assertEqual(q.taken_by, u)

    def test_take_by_owner(self):
        q = QuestionFactory()
        self.client.force_authenticate(user=q.creator)
        res = self.client.post(reverse("question-take", args=[q.id]))
        self.assertEqual(res.status_code, 400)
        q = Question.objects.get(id=q.id)
        self.assertEqual(q.taken_by, None)

    def test_take_conflict(self):
        u1 = UserFactory()
        u2 = UserFactory()
        taken_until = timezone.now() + timedelta(seconds=30)
        q = QuestionFactory(taken_until=taken_until, taken_by=u1)
        self.client.force_authenticate(user=u2)
        res = self.client.post(reverse("question-take", args=[q.id]))
        self.assertEqual(res.status_code, 409)
        q = Question.objects.get(id=q.id)
        self.assertEqual(q.taken_by, u1)

    def test_follow(self):
        q = QuestionFactory()
        u = UserFactory()
        self.client.force_authenticate(user=u)
        res = self.client.post(reverse("question-follow", args=[q.id]))
        self.assertEqual(res.status_code, 204)
        f = Follow.objects.get(user=u)
        self.assertEqual(f.follow_object, q)
        self.assertEqual(f.actor_only, False)

    def test_unfollow(self):
        q = QuestionFactory()
        u = UserFactory()
        actstream.actions.follow(u, q, actor_only=False)
        self.assertEqual(Follow.objects.filter(user=u).count(), 1)  # pre-condition
        self.client.force_authenticate(user=u)
        res = self.client.post(reverse("question-unfollow", args=[q.id]))
        self.assertEqual(res.status_code, 204)
        self.assertEqual(Follow.objects.filter(user=u).count(), 0)

    def test_remove_tags_without_perms(self):
        q = QuestionFactory()
        q.tags.add("test")
        q.tags.add("more")
        q.tags.add("tags")
        self.assertEqual(3, q.tags.count())

        u = UserFactory()
        self.client.force_authenticate(user=u)

        res = self.client.post(
            reverse("question-remove-tags", args=[q.id]),
            content_type="application/json",
            data=json.dumps({"tags": ["more", "tags"]}),
        )
        self.assertEqual(res.status_code, 403)
        self.assertEqual(3, q.tags.count())

    def test_remove_tags_with_perms(self):
        q = QuestionFactory()
        q.tags.add("test")
        q.tags.add("more")
        q.tags.add("tags")
        self.assertEqual(3, q.tags.count())

        u = UserFactory()
        add_permission(u, Question, "remove_tag")
        self.client.force_authenticate(user=u)

        res = self.client.post(
            reverse("question-remove-tags", args=[q.id]),
            content_type="application/json",
            data=json.dumps({"tags": ["more", "tags"]}),
        )
        self.assertEqual(res.status_code, 204)
        self.assertEqual(1, q.tags.count())

    def test_bleaching(self):
        """Tests whether question content is bleached."""
        q = QuestionFactory(content="<unbleached>Cupcakes are the best</unbleached>")
        url = reverse("question-detail", args=[q.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        assert "<unbleached>" not in res.data["content"]

    def test_auto_tagging(self):
        """Test that questions created via the API are auto-tagged."""
        tag = TagFactory(name="desktop")
        product = ProductFactory()
        aaq_config = AAQConfigFactory(associated_tags=[tag])
        ProductSupportConfigFactory(
            product=product,
            forum_config=aaq_config,
            is_active=True,
            default_support_type=ProductSupportConfig.SUPPORT_TYPE_FORUM,
        )

        q = QuestionFactory(product=product)
        self.client.force_authenticate(user=q.creator)
        tags_eq(q, [])

        res = self.client.post(
            reverse("question-set-metadata", args=[q.id]),
            content_type="application/json",
            data=json.dumps({"name": "product", "value": "desktop"}),
        )
        self.assertEqual(res.status_code, 200)
        tags_eq(q, [])

        res = self.client.post(
            reverse("question-auto-tag", args=[q.id]), content_type="application/json"
        )
        self.assertEqual(res.status_code, 204)
        tags_eq(q, ["desktop"])


class TestAnswerSerializerDeserialization(TestCase):
    def test_no_votes(self):
        a = AnswerFactory()
        serializer = api.AnswerSerializer(instance=a)
        self.assertEqual(serializer.data["num_helpful_votes"], 0)
        self.assertEqual(serializer.data["num_unhelpful_votes"], 0)

    def test_with_votes(self):
        a = AnswerFactory()
        AnswerVoteFactory(answer=a, helpful=True)
        AnswerVoteFactory(answer=a, helpful=True)
        AnswerVoteFactory(answer=a, helpful=False)
        AnswerVoteFactory()

        serializer = api.AnswerSerializer(instance=a)
        self.assertEqual(serializer.data["num_helpful_votes"], 2)
        self.assertEqual(serializer.data["num_unhelpful_votes"], 1)


class TestAnswerViewSet(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_query_count_is_fixed_for_distinct_authors(self):
        """Regression test for #7591.

        Locks the query count for an answer page whose answers have distinct
        creators and updated_by users. Those profiles are select_related, and
        the parent question is emitted as its FK id (no JOIN), so dropping a
        select_related -- or turning the question field into a related lookup
        -- would change this count.

        The expected count includes per-answer num_helpful_votes and
        num_unhelpful_votes count-queries, separate per-row reads not
        addressed here. Bump it if the serializer's related reads change.
        """
        question = QuestionFactory()
        for _ in range(3):
            answer = AnswerFactory(question=question, creator=UserFactory())
            answer.updated_by = UserFactory()
            answer.save()

        url = reverse("answer-list")
        with self.assertNumQueries(11):
            res = self.client.get(url)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 3)

    def test_create(self):
        q = QuestionFactory()
        u = UserFactory()
        self.client.force_authenticate(user=u)
        data = {
            "question": q.id,
            "content": "You just need to click the fox.",
        }
        self.assertEqual(Answer.objects.count(), 0)
        res = self.client.post(reverse("answer-list"), data)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Answer.objects.count(), 1)
        a = Answer.objects.all()[0]
        self.assertEqual(a.content, data["content"])
        self.assertEqual(a.content_parsed, res.data["content"])
        self.assertEqual(a.question, q)

    def test_delete_permissions(self):
        u1 = UserFactory()
        u2 = UserFactory()
        a = AnswerFactory(creator=u1)

        # Anonymous user can't delete
        self.client.force_authenticate(user=None)
        res = self.client.delete(reverse("answer-detail", args=[a.id]))
        self.assertEqual(res.status_code, 401)  # Unauthorized

        # Non-owner can't deletea
        self.client.force_authenticate(user=u2)
        res = self.client.delete(reverse("answer-detail", args=[a.id]))
        self.assertEqual(res.status_code, 403)  # Forbidden

        # Owner can delete
        self.client.force_authenticate(user=u1)
        res = self.client.delete(reverse("answer-detail", args=[a.id]))
        self.assertEqual(res.status_code, 204)  # No content

    def test_ordering(self):
        a1 = AnswerFactory()
        a2 = AnswerFactory()

        res = self.client.get(reverse("answer-list"))
        self.assertEqual(res.data["results"][0]["id"], a2.id)
        self.assertEqual(res.data["results"][1]["id"], a1.id)

        res = self.client.get(reverse("answer-list") + "?ordering=id")
        self.assertEqual(res.data["results"][0]["id"], a1.id)
        self.assertEqual(res.data["results"][1]["id"], a2.id)

        res = self.client.get(reverse("answer-list") + "?ordering=-id")
        self.assertEqual(res.data["results"][0]["id"], a2.id)
        self.assertEqual(res.data["results"][1]["id"], a1.id)

    def test_helpful(self):
        a = AnswerFactory()
        u = UserFactory()
        self.client.force_authenticate(user=u)
        res = self.client.post(reverse("answer-helpful", args=[a.id]))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, {"num_helpful_votes": 1, "num_unhelpful_votes": 0})
        self.assertEqual(Answer.objects.get(id=a.id).num_votes, 1)

    def test_helpful_rate_limit(self):
        u = UserFactory()
        self.client.force_authenticate(user=u)

        # The first ten votes by this user today should be fine.
        for _ in range(10):
            a = AnswerFactory()
            res = self.client.post(reverse("answer-helpful", args=[a.id]))
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.data, {"num_helpful_votes": 1, "num_unhelpful_votes": 0})
            self.assertEqual(Answer.objects.get(id=a.id).num_votes, 1)

        # The eleventh vote by this user today should trigger the rate limit.
        a = AnswerFactory()
        res = self.client.post(reverse("answer-helpful", args=[a.id]))
        self.assertEqual(res.status_code, 429)
        # The vote count should not have changed.
        self.assertEqual(Answer.objects.get(id=a.id).num_votes, 0)

    def test_helpful_double_vote(self):
        a = AnswerFactory()
        u = UserFactory()
        AnswerVoteFactory(answer=a, creator=u)
        self.client.force_authenticate(user=u)
        res = self.client.post(reverse("answer-helpful", args=[a.id]))
        self.assertEqual(res.status_code, 409)
        # It's 1, not 0, because one was created above. The failure cause is
        # if the number of votes is 2, one from above and one from the api call.
        self.assertEqual(Answer.objects.get(id=a.id).num_votes, 1)

    def test_helpful_answer_not_editable(self):
        q = QuestionFactory(is_locked=True)
        a = AnswerFactory(question=q)
        u = UserFactory()
        self.client.force_authenticate(user=u)
        res = self.client.post(reverse("answer-helpful", args=[a.id]))
        self.assertEqual(res.status_code, 403)
        self.assertEqual(Answer.objects.get(id=a.id).num_votes, 0)

    def test_follow(self):
        a = AnswerFactory()
        u = UserFactory()
        self.client.force_authenticate(user=u)
        self.assertEqual(Follow.objects.filter(user=u).count(), 0)  # pre-condition
        res = self.client.post(reverse("answer-follow", args=[a.id]))
        self.assertEqual(res.status_code, 204)
        f = Follow.objects.get(user=u)
        self.assertEqual(f.follow_object, a)
        self.assertEqual(f.actor_only, False)

    def test_unfollow(self):
        a = AnswerFactory()
        u = UserFactory()
        actstream.actions.follow(u, a, actor_only=False)
        self.assertEqual(Follow.objects.filter(user=u).count(), 1)  # pre-condition
        self.client.force_authenticate(user=u)
        res = self.client.post(reverse("answer-unfollow", args=[a.id]))
        self.assertEqual(res.status_code, 204)
        self.assertEqual(Follow.objects.filter(user=u).count(), 0)

    def test_bleaching(self):
        """Tests whether answer content is bleached."""
        a = AnswerFactory(content="<unbleached>Cupcakes are the best</unbleached>")
        url = reverse("answer-detail", args=[a.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        assert "<unbleached>" not in res.data["content"]

    def test_cannot_create_answer_on_locked_question(self):
        q = QuestionFactory(is_locked=True)
        u = UserFactory()
        self.client.force_authenticate(user=u)
        data = {"question": q.id, "content": "Sneaking onto a locked question."}
        res = self.client.post(reverse("answer-list"), data)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(Answer.objects.count(), 0)

    def test_cannot_create_answer_on_archived_question(self):
        q = QuestionFactory(is_archived=True)
        u = UserFactory()
        self.client.force_authenticate(user=u)
        data = {"question": q.id, "content": "Sneaking onto an archived question."}
        res = self.client.post(reverse("answer-list"), data)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(Answer.objects.count(), 0)

    def test_cannot_move_answer_onto_locked_question_via_patch(self):
        u = UserFactory()
        open_q = QuestionFactory()
        locked_q = QuestionFactory(is_locked=True)
        answer = AnswerFactory(question=open_q, creator=u)
        self.client.force_authenticate(user=u)
        res = self.client.patch(
            reverse("answer-detail", args=[answer.id]), {"question": locked_q.id}
        )
        self.assertEqual(res.status_code, 405)
        answer.refresh_from_db()
        self.assertEqual(answer.question, open_q)

    def test_put_is_not_allowed(self):
        u = UserFactory()
        answer = AnswerFactory(creator=u)
        self.client.force_authenticate(user=u)
        res = self.client.put(
            reverse("answer-detail", args=[answer.id]),
            {"question": answer.question_id, "content": "rewritten"},
        )
        self.assertEqual(res.status_code, 405)


class TestQuestionFilter(TestCase):
    def setUp(self):
        self.filter_instance = api.QuestionFilter()
        self.queryset = Question.objects.all()

    def filter(self, filter_data):
        return self.filter_instance.filter_metadata(
            self.queryset, "metadata", json.dumps(filter_data)
        )

    def test_filter_involved(self):
        q1 = QuestionFactory()
        a1 = AnswerFactory(question=q1)
        q2 = QuestionFactory(creator=a1.creator)

        qs = self.filter_instance.filter_involved(
            self.queryset, "filter_involved", q1.creator.username
        )
        self.assertEqual(list(qs), [q1])

        qs = self.filter_instance.filter_involved(
            self.queryset, "filter_involved", q2.creator.username
        )
        # The filter does not have a strong order.
        qs = sorted(qs, key=lambda q: q.id)
        self.assertEqual(qs, [q1, q2])

    def test_filter_is_solved(self):
        q1 = QuestionFactory()
        a1 = AnswerFactory(question=q1)
        q1.solution = a1
        q1.save()
        q2 = QuestionFactory()

        qs = self.filter_instance.filter_is_solved(self.queryset, "is_solved", True)
        self.assertEqual(list(qs), [q1])

        qs = self.filter_instance.filter_is_solved(self.queryset, "is_solved", False)
        self.assertEqual(list(qs), [q2])

    def test_filter_solved_by(self):
        q1 = QuestionFactory()
        a1 = AnswerFactory(question=q1)
        q1.solution = a1
        q1.save()
        q2 = QuestionFactory()
        AnswerFactory(question=q2, creator=a1.creator)
        q3 = QuestionFactory()
        a3 = AnswerFactory(question=q3)
        q3.solution = a3
        q3.save()

        qs = self.filter_instance.filter_solved_by(self.queryset, "solved_by", a1.creator.username)
        self.assertEqual(list(qs), [q1])

        qs = self.filter_instance.filter_solved_by(self.queryset, "solved_by", a3.creator.username)
        self.assertEqual(list(qs), [q3])

    def test_metadata_not_json(self):
        with self.assertRaises(APIException):
            self.filter_instance.filter_metadata(self.queryset, "metadata", "not json")

    def test_metadata_bad_json(self):
        with self.assertRaises(APIException):
            self.filter_instance.filter_metadata(self.queryset, "metadata", "not json")

    def test_single_filter_match(self):
        q1 = QuestionFactory(metadata={"os": "Linux"})
        QuestionFactory(metadata={"os": "OSX"})
        res = self.filter({"os": "Linux"})
        self.assertEqual(list(res), [q1])

    def test_single_filter_no_match(self):
        QuestionFactory(metadata={"os": "Linux"})
        QuestionFactory(metadata={"os": "OSX"})
        res = self.filter({"os": "Windows 8"})
        self.assertEqual(list(res), [])

    def test_multi_filter_is_and(self):
        q1 = QuestionFactory(metadata={"os": "Linux", "category": "troubleshooting"})
        QuestionFactory(metadata={"os": "OSX", "category": "troubleshooting"})
        res = self.filter({"os": "Linux", "category": "troubleshooting"})
        self.assertEqual(list(res), [q1])

    def test_list_value_is_or(self):
        q1 = QuestionFactory(metadata={"os": "Linux"})
        q2 = QuestionFactory(metadata={"os": "OSX"})
        QuestionFactory(metadata={"os": "Windows 7"})
        res = self.filter({"os": ["Linux", "OSX"]})
        self.assertEqual(sorted(res, key=lambda q: q.id), [q1, q2])

    def test_none_value_is_missing(self):
        q1 = QuestionFactory(metadata={})
        QuestionFactory(metadata={"os": "Linux"})
        res = self.filter({"os": None})
        self.assertEqual(list(res), [q1])

    def test_list_value_with_none(self):
        q1 = QuestionFactory(metadata={"os": "Linux"})
        q2 = QuestionFactory(metadata={})
        QuestionFactory(metadata={"os": "Windows 7"})
        res = self.filter({"os": ["Linux", None]})
        self.assertEqual(sorted(res, key=lambda q: q.id), [q1, q2])

    def test_is_taken(self):
        u = UserFactory()
        taken_until = timezone.now() + timedelta(seconds=30)
        q = QuestionFactory(taken_by=u, taken_until=taken_until)
        QuestionFactory()
        res = self.filter_instance.filter_is_taken(self.queryset, "is_taken", True)
        self.assertEqual(list(res), [q])

    def test_is_not_taken(self):
        u = UserFactory()
        taken_until = timezone.now() + timedelta(seconds=30)
        QuestionFactory(taken_by=u, taken_until=taken_until)
        q = QuestionFactory()
        res = self.filter_instance.filter_is_taken(self.queryset, "is_taken", False)
        self.assertEqual(list(res), [q])

    def test_is_taken_expired(self):
        u = UserFactory()
        taken_until = timezone.now() - timedelta(seconds=30)
        QuestionFactory(taken_by=u, taken_until=taken_until)
        res = self.filter_instance.filter_is_taken(self.queryset, "is_taken", True)
        self.assertEqual(list(res), [])

    def test_is_not_taken_expired(self):
        u = UserFactory()
        taken_until = timezone.now() - timedelta(seconds=30)
        q = QuestionFactory(taken_by=u, taken_until=taken_until)
        res = self.filter_instance.filter_is_taken(self.queryset, "is_taken", False)
        self.assertEqual(list(res), [q])

    def test_it_works_with_users_who_have_gotten_first_contrib_emails(self):
        # This flag caused a regression, tracked in bug 1163855.
        # The error was that the help text on the field was a str instead of a
        # unicode. Yes, really, that matters apparently.
        u = UserFactory(profile__first_answer_email_sent=True)
        QuestionFactory(creator=u)
        url = reverse("question-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
