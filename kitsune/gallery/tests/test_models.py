from nose.tools import eq_

from kitsune.gallery.models import Image
from kitsune.gallery.tests import image
from kitsune.sumo.tests import TestCase
from kitsune.upload.tasks import generate_thumbnail


class ImageTestCase(TestCase):
    def tearDown(self):
        Image.objects.all().delete()
        super(ImageTestCase, self).tearDown()

    def test_new_image(self):
        """New Image is created and saved"""
        img = image(title='Some title')
        eq_('Some title', img.title)
        eq_(150, img.file.width)
        eq_(200, img.file.height)

    def test_thumbnail_url_if_set(self):
        """thumbnail_url_if_set() returns self.thumbnail if set, or else
        returns self.file"""
        img = image()
        eq_(img.file.url, img.thumbnail_url_if_set())

        generate_thumbnail(img, 'file', 'thumbnail')
        eq_(img.thumbnail.url, img.thumbnail_url_if_set())
