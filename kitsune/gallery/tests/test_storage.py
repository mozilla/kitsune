import posixpath
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.db import transaction
from parameterized import parameterized
from storages.backends.gcloud import GoogleCloudStorage

from kitsune.gallery.models import Image
from kitsune.gallery.storage import (
    PRIVATE_MEDIA_URL,
    PRIVATE_PREFIX,
    private_images_enabled,
    private_storage,
)
from kitsune.gallery.tests import (
    PRIVATE_UPLOADS_OFF,
    ImageFactory,
    TemporaryMediaRoots,
    thumbnailed_image,
)
from kitsune.sumo.tests import TestCase
from kitsune.upload.tasks import generate_thumbnail
from kitsune.users.tests import GroupFactory, UserFactory
from kitsune.wiki.models import Audience
from kitsune.wiki.tests import AudienceFactory


class RollbackError(Exception):
    pass


class GalleryStorageTests(TemporaryMediaRoots, TestCase):
    def setUp(self):
        super().setUp()
        self.kb = AudienceFactory()

    def assert_stored(self, names, private):
        """Exactly these files are under the private root (or the media root), none elsewhere."""
        own, other = self.private_root, self.media_root
        if not private:
            own, other = other, own
        self.assertEqual(names, self.files_under(own))
        self.assertEqual(set(), self.files_under(other))

    @parameterized.expand([("private", True), ("public", False)])
    def test_file_location_follows_the_kb(self, _name, private):
        image = ImageFactory(audience=self.kb if private else Audience.objects.default())

        prefix = PRIVATE_PREFIX if private else ""
        self.assertTrue(image.file.name.startswith(f"{prefix}uploads/gallery/images/"))
        self.assert_stored({image.file.name}, private)
        self.assertEqual(
            (PRIVATE_MEDIA_URL if private else settings.MEDIA_URL) + image.file.name,
            image.file.url,
        )

    def test_file_save_without_audience_fails_closed(self):
        image = Image(creator=UserFactory(), is_draft=True, title="Shot")

        with self.assertRaises(Audience.DoesNotExist):
            image.file.save("shot.png", ContentFile(b""), save=False)

        self.assert_stored(set(), private=True)

    @parameterized.expand([("private", True), ("public", False)])
    def test_thumbnail_follows_its_source_name(self, _name, private):
        kb = self.kb if private else AudienceFactory(is_public=True)
        image = ImageFactory(audience=kb)
        # An admin can flip the knowledge base between upload and thumbnail; the name is fixed.
        Audience.objects.filter(pk=kb.pk).update(is_public=not kb.is_public)
        generate_thumbnail("gallery.Image", image.id, "file", "thumbnail")
        image.refresh_from_db()

        # Nested as before private images: the thumbnail is named from the file's full name.
        prefix = PRIVATE_PREFIX if private else ""
        self.assertEqual(
            f"{prefix}uploads/gallery/images/thumbnails/uploads/gallery/images",
            posixpath.dirname(image.thumbnail.name),
        )
        self.assert_stored({image.file.name, image.thumbnail.name}, private)

    def test_gcs_private_instance_settings(self):
        with self.settings(
            GS_BUCKET_NAME="pub",
            GS_PRIVATE_BUCKET_NAME="priv",
            GS_CUSTOM_ENDPOINT="https://cdn.example",
            GS_DEFAULT_ACL="publicRead",
        ):
            storage = private_storage()
            self.assertTrue(private_images_enabled())

        self.assertIsInstance(storage, GoogleCloudStorage)
        self.assertEqual("priv", storage.bucket_name)
        self.assertIsNone(storage.custom_endpoint)
        self.assertIsNone(storage.default_acl)
        self.assertEqual(1024 * 1024, storage.max_memory_size)

    @parameterized.expand(
        [
            ("without_bucket", {"GS_BUCKET_NAME": "pub", "GS_PRIVATE_BUCKET_NAME": ""}),
            ("same_bucket", {"GS_BUCKET_NAME": "pub", "GS_PRIVATE_BUCKET_NAME": "pub"}),
            (
                "on_s3",
                {"GS_BUCKET_NAME": "", "GS_PRIVATE_BUCKET_NAME": "priv", "AWS_ACCESS_KEY_ID": "k"},
            ),
        ]
    )
    def test_private_off(self, _name, overrides):
        with self.settings(**overrides):
            self.assertIsNone(private_storage())
            self.assertFalse(private_images_enabled())
            with self.assertRaises(ImproperlyConfigured):
                ImageFactory(audience=self.kb)

        self.assert_stored(set(), private=True)

    def test_private_off_with_private_rows(self):
        """Rows uploaded with private storage on: unreadable once off, bytes kept on delete."""
        group = GroupFactory()
        self.kb.groups.add(group)
        viewers = {
            "staff": UserFactory(groups=[GroupFactory(name=settings.STAFF_GROUP)]),
            "member": UserFactory(groups=[group]),
            "draft_creator": UserFactory(),
        }
        draft = thumbnailed_image(
            audience=self.kb, creator=viewers["draft_creator"], is_draft=True
        )
        # Dimensions given: measuring them would open a file that was never written.
        public_named = ImageFactory(
            audience=self.kb, file="uploads/gallery/images/shot.png", width=1, height=1
        )
        names = self.files_under(self.private_root)
        self.assertTrue(all(draft.is_readable_by(viewer) for viewer in viewers.values()))
        self.assertTrue(public_named.is_readable_by(viewers["member"]))

        with (
            self.settings(**PRIVATE_UPLOADS_OFF),
            patch("kitsune.gallery.storage.default_storage") as default,
        ):
            for label, viewer in viewers.items():
                with self.subTest(viewer=label):
                    self.assertFalse(draft.is_readable_by(viewer))
                    self.assertFalse(public_named.is_readable_by(viewer))
            # Made public since the upload: the file stays private by name.
            draft.audience.is_public = True
            draft.audience.save()
            self.assertFalse(draft.is_readable_by(AnonymousUser()))
            with (
                self.assertLogs("k.gallery", "WARNING"),
                self.captureOnCommitCallbacks(execute=True),
            ):
                draft.delete()

        default.delete.assert_not_called()
        self.assertEqual(names, self.files_under(self.private_root))

    def test_private_delete_waits_for_commit(self):
        image = thumbnailed_image(audience=self.kb)
        pk = image.pk
        names = {image.file.name, image.thumbnail.name}

        with self.captureOnCommitCallbacks(execute=True):
            with self.assertRaises(RollbackError), transaction.atomic():
                image.delete()
                raise RollbackError

        self.assertEqual(names, self.files_under(self.private_root))

        with self.captureOnCommitCallbacks(execute=True):
            Image.objects.get(pk=pk).delete()
            self.assertEqual(names, self.files_under(self.private_root))

        self.assertEqual(set(), self.files_under(self.private_root))

    def test_public_delete_unchanged(self):
        image = thumbnailed_image()
        self.assert_stored({image.file.name, image.thumbnail.name}, private=False)

        image.delete()

        self.assert_stored(set(), private=False)
