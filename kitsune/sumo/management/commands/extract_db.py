import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.apps import apps


HEADER = """\
#######################################################################
#
# Note: This file is a generated file--do not edit it directly!
# Instead make changes to the appropriate content in the database or
# write up a bug here:
#
#     https://bugzilla.mozilla.org/enter_bug.cgi?product=support.mozilla.org
#
# with the specific lines that are problematic and why.
#
# You can generate this file by running:
#
#     ./manage.py extract_db
#
#######################################################################
"""

L10N_STRING = 'pgettext("{context}", """{id}""")\n'


class Command(BaseCommand):
    """
    Pulls strings from the database and puts them in a python file,
    wrapping each one in a gettext call.

    The models and attributes to pull are defined by DB_LOCALIZE:

    DB_LOCALIZE = {
        'some_app': {
            SomeModel': {
                'attrs': ['attr_name', 'another_attr'],
            }
        },
        'another_app': {
            AnotherModel': {
                'attrs': ['more_attrs'],
                'comments': ['Comment that will appear to localizers.'],
            }
        },
    }

    Database columns are expected to be CharFields or TextFields.
    """

    help = "Pulls strings from the database and writes them to python file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output-file",
            "-o",
            default=os.path.join(settings.ROOT, "kitsune", "sumo", "db_strings.py"),
            dest="outputfile",
            help=("The file where extracted strings are written to. " "(Default: %default)"),
        )

    def handle(self, *args, **options):
        try:
            django_apps = settings.DB_LOCALIZE
        except AttributeError:
            raise CommandError("DB_LOCALIZE setting is not defined!")

        strings = []
        for app, models in list(django_apps.items()):
            for model, params in list(models.items()):
                model_class = apps.get_model(app, model)
                attrs = params["attrs"]
                qs = model_class.objects.all().values_list(*attrs).distinct()
                for item in qs:
                    for i in range(len(attrs)):
                        if not item[i]:
                            # Skip empty strings because empty string msgids
                            # are super bad.
                            continue
                        msg = {
                            "id": item[i],
                            "context": "DB: %s.%s.%s" % (app, model, attrs[i]),
                            "comments": params.get("comments"),
                        }
                        strings.append(msg)

        py_file = os.path.expanduser(options.get("outputfile"))
        py_file = os.path.abspath(py_file)

        print("Outputting db strings to: {filename}".format(filename=py_file))
        with open(py_file, "w+", encoding="utf-8") as f:
            f.write(HEADER)
            f.write("from django.utils.translation import pgettext\n\n")
            for s in strings:
                comments = s["comments"]
                if comments:
                    for c in comments:
                        f.write("# {comment}\n".format(comment=c))

                f.write(L10N_STRING.format(id=s["id"], context=s["context"]))
