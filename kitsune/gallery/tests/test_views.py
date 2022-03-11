from unittest import mock

from pyquery import PyQuery as pq

from kitsune.gallery import views
from kitsune.gallery.models import Image, Video
from kitsune.gallery.tests import ImageFactory, VideoFactory
from kitsune.gallery.views import _get_media_info
from kitsune.sumo.tests import LocalizingClient, TestCase, post
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import UserFactory, add_permission

TEST_IMG = "kitsune/upload/tests/media/test.jpg"


class DeleteEditImageTests(TestCase):
    client_class = LocalizingClient

    def setUp(self):
        super(DeleteEditImageTests, self).setUp()

    def tearDown(self):
        Image.objects.all().delete()
        super(DeleteEditImageTests, self).tearDown()

    def test_delete_image(self):
        """Deleting an uploaded image works."""
        im = ImageFactory()
        u = UserFactory()
        add_permission(u, Image, "delete_image")
        self.client.login(username=u.username, password="testpass")
        r = post(self.client, "gallery.delete_media", args=["image", im.id])

        self.assertEqual(200, r.status_code)
        self.assertEqual(0, Image.objects.count())

    def test_delete_image_without_permissions(self):
        """Can't delete an image I didn't create."""
        img = ImageFactory()
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")
        r = post(self.client, "gallery.delete_media", args=["image", img.id])

        self.assertEqual(403, r.status_code)
        self.assertEqual(1, Image.objects.count())

    def test_delete_own_image(self):
        """Can delete an image I created."""
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")
        img = ImageFactory(creator=u)
        r = post(self.client, "gallery.delete_media", args=["image", img.id])

        self.assertEqual(200, r.status_code)
        self.assertEqual(0, Image.objects.count())

    @mock.patch.object(views, "schedule_rebuild_kb")
    def test_schedule_rebuild_kb_on_delete(self, schedule_rebuild_kb):
        """KB rebuild scheduled on delete"""
        im = ImageFactory()
        u = UserFactory()
        add_permission(u, Image, "delete_image")
        self.client.login(username=u.username, password="testpass")
        r = post(self.client, "gallery.delete_media", args=["image", im.id])

        self.assertEqual(200, r.status_code)
        self.assertEqual(0, Image.objects.count())
        assert schedule_rebuild_kb.called

    def test_edit_own_image(self):
        """Can edit an image I created."""
        u = UserFactory()
        img = ImageFactory(creator=u)
        self.client.login(username=u.username, password="testpass")
        r = post(
            self.client, "gallery.edit_media", {"description": "arrr"}, args=["image", img.id]
        )

        self.assertEqual(200, r.status_code)
        self.assertEqual("arrr", Image.objects.get().description)

    def test_edit_image_without_permissions(self):
        """Can't edit an image I didn't create."""
        img = ImageFactory()
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")
        r = post(
            self.client, "gallery.edit_media", {"description": "arrr"}, args=["image", img.id]
        )

        self.assertEqual(403, r.status_code)

    def test_edit_image_with_permissions(self):
        """Editing image sets the updated_by field."""
        img = ImageFactory()
        u = UserFactory()
        add_permission(u, Image, "change_image")
        self.client.login(username=u.username, password="testpass")
        r = post(
            self.client, "gallery.edit_media", {"description": "arrr"}, args=["image", img.id]
        )

        self.assertEqual(200, r.status_code)
        self.assertEqual(u.username, Image.objects.get().updated_by.username)


class ViewHelpersTests(TestCase):
    def tearDown(self):
        Image.objects.all().delete()
        Video.objects.all().delete()
        super(ViewHelpersTests, self).setUp()

    def test_get_media_info_video(self):
        """Gets video and format info."""
        vid = VideoFactory()
        info_vid, info_format = _get_media_info(vid.pk, "video")
        self.assertEqual(vid.pk, info_vid.pk)
        self.assertEqual(None, info_format)

    def test_get_media_info_image(self):
        """Gets image and format info."""
        img = ImageFactory()
        info_img, info_format = _get_media_info(img.pk, "image")
        self.assertEqual(img.pk, info_img.pk)
        self.assertEqual("jpeg", info_format)


class SearchTests(TestCase):
    client_class = LocalizingClient

    def test_image_search(self):
        ImageFactory(title="fx2-quicktimeflash.png")
        ImageFactory(title="another-image.png")
        url = reverse("gallery.search", args=["image"])
        response = self.client.get(url, {"q": "quicktime"}, follow=True)
        doc = pq(response.content)
        self.assertEqual(1, len(doc("#media-list li")))

    def test_video_search(self):
        VideoFactory(title="0a85171f1802a3b0d9f46ffb997ddc02-1251659983-259-2.mp4")
        VideoFactory(title="another-video.mp4")
        url = reverse("gallery.search", args=["video"])
        response = self.client.get(url, {"q": "1802"}, follow=True)
        doc = pq(response.content)
        self.assertEqual(1, len(doc("#media-list li")))

    def test_search_description(self):
        ImageFactory(description="This image was automatically migrated")
        ImageFactory(description="This image was automatically migrated")
        ImageFactory(description="This image was automatically")
        url = reverse("gallery.search", args=["image"])
        response = self.client.get(url, {"q": "migrated"}, follow=True)
        doc = pq(response.content)
        self.assertEqual(2, len(doc("#media-list li")))

    def test_search_nonexistent(self):
        url = reverse("gallery.search", args=["foo"])
        response = self.client.get(url, {"q": "foo"}, follow=True)
        self.assertEqual(404, response.status_code)


class GalleryTests(TestCase):
    def test_gallery_invalid_type(self):
        url = reverse("gallery.gallery", args=["foo"])
        response = self.client.get(url, follow=True)
        self.assertEqual(404, response.status_code)

    def test_redirect(self):
        """/gallery redirects to /gallery/images"""
        response = self.client.get(reverse("gallery.home", locale="en-US"), follow=False)
        self.assertEqual(301, response.status_code)
        self.assertEqual("/en-US/gallery/images", response["location"])
