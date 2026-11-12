from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError

from kitsune.groups.membership import enterprise_profiles
from kitsune.groups.tasks import (
    ZendeskMembershipChanged,
    ZendeskUnavailable,
    sync_enterprise_zendesk_membership,
)


class Command(BaseCommand):
    help = (
        "Synchronize Zendesk memberships for current enterprise company members and leaders "
        "sequentially."
    )

    def handle(self, **options):
        if settings.READ_ONLY:
            raise CommandError(
                "Zendesk membership synchronization is unavailable in read-only mode."
            )
        profiles = enterprise_profiles()
        user_ids = sorted(
            {
                *profiles.filter(group__user__isnull=False).values_list("group__user", flat=True),
                *profiles.filter(leaders__isnull=False).values_list("leaders", flat=True),
            }
        )
        succeeded = failed = 0
        for user_id in user_ids:
            try:
                failure = sync_enterprise_zendesk_membership(user_id)
            except ZendeskUnavailable as error:
                name, status = error.args
                failure = f"ZendeskUnavailable {name} {status}"
            except (ZendeskMembershipChanged, DatabaseError) as error:
                failure = type(error).__name__
            if failure:
                failed += 1
                self.stderr.write(f"User {user_id}: {failure}.")
            else:
                succeeded += 1
                self.stdout.write(f"Synchronized user {user_id}.")
        self.stdout.write(f"Synchronized: {succeeded}; failed: {failed}.")
        if failed:
            raise CommandError("Zendesk membership synchronization is incomplete.")
