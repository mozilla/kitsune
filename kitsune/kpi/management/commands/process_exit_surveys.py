from datetime import datetime, timedelta

from django.core.management.base import BaseCommand

from kitsune.kpi.management import utils
from kitsune.kpi.surveygizmo_utils import (
    SURVEYS,
    add_email_to_campaign,
    get_email_addresses,
)


class Command(BaseCommand):
    help = "Exit survey handling."

    def handle(self, **options):
        """
        * Collect new exit survey results.
        * Save results to our metrics table.
        * Add new emails collected to the exit survey.
        """

        utils._process_exit_survey_results()

        # Get the email addresses from 4-5 hours ago and add them to the survey
        # campaign (skip this on stage).

        # The cron associated with this process is set to run every hour,
        # with the intent of providing a 4-5 hour wait period between when a
        # visitor enters their email address and is then sent a follow-up
        # survey.
        # The range here is set between 4 and 8 hours to be sure no emails are
        # missed should a particular cron run be skipped (e.g. during a deployment)
        startdatetime = datetime.now() - timedelta(hours=8)
        enddatetime = datetime.now() - timedelta(hours=4)

        for survey in list(SURVEYS.keys()):
            if (
                not SURVEYS[survey]["active"] or
                "email_collection_survey_id" not in SURVEYS[survey]
            ):
                # Some surveys don't have email collection on the site
                # (the askers survey, for example).
                continue

            emails = get_email_addresses(survey, startdatetime, enddatetime)
            for email in emails:
                add_email_to_campaign(survey, email)
