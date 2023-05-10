from django.contrib.auth.models import User
import graphene
from graphene_django import DjangoObjectType

from kitsune.users.models import ContributionAreas


class CurrentUserType(DjangoObjectType):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
        )

    is_contributor = graphene.Boolean()

    def resolve_is_contributor(self, info):
        """Return whether the current user is a contributor."""
        user = info.context.user
        return (
            user.is_authenticated
            and user.groups.filter(name__in=ContributionAreas.get_groups()).exists()
        )
