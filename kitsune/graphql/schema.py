import graphene
from graphene_django import DjangoObjectType

from kitsune.users.models import Profile


class ProfileType(DjangoObjectType):
    class Meta:
        model = Profile


class Query(graphene.ObjectType):
    profiles = graphene.List(ProfileType)

    def resolve_profiles(self, info, **kwargs):
        return Profile.objects.all()


schema = graphene.Schema(query=Query)
