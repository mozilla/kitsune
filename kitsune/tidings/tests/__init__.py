from factory import fuzzy
from factory.django import DjangoModelFactory

from kitsune.tidings.models import Watch


class WatchFactory(DjangoModelFactory):
    class Meta:
        model = Watch

    event_type = "fooevent"
    is_active = True
    secret = fuzzy.FuzzyText(length=10)
