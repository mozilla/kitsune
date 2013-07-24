import mock
from nose.tools import eq_
from pyquery import PyQuery as pq

from kitsune.gallery import views
from kitsune.gallery.models import Image, Video
from kitsune.gallery.tests import image, video
from kitsune.gallery.views import _get_media_info
from kitsune.sumo.tests import post, LocalizingClient, TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import user, add_permission


TEST_IMG = 'kitsune/upload/tests/media/test.jpg'


class DeleteEditImageTests(TestCase):
    client_class = LocalizingClient

    def setUp(self):
        super(DeleteEditImageTests, self).setUp()

    def tearDown(self):
        Image.objects.all().delete()
        super(DeleteEditImageTests, self).tearDown()

    def test_delete_image(self):
        """Deleting an uploaded image works."""
        im = image()
        u = user(save=True)
        add_permission(u, Image, 'delete_image')
        self.client.login(username=u.username, password='testpass')
        r = post(self.client, 'gallery.delete_media', args=['image', im.id])

        eq_(200, r.status_code)
        eq_(0, Image.objects.count())

    def test_delete_image_without_permissions(self):
        """Can't delete an image I didn't create."""
        img = image()
        u = user(save=True)
        self.client.login(username=u.username, password='testpass')
        r = post(self.client, 'gallery.delete_media', args=['image', img.id])

        eq_(403, r.status_code)
        eq_(1, Image.objects.count())

    def test_delete_own_image(self):
        """Can delete an image I created."""
        u = user(save=True)
        self.client.login(username=u.username, password='testpass')
        img = image(creator=u)
        r = post(self.client, 'gallery.delete_media', args=['image', img.id])

        eq_(200, r.status_code)
        eq_(0, Image.objects.count())

    @mock.patch.object(views, 'schedule_rebuild_kb')
    def test_schedule_rebuild_kb_on_delete(self, schedule_rebuild_kb):
        """KB rebuild scheduled on delete"""
        im = image()
        u = user(save=True)
        add_permission(u, Image, 'delete_image')
        self.client.login(username=u.username, password='testpass')
        r = post(self.client, 'gallery.delete_media', args=['image', im.id])

        eq_(200, r.status_code)
        eq_(0, Image.objects.count())
        assert schedule_rebuild_kb.called

    def test_edit_own_image(self):
        """Can edit an image I created."""
        u = user(save=True)
        img = image(creator=u)
        self.client.login(username=u.username, password='testpass')
        r = post(self.client, 'gallery.edit_media', {'description': 'arrr'},
                 args=['image', img.id])

        eq_(200, r.status_code)
        eq_('arrr', Image.uncached.get().description)

    def test_edit_image_without_permissions(self):
        """Can't edit an image I didn't create."""
        img = image()
        u = user(save=True)
        self.client.login(username=u.username, password='testpass')
        r = post(self.client, 'gallery.edit_media', {'description': 'arrr'},
                 args=['image', img.id])

        eq_(403, r.status_code)

    def test_edit_image_with_permissions(self):
        """Editing image sets the updated_by field."""
        img = image()
        u = user(save=True)
        add_permission(u, Image, 'change_image')
        self.client.login(username=u.username, password='testpass')
        r = post(self.client, 'gallery.edit_media', {'description': 'arrr'},
                 args=['image', img.id])

        eq_(200, r.status_code)
        eq_(u.username, Image.objects.get().updated_by.username)


class ViewHelpersTests(TestCase):

    def tearDown(self):
        Image.objects.all().delete()
        Video.objects.all().delete()
        super(ViewHelpersTests, self).setUp()

    def test_get_media_info_video(self):
        """Gets video and format info."""
        vid = video()
        info_vid, info_format = _get_media_info(vid.pk, 'video')
        eq_(vid.pk, info_vid.pk)
        eq_(None, info_format)

    def test_get_media_info_image(self):
        """Gets image and format info."""
        img = image()
        info_img, info_format = _get_media_info(img.pk, 'image')
        eq_(img.pk, info_img.pk)
        eq_('jpeg', info_format)


class SearchTests(TestCase):
    client_class = LocalizingClient

    def test_image_search(self):
        image(title='fx2-quicktimeflash.png')
        image(title='another-image.png')
        url = reverse('gallery.search', args=['image'])
        response = self.client.get(url, {'q': 'quicktime'}, follow=True)
        doc = pq(response.content)
        eq_(1, len(doc('#media-list li')))

    def test_video_search(self):
        video(title='0a85171f1802a3b0d9f46ffb997ddc02-1251659983-259-2.mp4')
        video(title='another-video.mp4')
        url = reverse('gallery.search', args=['video'])
        response = self.client.get(url, {'q': '1802'}, follow=True)
        doc = pq(response.content)
        eq_(1, len(doc('#media-list li')))

    def test_search_description(self):
        image(description='This image was automatically migrated')
        image(description='This image was automatically migrated')
        image(description='This image was automatically')
        url = reverse('gallery.search', args=['image'])
        response = self.client.get(url, {'q': 'migrated'}, follow=True)
        doc = pq(response.content)
        eq_(2, len(doc('#media-list li')))

    def test_search_nonexistent(self):
        url = reverse('gallery.search', args=['foo'])
        response = self.client.get(url, {'q': 'foo'}, follow=True)
        eq_(404, response.status_code)


class GalleryTests(TestCase):
    def test_gallery_invalid_type(self):
        url = reverse('gallery.gallery', args=['foo'])
        response = self.client.get(url, follow=True)
        eq_(404, response.status_code)

    def test_redirect(self):
        """/gallery redirects to /gallery/images"""
        response = self.client.get(reverse('gallery.home', locale='en-US'),
                                   follow=False)
        eq_(301, response.status_code)
        eq_('http://testserver/en-US/gallery/images', response['location'])
