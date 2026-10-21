from uuid import uuid4

import factory
from django.conf import settings

from kitsune.groups.models import EnterpriseInvitation, GroupProfile
from kitsune.users.tests import GroupFactory, UserFactory


class GroupProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GroupProfile

    group = factory.SubFactory(GroupFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        return model_class.objects.add_root(create_kwargs=kwargs)


class EnterpriseCompanyFactory(GroupProfileFactory):
    root = None
    slug = factory.LazyFunction(lambda: str(uuid4()))

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        root = kwargs.pop("root")
        if root is None:
            root = model_class.objects.filter(slug=settings.ENTERPRISE_GROUP_SLUG, depth=1).first()
            if root is None:
                root = GroupProfileFactory(
                    slug=settings.ENTERPRISE_GROUP_SLUG,
                    visibility=GroupProfile.Visibility.PRIVATE,
                )
        return model_class.objects.add_child(root, create_kwargs=kwargs)


class DepartmentFactory(GroupProfileFactory):
    company = factory.SubFactory(EnterpriseCompanyFactory)
    slug = factory.LazyFunction(lambda: str(uuid4()))

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        company = kwargs.pop("company")
        return model_class.objects.add_child(company, create_kwargs=kwargs)


class EnterpriseInvitationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EnterpriseInvitation

    company = factory.SubFactory(GroupProfileFactory)
    user = factory.SubFactory(UserFactory)
    email = factory.LazyAttribute(lambda invitation: invitation.user.email.casefold())
