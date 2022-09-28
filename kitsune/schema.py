import graphene

from kitsune.graphql import query as kitsune_query


class Query(kitsune_query.Query, graphene.ObjectType):
    """Top level Query.

    Inherits from Query classes in other apps.
    """

    ...


schema = graphene.Schema(query=Query)
