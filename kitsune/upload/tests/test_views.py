import json
import os

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client

from kitsune.questions.tests import AnswerFactory, QuestionFactory
from kitsune.sumo.tests import TestCase, post
from kitsune.upload.forms import MSG_IMAGE_LONG
from kitsune.upload.models import ImageAttachment
from kitsune.users.tests import UserFactory


class UploadImageTestCase(TestCase):
    def setUp(self):
        super(UploadImageTestCase, self).setUp()
        self.user = UserFactory(username="berker")
        self.question = QuestionFactory(creator=self.user)
        self.client.login(username=self.user.username, password="testpass")

    def tearDown(self):
        ImageAttachment.objects.all().delete()
        super(UploadImageTestCase, self).tearDown()

    def test_model_not_whitelisted(self):
        """Specifying a model we don't allow returns 400."""
        r = self._make_post_request(image="", args=["wiki.Document", 123])

        self.assertEqual(400, r.status_code)
        json_r = json.loads(r.content)
        self.assertEqual("error", json_r["status"])
        self.assertEqual("Model not allowed.", json_r["message"])

    def test_object_notexist(self):
        """Upload nothing returns 404 error and html content."""
        r = self._make_post_request(image="", args=["questions.Question", 123])

        self.assertEqual(404, r.status_code)
        json_r = json.loads(r.content)
        self.assertEqual("error", json_r["status"])
        self.assertEqual("Object does not exist.", json_r["message"])

    def test_empty_image(self):
        """Upload nothing returns 400 error and json content."""
        r = self._make_post_request(image="")

        self.assertEqual(400, r.status_code)
        json_r = json.loads(r.content)
        self.assertEqual("error", json_r["status"])
        self.assertEqual("Invalid or no image received.", json_r["message"])
        self.assertEqual("You have not selected an image to upload.", json_r["errors"]["image"][0])

    def test_upload_image(self):
        """Uploading an image works."""
        with open("kitsune/upload/tests/media/test.jpg", "rb") as f:
            r = self._make_post_request(image=f)

        self.assertEqual(200, r.status_code)
        json_r = json.loads(r.content)
        self.assertEqual("success", json_r["status"])
        file = json_r["file"]
        self.assertEqual("test.png", file["name"])
        self.assertEqual(90, file["width"])
        self.assertEqual(120, file["height"])
        name = "098f6b.png"
        message = 'Url "%s" does not contain "%s"' % (file["url"], name)
        assert name in file["url"], message

        self.assertEqual(1, ImageAttachment.objects.count())
        image = ImageAttachment.objects.all()[0]
        self.assertEqual(self.user.username, image.creator.username)
        self.assertEqual(150, image.file.width)
        self.assertEqual(200, image.file.height)
        self.assertEqual("question", image.content_type.model)

    def test_upload_unicode_image(self):
        """Uploading an unicode image works."""
        with open("kitsune/upload/tests/media/123ascii\u6709\u52b9.jpg", "rb") as f:
            r = self._make_post_request(image=f)

        self.assertEqual(200, r.status_code)
        json_r = json.loads(r.content)
        self.assertEqual("success", json_r["status"])

    def test_delete_image_logged_out(self):
        """Can't delete an image logged out."""
        # Upload the image first
        self.test_upload_image()
        im = ImageAttachment.objects.all()[0]
        self.client.logout()
        r = self._make_post_request(args=[im.id])
        self.assertEqual(403, r.status_code)
        assert ImageAttachment.objects.exists()

    def test_delete_image_no_permission(self):
        """Can't delete an image without permission."""
        u = UserFactory(username="tagger")
        assert not u.has_perm("upload.delete_imageattachment")
        self.test_upload_image()
        im = ImageAttachment.objects.all()[0]
        self.client.login(username="tagger", password="testpass")
        r = self._make_post_request(args=[im.id])
        self.assertEqual(403, r.status_code)
        assert ImageAttachment.objects.exists()

    def test_delete_image_owner(self):
        """Users can delete their own images."""
        self.test_upload_image()
        im = ImageAttachment.objects.all()[0]
        r = self._make_post_request(args=[im.id])
        self.assertEqual(200, r.status_code)
        json_r = json.loads(r.content)
        self.assertEqual("success", json_r["status"])
        assert not ImageAttachment.objects.exists()

    def test_delete_image_with_permission(self):
        """Users with permission can delete images."""
        ct = ContentType.objects.get_for_model(ImageAttachment)
        p = Permission.objects.get_or_create(codename="delete_imageattachment", content_type=ct)[0]
        self.user.user_permissions.add(p)
        assert self.user.has_perm("upload.delete_imageattachment")

        self.test_upload_image()
        im = ImageAttachment.objects.all()[0]
        r = self._make_post_request(args=[im.id])
        self.assertEqual(200, r.status_code)
        json_r = json.loads(r.content)
        self.assertEqual("success", json_r["status"])
        assert not ImageAttachment.objects.exists()

    def test_delete_no_image(self):
        """Trying to delete a non-existent image 404s."""
        r = self._make_post_request(args=[123])
        self.assertEqual(404, r.status_code)
        data = json.loads(r.content)
        self.assertEqual("error", data["status"])

    def test_invalid_image(self):
        """Make sure invalid files are not accepted as images."""
        with open("kitsune/upload/__init__.py", "rb") as f:
            r = self._make_post_request(image=f)

        self.assertEqual(400, r.status_code)
        json_r = json.loads(r.content)
        self.assertEqual("error", json_r["status"])
        self.assertEqual("Invalid or no image received.", json_r["message"])
        self.assertEqual("The submitted file is empty.", json_r["errors"]["image"][0])

    def test_invalid_image_extensions(self):
        """
        Make sure invalid extensions aren't accepted as images.
        """
        with open("kitsune/upload/tests/media/test_invalid.ext", "rb") as f:
            r = self._make_post_request(image=f)

        self.assertEqual(400, r.status_code)
        json_r = json.loads(r.content)
        self.assertEqual("error", json_r["status"])
        self.assertEqual("Invalid or no image received.", json_r["message"])
        self.assertEqual(
            json_r["errors"]["image"][0],
            "File extension “ext” is not allowed. Allowed extensions are: jpg, jpeg, png, gif.",
        )

    def test_unsupported_image_extensions(self):
        """
        Make sure valid image types that are not whitelisted aren't accepted as images.
        """
        with open("kitsune/upload/tests/media/test.tiff", "rb") as f:
            r = self._make_post_request(image=f)

        self.assertEqual(400, r.status_code)
        json_r = json.loads(r.content)
        self.assertEqual("error", json_r["status"])
        self.assertEqual("Invalid or no image received.", json_r["message"])
        self.assertEqual(
            json_r["errors"]["image"][0],
            "File extension “tiff” is not allowed. Allowed extensions are: jpg, jpeg, png, gif.",
        )

    def test_upload_long_filename(self):
        """Uploading an image with a filename that's too long fails."""
        # Windows has problems with large file names, so we create the
        # file in the test and if this fails, we assume we're on a
        # Windows file system and skip.
        #
        # FIXME: Is that an ok assumption to make?

        thisdir = os.path.dirname(__file__)
        path = os.path.join(thisdir, "media", "test.jpg")
        with open(path, "rb") as f:
            long_file_name = ("long_file_name" * 17) + ".jpg"
            image = SimpleUploadedFile(
                name=long_file_name, content=f.read(), content_type="image/jpg"
            )
            r = self._make_post_request(image=image)

        self.assertEqual(400, r.status_code)
        json_r = json.loads(r.content)
        self.assertEqual("error", json_r["status"])
        self.assertEqual("Invalid or no image received.", json_r["message"])
        self.assertEqual(
            MSG_IMAGE_LONG % {"length": 242, "max": settings.MAX_FILENAME_LENGTH},
            json_r["errors"]["image"][0],
        )

    def test_non_owner_upload_to_question(self):
        """
        Disallow associating an image with a question that the user did not create,
        except when the user is a superuser.
        """
        self._test_non_owner_upload("questions.Question", self.question.pk, is_superuser=True)

    def test_non_owner_upload_to_answer(self):
        """
        Disallow associating an image with an answer that the user did not create,
        except when the user is a superuser.
        """
        answer = AnswerFactory(creator=self.user)
        self._test_non_owner_upload("questions.Answer", answer.pk, is_superuser=True)

    def test_upload_to_different_user_as_superuser(self):
        """
        Disallow associating an image with a user different than the requesting user,
        except when the user is a superuser.
        """
        self._test_non_owner_upload("auth.User", self.user.pk, is_superuser=True)

    def test_upload_to_different_user_as_contributor(self):
        """
        Disallow associating an image with a user different than the requesting user,
        except when the user is member of the `trusted contributor` group.
        """
        self._test_non_owner_upload(
            "auth.User", self.user.pk, is_superuser=False, group_name="trusted contributors"
        )

    def _test_non_owner_upload(self, object_name, object_pk, is_superuser=False, group_name=""):
        other_client = Client()
        other_user = UserFactory(username="ringo")
        other_client.login(username=other_user.username, password="testpass")

        # The target or the creator of the target is different than the requesting user,
        # so this request to upload and associate an image should be rejected as bad.
        r = self._make_post_request(client=other_client, image="", args=(object_name, object_pk))

        self.assertEqual(400, r.status_code)
        json_r = json.loads(r.content)
        self.assertEqual("error", json_r["status"])
        self.assertEqual(
            "You cannot associate an image with an object you do not own.",
            json_r["message"],
        )
        assert not ImageAttachment.objects.exists()

        # Superusers are exempt from the owner restriction.
        if is_superuser:
            other_user.is_superuser = True
            other_user.save()

        if group_name:
            group, _ = Group.objects.get_or_create(name=group_name)
            other_user.groups.add(group)

        with open("kitsune/upload/tests/media/test.jpg", "rb") as f:
            r = self._make_post_request(
                client=other_client, image=f, args=(object_name, object_pk)
            )

        self.assertEqual(200, r.status_code)
        images = ImageAttachment.objects.all()
        self.assertEqual(1, len(images))
        self.assertEqual(other_user.username, images[0].creator.username)
        self.assertEqual(object_name.split(".")[-1].lower(), images[0].content_type.model)

    def _make_post_request(self, **kwargs):
        if "args" not in kwargs:
            kwargs["args"] = ["questions.Question", self.question.pk]
        if "image" in kwargs:
            image = {"image": kwargs["image"]}
        else:
            image = {}
        if len(kwargs["args"]) == 2:
            view = "upload.up_image_async"
        elif len(kwargs["args"]) == 1:
            view = "upload.del_image_async"
        else:
            raise ValueError
        return post(kwargs.get("client", self.client), view, image, args=kwargs["args"])
