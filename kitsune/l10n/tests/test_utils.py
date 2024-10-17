from datetime import timedelta

from django.core.exceptions import ValidationError
from django_celery_beat.models import IntervalSchedule, PeriodicTask

from kitsune.l10n.utils import (
    duration_to_text,
    get_l10n_bot,
    manage_heartbeat,
    text_to_duration,
)
from kitsune.sumo.tests import TestCase


class UtilsTests(TestCase):

    def test_text_to_duration(self):
        self.assertEqual(text_to_duration(" 3 minutes"), timedelta(minutes=3))
        self.assertEqual(text_to_duration(" 5  hours "), timedelta(hours=5))
        self.assertEqual(text_to_duration("7 days"), timedelta(days=7))
        self.assertEqual(text_to_duration("0"), timedelta(0))
        with self.assertRaises(ValidationError):
            text_to_duration("")
        with self.assertRaises(ValidationError):
            text_to_duration("1 minute")
        with self.assertRaises(ValidationError):
            text_to_duration("-3 minutes")
        with self.assertRaises(ValidationError):
            text_to_duration("7 seconds")
        with self.assertRaises(ValidationError):
            text_to_duration("9hours")
        with self.assertRaises(ValidationError):
            text_to_duration("hours 4")

    def test_duration_to_text(self):
        self.assertEqual(duration_to_text(timedelta(minutes=3)), "3 minutes")
        self.assertEqual(duration_to_text(timedelta(hours=5)), "5 hours")
        self.assertEqual(duration_to_text(timedelta(days=7)), "7 days")
        self.assertEqual(duration_to_text(timedelta(days=2, hours=4, minutes=12)), "3132 minutes")
        self.assertEqual(duration_to_text(timedelta(hours=4, minutes=12)), "252 minutes")
        self.assertEqual(duration_to_text(timedelta(days=1, hours=4)), "28 hours")
        self.assertEqual(duration_to_text(timedelta(days=1, hours=24)), "2 days")
        self.assertEqual(duration_to_text(timedelta(days=2, hours=23, minutes=60)), "3 days")

    def test_get_l10n_bot(self):
        l10n_bot1 = get_l10n_bot()
        self.assertEqual(l10n_bot1.username, "sumo-l10n-bot")
        self.assertEqual(l10n_bot1.email, "sumodev@mozilla.com")
        self.assertTrue(l10n_bot1.profile)
        self.assertEqual(l10n_bot1.profile.name, "SUMO Localization Bot")
        l10n_bot2 = get_l10n_bot()
        self.assertEqual(l10n_bot2.id, l10n_bot1.id)
        self.assertEqual(l10n_bot2.profile.pk, l10n_bot1.profile.pk)

    def test_manage_heartbeat(self):
        self.assertEqual(IntervalSchedule.objects.count(), 0)
        self.assertEqual(PeriodicTask.objects.count(), 0)

        duration1 = timedelta(hours=4)
        duration2 = timedelta(hours=2)

        manage_heartbeat(duration1)

        self.assertEqual(IntervalSchedule.objects.count(), 1)
        self.assertEqual(IntervalSchedule.objects.filter(every=4, period="hours").count(), 1)
        self.assertEqual(PeriodicTask.objects.count(), 1)
        self.assertEqual(
            PeriodicTask.objects.filter(
                name="L10n Heartbeat",
                interval=IntervalSchedule.objects.filter(every=4, period="hours").get(),
            ).count(),
            1,
        )

        manage_heartbeat(duration2)

        self.assertEqual(IntervalSchedule.objects.count(), 2)
        self.assertEqual(IntervalSchedule.objects.filter(every=4, period="hours").count(), 1)
        self.assertEqual(IntervalSchedule.objects.filter(every=2, period="hours").count(), 1)
        self.assertEqual(PeriodicTask.objects.count(), 1)
        self.assertEqual(
            PeriodicTask.objects.filter(
                name="L10n Heartbeat",
                interval=IntervalSchedule.objects.filter(every=2, period="hours").get(),
            ).count(),
            1,
        )

        manage_heartbeat(duration1)

        self.assertEqual(IntervalSchedule.objects.count(), 2)
        self.assertEqual(IntervalSchedule.objects.filter(every=4, period="hours").count(), 1)
        self.assertEqual(IntervalSchedule.objects.filter(every=2, period="hours").count(), 1)
        self.assertEqual(PeriodicTask.objects.count(), 1)
        self.assertEqual(
            PeriodicTask.objects.filter(
                name="L10n Heartbeat",
                interval=IntervalSchedule.objects.filter(every=4, period="hours").get(),
            ).count(),
            1,
        )

        manage_heartbeat(timedelta(0))

        self.assertEqual(IntervalSchedule.objects.count(), 2)
        self.assertEqual(IntervalSchedule.objects.filter(every=4, period="hours").count(), 1)
        self.assertEqual(IntervalSchedule.objects.filter(every=2, period="hours").count(), 1)
        self.assertEqual(PeriodicTask.objects.count(), 0)
