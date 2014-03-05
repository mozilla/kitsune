#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Finds revisions from the Thunderbird migration that don't have based_on
set correctly, and are still relavent, and fixes that.

Run this script like `./manage.py runscript fix_tb_basedon`.
"""

import sys
from traceback import print_exc

from django.db.models import Q

from kitsune.wiki.models import Document, Revision


MARKER_COMMENT = 'Fake revision for localization fiddling.'


def run():
    try:
        run_()
    except Exception:
        print_exc()
        raise


class Progress():

    def __init__(self, total):
        self.current = 0
        self.total = total

    def tick(self, incr=1):
        self.current += incr
        self.draw()

    def draw(self):
        self._wr('{0.current} / {0.total}\r'.format(self))

    def _wr(self, s):
        sys.stdout.write(s)
        sys.stdout.flush()


def run_():
    to_process = list(Document.objects.filter(
        ~Q(parent=None),
        current_revision__based_on=None,
        products__slug='thunderbird'))

    if len(to_process) == 0:
        print 'Nothing to do.'

    prog = Progress(len(to_process))

    for doc in to_process:
        prog.tick()
        oldest_parent_rev = (Revision.objects.filter(document=doc.parent)
                             .order_by('id')[0])

        # It has localizations, clearly it should be localizable.
        if not doc.parent.is_localizable:
            doc.parent.is_localizable = True
            doc.parent.save()

        doc.current_revision.based_on = oldest_parent_rev
        doc.current_revision.save()
