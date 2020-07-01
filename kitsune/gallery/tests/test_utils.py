from django.core.exceptions import PermissionDenied
from django.core.files import File
from nose.tools import raises

from kitsune.gallery.models import Image
from kitsune.gallery.models import Video
from kitsune.gallery.tests import ImageFactory
from kitsune.gallery.tests import VideoFactory
from kitsune.gallery.utils import check_media_permissions
from kitsune.gallery.utils import create_image
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.upload.tests import check_file_info
from kitsune.users.tests import add_permission
from kitsune.users.tests import UserFactory


class CheckPermissionsTestCase(TestCase):

    def setUp(self):
        super(CheckPermissionsTestCase, self).setUp()
        self.user = UserFactory()

    def tearDown(self):
        Image.objects.all().delete()
        Video.objects.all().delete()
        super(CheckPermissionsTestCase, self).tearDown()

    def test_check_own_object(self):
        """tagger can edit a video s/he doesn't own."""
        vid = VideoFactory(creator=self.user)
        check_media_permissions(vid, self.user, 'change')

    @raises(PermissionDenied)
    def test_check_not_own_object(self):
        """tagger cannot delete an image s/he doesn't own."""
        img = ImageFactory()
        # This should raise
        check_media_permissions(img, self.user, 'delete')

    def test_check_has_perm(self):
        """User with django permission has perm to change video."""
        vid = VideoFactory(creator=self.user)
        u = UserFactory()
        add_permission(u, Video, 'change_video')
        check_media_permissions(vid, u, 'change')


class CreateImageTestCase(TestCase):

    def setUp(self):
        super(CreateImageTestCase, self).setUp()
        self.user = UserFactory()

    def tearDown(self):
        Image.objects.all().delete()
        super(CreateImageTestCase, self).tearDown()

    def test_create_image(self):
        """
        An image is created from an uploaded file.

        Verifies all appropriate fields are correctly set.
        """
        with open('kitsune/upload/tests/media/test.jpg', 'rb') as f:
            up_file = File(f)
            file_info = create_image({'image': up_file}, self.user)

        image = Image.objects.all()[0]
        delete_url = reverse('gallery.delete_media',
                             args=['image', image.id])
        check_file_info(
            file_info, name='test.png',
            width=90, height=120, delete_url=delete_url,
            url=image.get_absolute_url(), thumbnail_url=image.file.url)
