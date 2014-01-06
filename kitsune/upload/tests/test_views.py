import json

from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from nose.tools import eq_

from kitsune.questions.tests import question
from kitsune.sumo.tests import post, LocalizingClient, TestCase
from kitsune.upload.forms import MSG_IMAGE_LONG
from kitsune.upload.models import ImageAttachment
from kitsune.users.tests import user


class UploadImageTestCase(TestCase):
    client_class = LocalizingClient

    def setUp(self):
        super(UploadImageTestCase, self).setUp()
        self.user = user(username='berker', save=True)
        self.question = question(save=True)
        self.client.login(username=self.user.username, password='testpass')

    def tearDown(self):
        ImageAttachment.objects.all().delete()
        super(UploadImageTestCase, self).tearDown()

    def test_model_not_whitelisted(self):
        """Specifying a model we don't allow returns 400."""
        r = self._make_post_request(image='', args=['wiki.Document', 123])

        eq_(400, r.status_code)
        json_r = json.loads(r.content)
        eq_('error', json_r['status'])
        eq_('Model not allowed.', json_r['message'])

    def test_object_notexist(self):
        """Upload nothing returns 404 error and html content."""
        r = self._make_post_request(image='', args=['questions.Question', 123])

        eq_(404, r.status_code)
        json_r = json.loads(r.content)
        eq_('error', json_r['status'])
        eq_('Object does not exist.', json_r['message'])

    def test_empty_image(self):
        """Upload nothing returns 400 error and json content."""
        r = self._make_post_request(image='')

        eq_(400, r.status_code)
        json_r = json.loads(r.content)
        eq_('error', json_r['status'])
        eq_('Invalid or no image received.', json_r['message'])
        eq_('You have not selected an image to upload.',
            json_r['errors']['image'][0])

    def test_upload_image(self):
        """Uploading an image works."""
        with open('kitsune/upload/tests/media/test.jpg') as f:
            r = self._make_post_request(image=f)

        eq_(200, r.status_code)
        json_r = json.loads(r.content)
        eq_('success', json_r['status'])
        file = json_r['file']
        eq_('test.png', file['name'])
        eq_(90, file['width'])
        eq_(120, file['height'])
        name = '098f6b.png'
        message = 'Url "%s" does not contain "%s"' % (file['url'], name)
        assert (name in file['url']), message

        eq_(1, ImageAttachment.objects.count())
        image = ImageAttachment.objects.all()[0]
        eq_(self.user.username, image.creator.username)
        eq_(150, image.file.width)
        eq_(200, image.file.height)
        eq_('question', image.content_type.model)

    def test_upload_unicode_image(self):
        """Uploading an unicode image works."""
        with open(u'kitsune/upload/tests/media/123ascii\u6709\u52b9.jpg') as f:
            r = self._make_post_request(image=f)

        eq_(200, r.status_code)
        json_r = json.loads(r.content)
        eq_('success', json_r['status'])

    def test_delete_image_logged_out(self):
        """Can't delete an image logged out."""
        # Upload the image first
        self.test_upload_image()
        im = ImageAttachment.objects.all()[0]
        self.client.logout()
        r = self._make_post_request(args=[im.id])
        eq_(403, r.status_code)
        assert ImageAttachment.uncached.exists()

    def test_delete_image_no_permission(self):
        """Can't delete an image without permission."""
        u = user(username='tagger', save=True)
        assert not u.has_perm('upload.delete_imageattachment')
        self.test_upload_image()
        im = ImageAttachment.objects.all()[0]
        self.client.login(username='tagger', password='testpass')
        r = self._make_post_request(args=[im.id])
        eq_(403, r.status_code)
        assert ImageAttachment.uncached.exists()

    def test_delete_image_owner(self):
        """Users can delete their own images."""
        self.test_upload_image()
        im = ImageAttachment.objects.all()[0]
        r = self._make_post_request(args=[im.id])
        eq_(200, r.status_code)
        json_r = json.loads(r.content)
        eq_('success', json_r['status'])
        assert not ImageAttachment.uncached.exists()

    def test_delete_image_with_permission(self):
        """Users with permission can delete images."""
        ct = ContentType.objects.get_for_model(ImageAttachment)
        p = Permission.objects.get_or_create(
            codename='delete_imageattachment',
            content_type=ct)[0]
        self.user.user_permissions.add(p)
        assert self.user.has_perm('upload.delete_imageattachment')

        self.test_upload_image()
        im = ImageAttachment.objects.all()[0]
        r = self._make_post_request(args=[im.id])
        eq_(200, r.status_code)
        json_r = json.loads(r.content)
        eq_('success', json_r['status'])
        assert not ImageAttachment.uncached.exists()

    def test_delete_no_image(self):
        """Trying to delete a non-existent image 404s."""
        r = self._make_post_request(args=[123])
        eq_(404, r.status_code)
        data = json.loads(r.content)
        eq_('error', data['status'])

    def test_invalid_image(self):
        """Make sure invalid files are not accepted as images."""
        with open('kitsune/upload/__init__.py', 'rb') as f:
            r = self._make_post_request(image=f)

        eq_(400, r.status_code)
        json_r = json.loads(r.content)
        eq_('error', json_r['status'])
        eq_('Invalid or no image received.', json_r['message'])
        eq_('The submitted file is empty.', json_r['errors']['image'][0])

    def test_invalid_image_extensions(self):
        """Make sure invalid extensions are not accepted as images."""
        with open('kitsune/upload/tests/media/test_invalid.ext', 'rb') as f:
            r = self._make_post_request(image=f)

        eq_(400, r.status_code)
        json_r = json.loads(r.content)
        eq_('error', json_r['status'])
        eq_('Invalid or no image received.', json_r['message'])
        eq_('Please upload an image with one of the following extensions: '
            'jpg, jpeg, png, gif.', json_r['errors']['__all__'][0])

    def test_upload_long_filename(self):
        """Uploading an image with a filename that's too long fails."""
        path = 'kitsune/upload/tests/media/' + 'long_file_name' * 17 + '.jpg'
        with open(path) as f:
            r = self._make_post_request(image=f)

        eq_(400, r.status_code)
        json_r = json.loads(r.content)
        eq_('error', json_r['status'])
        eq_('Invalid or no image received.', json_r['message'])
        eq_(MSG_IMAGE_LONG % {'length': 242,
                              'max': settings.MAX_FILENAME_LENGTH},
            json_r['errors']['image'][0])

    def _make_post_request(self, **kwargs):
        if 'args' not in kwargs:
            kwargs['args'] = ['questions.Question', self.question.pk]
        if 'image' in kwargs:
            image = {'image': kwargs['image']}
        else:
            image = {}
        if len(kwargs['args']) == 2:
            view = 'upload.up_image_async'
        elif len(kwargs['args']) == 1:
            view = 'upload.del_image_async'
        else:
            raise ValueError
        return post(self.client, view, image, args=kwargs['args'])
