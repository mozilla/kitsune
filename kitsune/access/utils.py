def has_perm(user, perm, obj):
    """
    Returns true if the user has the permission globally or on the given object.
    """
    return user.has_perm(perm) or user.has_perm(perm, obj)
