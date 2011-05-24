import os

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files import File
from django.core.files.images import ImageFile

from nose.tools import eq_

from questions.models import Question
from sumo.tests import TestCase
from upload.models import ImageAttachment
from upload.tasks import (_scale_dimensions, _create_image_thumbnail,
                          generate_thumbnail)


class ScaleDimensionsTestCase(TestCase):

    def test_scale_dimensions_default(self):
        """A square image of exact size is not scaled."""
        ts = settings.THUMBNAIL_SIZE
        (width, height) = _scale_dimensions(ts, ts, ts)
        eq_(ts, width)
        eq_(ts, height)

    def test_small(self):
        """A small image is not scaled."""
        ts = settings.THUMBNAIL_SIZE / 2
        (width, height) = _scale_dimensions(ts, ts)
        eq_(ts, width)
        eq_(ts, height)

    def test_width_large(self):
        """An image with large width is scaled to width=MAX."""
        ts = 120
        (width, height) = _scale_dimensions(ts * 3 + 10, ts - 1, ts)
        eq_(ts, width)
        eq_(38, height)

    def test_large_height(self):
        """An image with large height is scaled to height=MAX."""
        ts = 150
        (width, height) = _scale_dimensions(ts - 2, ts * 2 + 9, ts)
        eq_(71, width)
        eq_(ts, height)

    def test_large_both_height(self):
        """An image with both large is scaled to the largest - height."""
        ts = 150
        (width, height) = _scale_dimensions(ts * 2 + 13, ts * 5 + 30, ts)
        eq_(60, width)
        eq_(ts, height)

    def test_large_both_width(self):
        """An image with both large is scaled to the largest - width."""
        ts = 150
        (width, height) = _scale_dimensions(ts * 20 + 8, ts * 4 + 36, ts)
        eq_(ts, width)
        eq_(31, height)


class CreateThumbnailTestCase(TestCase):

    def test_create_image_thumbnail_default(self):
        """A thumbnail is created from an image file."""
        thumb_content = _create_image_thumbnail(
            'apps/upload/tests/media/test.jpg')
        actual_thumb = ImageFile(thumb_content)
        with open('apps/upload/tests/media/test_thumb.jpg') as f:
            expected_thumb = ImageFile(f)

        eq_(expected_thumb.width, actual_thumb.width)
        eq_(expected_thumb.height, actual_thumb.height)

    def test_create_image_thumbnail_avatar(self):
        """An avatar is created from an image file."""
        thumb_content = _create_image_thumbnail(
            'apps/upload/tests/media/test.jpg',
            settings.AVATAR_SIZE, is_avatar=True)
        actual_thumb = ImageFile(thumb_content)
        
        eq_(settings.AVATAR_SIZE, actual_thumb.width)
        eq_(settings.AVATAR_SIZE, actual_thumb.height)


class GenerateThumbnail(TestCase):
    fixtures = ['users.json', 'questions.json']

    def setUp(self):
        super(GenerateThumbnail, self).setUp()
        self.user = User.objects.all()[0]
        self.obj = Question.objects.all()[0]

    def tearDown(self):
        ImageAttachment.objects.all().delete()

    def _image_with_thumbnail(self):
        image = ImageAttachment(content_object=self.obj, creator=self.user)
        with open('apps/upload/tests/media/test.jpg') as f:
            up_file = File(f)
            image.file.save(up_file.name, up_file, save=True)
        generate_thumbnail(image, 'file', 'thumbnail')
        return image

    def test_generate_thumbnail_default(self):
        """generate_thumbnail creates a thumbnail."""
        image = self._image_with_thumbnail()

        eq_(90, image.thumbnail.width)
        eq_(120, image.thumbnail.height)

    def test_generate_no_file(self):
        """generate_thumbnail does not fail when no file is provided."""
        image = ImageAttachment(content_object=self.obj, creator=self.user)
        generate_thumbnail(image, 'file', 'thumbnail')

    def test_generate_deleted_file(self):
        """generate_thumbnail does not fail if file doesn't actually exist."""
        image = ImageAttachment(content_object=self.obj, creator=self.user)
        with open('apps/upload/tests/media/test.jpg') as f:
            up_file = File(f)
            image.file.save(up_file.name, up_file, save=True)
        # The field will be set but the file isn't there.
        os.remove(image.file.path)
        generate_thumbnail(image, 'file', 'thumbnail')

    def test_generate_thumbnail_twice(self):
        """generate_thumbnail replaces old thumbnail."""
        image = self._image_with_thumbnail()
        old_path = image.thumbnail.path

        # The thumbnail exists.
        assert os.path.isfile(old_path)

        generate_thumbnail(image, 'file', 'thumbnail')
        new_path = image.thumbnail.path

        # The thumbnail was replaced.
        # Avoid potential failure when old thumbnail was saved 1 second ago.
        assert os.path.isfile(new_path)
        # Old file is either replaced or deleted.
        if old_path != new_path:
            assert not os.path.exists(old_path)
