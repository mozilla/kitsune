import factory

from kitsune.groups.models import EnterpriseInvitation, GroupProfile
from kitsune.users.tests import GroupFactory, UserFactory


class GroupProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GroupProfile

    group = factory.SubFactory(GroupFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        return model_class.objects.add_root(create_kwargs=kwargs)


class EnterpriseInvitationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EnterpriseInvitation

    company = factory.SubFactory(GroupProfileFactory)
    user = factory.SubFactory(UserFactory)
    email = factory.LazyAttribute(lambda invitation: invitation.user.email.casefold())
