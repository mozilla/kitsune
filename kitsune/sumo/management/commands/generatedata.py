# ported from https://github.com/willkg/django-eadred

import imp

from django.conf import settings
from django.core.management.base import BaseCommand

from importlib import import_module


class Command(BaseCommand):
    help = "Generates sample data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--with",
            action="append",
            dest="param",
            help="Pass key=val style param to generate_sampledata",
        )

    def handle(self, *args, **options):
        if options.get("param"):
            for item in options["param"]:
                if "=" in item:
                    key, val = item.split("=")
                else:
                    key, val = item, True
                options[key] = val

        # Allows you to specify which apps to generate sampledata for.
        if not args:
            args = []

        for app in settings.INSTALLED_APPS:
            if args and app not in args:
                continue

            try:
                app_path = import_module(app).__path__
            except AttributeError:
                continue

            try:
                imp.find_module("sampledata", app_path)
            except ImportError:
                continue

            module = import_module("%s.sampledata" % app)
            if hasattr(module, "generate_sampledata"):
                self.stdout.write("Generating sample data from %s...\n" % app)
                module.generate_sampledata(options)

        self.stdout.write("Done!\n")
