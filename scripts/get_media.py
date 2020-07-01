"""
Downloads image files for gallery images from the CDN.

Run this script like `./manage.py runscript get_media`.
"""
import os
import urllib.error
import urllib.parse
import urllib.request

from kitsune.gallery.models import Image
from kitsune.sumo.utils import Progress


BASE_URL = 'https://support.cdn.mozilla.net'


def run():
    image_urls = list(Image.objects.values_list('file', flat=True))

    progress = Progress(len(image_urls), 100)
    progress.draw()

    for path in image_urls:
        path = 'media/' + path
        url = BASE_URL + '/' + path

        try:
            os.makedirs(os.path.dirname(path))
        except OSError as e:
            if e.errno != 17:
                raise e

        try:
            urllib.request.urlretrieve(url, path)
        except urllib.error.ContentTooShortError:
            print("Couldn't download", path)
        progress.tick()
    print('\nDone')
