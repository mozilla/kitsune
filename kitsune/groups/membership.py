from collections import defaultdict
from contextlib import contextmanager
from hashlib import sha256

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import connections, transaction
from django.utils.translation import gettext_lazy as _lazy

_HIERARCHY_LOCK_KEY = int.from_bytes(
    sha256(b"sumo-enterprise-group-hierarchy").digest()[:8], signed=True
)


@contextmanager
def lock_enterprise_hierarchy(*, using="default", exclusive=False):
    """Hold the tree stable until commit, before locking company or user rows.

    Membership mutations share the gate; hierarchy mutations take it exclusively.
    Callers that also save profiles or lock companies must enter this context first.
    Never upgrade a shared gate to exclusive in a concurrent mutation path.
    """
    with transaction.atomic(using=using):
        with connections[using].cursor() as cursor:
            if exclusive:
                cursor.execute("SELECT pg_advisory_xact_lock(%s)", [_HIERARCHY_LOCK_KEY])
            else:
                cursor.execute("SELECT pg_advisory_xact_lock_shared(%s)", [_HIERARCHY_LOCK_KEY])
        yield


def _enterprise_profiles(using):
    # The manager calls the move guard, so importing GroupProfile here would cycle.
    profiles = apps.get_model("groups", "GroupProfile").objects.using(using)
    root_path = (
        profiles.filter(slug=settings.ENTERPRISE_GROUP_SLUG, depth=1)
        .values_list("path", flat=True)
        .first()
    )
    if root_path is None:
        return profiles.none()
    return profiles.filter(path__startswith=root_path, depth__gte=2)


def _company_paths(group_ids, using):
    profiles = _enterprise_profiles(using)
    company_path_length = profiles.model.steplen * 2
    companies = defaultdict(set)
    for group_id, path in profiles.filter(group_id__in=group_ids).values_list("group_id", "path"):
        # A Group can have several profiles, including profiles in different companies.
        companies[group_id].add(path[:company_path_length])
    return companies


def _validate_memberships(user_ids, group_ids, *, replace, using, check_existing=False):
    if not user_ids:
        return
    proposed = _company_paths(group_ids, using) if group_ids else {}
    proposed_companies = set().union(*proposed.values()) if proposed else set()
    if not proposed_companies and not check_existing:
        return

    companies_by_user = {user_id: set(proposed_companies) for user_id in user_ids}
    if not replace:
        memberships = list(
            User.groups.through.objects.using(using)
            .filter(user_id__in=user_ids)
            .values_list("user_id", "group_id")
        )
        existing = _company_paths({group_id for _, group_id in memberships}, using)
        for user_id, group_id in memberships:
            companies_by_user[user_id].update(existing.get(group_id, ()))

    if any(len(companies) > 1 for companies in companies_by_user.values()):
        raise ValidationError(
            _lazy(
                "A user can belong to only one enterprise company. "
                "Remove conflicting company memberships before adding another."
            ),
            code="company_conflict",
        )


def validate_enterprise_memberships(user_ids, group_ids, *, replace=False, using="default"):
    """Validate additions, or a complete replacement, without disclosing memberships.

    This is early feedback only. Writers must use the M2M managers or hold
    guard_enterprise_memberships around both validation and persistence.
    """
    user_ids = tuple(set(user_ids))
    group_ids = tuple(set(group_ids))
    if not user_ids:
        return
    with lock_enterprise_hierarchy(using=using):
        _validate_memberships(user_ids, group_ids, replace=replace, using=using)


def _lock_users(user_ids, using):
    # Stable ordering prevents deadlocks between overlapping membership batches.
    list(
        User.all_users.using(using)
        .filter(pk__in=user_ids)
        .order_by("pk")
        .select_for_update()
        .values_list("pk", flat=True)
    )


@contextmanager
def guard_enterprise_memberships(user_ids, group_ids, *, replace=False, using="default"):
    """Serialize validation and writes; callers must not lock companies afterward."""
    user_ids = tuple(set(user_ids))
    group_ids = tuple(set(group_ids))
    with lock_enterprise_hierarchy(using=using):
        _lock_users(user_ids, using)
        _validate_memberships(user_ids, group_ids, replace=replace, using=using)
        yield


def _profile_companies(profile_ids, using):
    profiles = _enterprise_profiles(using)
    company_path_length = profiles.model.steplen * 2
    companies = dict(profiles.filter(depth=2).values_list("path", "pk"))
    return {
        profile_id: (group_id, companies[path[:company_path_length]])
        for profile_id, group_id, path in profiles.filter(pk__in=profile_ids).values_list(
            "pk", "group_id", "path"
        )
    }


def validate_enterprise_group_memberships(profile, *, using="default"):
    """Validate an inserted/reassigned profile while its exclusive gate is held."""
    if not _enterprise_profiles(using).filter(pk=profile.pk).exists():
        return
    user_ids = tuple(
        User.groups.through.objects.using(using)
        .filter(group_id=profile.group_id)
        .values_list("user_id", flat=True)
    )
    _lock_users(user_ids, using)
    _validate_memberships(user_ids, (), replace=False, using=using, check_existing=True)


@contextmanager
def guard_enterprise_group_move(node, target, *, using="default"):
    """Validate the actual treebeard result and roll back an unsafe move atomically.

    Company primary keys, not materialized paths, identify ancestry: treebeard can
    renumber unrelated siblings while moving a subtree. The exclusive gate also
    covers empty groups that gain their first member concurrently with a move.
    """
    try:
        with lock_enterprise_hierarchy(using=using, exclusive=True):
            node.refresh_from_db(using=using)
            target.refresh_from_db(using=using)
            profile_ids = tuple(
                node.__class__.objects.using(using)
                .filter(path__startswith=node.path)
                .values_list("pk", flat=True)
            )
            before = _profile_companies(profile_ids, using)
            yield
            after = _profile_companies(profile_ids, using)
            changed_groups = set()
            for profile_id in before.keys() | after.keys():
                old_membership = before.get(profile_id)
                new_membership = after.get(profile_id)
                if old_membership != new_membership:
                    if old_membership is not None:
                        changed_groups.add(old_membership[0])
                    if new_membership is not None:
                        changed_groups.add(new_membership[0])
            if changed_groups:
                user_ids = tuple(
                    User.groups.through.objects.using(using)
                    .filter(group_id__in=changed_groups)
                    .values_list("user_id", flat=True)
                    .distinct()
                )
                _lock_users(user_ids, using)
                _validate_memberships(
                    user_ids, (), replace=False, using=using, check_existing=True
                )
    finally:
        # treebeard refreshes these objects before validation; restore them on rollback too.
        node.refresh_from_db(using=using)
        target.refresh_from_db(using=using)
