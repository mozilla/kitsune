"""
Downloads image files for gallery images from the CDN.

Run this script like `./manage.py runscript get_media`.
"""

import os
import sys
from datetime import datetime

import urllib

from kitsune.gallery.models import Image
from kitsune.sumo.utils import Progress


BASE_URL = 'https://support.cdn.mozilla.net'


def run():
    # Fetching things from the DB can error, which is sad.
    images = list(safe_exhaust_queryset(Image.objects.all()))
    progress = Progress(len(images), 100)
    progress.draw()

    for img in images:
        url = BASE_URL + img.file.url
        path = img.file.url[1:]  # Remove leading '/'

        if os.path.exists(path):
            progress.tick()
            continue

        try:
            os.makedirs(os.path.dirname(path))
        except OSError as e:
            if e.errno != 17:
                raise e

        try:
            urllib.urlretrieve(url, path)
        except urllib.ContentTooShortError:
            print "Couldn't download", path
            try:
                os.unlink(path)
            except IOError:
                pass
        progress.tick()
    print '\nDone'


def safe_exhaust(it):
    """Safely exhaust an iterable, skipping any items that raise IOErrors."""
    it = iter(it)
    while True:
        try:
            yield next(it)
        except StopIteration:
            break
        except IOError as e:
            if e.errno != 2:
                raise e
