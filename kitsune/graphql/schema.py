import graphene
from django.contrib.auth.models import User
from graphene_django import DjangoObjectType

from kitsune.users.utils import user_is_contributor


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
        return user_is_contributor(info.context.user)
