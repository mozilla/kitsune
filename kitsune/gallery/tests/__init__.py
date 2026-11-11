import tempfile
from pathlib import Path

import factory
from django.conf import settings
from django.test import override_settings

from kitsune.gallery.models import Image
from kitsune.sumo.tests import FuzzyUnicode
from kitsune.upload.tasks import generate_thumbnail
from kitsune.users.tests import GroupFactory, UserFactory
from kitsune.wiki.models import Audience
from kitsune.wiki.tests import AudienceFactory

# Public storage on GCS without a private bucket: private uploads are off.
PRIVATE_UPLOADS_OFF = {"GS_BUCKET_NAME": "pub", "GS_PRIVATE_BUCKET_NAME": ""}


class ImageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Image

    creator = factory.SubFactory(UserFactory)
    audience = factory.LazyFunction(Audience.objects.default)
    description = FuzzyUnicode()
    file = factory.django.ImageField()
    title = FuzzyUnicode()


def thumbnailed_image(**kwargs):
    """An image with its thumbnail generated, as after a finalized upload."""
    image = ImageFactory(**kwargs)
    generate_thumbnail("gallery.Image", image.id, "file", "thumbnail")
    image.refresh_from_db()
    return image


def header_tokens(response, name):
    """The comma-separated tokens of a response header, lowercased."""
    return {token.strip().lower() for token in response.get(name, "").split(",")}


def private_headers(response):
    """Whether the response stays out of shared caches and referrers (sumo.utils.mark_private)."""
    return {"private", "no-store"} <= header_tokens(response, "Cache-Control") and (
        response.get("Referrer-Policy") == "strict-origin"
    )


class TemporaryMediaRoots:
    """Mixin for TestCases: MEDIA_ROOT and PRIVATE_MEDIA_ROOT in a throwaway directory."""

    def setUp(self):
        super().setUp()
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.media_root = root / "media"
        self.private_root = root / "private"
        self.enterContext(
            override_settings(
                MEDIA_ROOT=str(self.media_root), PRIVATE_MEDIA_ROOT=str(self.private_root)
            )
        )

    @staticmethod
    def files_under(root):
        """Paths of the files under root, relative to it."""
        return {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}


class PrivateKnowledgeBases(TemporaryMediaRoots):
    """
    Mixin for TestCases: private knowledge bases foo and bar, a member of each, Staff, a user
    without private access, and anonymous.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        foo_group, bar_group = GroupFactory(), GroupFactory()
        cls.foo = AudienceFactory(name="Foo", groups=[foo_group])
        cls.bar = AudienceFactory(name="Bar", groups=[bar_group])
        cls.users = {
            "foo_member": UserFactory(groups=[foo_group]),
            "bar_member": UserFactory(groups=[bar_group]),
            "staff": UserFactory(groups=[GroupFactory(name=settings.STAFF_GROUP)]),
            "no_access": UserFactory(),
            "anonymous": None,
        }

    def login(self, viewer):
        if self.users[viewer] is None:
            self.client.logout()
        else:
            self.client.force_login(self.users[viewer])
