# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

import mock
from actstream.models import Action, Follow
from django.core.management import call_command
from django.db.models import Q
from nose.tools import eq_, ok_, raises
from taggit.models import Tag

import kitsune.sumo.models
from kitsune.flagit.models import FlaggedObject
from kitsune.questions import config, models
from kitsune.questions.events import QuestionReplyEvent
from kitsune.questions.models import (
    AlreadyTakenException,
    Answer,
    InvalidUserException,
    Question,
    QuestionMetaData,
    QuestionVisits,
    VoteMetadata,
    _has_beta,
    _tenths_version,
)
from kitsune.questions.tasks import update_answer_pages
from kitsune.questions.tests import (
    AnswerFactory,
    QuestionFactory,
    QuestionVoteFactory,
    TestCaseBase,
    tags_eq,
)
from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.sumo import googleanalytics
from kitsune.sumo.tests import TestCase
from kitsune.tags.tests import TagFactory
from kitsune.tags.utils import add_existing_tag
from kitsune.users.tests import UserFactory
from kitsune.wiki.tests import TranslatedRevisionFactory


class TestAnswer(TestCaseBase):
    """Test the Answer model"""

    def test_new_answer_updates_question(self):
        """Test saving a new answer updates the corresponding question.
        Specifically, last_post and num_replies should update."""
        q = QuestionFactory(title="Test Question", content="Lorem Ipsum Dolor")
        updated = q.updated

        eq_(0, q.num_answers)
        eq_(None, q.last_answer)

        a = AnswerFactory(question=q, content="Test Answer")
        a.save()

        q = Question.objects.get(pk=q.id)
        eq_(1, q.num_answers)
        eq_(a, q.last_answer)
        self.assertNotEqual(updated, q.updated)

    def test_delete_question_removes_flag(self):
        """Deleting a question also removes the flags on that question."""
        q = QuestionFactory(title="Test Question", content="Lorem Ipsum Dolor")

        u = UserFactory()
        FlaggedObject.objects.create(
            status=0, content_object=q, reason="language", creator_id=u.id
        )
        eq_(1, FlaggedObject.objects.count())

        q.delete()
        eq_(0, FlaggedObject.objects.count())

    def test_delete_answer_removes_flag(self):
        """Deleting an answer also removes the flags on that answer."""
        q = QuestionFactory(title="Test Question", content="Lorem Ipsum Dolor")

        a = AnswerFactory(question=q, content="Test Answer")

        u = UserFactory()
        FlaggedObject.objects.create(
            status=0, content_object=a, reason="language", creator_id=u.id
        )
        eq_(1, FlaggedObject.objects.count())

        a.delete()
        eq_(0, FlaggedObject.objects.count())

    def test_delete_last_answer_of_question(self):
        """Deleting the last_answer of a Question should update the question.
        """
        yesterday = datetime.now() - timedelta(days=1)
        q = AnswerFactory(created=yesterday).question
        last_answer = q.last_answer

        # add a new answer and verify last_answer updated
        a = AnswerFactory(question=q, content="Test Answer")
        q = Question.objects.get(pk=q.id)

        eq_(q.last_answer.id, a.id)

        # delete the answer and last_answer should go back to previous value
        a.delete()
        q = Question.objects.get(pk=q.id)
        eq_(q.last_answer.id, last_answer.id)
        eq_(Answer.objects.filter(pk=a.id).count(), 0)

    def test_delete_solution_of_question(self):
        """Deleting the solution of a Question should update the question.
        """
        # set a solution to the question
        q = AnswerFactory().question
        solution = q.last_answer
        q.solution = solution
        q.save()

        # delete the solution and question.solution should go back to None
        solution.delete()
        q = Question.objects.get(pk=q.id)
        eq_(q.solution, None)

    def test_update_page_task(self):
        a = AnswerFactory()
        a.page = 4
        a.save()
        a = Answer.objects.get(pk=a.id)
        assert a.page == 4
        update_answer_pages(a.question)
        a = Answer.objects.get(pk=a.id)
        assert a.page == 1

    def test_delete_updates_pages(self):
        a1 = AnswerFactory()
        a2 = AnswerFactory(question=a1.question)
        AnswerFactory(question=a1.question)
        a1.page = 7
        a1.save()
        a2.delete()
        a3 = Answer.objects.filter(question=a1.question)[0]
        assert a3.page == 1, "Page was %s" % a3.page

    def test_creator_num_answers(self):
        a = AnswerFactory()

        eq_(a.creator_num_answers, 1)

        AnswerFactory(creator=a.creator)
        eq_(a.creator_num_answers, 2)

    def test_creator_num_solutions(self):
        a = AnswerFactory()
        q = a.question

        q.solution = a
        q.save()

        eq_(a.creator_num_solutions, 1)

    def test_content_parsed_with_locale(self):
        """Make sure links to localized articles work."""
        rev = TranslatedRevisionFactory(
            is_approved=True, document__title=u"Un mejor títuolo", document__locale="es"
        )

        a = AnswerFactory(question__locale="es", content=u"[[%s]]" % rev.document.title)

        assert "es/kb/%s" % rev.document.slug in a.content_parsed

    def test_creator_follows(self):
        a = AnswerFactory()
        follows = Follow.objects.filter(user=a.creator)

        # It's a pain to filter this from the DB, since follow_object is a
        # ContentType field, so instead, do it in Python.
        eq_(len(follows), 2)
        answer_follow = [f for f in follows if f.follow_object == a][0]
        question_follow = [f for f in follows if f.follow_object == a.question][0]

        eq_(question_follow.actor_only, False)
        eq_(answer_follow.actor_only, False)


class TestQuestionMetadata(TestCaseBase):
    """Tests handling question metadata"""

    def setUp(self):
        super(TestQuestionMetadata, self).setUp()

        # add a new Question to test with
        self.question = QuestionFactory(
            title="Test Question", content="Lorem Ipsum Dolor"
        )

    def test_add_metadata(self):
        """Test the saving of metadata."""
        metadata = {"version": u"3.6.3", "os": u"Windows 7"}
        self.question.add_metadata(**metadata)
        saved = QuestionMetaData.objects.filter(question=self.question)
        eq_(dict((x.name, x.value) for x in saved), metadata)

    def test_metadata_property(self):
        """Test the metadata property on Question model."""
        self.question.add_metadata(crash_id="1234567890")
        eq_("1234567890", self.question.metadata["crash_id"])

    def test_product_property(self):
        """Test question.product property."""
        self.question.add_metadata(product="desktop")
        eq_(config.products["desktop"], self.question.product_config)

    def test_category_property(self):
        """Test question.category property."""
        self.question.add_metadata(product="desktop")
        self.question.add_metadata(category="fix-problems")
        eq_(
            config.products["desktop"]["categories"]["fix-problems"],
            self.question.category_config,
        )

    def test_clear_mutable_metadata(self):
        """Make sure it works and clears the internal cache.

        crash_id should get cleared, while product, category, and useragent
        should remain.

        """
        q = self.question
        q.add_metadata(
            product="desktop",
            category="fix-problems",
            useragent="Fyerfocks",
            crash_id="7",
        )

        q.metadata
        q.clear_mutable_metadata()
        md = q.metadata
        assert (
            "crash_id" not in md
        ), "clear_mutable_metadata() didn't clear the cached metadata."
        eq_(dict(product="desktop", category="fix-problems", useragent="Fyerfocks"), md)

    def test_auto_tagging(self):
        """Make sure tags get applied based on metadata on first save."""
        Tag.objects.create(slug="green", name="green")
        Tag.objects.create(slug="Fix problems", name="fix-problems")
        q = self.question
        q.add_metadata(
            product="desktop", category="fix-problems", ff_version="3.6.8", os="GREen"
        )
        q.save()
        q.auto_tag()
        tags_eq(q, ["desktop", "fix-problems", "Firefox 3.6.8", "Firefox 3.6", "green"])

    def test_auto_tagging_aurora(self):
        """Make sure versions with prerelease suffix are tagged properly."""
        q = self.question
        q.add_metadata(ff_version="18.0a2")
        q.save()
        q.auto_tag()
        tags_eq(q, ["Firefox 18.0"])

    def test_auto_tagging_restraint(self):
        """Auto-tagging shouldn't tag unknown Firefox versions or OSes."""
        q = self.question
        q.add_metadata(ff_version="allyourbase", os="toaster 1.0")
        q.save()
        q.auto_tag()
        tags_eq(q, [])

    def test_tenths_version(self):
        """Test the filter that turns 1.2.3 into 1.2."""
        eq_(_tenths_version("1.2.3beta3"), "1.2")
        eq_(_tenths_version("1.2rc"), "1.2")
        eq_(_tenths_version("1.w"), "")

    def test_has_beta(self):
        """Test the _has_beta helper."""
        assert _has_beta("5.0", {"5.0b3": "2011-06-01"})
        assert not _has_beta("6.0", {"5.0b3": "2011-06-01"})
        assert not _has_beta("5.5", {"5.0b3": "2011-06-01"})
        assert _has_beta("5.7", {"5.7b1": "2011-06-01"})
        assert _has_beta("11.0", {"11.0b7": "2011-06-01"})
        assert not _has_beta("10.0", {"11.0b7": "2011-06-01"})


class QuestionTests(TestCaseBase):
    """Tests for Question model"""

    def test_save_updated(self):
        """Saving with the `update` option should update `updated`."""
        q = QuestionFactory()
        updated = q.updated
        q.save(update=True)
        self.assertNotEqual(updated, q.updated)

    def test_save_no_update(self):
        """Saving without the `update` option shouldn't update `updated`."""
        q = QuestionFactory()
        updated = q.updated
        q.save()
        eq_(updated, q.updated)

    def test_default_manager(self):
        """Assert Question's default manager is SUMO's ManagerBase.

        This is easy to get wrong when mixing in taggability.

        """
        eq_(
            Question._default_manager.__class__,
            kitsune.questions.managers.QuestionManager,
        )

    def test_notification_created(self):
        """Creating a new question auto-watches it for answers."""

        u = UserFactory()
        q = QuestionFactory(creator=u, title="foo", content="bar")

        assert QuestionReplyEvent.is_notifying(u, q)

    def test_no_notification_on_update(self):
        """Saving an existing question does not watch it."""

        q = QuestionFactory()
        QuestionReplyEvent.stop_notifying(q.creator, q)
        assert not QuestionReplyEvent.is_notifying(q.creator, q)

        q.save()
        assert not QuestionReplyEvent.is_notifying(q.creator, q)

    def test_is_solved_property(self):
        a = AnswerFactory()
        q = a.question
        assert not q.is_solved
        q.solution = a
        q.save()
        assert q.is_solved

    def test_recent_counts(self):
        """Verify recent_asked_count and recent unanswered count."""
        # create a question for each of past 4 days
        now = datetime.now()
        QuestionFactory(created=now)
        QuestionFactory(created=now - timedelta(hours=12), is_locked=True)
        q = QuestionFactory(created=now - timedelta(hours=23))
        AnswerFactory(question=q)
        # 25 hours instead of 24 to avoid random test fails.
        QuestionFactory(created=now - timedelta(hours=25))

        # Only 3 are recent from last 72 hours, 1 has an answer.
        eq_(3, Question.recent_asked_count())
        eq_(1, Question.recent_unanswered_count())

    def test_recent_counts_with_filter(self):
        """Verify that recent_asked_count and recent_unanswered_count
        respect filters passed."""

        now = datetime.now()
        QuestionFactory(created=now, locale="en-US")
        q = QuestionFactory(created=now, locale="en-US")
        AnswerFactory(question=q)

        QuestionFactory(created=now, locale="pt-BR")
        QuestionFactory(created=now, locale="pt-BR")
        q = QuestionFactory(created=now, locale="pt-BR")
        AnswerFactory(question=q)

        # 5 asked recently, 3 are unanswered
        eq_(5, Question.recent_asked_count())
        eq_(3, Question.recent_unanswered_count())

        # check english (2 asked, 1 unanswered)
        locale_filter = Q(locale="en-US")
        eq_(2, Question.recent_asked_count(locale_filter))
        eq_(1, Question.recent_unanswered_count(locale_filter))

        # check pt-BR (3 asked, 2 unanswered)
        locale_filter = Q(locale="pt-BR")
        eq_(3, Question.recent_asked_count(locale_filter))
        eq_(2, Question.recent_unanswered_count(locale_filter))

    def test_from_url(self):
        """Verify question returned from valid URL."""
        q = QuestionFactory()

        eq_(q, Question.from_url("/en-US/questions/%s" % q.id))
        eq_(q, Question.from_url("/es/questions/%s" % q.id))
        eq_(q, Question.from_url("/questions/%s" % q.id))

    def test_from_url_id_only(self):
        """Verify question returned from valid URL."""
        # When requesting the id, the existence of the question isn't checked.
        eq_(123, Question.from_url("/en-US/questions/123", id_only=True))
        eq_(234, Question.from_url("/es/questions/234", id_only=True))
        eq_(345, Question.from_url("/questions/345", id_only=True))

    def test_from_invalid_url(self):
        """Verify question returned from valid URL."""
        q = QuestionFactory()

        eq_(None, Question.from_url("/en-US/questions/%s/edit" % q.id))
        eq_(None, Question.from_url("/en-US/kb/%s" % q.id))
        eq_(None, Question.from_url("/random/url"))
        eq_(None, Question.from_url("/en-US/questions/dashboard/metrics"))

    def test_editable(self):
        q = QuestionFactory()
        assert q.editable  # unlocked/unarchived
        q.is_archived = True
        assert not q.editable  # unlocked/archived
        q.is_locked = True
        assert not q.editable  # locked/archived
        q.is_archived = False
        assert not q.editable  # locked/unarchived
        q.is_locked = False
        assert q.editable  # unlocked/unarchived

    def test_age(self):
        now = datetime.now()
        ten_days_ago = now - timedelta(days=10)
        thirty_seconds_ago = now - timedelta(seconds=30)

        q1 = QuestionFactory(created=ten_days_ago)
        q2 = QuestionFactory(created=thirty_seconds_ago)

        # This test relies on datetime.now() being called in the age
        # property, so this delta check makes it less likely to fail
        # randomly.
        assert abs(q1.age - 10 * 24 * 60 * 60) < 2, "q1.age (%s) != 10 days" % q1.age
        assert abs(q2.age - 30) < 2, "q2.age (%s) != 30 seconds" % q2.age

    def test_is_taken(self):
        q = QuestionFactory()
        u = UserFactory()
        eq_(q.is_taken, False)

        q.taken_by = u
        q.taken_until = datetime.now() + timedelta(seconds=600)
        q.save()
        eq_(q.is_taken, True)

        q.taken_by = None
        q.taken_until = None
        q.save()
        eq_(q.is_taken, False)

    def test_take(self):
        u = UserFactory()
        q = QuestionFactory()
        q.take(u)
        eq_(q.taken_by, u)
        ok_(q.taken_until is not None)

    @raises(InvalidUserException)
    def test_take_creator(self):
        q = QuestionFactory()
        q.take(q.creator)

    @raises(AlreadyTakenException)
    def test_take_twice_fails(self):
        u1 = UserFactory()
        u2 = UserFactory()
        q = QuestionFactory()
        q.take(u1)
        q.take(u2)

    def test_take_twice_same_user_refreshes_time(self):
        u = UserFactory()
        first_taken_until = datetime.now() - timedelta(minutes=5)
        q = QuestionFactory(taken_by=u, taken_until=first_taken_until)
        q.take(u)
        ok_(q.taken_until > first_taken_until)

    def test_take_twice_forced(self):
        u1 = UserFactory()
        u2 = UserFactory()
        q = QuestionFactory()
        q.take(u1)
        q.take(u2, force=True)
        eq_(q.taken_by, u2)

    def test_taken_until_is_set(self):
        u = UserFactory()
        q = QuestionFactory()
        q.take(u)
        assert q.taken_until > datetime.now()

    def test_is_taken_clears(self):
        u = UserFactory()
        taken_until = datetime.now() - timedelta(seconds=30)
        q = QuestionFactory(taken_by=u, taken_until=taken_until)
        # Testin q.is_taken should clear out ``taken_by`` and ``taken_until``,
        # since taken_until is in the past.
        eq_(q.is_taken, False)
        eq_(q.taken_by, None)
        eq_(q.taken_until, None)

    def test_creator_follows(self):
        q = QuestionFactory()
        f = Follow.objects.get(user=q.creator)
        eq_(f.follow_object, q)
        eq_(f.actor_only, False)


class AddExistingTagTests(TestCaseBase):
    """Tests for the add_existing_tag helper function."""

    def setUp(self):
        super(AddExistingTagTests, self).setUp()
        self.untagged_question = QuestionFactory()

    def test_tags_manager(self):
        """Make sure the TaggableManager exists.

        Full testing of functionality is a matter for taggit's tests.

        """
        tags_eq(self.untagged_question, [])

    def test_add_existing_case_insensitive(self):
        """Assert add_existing_tag works case-insensitively."""
        TagFactory(name="lemon", slug="lemon")
        add_existing_tag("LEMON", self.untagged_question.tags)
        tags_eq(self.untagged_question, [u"lemon"])

    @raises(Tag.DoesNotExist)
    def test_add_existing_no_such_tag(self):
        """Assert add_existing_tag doesn't work when the tag doesn't exist."""
        add_existing_tag("nonexistent tag", self.untagged_question.tags)


class OldQuestionsArchiveTest(ElasticTestCase):
    def test_archive_old_questions(self):
        last_updated = datetime.now() - timedelta(days=100)

        # created just now
        q1 = QuestionFactory()

        # created 200 days ago
        q2 = QuestionFactory(
            created=datetime.now() - timedelta(days=200), updated=last_updated
        )

        # created 200 days ago, already archived
        q3 = QuestionFactory(
            created=datetime.now() - timedelta(days=200),
            is_archived=True,
            updated=last_updated,
        )

        self.refresh()

        call_command("auto_archive_old_questions")

        # There are three questions.
        eq_(len(list(Question.objects.all())), 3)

        # q2 and q3 are now archived and updated times are the same
        archived_questions = list(Question.objects.filter(is_archived=True))
        eq_(
            sorted([(q.id, q.updated.date()) for q in archived_questions]),
            [(q.id, q.updated.date()) for q in [q2, q3]],
        )

        # q1 is still unarchived.
        archived_questions = list(Question.objects.filter(is_archived=False))
        eq_(sorted([q.id for q in archived_questions]), [q1.id])


class QuestionVisitsTests(TestCase):
    """Tests for the pageview statistics gathering."""

    # Need to monkeypatch close_old_connections out because it
    # does something screwy with the testing infra around transactions.
    @mock.patch.object(models, "close_old_connections")
    @mock.patch.object(
        googleanalytics, "pageviews_by_question",
    )
    def test_visit_count_from_analytics(
        self, pageviews_by_question, close_old_connections
    ):
        """Verify stored visit counts from mocked data."""
        q1 = QuestionFactory()
        q2 = QuestionFactory()
        q3 = QuestionFactory()

        pageviews_by_question.return_value = {
            q1.id: 42,
            q2.id: 27,
            q3.id: 1337,
            123459: 3,
        }

        QuestionVisits.reload_from_analytics()
        eq_(3, QuestionVisits.objects.count())
        eq_(42, QuestionVisits.objects.get(question_id=q1.id).visits)
        eq_(27, QuestionVisits.objects.get(question_id=q2.id).visits)
        eq_(1337, QuestionVisits.objects.get(question_id=q3.id).visits)

        # Change the data and run again to cover the update case.
        pageviews_by_question.return_value = {
            q1.id: 100,
            q2.id: 200,
            q3.id: 300,
        }
        QuestionVisits.reload_from_analytics()
        eq_(3, QuestionVisits.objects.count())
        eq_(100, QuestionVisits.objects.get(question_id=q1.id).visits)
        eq_(200, QuestionVisits.objects.get(question_id=q2.id).visits)
        eq_(300, QuestionVisits.objects.get(question_id=q3.id).visits)


class QuestionVoteTests(TestCase):
    def test_add_metadata_over_1000_chars(self):
        qv = QuestionVoteFactory()
        qv.add_metadata("test1", "a" * 1001)
        metadata = VoteMetadata.objects.all()[0]
        eq_("a" * 1000, metadata.value)


class TestActions(TestCase):
    def test_question_create_action(self):
        """When a question is created, an Action is created too."""
        q = QuestionFactory()
        a = Action.objects.action_object(q).get()
        eq_(a.actor, q.creator)
        eq_(a.verb, "asked")
        eq_(a.target, None)

    def test_answer_create_action(self):
        """When an answer is created, an Action is created too."""
        q = QuestionFactory()
        ans = AnswerFactory(question=q)
        act = Action.objects.action_object(ans).get()
        eq_(act.actor, ans.creator)
        eq_(act.verb, "answered")
        eq_(act.target, q)

    def test_question_change_no_action(self):
        """When a question is changed, no Action should be created."""
        q = QuestionFactory()
        Action.objects.all().delete()
        q.save()  # trigger another post_save hook
        eq_(Action.objects.count(), 0)

    def test_answer_change_no_action(self):
        """When an answer is changed, no Action should be created."""
        q = QuestionFactory()
        Action.objects.all().delete()
        q.save()  # trigger another post_save hook
        eq_(Action.objects.count(), 0)

    def test_question_solved_makes_action(self):
        """When an answer is marked as the solution to a question, an Action should be created."""
        ans = AnswerFactory()
        Action.objects.all().delete()
        ans.question.set_solution(ans, ans.question.creator)

        act = Action.objects.action_object(ans).get()
        eq_(act.actor, ans.question.creator)
        eq_(act.verb, "marked as a solution")
        eq_(act.target, ans.question)
