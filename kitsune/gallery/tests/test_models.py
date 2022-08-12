from unittest.mock import patch

from django.core.files.base import ContentFile

from kitsune.gallery.models import Image
from kitsune.gallery.tests import ImageFactory
from kitsune.sumo.tests import TestCase
from kitsune.upload.tasks import generate_thumbnail


@patch("kitsune.upload.tasks._create_image_thumbnail")
class ImageTestCase(TestCase):
    def tearDown(self):
        Image.objects.all().delete()
        super(ImageTestCase, self).tearDown()

    def test_thumbnail_url_if_set(self, create_thumbnail_mock):
        """thumbnail_url_if_set() returns self.thumbnail if set, or else
        returns self.file"""
        img = ImageFactory()
        self.assertEqual(img.file.url, img.thumbnail_url_if_set())

        create_thumbnail_mock.return_value = ContentFile("the dude")
        generate_thumbnail("gallery.Image", img.id, "file", "thumbnail")
        img.refresh_from_db()
        self.assertEqual(img.thumbnail.url, img.thumbnail_url_if_set())
