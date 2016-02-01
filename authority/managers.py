from django.db import models
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType


class PermissionManager(models.Manager):

    def get_content_type(self, obj):
        return ContentType.objects.get_for_model(obj)

    def get_for_model(self, obj):
        return self.filter(content_type=self.get_content_type(obj))

    def for_object(self, obj, approved=True):
        return self.get_for_model(obj).select_related(
            'user', 'creator', 'group', 'content_type'
        ).filter(object_id=obj.id, approved=approved)

    def for_user(self, user, obj, check_groups=True):
        perms = self.get_for_model(obj)
        if not check_groups:
            return perms.select_related('user', 'creator').filter(user=user)

        # Hacking user to user__pk to workaround deepcopy bug:
        # http://bugs.python.org/issue2460
        # Which is triggered by django's deepcopy which backports that fix in
        # Django 1.2
        return perms.select_related(
            'user',
            'creator'
        ).prefetch_related(
            'user__groups'
        ).filter(
            Q(user__pk=user.pk) | Q(group__in=user.groups.all())
        )

    def user_permissions(
            self, user, perm, obj, approved=True, check_groups=True):
        return self.for_user(
            user,
            obj,
            check_groups,
        ).filter(
            codename=perm,
            approved=approved,
        )

    def group_permissions(self, group, perm, obj, approved=True):
        """
        Get objects that have Group perm permission on
        """
        return self.get_for_model(obj).select_related(
            'user', 'group', 'creator').filter(group=group, codename=perm,
                                               approved=approved)

    def delete_objects_permissions(self, obj):
        """
        Delete permissions related to an object instance
        """
        perms = self.for_object(obj)
        perms.delete()

    def delete_user_permissions(self, user, perm, obj, check_groups=False):
        """
        Remove granular permission perm from user on an object instance
        """
        user_perms = self.user_permissions(user, perm, obj, check_groups=False)
        if not user_perms.filter(object_id=obj.id):
            return
        perms = self.user_permissions(user, perm, obj).filter(object_id=obj.id)
        perms.delete()
