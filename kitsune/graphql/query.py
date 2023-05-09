import graphene

from kitsune.graphql.schema import CurrentUserType


class Query(graphene.ObjectType):
    current_user = graphene.Field(CurrentUserType)

    def resolve_current_user(root, info):
        """Return the current user."""
        user = info.context.user
        if user.is_authenticated:
            return user
        return None
