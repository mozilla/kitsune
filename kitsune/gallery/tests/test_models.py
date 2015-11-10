from nose.tools import eq_

from kitsune.gallery.models import Image
from kitsune.gallery.tests import ImageFactory
from kitsune.sumo.tests import TestCase
from kitsune.upload.tasks import generate_thumbnail


class ImageTestCase(TestCase):
    def tearDown(self):
        Image.objects.all().delete()
        super(ImageTestCase, self).tearDown()

    def test_thumbnail_url_if_set(self):
        """thumbnail_url_if_set() returns self.thumbnail if set, or else
        returns self.file"""
        img = ImageFactory()
        eq_(img.file.url, img.thumbnail_url_if_set())

        generate_thumbnail(img, 'file', 'thumbnail')
        eq_(img.thumbnail.url, img.thumbnail_url_if_set())
