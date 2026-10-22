import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from zenpy.lib.exception import APIException, ZenpyException

from kitsune.groups.membership import enterprise_profiles
from kitsune.groups.tasks import ZendeskMembershipChanged, sync_enterprise_zendesk_membership


class Command(BaseCommand):
    help = "Synchronize Zendesk memberships for current enterprise company members sequentially."

    def handle(self, **options):
        if settings.READ_ONLY:
            raise CommandError(
                "Zendesk membership synchronization is unavailable in read-only mode."
            )
        user_ids = (
            enterprise_profiles()
            .filter(group__user__isnull=False)
            .order_by("group__user")
            .values_list("group__user", flat=True)
            .distinct()
        )
        succeeded = failed = 0
        for user_id in user_ids.iterator():
            try:
                failure = sync_enterprise_zendesk_membership(user_id)
            except (
                APIException,
                ZenpyException,
                requests.RequestException,
                ZendeskMembershipChanged,
            ) as error:
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
