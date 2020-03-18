from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django_statsd.clients import statsd

from kitsune.kpi.surveygizmo_utils import add_email_to_campaign
from kitsune.questions.models import Question


class Command(BaseCommand):
    help = "Add question askers to a surveygizmo campaign to get surveyed."

    def handle(self, **options):
        # We get the email addresses of all users that asked a question 2 days
        # ago. Then, all we have to do is send the email address to surveygizmo
        # and it does the rest.
        two_days_ago = date.today() - timedelta(days=2)
        yesterday = date.today() - timedelta(days=1)

        emails = Question.objects.filter(
            created__gte=two_days_ago, created__lt=yesterday
        ).values_list("creator__email", flat=True)

        for email in emails:
            add_email_to_campaign("askers", email)

        statsd.gauge("survey.askers", len(emails))
