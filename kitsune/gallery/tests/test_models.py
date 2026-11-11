from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.files.base import ContentFile
from django.db import IntegrityError, transaction

from kitsune.gallery.models import Image
from kitsune.gallery.tests import ImageFactory, TemporaryMediaRoots
from kitsune.sumo.tests import TestCase
from kitsune.upload.tasks import generate_thumbnail
from kitsune.users.tests import GroupFactory, UserFactory
from kitsune.wiki.models import Audience
from kitsune.wiki.tests import AudienceFactory


@patch("kitsune.upload.utils.create_image_thumbnail")
class ImageTestCase(TestCase):
    def tearDown(self):
        Image.objects.all().delete()
        super().tearDown()

    def test_thumbnail_url_if_set(self, create_thumbnail_mock):
        """thumbnail_url_if_set() returns self.thumbnail if set, or else
        returns self.file"""
        img = ImageFactory()
        self.assertEqual(img.file.url, img.thumbnail_url_if_set())

        create_thumbnail_mock.return_value = ContentFile("the dude")
        generate_thumbnail("gallery.Image", img.id, "file", "thumbnail")
        img.refresh_from_db()
        self.assertEqual(img.thumbnail.url, img.thumbnail_url_if_set())


class ImageAudienceTests(TemporaryMediaRoots, TestCase):
    def setUp(self):
        super().setUp()
        self.default = Audience.objects.default()

    def test_is_readable_by(self):
        foo_group, bar_group = GroupFactory(), GroupFactory()
        foo = AudienceFactory(groups=[foo_group])
        AudienceFactory(groups=[bar_group])
        creator = UserFactory()
        images = {
            "public": ImageFactory(audience=self.default),
            "foo_draft": ImageFactory(audience=foo, creator=creator, is_draft=True),
            "foo_finalized": ImageFactory(audience=foo, creator=creator),
        }
        viewers = {
            "anonymous": AnonymousUser(),
            "staff": UserFactory(groups=[GroupFactory(name=settings.STAFF_GROUP)]),
            "member": UserFactory(groups=[foo_group]),
            "bar": UserFactory(groups=[bar_group]),
            "creator": creator,
        }
        readers = {
            "public": {"anonymous", "staff", "member", "bar", "creator"},
            "foo_draft": {"staff", "member", "creator"},
            "foo_finalized": {"staff", "member"},
        }

        for image_name, image in images.items():
            for viewer_name, viewer in viewers.items():
                with self.subTest(image=image_name, viewer=viewer_name):
                    self.assertEqual(
                        image.is_readable_by(viewer), viewer_name in readers[image_name]
                    )

    def test_public_image_is_readable_without_queries(self):
        image = ImageFactory(audience=self.default)
        image = Image.objects.select_related("audience").get(pk=image.pk)

        with self.assertNumQueries(0):
            self.assertTrue(image.is_readable_by(AnonymousUser()))

    def test_title_unique_per_kb(self):
        foo, bar = AudienceFactory(), AudienceFactory()
        ImageFactory(title="Shot", audience=self.default)
        ImageFactory(title="Shot", audience=foo)
        ImageFactory(title="Shot", audience=bar)

        for audience in (self.default, foo):
            with self.subTest(audience=audience.slug):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    ImageFactory(title="Shot", audience=audience)

    def test_public_and_private_in(self):
        foo, public_kb = AudienceFactory(), AudienceFactory(is_public=True)
        images = {
            "default": ImageFactory(audience=self.default),
            "default_draft": ImageFactory(audience=self.default, is_draft=True),
            "public_kb": ImageFactory(audience=public_kb),
            "foo": ImageFactory(audience=foo),
            "foo_draft": ImageFactory(audience=foo, is_draft=True),
            "bar": ImageFactory(audience=AudienceFactory()),
        }
        cases = {
            "public": (Image.objects.public(), {"default", "default_draft", "public_kb"}),
            "private_in foo": (Image.objects.private_in(foo), {"foo"}),
            "private_in public_kb": (Image.objects.private_in(public_kb), set()),
            "private_in default": (Image.objects.private_in(self.default), set()),
        }

        for label, (queryset, expected) in cases.items():
            with self.subTest(label):
                self.assertCountEqual(queryset, [images[name] for name in expected])
