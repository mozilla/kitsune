from zoneinfo import ZoneInfo

import factory
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType

from kitsune.sumo.tests import FuzzyUnicode, LocalizingClient, TestCase
from kitsune.tidings.models import Watch
from kitsune.users.models import AccountEvent, ContributionAreas, Profile, Setting


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
        user.groups.add(
            GroupFactory(name=factory.fuzzy.FuzzyChoice(ContributionAreas.get_groups()))
        )


class ProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Profile

    name = FuzzyUnicode()
    bio = FuzzyUnicode()
    website = "http://support.example.com"
    timezone = ZoneInfo("US/Pacific")
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
