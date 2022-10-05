import graphene
from django.contrib.auth.models import User

from kitsune.graphql.schema import ContributorType


class Query(graphene.ObjectType):
    is_contributor = graphene.Field(ContributorType)

    def resolve_is_contributor(root, info):
        """Return the current user if they are a contributor."""
        # by default we reject non logged in users
        user = info.context.user

        try:
            contributor = User.objects.get(username=user.username)
        except User.DoesNotExist:
            pass
        else:
            if contributor.groups.filter(name="Contributors").exists():
                return contributor
        return None
