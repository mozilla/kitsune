from django.contrib.auth.models import User
from graphene_django import DjangoObjectType


class ContributorType(DjangoObjectType):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
        )
