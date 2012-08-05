from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.files import File

from nose.tools import eq_

from questions.tests import question
from sumo.tests import TestCase
from upload.models import ImageAttachment
from upload.tasks import generate_thumbnail
from users.tests import user


class ImageAttachmentTestCase(TestCase):

    def setUp(self):
        super(ImageAttachmentTestCase, self).setUp()
        self.user = user(save=True)
        self.obj = question(save=True)
        self.ct = ContentType.objects.get_for_model(self.obj)

    def tearDown(self):
        ImageAttachment.objects.all().delete()
        super(ImageAttachmentTestCase, self).tearDown()

    def test_thumbnail_if_set(self):
        """thumbnail_if_set() returns self.thumbnail if set, or else returns
        self.file"""
        image = ImageAttachment(content_object=self.obj, creator=self.user)
        with open('apps/upload/tests/media/test.jpg') as f:
            up_file = File(f)
            image.file.save(up_file.name, up_file, save=True)

        eq_(image.file, image.thumbnail_if_set())

        generate_thumbnail(image, 'file', 'thumbnail')
        eq_(image.thumbnail, image.thumbnail_if_set())
