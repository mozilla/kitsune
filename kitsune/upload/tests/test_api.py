from nose.tools import eq_

from kitsune.sumo.tests import TestCase
from kitsune.upload.tests import ImageAttachmentFactory
from kitsune.upload import api


class ImageAttachmentSerializerTests(TestCase):
    def test_expected_fields(self):
        image = ImageAttachmentFactory()
        serializer = api.ImageAttachmentSerializer(instance=image)

        eq_(serializer.data["url"], image.get_absolute_url())
        eq_(serializer.data["thumbnail_url"], image.thumbnail_if_set().url)
