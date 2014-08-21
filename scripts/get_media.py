#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Downloads image files for gallery images from the CDN.

Run this script like `./manage.py runscript get_media`.
"""

import sys
from datetime import datetime

import urllib

from kitsune.gallery.models import Image


BASE_URL = 'https://support.cdn.mozilla.net'


def run():
    images = list(Image.objects.all())
    progress = Progress(len(images))
    progress.draw()

    for img in images:
        url = BASE_URL + img.file.url
        path = img.file.url[1:]  # Remove leading '/'
        try:
            urllib.urlretrieve(url, path)
        except urllib.ContentTooShortError:
            print "Couldn't download", path
        progress.tick()
    print '\nDone'


class Progress():

    milestone_stride = 101

    def __init__(self, total):
        self.current = 0
        self.total = total
        self.milestone_time = datetime.now()
        self.estimated = '?'

    def tick(self, incr=1):
        self.current += incr

        if self.current and self.current % self.milestone_stride == 0:
            now = datetime.now()
            duration = now - self.milestone_time
            duration = duration.seconds + duration.microseconds / 1e6
            rate = self.milestone_stride / duration
            remaining = self.total - self.current
            self.estimated = int(remaining / rate / 60)
            self.milestone_time = now

        self.draw()

    def draw(self):
        self._wr('{0.current} / {0.total} (Est. {0.estimated} min. remaining)\r'.format(self))

    def _wr(self, s):
        sys.stdout.write(s)
        sys.stdout.flush()
