from django.db.models import Q
from django_jinja import library

from kitsune.karma.models import Title


@library.global_function
def karma_titles(user, viewer=None):
    """
    Return a list of titles for a given user.

    Only includes titles from groups that are visible to the viewer
    to prevent leaking private group membership.

    Args:
        user: User to get titles for
        viewer: User viewing the titles (None for anonymous, defaults to request.user in template)
    """
    from kitsune.groups.models import GroupProfile

    # Titles directly assigned to the user
    user_titles = Q(users=user)

    # Get visible GroupProfiles for this user (filtered by visibility)
    visible_group_profiles = GroupProfile.objects.visible(viewer).filter(group__user=user)
    visible_group_ids = list(visible_group_profiles.values_list('group_id', flat=True))

    # Get groups without GroupProfiles (legacy groups) - include them regardless of viewer
    groups_with_profiles = GroupProfile.objects.filter(group__user=user).values_list('group_id', flat=True)
    legacy_group_ids = list(
        user.groups.exclude(id__in=groups_with_profiles).values_list('id', flat=True)
    )

    # Combine visible + legacy
    all_visible_group_ids = visible_group_ids + legacy_group_ids
    group_titles = Q(groups__id__in=all_visible_group_ids)

    return Title.objects.filter(user_titles | group_titles).distinct()
