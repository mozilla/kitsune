from datetime import datetime

from django.core.files import File

from kitsune.gallery.models import Image, Video
from kitsune.users.tests import user


def image(file_and_save=True, **kwargs):
    """Return a saved image."""
    u = None
    if 'creator' not in kwargs:
        u = user(save=True)

    defaults = {'title': 'Some title %s' % str(datetime.now()),
                'description': 'Some description %s' % str(datetime.now()),
                'creator': u}
    defaults.update(kwargs)

    img = Image(**defaults)
    if not file_and_save:
        return img

    if 'file' not in kwargs:
        with open('kitsune/upload/tests/media/test.jpg') as f:
            up_file = File(f)
            img.file.save(up_file.name, up_file, save=True)

    return img


def video(file_and_save=True, **kwargs):
    """Return a saved video."""
    u = None
    if 'creator' not in kwargs:
        u = user(save=True)

    defaults = {'title': 'Some title', 'description': 'Some description',
                'creator': u}
    defaults.update(kwargs)

    vid = Video(**defaults)
    if not file_and_save:
        return vid

    if 'file' not in kwargs:
        with open('kitsune/gallery/tests/media/test.webm') as f:
            up_file = File(f)
            vid.webm.save(up_file.name, up_file, save=False)
        with open('kitsune/gallery/tests/media/test.ogv') as f:
            up_file = File(f)
            vid.ogv.save(up_file.name, up_file, save=False)
        with open('kitsune/gallery/tests/media/test.flv') as f:
            up_file = File(f)
            vid.flv.save(up_file.name, up_file, save=False)
        vid.save()

    return vid
