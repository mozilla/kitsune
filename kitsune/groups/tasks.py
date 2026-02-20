import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count, Exists, F, OuterRef, Q, Subquery
from django.utils import timezone

from kitsune.sumo.decorators import skip_if_read_only_mode

log = logging.getLogger("k.task")


@shared_task
@skip_if_read_only_mode
def remove_inactive_users_from_groups():
    """Remove users inactive for 6+ months from all group membership and leadership roles."""
    from kitsune.groups.models import GroupProfile
    from kitsune.users.models import Deactivation

    User = get_user_model()
    cutoff = timezone.now() - timedelta(days=settings.INACTIVE_GROUP_MEMBER_RETENTION_DAYS)

    # Identify removable users. Evaluate the query once here, in order to avoid
    # multiple evaluations if left for evaluation within each of query below.
    removable_user_ids = list(
        User.objects.filter(is_active=False)
        .filter(Q(groups__isnull=False) | Q(groupprofile__isnull=False))
        .annotate(
            deactivated=Subquery(
                Deactivation.objects.filter(user=OuterRef("pk"))
                .order_by("-date")
                .values("date")[:1]
            )
        )
        .filter(deactivated__lte=cutoff)
        .values_list("pk", flat=True)
        .distinct()
    )

    if not removable_user_ids:
        log.info("No inactive users found to remove from their groups.")
        return

    # Identify root group-profiles that would be left leaderless.
    vulnerable_roots = (
        GroupProfile.objects.filter(depth=1)
        .annotate(
            total_leaders=Count("leaders"),
            removable_leaders=Count("leaders", filter=Q(leaders__in=removable_user_ids)),
        )
        .filter(total_leaders__gt=0, total_leaders=F("removable_leaders"))
    )

    for prof in vulnerable_roots.select_related("group"):
        log.warning(
            "Skipping the removal of inactive leader(s) from the root "
            f'group "{prof}" because it would become leaderless.'
        )

    # Bulk delete using the implicit "through" models for efficiency.
    # Bulk delete leaders, excluding those who were protected from removal.
    leaders_removed, _ = (
        GroupProfile.leaders.through.objects.filter(user__in=removable_user_ids)
        .exclude(groupprofile__in=vulnerable_roots)
        .delete()
    )
    # Bulk delete members, excluding those who were protected from removal as leaders.
    members_removed, _ = (
        User.groups.through.objects.filter(user__in=removable_user_ids)
        # Exclude members that are also leaders that could not be removed.
        .exclude(
            Exists(
                GroupProfile.leaders.through.objects.filter(
                    user_id=OuterRef("user_id"),
                    groupprofile__group_id=OuterRef("group_id"),
                    groupprofile__in=vulnerable_roots,
                )
            )
        )
        .delete()
    )

    log.info(
        f"Removed {leaders_removed} inactive leader(s) and "
        f"{members_removed} inactive member(s) from their groups."
    )
