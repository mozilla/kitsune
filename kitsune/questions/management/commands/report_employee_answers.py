from django.core.management.base import BaseCommand

from kitsune.questions.tasks import report_employee_answers


class Command(BaseCommand):
    help = "Send an email about employee answered questions."

    def handle(self, **options):
        report_employee_answers()
