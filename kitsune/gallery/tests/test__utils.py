from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.files import File

from kitsune.gallery.models import Image, Video
from kitsune.gallery.tests import image, video
from kitsune.gallery.utils import (
    create_image, create_video, check_media_permissions)
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.upload.tests import check_file_info
from kitsune.users.tests import user, add_permission


class CheckPermissionsTestCase(TestCase):

    def setUp(self):
        super(CheckPermissionsTestCase, self).setUp()
        self.user = user(save=True)

    def tearDown(self):
        Image.objects.all().delete()
        Video.objects.all().delete()
        super(CheckPermissionsTestCase, self).tearDown()

    def test_check_own_object(self):
        """tagger can edit a video s/he doesn't own."""
        vid = video(creator=self.user)
        check_media_permissions(vid, self.user, 'change')

    def test_check_not_own_object(self):
        """tagger cannot delete an image s/he doesn't own."""
        img = image()
        fn = lambda: check_media_permissions(img, self.user, 'delete')
        self.assertRaises(PermissionDenied, fn)

    def test_check_has_perm(self):
        """User with django permission has perm to change video."""
        vid = video(creator=self.user)
        u = user(save=True)
        add_permission(u, Video, 'change_video')
        check_media_permissions(vid, u, 'change')


class CreateImageTestCase(TestCase):

    def setUp(self):
        super(CreateImageTestCase, self).setUp()
        self.user = user(save=True)

    def tearDown(self):
        Image.objects.all().delete()
        super(CreateImageTestCase, self).tearDown()

    def test_create_image(self):
        """
        An image is created from an uploaded file.

        Verifies all appropriate fields are correctly set.
        """
        with open('kitsune/upload/tests/media/test.jpg') as f:
            up_file = File(f)
            file_info = create_image({'image': up_file}, self.user)

        image = Image.objects.all()[0]
        delete_url = reverse('gallery.delete_media',
                             args=['image', image.id])
        check_file_info(
            file_info, name='test.png',
            width=90, height=120, delete_url=delete_url,
            url=image.get_absolute_url(), thumbnail_url=image.file.url)


class CreateVideoTestCase(TestCase):

    def setUp(self):
        super(CreateVideoTestCase, self).setUp()
        self.user = user(save=True)

    def tearDown(self):
        Video.objects.all().delete()
        super(CreateVideoTestCase, self).tearDown()

    def test_create_video(self):
        """
        A video is created from an uploaded file.

        Verifies all appropriate fields are correctly set.
        """
        with open('kitsune/gallery/tests/media/test.flv') as f:
            up_file = File(f)
            file_info = create_video({'flv': up_file}, self.user)

        vid = Video.objects.all()[0]
        delete_url = reverse('gallery.delete_media',
                             args=['video', vid.id])
        check_file_info(
            file_info, name='kitsune/gallery/tests/media/test.flv',
            width=32, height=32, delete_url=delete_url,
            url=vid.get_absolute_url(),
            thumbnail_url=settings.GALLERY_VIDEO_THUMBNAIL_PROGRESS_URL)
