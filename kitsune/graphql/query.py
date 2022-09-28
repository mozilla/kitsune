import graphene
from django.contrib.auth.models import User

from kitsune.graphql.schema import ContributorType


class Query(graphene.ObjectType):
    is_contributor = graphene.Field(ContributorType, username=graphene.String())

    def resolve_is_contributor(root, info, username):
        try:
            contributor = User.objects.get(username=username)
        except User.DoesNotExist:
            pass
        else:
            if contributor.groups.filter(name="Contributors").exists():
                return contributor
        return None
