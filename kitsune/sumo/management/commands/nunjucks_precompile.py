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
        files = os.listdir(path('static/tpl'))

        if not os.path.exists(path('static/js/templates')):
            os.makedirs(path('static/js/templates'))

        for f in files:
            if f.endswith('.html'):
                tpl = f[:-5]
                cmd = '%s %s > %s' % (
                    settings.NUNJUCKS_PRECOMPILE_BIN,
                    path('static/tpl'),
                    path('static/js/templates/%s.js' % tpl))
                subprocess.call(cmd, shell=True)
