from datetime import timedelta

import factory
from django.utils import timezone

from kitsune.announcements.models import Announcement
from kitsune.sumo.tests import FuzzyUnicode
from kitsune.users.tests import UserFactory


class AnnouncementFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Announcement
        exclude = ["visible_dates"]

    content = FuzzyUnicode()
    creator = factory.SubFactory(UserFactory)
    show_after = factory.LazyAttribute(lambda a: timezone.now() - timedelta(days=2))
    visible_dates = True
    send_email = False

    @factory.lazy_attribute
    def show_until(self):
        if self.visible_dates:
            return None
        else:
            return timezone.now() - timedelta(days=1)
