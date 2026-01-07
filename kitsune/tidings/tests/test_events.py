from kitsune.sumo.tests import TestCase
from kitsune.tidings.events import unique_by_email
from kitsune.tidings.tests import WatchFactory
from kitsune.users.tests import UserFactory


class UniqueByEmailTests(TestCase):
    def test_unique_by_email(self):
        u1 = UserFactory(email="Alice@example.com")
        u2 = UserFactory(email="sally@example.com")
        u3 = UserFactory(email="")
        u4 = UserFactory(email="")

        w1 = WatchFactory(user=u1, event_type="thread reply")
        w2 = WatchFactory(user=u1, event_type="forum thread")
        w3 = WatchFactory(user=u2, event_type="thread reply")
        w4 = WatchFactory(user=u2, event_type="forum thread")
        w5 = WatchFactory(email="alice@example.com")
        w6 = WatchFactory(email="ringo@example.com")

        results = list(
            unique_by_email(
                [(u1, [w1]), (u2, [w3])], [(u3, [w5]), (u1, [w2]), (u2, [w4]), (u4, [w6])]
            )
        )

        self.assertEqual(len(results), 3)
        user, watches = results[0]
        self.assertTrue(user.is_authenticated)
        self.assertEqual(user.email, "sally@example.com")
        self.assertEqual(len(watches), 2)
        self.assertEqual({w.event_type for w in watches}, {w3.event_type, w4.event_type})
        user, watches = results[1]
        self.assertFalse(user.is_authenticated)
        self.assertEqual(user.email, "ringo@example.com")
        self.assertEqual(watches, [w6])
        user, watches = results[2]
        self.assertTrue(user.is_authenticated)
        self.assertEqual(user.email, "Alice@example.com")
        self.assertEqual(len(watches), 3)
        self.assertEqual(
            {w.event_type for w in watches}, {w1.event_type, w2.event_type, w5.event_type}
        )
