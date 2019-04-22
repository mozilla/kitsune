from datetime import datetime, timedelta

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from kitsune.customercare.models import Reply
from kitsune.kpi.management import utils
from kitsune.kpi.surveygizmo_utils import SURVEYS
from kitsune.questions.models import Answer
from kitsune.wiki.models import Revision


class Command(BaseCommand):
    def handle(self, **options):
        querysets = [
            (Revision.objects.all(), ("creator", "reviewer")),
            (Answer.objects.not_by_asker(), ("creator",)),
            (Reply.objects.all(), ("user",)),
        ]

        end = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        start = end - timedelta(days=30)

        users = utils._get_cohort(querysets, (start, end))

        for u in users:
            p = u.profile
            if p.csat_email_sent is None or p.csat_email_sent < start:
                survey_id = SURVEYS["general"]["community_health"]
                campaign_id = SURVEYS["general"]["community_health_campaign_id"]

                try:
                    requests.put(
                        "https://restapi.surveygizmo.com/v4/survey/{survey}/surveycampaign/"
                        "{campaign}/contact?semailaddress={email}&api_token={token}"
                        "&api_token_secret={secret}&allowdupe=true".format(
                            survey=survey_id,
                            campaign=campaign_id,
                            email=u.email,
                            token=settings.SURVEYGIZMO_API_TOKEN,
                            secret=settings.SURVEYGIZMO_API_TOKEN_SECRET,
                        ),
                        timeout=30,
                    )
                except requests.exceptions.Timeout:
                    print("Timed out adding: %s" % u.email)
                else:
                    p.csat_email_sent = datetime.now()
                    p.save()
