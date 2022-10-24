from copy import deepcopy

from parameterized import parameterized

from kitsune.questions.models import Answer, Question
from kitsune.questions.tests import AnswerFactory, QuestionFactory
from kitsune.questions.utils import (
    get_mobile_product_from_ua,
    mark_content_as_spam,
    num_answers,
    num_questions,
    num_solutions,
    remove_pii,
    remove_home_dir_pii,
)
from kitsune.sumo.tests import TestCase
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
