import graphene

from kitsune.graphql.schema import ContributorType
from kitsune.users.models import ContributionAreas


class Query(graphene.ObjectType):
    is_contributor = graphene.Field(ContributorType)

    def resolve_is_contributor(root, info):
        """Return the current user if they are a contributor."""
        # by default we reject non logged in users
        user = info.context.user

        if user.is_authenticated and user.groups.filter(name__in=ContributionAreas.get_groups()):
            return user
        return None
