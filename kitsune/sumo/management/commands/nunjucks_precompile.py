import os
import subprocess

from django.conf import settings
from django.core.management.base import BaseCommand


ROOT = os.path.realpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
path = lambda *a: os.path.join(ROOT, *a)


class Command(BaseCommand):
    help = 'Precompiles nunjuck templates'

    def handle(self, *args, **kwargs):
        cmd = '%s %s > %s' % (
            settings.NUNJUCKS_PRECOMPILE_BIN,
            path('static/tpl'),
            path('static/js/nunjucks-templates.js'))
        subprocess.call(cmd, shell=True)
