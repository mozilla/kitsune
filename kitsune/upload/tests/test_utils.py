from unittest import mock

from django.conf import settings
from django.core.files import File
from django.test import override_settings
from PIL import Image

from kitsune.questions.tests import QuestionFactory
from kitsune.sumo.tests import TestCase
from kitsune.upload.models import ImageAttachment
from kitsune.upload.tests import check_file_info, get_file_name
from kitsune.upload.utils import (
    FileTooLargeError,
    check_file_size,
    create_imageattachment,
    open_as_pil_image,
)
from kitsune.users.tests import UserFactory


class OpenAsPILImageTestCase(TestCase):
    def test_valid_image(self):
        """open_as_pil_image returns a PIL image for a valid file."""
        with open("kitsune/upload/tests/media/test.jpg", "rb") as f:
            image = open_as_pil_image(f)
            image.close()

    @override_settings(IMAGE_MAX_PIXELS=1)
    def test_image_too_large(self):
        """open_as_pil_image raises FileTooLargeError when dimensions exceed IMAGE_MAX_PIXELS."""
        with open("kitsune/upload/tests/media/test.jpg", "rb") as f:
            with self.assertRaises(FileTooLargeError):
                open_as_pil_image(f)

    @mock.patch("kitsune.upload.utils.Image.open", side_effect=Image.DecompressionBombError)
    def test_decompression_bomb(self, _):
        """open_as_pil_image raises FileTooLargeError on DecompressionBombError."""
        with self.assertRaises(FileTooLargeError):
            open_as_pil_image(mock.MagicMock())


class CheckFileSizeTestCase(TestCase):
    """Tests for check_file_size"""

    def test_check_file_size_under(self):
        """No exception should be raised"""
        with open("kitsune/upload/tests/media/test.jpg", "rb") as f:
            up_file = File(f)
            check_file_size(up_file, settings.IMAGE_MAX_FILESIZE)

    def test_check_file_size_over(self):
        """FileTooLargeError should be raised"""
        with self.assertRaises(FileTooLargeError):
            with open("kitsune/upload/tests/media/test.jpg", "rb") as f:
                up_file = File(f)
                check_file_size(up_file, 0)


class CreateImageAttachmentTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.obj = QuestionFactory()

    def tearDown(self):
        ImageAttachment.objects.all().delete()
        super().tearDown()

    def test_create_imageattachment(self):
        """
        An image attachment is created from an uploaded file.

        Verifies all appropriate fields are correctly set.
        """
        with open("kitsune/upload/tests/media/test.jpg", "rb") as f:
            up_file = File(f)
            file_info = create_imageattachment({"image": up_file}, self.user, self.obj)

        image = ImageAttachment.objects.all()[0]
        check_file_info(
            file_info,
            name="test.png",
            width=90,
            height=120,
            delete_url=image.get_delete_url(),
            url=image.get_absolute_url(),
            thumbnail_url=image.thumbnail.url,
        )

    def test_create_imageattachment_when_animated(self):
        """
        An image attachment is created from an uploaded animated GIF file.

        Verifies all appropriate fields are correctly set.
        """
        filepath = "kitsune/upload/tests/media/animated.gif"
        with open(filepath, "rb") as f:
            up_file = File(f)
            file_info = create_imageattachment({"image": up_file}, self.user, self.obj)

        image = ImageAttachment.objects.all()[0]
        check_file_info(
            file_info,
            name=filepath,
            width=120,
            height=120,
            delete_url=image.get_delete_url(),
            url=image.get_absolute_url(),
            thumbnail_url=image.thumbnail.url,
        )


class FileNameTestCase(TestCase):
    def _match_file_name(self, name, name_end):
        assert name.endswith(name_end), '"{}" does not end with "{}"'.format(name, name_end)

    def test_empty_file_name(self):
        self._match_file_name("", "")

    def test_empty_file_name_with_extension(self):
        self._match_file_name(get_file_name(".wtf"), "3f8242")

    def test_ascii(self):
        self._match_file_name(get_file_name("some ascii.jpg"), "5959e0.jpg")

    def test_ascii_dir(self):
        self._match_file_name(get_file_name("dir1/dir2/some ascii.jpg"), "5959e0.jpg")

    def test_low_unicode(self):
        self._match_file_name(get_file_name("157d9383e6aeba7180378fd8c1d46f80.gif"), "bdaf1a.gif")

    def test_high_unicode(self):
        self._match_file_name(get_file_name("\u6709\u52b9.jpeg"), "ce1518.jpeg")

    def test_full_mixed(self):
        self._match_file_name(
            get_file_name("123\xe5\xe5\xee\xe9\xf8\xe7\u6709\u52b9.png"), "686c11.png"
        )
