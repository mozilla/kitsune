"""
Downloads image files for gallery images from the CDN.

Run this script like `./manage.py runscript get_media`.
"""

import sys
from datetime import datetime

import urllib

from kitsune.gallery.models import Image
from kitsune.sumo.utils import Progress


BASE_URL = 'https://support.cdn.mozilla.net'


def run():
    images = list(Image.objects.all())
    progress = Progress(len(images), 100)
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
