import json
from datetime import date, timedelta

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from kitsune.kpi.models import (
    CONTRIBUTORS_CSAT_METRIC_CODE,
    KB_ENUS_CONTRIBUTORS_CSAT_METRIC_CODE,
    KB_L10N_CONTRIBUTORS_CSAT_METRIC_CODE,
    SUPPORT_FORUM_CONTRIBUTORS_CSAT_METRIC_CODE,
    Metric,
    MetricKind,
)
from kitsune.kpi.surveygizmo_utils import SURVEYS


class Command(BaseCommand):
    def handle(self, **options):
        user = settings.SURVEYGIZMO_USER
        password = settings.SURVEYGIZMO_PASSWORD
        startdate = date.today() - timedelta(days=2)
        enddate = date.today() - timedelta(days=1)
        page = 1
        more_pages = True
        survey_id = SURVEYS["general"]["community_health"]

        csat = {
            CONTRIBUTORS_CSAT_METRIC_CODE: 0,
            SUPPORT_FORUM_CONTRIBUTORS_CSAT_METRIC_CODE: 0,
            KB_ENUS_CONTRIBUTORS_CSAT_METRIC_CODE: 0,
            KB_L10N_CONTRIBUTORS_CSAT_METRIC_CODE: 0,
        }

        counts = {
            CONTRIBUTORS_CSAT_METRIC_CODE: 0,
            SUPPORT_FORUM_CONTRIBUTORS_CSAT_METRIC_CODE: 0,
            KB_ENUS_CONTRIBUTORS_CSAT_METRIC_CODE: 0,
            KB_L10N_CONTRIBUTORS_CSAT_METRIC_CODE: 0,
        }

        while more_pages:
            response = requests.get(
                "https://restapi.surveygizmo.com/v2/survey/{survey}"
                "/surveyresponse?"
                "filter[field][0]=datesubmitted"
                "&filter[operator][0]=>=&filter[value][0]={start}+0:0:0"
                "&filter[field][1]=datesubmitted"
                "&filter[operator][1]=<&filter[value][1]={end}+0:0:0"
                "&filter[field][2]=status&filter[operator][2]=="
                "&filter[value][2]=Complete"
                "&resultsperpage=500"
                "&page={page}"
                "&user:pass={user}:{password}".format(
                    survey=survey_id,
                    start=startdate,
                    end=enddate,
                    page=page,
                    user=user,
                    password=password,
                ),
                timeout=300,
            )

            results = json.loads(response.content)
            total_pages = results.get("total_pages", 1)
            more_pages = page < total_pages

            if "data" in results:
                for r in results["data"]:
                    try:
                        rating = int(r["[question(3)]"])
                    except ValueError:
                        # CSAT question was not answered
                        pass
                    else:
                        csat[CONTRIBUTORS_CSAT_METRIC_CODE] += rating
                        counts[CONTRIBUTORS_CSAT_METRIC_CODE] += 1

                        if len(r["[question(4), option(10011)]"]):  # Support Forum
                            csat[SUPPORT_FORUM_CONTRIBUTORS_CSAT_METRIC_CODE] += rating
                            counts[SUPPORT_FORUM_CONTRIBUTORS_CSAT_METRIC_CODE] += 1

                        if len(r["[question(4), option(10012)]"]):  # KB EN-US
                            csat[KB_ENUS_CONTRIBUTORS_CSAT_METRIC_CODE] += rating
                            counts[KB_ENUS_CONTRIBUTORS_CSAT_METRIC_CODE] += 1

                        if len(r["[question(4), option(10013)]"]):  # KB L10N
                            csat[KB_L10N_CONTRIBUTORS_CSAT_METRIC_CODE] += rating
                            counts[KB_L10N_CONTRIBUTORS_CSAT_METRIC_CODE] += 1

            page += 1

        for code in csat:
            metric_kind = MetricKind.objects.get_or_create(code=code)[0]
            value = (
                csat[code] // counts[code] if counts[code] else 50
            )  # If no responses assume neutral
            Metric.objects.update_or_create(
                kind=metric_kind,
                start=startdate,
                end=enddate,
                defaults={"value": value},
            )
