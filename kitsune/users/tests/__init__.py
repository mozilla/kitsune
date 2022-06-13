import factory
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType

from kitsune.messages.utils import send_message
from kitsune.sumo.tests import FuzzyUnicode, LocalizingClient, TestCase
from kitsune.tidings.models import Watch
from kitsune.users.models import CONTRIBUTOR_GROUP, AccountEvent, Profile, Setting


class TestCaseBase(TestCase):
    """Base TestCase for the users app test cases."""

    client_class = LocalizingClient


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.fuzzy.FuzzyText()
    email = factory.LazyAttribute(lambda u: "{}@example.com".format(u.username))
    password = factory.PostGenerationMethodCall("set_password", "testpass")

    # We pass in 'user' to link the generated Profile to our just-generated User.
    # This will call ProfileFactory(user=our_new_user), thus skipping the SubFactory.
    profile = factory.RelatedFactory("kitsune.users.tests.ProfileFactory", "user")

    @factory.post_generation
    def groups(user, created, extracted, **kwargs):
        groups = extracted or []
        for group in groups:
            user.groups.add(group)


class ContributorFactory(UserFactory):
    @factory.post_generation
    def add_contributor_group(user, *args, **kwargs):
        user.groups.add(GroupFactory(name=CONTRIBUTOR_GROUP))


class ProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Profile

    name = FuzzyUnicode()
    bio = FuzzyUnicode()
    website = "http://support.example.com"
    timezone = None
    country = "US"
    city = "Portland"
    locale = "en-US"
    is_fxa_migrated = True
    user = factory.SubFactory(UserFactory, profile=None)


class GroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Group
        django_get_or_create = ("name",)

    name = factory.fuzzy.FuzzyText()


def add_permission(user, model, permission_codename):
    """Add a permission to a user.

    Creates the permission if it doesn't exist.

    """
    content_type = ContentType.objects.get_for_model(model)
    permission, created = Permission.objects.get_or_create(
        codename=permission_codename,
        content_type=content_type,
        defaults={"name": permission_codename},
    )
    user.user_permissions.add(permission)


class SettingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Setting

    name = factory.fuzzy.FuzzyText()
    value = factory.fuzzy.FuzzyText()


# pulled from https://github.com/mozilla/django-tidings/blob/master/tests/base.py#L23
def tidings_watch(save=False, **kwargs):
    # TODO: better defaults, when there are events available.
    defaults = {"user": kwargs.get("user"), "is_active": True, "secret": "abcdefghjk"}
    defaults.update(kwargs)
    w = Watch.objects.create(**defaults)
    if save:
        w.save()
    return w


class AccountEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AccountEvent

    status = AccountEvent.UNPROCESSED
    fxa_uid = "54321"
    jwt_id = "e19ed6c5-4816-4171-aa43-56ffe80dbda1"
    issued_at = "1565720808"
    profile = factory.SubFactory(ProfileFactory)


class ConversationFactory:
    """
    Populate inboxes and outboxes with messages between a primary user and a number of other users.
    """

    def __init__(self, primary_user=None, number_of_other_users=2):
        # Set or create the primary user and create some other users.
        self.user = primary_user or UserFactory()
        self.other_users = UserFactory.create_batch(number_of_other_users)
        # Populate the inboxes and outboxes of the users.
        for sender in self.other_users:
            send_message([self.user], "foo", sender=sender)
        send_message(self.other_users, "bar", sender=self.user)
        # Confirm our expectations.
        assert self.user.outbox.count() == 1
        assert self.user.inbox.count() == len(self.other_users)
        assert self.inboxes_and_outboxes_of_others_are_populated()

    def inbox_and_outbox_of_primary_user_are_empty(self):
        return (self.user.inbox.count() == 0) and (self.user.outbox.count() == 0)

    def inboxes_and_outboxes_of_others_are_populated(self):
        return all(
            user.inbox.count() == 1 and user.outbox.count() == 1 for user in self.other_users
        )
