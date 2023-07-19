from graphene.utils.is_introspection_key import is_introspection_key


class DisableIntrospectionMiddleware:
    def resolve(self, next, root, info, **kwargs):
        if is_introspection_key(info.field_name):
            raise Exception("GraphQL introspection is disabled.")
        return next(root, info, **kwargs)
