import os
import subprocess

from django.conf import settings
from django.core.management.base import BaseCommand


ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))


def path(*parts):
    return os.path.join(ROOT, *parts)


class Command(BaseCommand):
    help = "Precompiles nunjuck templates"

    def handle(self, *args, **kwargs):
        try:
            os.makedirs(path("static/sumo/js/templates"))
        except OSError:
            pass

        try:
            os.makedirs(path("static/sumo/tpl"))
        except OSError:
            pass

        files = os.listdir(path("static/sumo/tpl"))

        for f in files:
            if f.endswith(".html"):
                tpl = f[:-5]
                cmd = "%s %s > %s" % (
                    settings.NUNJUCKS_PRECOMPILE_BIN,
                    path("static/sumo/tpl"),
                    path("static/sumo/js/templates/%s.js" % tpl),
                )
                subprocess.call(cmd, shell=True)
