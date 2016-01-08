import jinja2
from django_jinja import library

from kitsune import access


@jinja2.contextfunction
@library.global_function
def has_perm(context, perm, obj):
    """
    Check if the user has a permission on a specific object.

    Returns boolean.
    """
    return access.has_perm(context['request'].user, perm, obj)


@jinja2.contextfunction
@library.global_function
def has_perm_or_owns(context, perm, obj, perm_obj, field_name='creator'):
    """
    Check if the user has a permission or owns the object.

    Ownership is determined by comparing perm_obj.field_name to the user in
    context.
    """
    user = context['request'].user
    if user.is_anonymous():
        return False
    return access.has_perm_or_owns(user, perm, obj, perm_obj, field_name)
