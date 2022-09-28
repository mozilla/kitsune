from django.contrib.auth.models import User
from graphene_django import DjangoObjectType


class ContributorType(DjangoObjectType):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
        )

    @classmethod
    def get_queryset(cls, queryset, info):
        """Do not return inactive users of info to non logged in users."""
        user = info.context.user
        if user.is_anonymous or not user.is_active:
            return queryset.none()
        return super().get_queryset(queryset, info)
