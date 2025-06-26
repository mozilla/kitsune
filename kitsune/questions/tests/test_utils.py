from copy import deepcopy

from django.contrib.contenttypes.models import ContentType
from parameterized import parameterized

from kitsune.flagit.models import FlaggedObject
from kitsune.forums.models import Thread as ForumThread, Post as ForumPost
from kitsune.forums.tests import (
    ThreadFactory as ForumThreadFactory,
    PostFactory as ForumPostFactory,
)
from kitsune.kbforums.models import Thread as KBForumThread, Post as KBForumPost
from kitsune.kbforums.tests import (
    ThreadFactory as KBForumThreadFactory,
    PostFactory as KBForumPostFactory,
)
from kitsune.llm.questions.classifiers import ModerationAction
from kitsune.products.tests import TopicFactory
from kitsune.questions.models import Answer, Question
from kitsune.questions.tests import AnswerFactory, QuestionFactory
from kitsune.questions.utils import (
    get_mobile_product_from_ua,
    mark_content_as_spam,
    num_answers,
    num_questions,
    num_solutions,
    process_classification_result,
    remove_pii,
    remove_home_dir_pii,
)
from kitsune.sumo.tests import TestCase
from kitsune.users.models import Profile
from kitsune.users.tests import UserFactory


class ContributionCountTestCase(TestCase):
    def test_num_questions(self):
        """Answers are counted correctly on a user."""
        u = UserFactory()
        self.assertEqual(num_questions(u), 0)

        q1 = QuestionFactory(creator=u)
        self.assertEqual(num_questions(u), 1)

        q2 = QuestionFactory(creator=u)
        self.assertEqual(num_questions(u), 2)

        q1.delete()
        self.assertEqual(num_questions(u), 1)

        q2.delete()
        self.assertEqual(num_questions(u), 0)

    def test_num_answers(self):
        u = UserFactory()
        q = QuestionFactory()
        self.assertEqual(num_answers(u), 0)

        a1 = AnswerFactory(creator=u, question=q)
        self.assertEqual(num_answers(u), 1)

        a2 = AnswerFactory(creator=u, question=q)
        self.assertEqual(num_answers(u), 2)

        a1.delete()
        self.assertEqual(num_answers(u), 1)

        a2.delete()
        self.assertEqual(num_answers(u), 0)

    def test_num_solutions(self):
        u = UserFactory()
        q1 = QuestionFactory()
        q2 = QuestionFactory()
        a1 = AnswerFactory(creator=u, question=q1)
        a2 = AnswerFactory(creator=u, question=q2)
        self.assertEqual(num_solutions(u), 0)

        q1.solution = a1
        q1.save()
        self.assertEqual(num_solutions(u), 1)

        q2.solution = a2
        q2.save()
        self.assertEqual(num_solutions(u), 2)

        q1.solution = None
        q1.save()
        self.assertEqual(num_solutions(u), 1)

        a2.delete()
        self.assertEqual(num_solutions(u), 0)


class FlagUserContentAsSpamTestCase(TestCase):
    def test_flag_content_as_spam(self):
        # Create some questions and answers by the user.
        u = UserFactory()
        QuestionFactory(creator=u)
        QuestionFactory(creator=u)
        AnswerFactory(creator=u)
        AnswerFactory(creator=u)
        AnswerFactory(creator=u)

        # Verify they are not marked as spam yet.
        self.assertEqual(2, Question.objects.filter(is_spam=False, creator=u).count())
        self.assertEqual(0, Question.objects.filter(is_spam=True, creator=u).count())
        self.assertEqual(3, Answer.objects.filter(is_spam=False, creator=u).count())
        self.assertEqual(0, Answer.objects.filter(is_spam=True, creator=u).count())

        # Flag content as spam and verify it is updated.
        mark_content_as_spam(u, UserFactory())
        self.assertEqual(0, Question.objects.filter(is_spam=False, creator=u).count())
        self.assertEqual(2, Question.objects.filter(is_spam=True, creator=u).count())
        self.assertEqual(0, Answer.objects.filter(is_spam=False, creator=u).count())
        self.assertEqual(3, Answer.objects.filter(is_spam=True, creator=u).count())

    def test_mark_content_as_spam_deletes_kbforum_threads_and_posts(self):
        # Create a user and some kbforum content
        u = UserFactory()
        another_user = UserFactory()

        # Create kbforum threads and posts by the user
        kbforum_thread1 = KBForumThreadFactory(creator=u)
        kbforum_thread2 = KBForumThreadFactory(creator=u)
        kbforum_post1 = KBForumPostFactory(creator=u)
        kbforum_post2 = KBForumPostFactory(creator=u)

        # Create some content by another user (should not be deleted)
        other_kbforum_thread = KBForumThreadFactory(creator=another_user)
        other_kbforum_post = KBForumPostFactory(creator=another_user)

        # Store IDs for verification
        thread_ids = [kbforum_thread1.id, kbforum_thread2.id]
        post_ids = [kbforum_post1.id, kbforum_post2.id]
        other_thread_id = other_kbforum_thread.id
        other_post_id = other_kbforum_post.id

        # Verify content exists before deletion
        self.assertEqual(2, KBForumThread.objects.filter(creator=u).count())
        self.assertEqual(2, KBForumPost.objects.filter(creator=u).count())
        self.assertEqual(1, KBForumThread.objects.filter(creator=another_user).count())
        self.assertEqual(1, KBForumPost.objects.filter(creator=another_user).count())

        # Mark content as spam
        mark_content_as_spam(u, UserFactory())

        # Verify user's kbforum content is deleted
        self.assertEqual(0, KBForumThread.objects.filter(creator=u).count())
        self.assertEqual(0, KBForumPost.objects.filter(creator=u).count())
        self.assertFalse(KBForumThread.objects.filter(id__in=thread_ids).exists())
        self.assertFalse(KBForumPost.objects.filter(id__in=post_ids).exists())

        # Verify other user's content remains untouched
        self.assertEqual(1, KBForumThread.objects.filter(creator=another_user).count())
        self.assertEqual(1, KBForumPost.objects.filter(creator=another_user).count())
        self.assertTrue(KBForumThread.objects.filter(id=other_thread_id).exists())
        self.assertTrue(KBForumPost.objects.filter(id=other_post_id).exists())

    def test_mark_content_as_spam_deletes_forum_threads_and_posts(self):
        # Create a user and some forum content
        u = UserFactory()
        another_user = UserFactory()

        # Create forum threads explicitly (with posts=[] to prevent auto-post creation)
        forum_thread1 = ForumThreadFactory(creator=u, posts=[])
        forum_thread2 = ForumThreadFactory(creator=u, posts=[])

        # Create forum posts on existing threads
        forum_post1 = ForumPostFactory(author=u, thread=forum_thread1)
        forum_post2 = ForumPostFactory(author=u, thread=forum_thread2)

        # Create some content by another user (should not be deleted)
        other_forum_thread = ForumThreadFactory(creator=another_user, posts=[])
        other_forum_post = ForumPostFactory(author=another_user, thread=other_forum_thread)

        # Store IDs for verification
        thread_ids = [forum_thread1.id, forum_thread2.id]
        post_ids = [forum_post1.id, forum_post2.id]
        other_thread_id = other_forum_thread.id
        other_post_id = other_forum_post.id

        # Verify content exists before deletion
        self.assertEqual(2, ForumThread.objects.filter(creator=u).count())
        self.assertEqual(2, ForumPost.objects.filter(author=u).count())
        self.assertEqual(1, ForumThread.objects.filter(creator=another_user).count())
        self.assertEqual(1, ForumPost.objects.filter(author=another_user).count())

        # Mark content as spam
        mark_content_as_spam(u, UserFactory())

        # Verify user's forum content is deleted
        self.assertEqual(0, ForumThread.objects.filter(creator=u).count())
        self.assertEqual(0, ForumPost.objects.filter(author=u).count())
        self.assertFalse(ForumThread.objects.filter(id__in=thread_ids).exists())
        self.assertFalse(ForumPost.objects.filter(id__in=post_ids).exists())

        # Verify other user's content remains untouched
        self.assertEqual(1, ForumThread.objects.filter(creator=another_user).count())
        self.assertEqual(1, ForumPost.objects.filter(author=another_user).count())
        self.assertTrue(ForumThread.objects.filter(id=other_thread_id).exists())
        self.assertTrue(ForumPost.objects.filter(id=other_post_id).exists())

    def test_mark_content_as_spam_comprehensive(self):
        # Test that all content types are handled correctly in a single operation
        u = UserFactory()
        moderator = UserFactory()

        # Create questions and answers
        for _ in range(2):
            QuestionFactory(creator=u)
            AnswerFactory(creator=u)

        # Create kbforum content
        kbforum_thread = KBForumThreadFactory(creator=u)
        kbforum_post = KBForumPostFactory(creator=u)

        # Create forum content
        forum_thread = ForumThreadFactory(creator=u, posts=[])
        forum_post = ForumPostFactory(author=u, thread=forum_thread)

        # Store IDs for verification
        kbforum_thread_id = kbforum_thread.id
        kbforum_post_id = kbforum_post.id
        forum_thread_id = forum_thread.id
        forum_post_id = forum_post.id

        # Verify initial state
        self.assertEqual(2, Question.objects.filter(creator=u, is_spam=False).count())
        self.assertEqual(2, Answer.objects.filter(creator=u, is_spam=False).count())
        self.assertEqual(1, KBForumThread.objects.filter(creator=u).count())
        self.assertEqual(1, KBForumPost.objects.filter(creator=u).count())
        self.assertEqual(1, ForumThread.objects.filter(creator=u).count())
        self.assertEqual(1, ForumPost.objects.filter(author=u).count())

        # Mark content as spam
        mark_content_as_spam(u, moderator)

        # Verify questions and answers are marked as spam (not deleted)
        self.assertEqual(0, Question.objects.filter(creator=u, is_spam=False).count())
        self.assertEqual(2, Question.objects.filter(creator=u, is_spam=True).count())
        self.assertEqual(0, Answer.objects.filter(creator=u, is_spam=False).count())
        self.assertEqual(2, Answer.objects.filter(creator=u, is_spam=True).count())

        # Verify forum content is deleted
        self.assertEqual(0, KBForumThread.objects.filter(creator=u).count())
        self.assertEqual(0, KBForumPost.objects.filter(creator=u).count())
        self.assertEqual(0, ForumThread.objects.filter(creator=u).count())
        self.assertEqual(0, ForumPost.objects.filter(author=u).count())
        self.assertFalse(KBForumThread.objects.filter(id=kbforum_thread_id).exists())
        self.assertFalse(KBForumPost.objects.filter(id=kbforum_post_id).exists())
        self.assertFalse(ForumThread.objects.filter(id=forum_thread_id).exists())
        self.assertFalse(ForumPost.objects.filter(id=forum_post_id).exists())


class GetMobileProductFromUATests(TestCase):
    @parameterized.expand(
        [
            ("Mozilla/5.0 (Android; Mobile; rv:40.0) Gecko/40.0 Firefox/40.0", "mobile"),
            ("Mozilla/5.0 (Android; Tablet; rv:40.0) Gecko/40.0 Firefox/40.0", "mobile"),
            ("Mozilla/5.0 (Android 4.4; Mobile; rv:41.0) Gecko/41.0 Firefox/41.0", "mobile"),
            ("Mozilla/5.0 (Android 4.4; Tablet; rv:41.0) Gecko/41.0 Firefox/41.0", "mobile"),
            (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 12_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/7.0.4 Mobile/16B91 Safari/605.1.15",  # noqa: E501
                "ios",
            ),
            (
                "Mozilla/5.0 (Android 10; Mobile; rv:76.0) Gecko/76.0 Firefox/76.0",
                "mobile",
            ),
            (
                "Mozilla/5.0 (Linux; Android 8.1.0; Redmi 6A Build/O11019; rv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Rocket/1.9.2(13715) Chrome/76.0.3809.132 Mobile Safari/537.36",  # noqa: E501
                "firefox-lite",
            ),
            (  # Chrome on Android:
                "Mozilla/5.0 (Linux; Android 8.0.0; Pixel 2 XL Build/OPD1.170816.004) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Mobile Safari/537.36",  # noqa: E501
                None,
            ),
        ]
    )
    def test_user_agents(self, ua, expected):
        self.assertEqual(expected, get_mobile_product_from_ua(ua))


class PIIRemovalTests(TestCase):
    @parameterized.expand(
        [
            ("C:\\User\\ringo", "C:\\User\\<USERNAME>"),
            ("C:\\Users\\ringo\\Songs", "C:\\Users\\<USERNAME>\\Songs"),
            ("C:\\WINNT\\Profiles\\ringo\\Songs\\", "C:\\WINNT\\Profiles\\<USERNAME>\\Songs\\"),
            (
                "C:\\Documents and Settings\\ringo\\Songs",
                "C:\\Documents and Settings\\<USERNAME>\\Songs",
            ),
            (
                "C:\\Users\\ringo\\AppData and C:\\Users\\ringo\\Songs",
                "C:\\Users\\<USERNAME>\\AppData and C:\\Users\\<USERNAME>\\Songs",
            ),
            ("/user/ringo", "/user/<USERNAME>"),
            ("/Users/ringo/Music", "/Users/<USERNAME>/Music"),
            ("here is the path: /home/ringo/music", "here is the path: /home/<USERNAME>/music"),
            (
                "/Users/ringo/Music and /Users/ringo/Documents",
                "/Users/<USERNAME>/Music and /Users/<USERNAME>/Documents",
            ),
        ]
    )
    def test_remove_home_dir_pii(self, text, expected):
        self.assertEqual(remove_home_dir_pii(text), expected)

    def test_remove_pii(self):
        data = {
            "application": {
                "name": "Firefox",
                "osVersion": "Windows_NT 10.0 19041",
                "version": "88.0",
                "buildID": "20210415204500",
                "distributionID": "",
                "userAgent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) "
                    "Gecko/20100101 Firefox/88.0"
                ),
                "safeMode": False,
                "updateChannel": "release",
                "supportURL": "https://support.mozilla.org/1/firefox/88.0/WINNT/en-US/",
                "numTotalWindows": 1,
                "numFissionWindows": 0,
                "numRemoteWindows": 1,
                "launcherProcessState": 0,
                "fissionAutoStart": False,
                "fissionDecisionStatus": "disabledByDefault",
                "remoteAutoStart": True,
                "policiesStatus": 0,
                "keyLocationServiceGoogleFound": True,
                "keySafebrowsingGoogleFound": True,
                "keyMozillaFound": True,
            },
            "environmentVariables": {
                "MOZ_CRASHREPORTER_DATA_DIRECTORY": (
                    "C:\\Users\\ringo\\AppData\\Roaming\\Mozilla\\Firefox\\Crash Reports"
                ),
                "MOZ_CRASHREPORTER_PING_DIRECTORY": (
                    "C:\\Users\\ringo\\AppData\\Roaming\\Mozilla\\Firefox\\Pending Pings"
                ),
            },
            "startupCache": {
                "IgnoreDiskCache": False,
                "paths": {
                    "DiskCachePath": "C:\\Users\\ringo\\AppData\\Local\\Mozilla\\Firefox",
                },
            },
        }
        expected = deepcopy(data)
        expected["environmentVariables"][
            "MOZ_CRASHREPORTER_DATA_DIRECTORY"
        ] = "C:\\Users\\<USERNAME>\\AppData\\Roaming\\Mozilla\\Firefox\\Crash Reports"
        expected["environmentVariables"][
            "MOZ_CRASHREPORTER_PING_DIRECTORY"
        ] = "C:\\Users\\<USERNAME>\\AppData\\Roaming\\Mozilla\\Firefox\\Pending Pings"
        expected["startupCache"]["paths"][
            "DiskCachePath"
        ] = "C:\\Users\\<USERNAME>\\AppData\\Local\\Mozilla\\Firefox"
        remove_pii(data)
        self.assertDictEqual(data, expected)


class ProcessClassificationResultTests(TestCase):

    def setUp(self):
        self.topic1 = TopicFactory()
        self.topic2 = TopicFactory()
        self.sumo_bot = Profile.get_sumo_bot()

    def test_spam_result(self):
        question = QuestionFactory(topic=self.topic1)
        classification_result = dict(
            action=ModerationAction.SPAM,
        )
        self.assertFalse(question.is_spam)
        self.assertIsNone(question.marked_as_spam)
        self.assertIsNone(question.marked_as_spam_by)
        self.assertEqual(question.topic, self.topic1)

        process_classification_result(question, classification_result)

        question.refresh_from_db()

        self.assertTrue(question.is_spam)
        self.assertIsNotNone(question.marked_as_spam)
        self.assertEqual(question.marked_as_spam_by, self.sumo_bot)

    def test_flagged_result(self):
        question = QuestionFactory(topic=self.topic1)
        classification_result = dict(
            action=ModerationAction.FLAG_REVIEW,
            spam_result=dict(reason="I think it is spam?"),
        )

        q_ct = ContentType.objects.get_for_model(question)

        self.assertFalse(question.is_spam)
        self.assertFalse(
            FlaggedObject.objects.filter(content_type=q_ct, object_id=question.id).exists()
        )
        self.assertEqual(question.topic, self.topic1)

        process_classification_result(question, classification_result)

        question.refresh_from_db()

        self.assertFalse(question.is_spam)
        self.assertEqual(question.topic, self.topic1)
        self.assertTrue(
            FlaggedObject.objects.filter(
                content_type=q_ct,
                object_id=question.id,
                creator=self.sumo_bot,
                reason=FlaggedObject.REASON_SPAM,
                status=FlaggedObject.FLAG_PENDING,
                notes__contains="I think it is spam?",
            ).exists()
        )

    def test_topic_result_with_change(self):
        question = QuestionFactory(topic=self.topic1, tags=[self.topic1.slug])
        classification_result = dict(
            action=ModerationAction.NOT_SPAM,
            topic_result=dict(
                topic=self.topic2.title,
                reason="Dude, it is so topic2.",
            ),
        )

        q_ct = ContentType.objects.get_for_model(question)

        self.assertFalse(question.is_spam)
        self.assertFalse(
            FlaggedObject.objects.filter(content_type=q_ct, object_id=question.id).exists()
        )
        self.assertEqual(question.topic, self.topic1)
        self.assertEqual(set(tag.name for tag in question.my_tags), {self.topic1.slug})

        process_classification_result(question, classification_result)

        question.refresh_from_db()

        self.assertFalse(question.is_spam)
        self.assertEqual(question.topic, self.topic2)
        self.assertEqual(set(tag.name for tag in question.my_tags), {self.topic2.slug})
        self.assertTrue(
            FlaggedObject.objects.filter(
                content_type=q_ct,
                object_id=question.id,
                creator=self.sumo_bot,
                status=FlaggedObject.FLAG_ACCEPTED,
                reason=FlaggedObject.REASON_CONTENT_MODERATION,
                notes__contains="Dude, it is so topic2.",
            ).exists()
        )

    def test_topic_result_with_no_initial_topic(self):
        question = QuestionFactory(topic=None)
        classification_result = dict(
            action=ModerationAction.NOT_SPAM,
            topic_result=dict(
                topic=self.topic2.title,
                reason="Dude, it is so topic2.",
            ),
        )

        q_ct = ContentType.objects.get_for_model(question)

        self.assertFalse(question.is_spam)
        self.assertFalse(
            FlaggedObject.objects.filter(content_type=q_ct, object_id=question.id).exists()
        )
        self.assertIsNone(question.topic)
        self.assertFalse(question.my_tags)

        process_classification_result(question, classification_result)

        question.refresh_from_db()

        self.assertFalse(question.is_spam)
        self.assertEqual(question.topic, self.topic2)
        self.assertEqual(set(tag.name for tag in question.my_tags), {self.topic2.slug})
        self.assertTrue(
            FlaggedObject.objects.filter(
                content_type=q_ct,
                object_id=question.id,
                creator=self.sumo_bot,
                status=FlaggedObject.FLAG_ACCEPTED,
                reason=FlaggedObject.REASON_CONTENT_MODERATION,
                notes__contains="Dude, it is so topic2.",
            ).exists()
        )

    def test_topic_result_with_no_change(self):
        question = QuestionFactory(topic=self.topic1, tags=[self.topic1.slug])
        classification_result = dict(
            action=ModerationAction.NOT_SPAM,
            topic_result=dict(
                topic=self.topic1.title,
                reason="Dude, it is so topic1.",
            ),
        )

        q_ct = ContentType.objects.get_for_model(question)

        self.assertFalse(question.is_spam)
        self.assertFalse(
            FlaggedObject.objects.filter(content_type=q_ct, object_id=question.id).exists()
        )
        self.assertEqual(question.topic, self.topic1)
        self.assertEqual(set(tag.name for tag in question.my_tags), {self.topic1.slug})

        process_classification_result(question, classification_result)

        question.refresh_from_db()

        self.assertFalse(question.is_spam)
        self.assertEqual(question.topic, self.topic1)
        self.assertEqual(set(tag.name for tag in question.my_tags), {self.topic1.slug})
        self.assertTrue(
            FlaggedObject.objects.filter(
                content_type=q_ct,
                object_id=question.id,
                creator=self.sumo_bot,
                status=FlaggedObject.FLAG_ACCEPTED,
                reason=FlaggedObject.REASON_CONTENT_MODERATION,
                notes__contains="Dude, it is so topic1.",
            ).exists()
        )
