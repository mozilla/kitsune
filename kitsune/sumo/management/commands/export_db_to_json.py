from datetime import datetime

from django.apps import apps
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

# TODO: remove this once we have s3 ready
PATH = "/tmp/"


class Command(BaseCommand):
    help = "Export application tables to json."

    def handle(self, *args, **options):
        """Get all the table for each installed application
        and dump them to json in indvidual files.
        """

        sumo_apps = map(
            lambda x: x.split("kitsune.")[1],
            [app for app in settings.INSTALLED_APPS if app.startswith("kitsune")],
        )
        db_models = [model for app in sumo_apps for model in apps.get_app_config(app).get_models()]

        for model in db_models:
            unix_time = datetime.now().strftime("%s")
            filename = PATH + f"{model.__name__}-{unix_time}.json"
            with open(filename, "w") as f:
                call_command(
                    "dumpdata",
                    f"{model._meta.app_config.label}.{model.__name__}",
                    format="json",
                    indent=4,
                    stdout=f,
                )
