import factory
from actstream.models import Action

from kitsune.notifications.models import Notification
from kitsune.users.tests import UserFactory


class ActionFactory(factory.DjangoModelFactory):
    class Meta:
        model = Action

    actor = factory.SubFactory(UserFactory)
    verb = "looked at"


class NotificationFactory(factory.DjangoModelFactory):
    class Meta:
        model = Notification

    owner = factory.SubFactory(UserFactory)
    action = factory.SubFactory(ActionFactory)
