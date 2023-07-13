import graphene

from kitsune.graphql.query import Query


schema = graphene.Schema(query=Query)
