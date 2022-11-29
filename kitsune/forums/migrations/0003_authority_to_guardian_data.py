from django.apps import apps as global_apps
from django.contrib.auth.models import Permission
from django.db import migrations


AUTHORITY_TO_GUARDIAN = {
    "forums_forum.thread_edit_forum": ("edit_forum_thread", "Can edit forum threads"),
    "forums_forum.thread_delete_forum": ("delete_forum_thread", "Can delete forum threads"),
    "forums_forum.thread_move_forum": (
        "move_forum_thread",
        "Can move threads between forums",
    ),
    "forums_forum.thread_sticky_forum": (
        "sticky_forum_thread",
        "Can mark/unmark a forum thread as sticky",
    ),
    "forums_forum.thread_locked_forum": (
        "lock_forum_thread",
        "Can lock/unlock forum threads",
    ),
    "forums_forum.post_edit_forum": (
        "edit_forum_thread_post",
        "Can edit posts within forum threads",
    ),
    "forums_forum.post_delete_forum": (
        "delete_forum_thread_post",
        "Can delete posts within forum threads",
    ),
    "forums_forum.post_in_forum": ("post_in_forum", "Can post in restricted forums"),
    "forums_forum.view_in_forum": ("view_in_forum", "Can view restricted forums"),
}


def get_or_create_guardian_perm(authority_perm):
    """
    Given an authority.models.Permission instance, returns its equivalent Django
    Permission (django.contrib.auth.models.Permission) instance. If the equivalent
    Django Permission instance doesn't already exist, it is created.
    """
    assert authority_perm.codename in AUTHORITY_TO_GUARDIAN

    codename, name = AUTHORITY_TO_GUARDIAN[authority_perm.codename]

    return Permission.objects.get_or_create(
        name=name,
        codename=codename,
        content_type=authority_perm.content_type,
    )[0]


def migrate_authority_to_guardian(apps, schema_editor):
    """
    Convert the Authority object-level permission assignments into
    Guardian object-level permission assignments, and also set the
    the "restrict_viewing" and/or "restrict_posting" attributes of
    any forums as needed.
    """

    try:
        from guardian.shortcuts import assign_perm
    except ImportError:
        # The django-guardian app is not installed.
        return

    try:
        from authority.models import Permission
    except ImportError:
        # The django-authority app is not installed.
        return

    for perm in Permission.objects.all():
        if not perm.content_object:
            # If the object (Forum instance) no longer exists, skip it.
            continue

        forum = perm.content_object

        # If "view_in_forum" or "post_in_forum" is defined on a forum, we need
        # to set that forum's "restrict_viewing" or "restrict_posting" attribute
        # in our world of object-level permissions based on django-guardian.
        if perm.codename == "forums_forum.view_in_forum":
            forum.restrict_viewing = True
            forum.save()
            print(f'restricted viewing of forum "{forum.name} ({forum.slug})"')
        elif perm.codename == "forums_forum.post_in_forum":
            forum.restrict_posting = True
            forum.save()
            print(f'restricted posting in forum "{forum.name} ({forum.slug})"')

        if not (perm.user or perm.group):
            # The permission is not assigned to any user or group. This case
            # is allowed in django-authority, and in our case it's used only
            # when restricting some forums, so it's already handled by the
            # preceding code. There's no equivalent to this within the world
            # of django-guardian.
            continue

        assign_perm(
            get_or_create_guardian_perm(perm),
            perm.group if perm.group else perm.user,
            forum,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("forums", "0002_auto_20221031_0956"),
    ]

    if global_apps.is_installed("authority"):
        dependencies.append(("authority", "0001_initial"))

    if global_apps.is_installed("guardian"):
        dependencies.append(("guardian", "0002_generic_permissions_index"))

    operations = [
        migrations.RunPython(migrate_authority_to_guardian, migrations.RunPython.noop),
    ]
