import json
from unittest import mock

from django.test import override_settings
from parameterized import parameterized
from pyquery import PyQuery as pq

from kitsune.gallery import views
from kitsune.gallery.models import Image
from kitsune.gallery.storage import PRIVATE_MEDIA_URL
from kitsune.gallery.tests import (
    PRIVATE_UPLOADS_OFF,
    ImageFactory,
    PrivateKnowledgeBases,
    private_headers,
)
from kitsune.gallery.views import _get_media_info
from kitsune.sumo.templatetags.jinja_helpers import urlparams
from kitsune.sumo.tests import TestCase, post
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import UserFactory, add_permission
from kitsune.wiki.models import Audience

MEDIA_PAGES = {
    "media": "gallery.media",
    "edit": "gallery.edit_media",
    "delete": "gallery.delete_media",
}
TEST_IMG = "kitsune/upload/tests/media/test.jpg"


class DeleteEditImageTests(TestCase):
    def setUp(self):
        super().setUp()

    def tearDown(self):
        Image.objects.all().delete()
        super().tearDown()

    def test_delete_image(self):
        """Deleting an uploaded image works."""
        im = ImageFactory()
        u = UserFactory()
        add_permission(u, Image, "delete_image")
        self.client.login(username=u.username, password="testpass")
        r = post(self.client, "gallery.delete_media", args=[im.id])

        self.assertEqual(200, r.status_code)
        self.assertEqual(0, Image.objects.count())

    def test_delete_image_without_permissions(self):
        """Can't delete an image I didn't create."""
        img = ImageFactory()
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")
        r = post(self.client, "gallery.delete_media", args=[img.id])

        self.assertEqual(403, r.status_code)
        self.assertEqual(1, Image.objects.count())

    def test_delete_own_image(self):
        """Can delete an image I created."""
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")
        img = ImageFactory(creator=u)
        r = post(self.client, "gallery.delete_media", args=[img.id])

        self.assertEqual(200, r.status_code)
        self.assertEqual(0, Image.objects.count())

    @mock.patch.object(views, "schedule_rebuild_kb")
    def test_schedule_rebuild_kb_on_delete(self, schedule_rebuild_kb):
        """KB rebuild scheduled on delete"""
        im = ImageFactory()
        u = UserFactory()
        add_permission(u, Image, "delete_image")
        self.client.login(username=u.username, password="testpass")
        r = post(self.client, "gallery.delete_media", args=[im.id])

        self.assertEqual(200, r.status_code)
        self.assertEqual(0, Image.objects.count())
        assert schedule_rebuild_kb.called

    def test_edit_own_image(self):
        """Can edit an image I created."""
        u = UserFactory()
        img = ImageFactory(creator=u)
        self.client.login(username=u.username, password="testpass")
        r = post(self.client, "gallery.edit_media", {"description": "arrr"}, args=[img.id])

        self.assertEqual(200, r.status_code)
        self.assertEqual("arrr", Image.objects.get().description)

    def test_edit_image_without_permissions(self):
        """Can't edit an image I didn't create."""
        img = ImageFactory()
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")
        r = post(self.client, "gallery.edit_media", {"description": "arrr"}, args=[img.id])

        self.assertEqual(403, r.status_code)

    def test_edit_image_with_permissions(self):
        """Editing image sets the updated_by field."""
        img = ImageFactory()
        u = UserFactory()
        add_permission(u, Image, "change_image")
        self.client.login(username=u.username, password="testpass")
        r = post(self.client, "gallery.edit_media", {"description": "arrr"}, args=[img.id])

        self.assertEqual(200, r.status_code)
        self.assertEqual(u.username, Image.objects.get().updated_by.username)

    def test_edit_image_avoids_draft_constraint(self):
        """
        Ensure that editing an image doesn't trigger the creator/draft
        database constraint on images. In other words, this tests that
        we never set is_draft to False when saving an edit to an image.
        """
        # Setup the user to have one image with is_draft=False and another
        # with is_draft=None. The intention of the creator/draft database
        # constraint is to ensure that a user can never create more than
        # one draft image. However, it works both ways. It also retricts
        # a user to at most one image with is_draft=False. Since a user
        # should be able to create more than one non-draft image, we should
        # never set is_draft to False. It should be set to None (Null) to
        # avoid triggering the constraint altogether.
        u = UserFactory()
        ImageFactory(creator=u, title="first image", is_draft=False)
        img = ImageFactory(creator=u, title="second image", is_draft=None)
        self.client.login(username=u.username, password="testpass")
        # Ensure that an edit to the second image doesn't set is_draft to False
        # and trigger the creator/draft database constraint.
        r = post(
            self.client,
            "gallery.edit_media",
            {"description": "yada yada"},
            locale="en-US",
            args=[img.id],
        )
        self.assertEqual(200, r.status_code)
        img = Image.objects.get(id=img.id)
        self.assertEqual(img.description, "yada yada")
        self.assertEqual(img.updated_by.username, u.username)


class ViewHelpersTests(TestCase):
    def tearDown(self):
        Image.objects.all().delete()
        super().setUp()

    def test_get_media_info_image(self):
        """Gets image and format info."""
        img = ImageFactory()
        info_img, info_format = _get_media_info(img.pk, UserFactory())
        self.assertEqual(img.pk, info_img.pk)
        self.assertEqual("jpeg", info_format)


class SearchTests(TestCase):
    def test_image_search(self):
        ImageFactory(title="fx2-quicktimeflash.png")
        ImageFactory(title="another-image.png")
        url = reverse("gallery.search")
        response = self.client.get(url, {"q": "quicktime"}, follow=True)
        doc = pq(response.content)
        self.assertEqual(1, len(doc("#media-list li")))

    def test_search_description(self):
        ImageFactory(description="This image was automatically migrated")
        ImageFactory(description="This image was automatically migrated")
        ImageFactory(description="This image was automatically")
        url = reverse("gallery.search")
        response = self.client.get(url, {"q": "migrated"}, follow=True)
        doc = pq(response.content)
        self.assertEqual(2, len(doc("#media-list li")))


class GalleryTests(TestCase):
    def test_redirect(self):
        """/gallery redirects to /gallery/images"""
        response = self.client.get(reverse("gallery.home", locale="en-US"), follow=False)
        self.assertEqual(301, response.status_code)
        self.assertEqual("/en-US/gallery/images", response["location"])


def listed_titles(response):
    return [link.get("title") for link in pq(response.content)("#media-list a")]


class PrivateUploadTests(PrivateKnowledgeBases, TestCase):
    def audience(self, name):
        return self.foo if name == "foo" else Audience.objects.default()

    def choice(self, name):
        return str(self.foo.pk) if name == "foo" else "public"

    def upload(self, viewer, **data):
        self.login(viewer)
        with open(TEST_IMG, "rb") as f:
            return self.client.post(reverse("gallery.upload_async"), {"file": f, **data})

    def finalize(self, viewer, url_name="gallery.upload", args=(), **data):
        """Posts the finalize (or edit) form, with the thumbnail and compression tasks stubbed."""
        self.login(viewer)
        with mock.patch.multiple(
            views, generate_thumbnail=mock.DEFAULT, compress_image=mock.DEFAULT
        ):
            return self.client.post(
                reverse(url_name, args=args),
                {"locale": "en-US", "description": "A description.", **data},
            )

    def stored(self):
        """The names of the files under the public and the private media root."""
        return self.files_under(self.media_root), self.files_under(self.private_root)

    def assert_rejected(self, response):
        self.assertEqual(400, response.status_code)
        self.assertEqual("error", json.loads(response.content)["status"])
        self.assertFalse(Image.objects.exists())
        self.assertEqual((set(), set()), self.stored())

    def test_upload_async_private(self):
        with mock.patch.object(views, "schedule_rebuild_kb") as schedule_rebuild_kb:
            response = self.upload("foo_member", knowledge_base=str(self.foo.pk))

        self.assertEqual(200, response.status_code)
        image = Image.objects.get()
        self.assertEqual((self.foo, True), (image.audience, image.is_draft))
        self.assertEqual((set(), {image.file.name}), self.stored())
        thumbnail_url = json.loads(response.content)["file"]["thumbnail_url"]
        self.assertTrue(thumbnail_url.startswith(PRIVATE_MEDIA_URL))
        schedule_rebuild_kb.assert_called_once_with()

    @parameterized.expand([("no_choice", "foo_member", None), ("other_kb", "bar_member", "foo")])
    def test_upload_async_rejects_a_bad_choice(self, _name, viewer, knowledge_base):
        data = {} if knowledge_base is None else {"knowledge_base": self.choice(knowledge_base)}

        self.assert_rejected(self.upload(viewer, **data))

    def test_upload_async_no_access_is_public(self):
        response = self.upload("no_access")

        self.assertEqual(200, response.status_code)
        image = Image.objects.get()
        self.assertEqual((Audience.objects.default(), True), (image.audience, image.is_draft))
        self.assertEqual(({image.file.name}, set()), self.stored())

    def test_private_uploads_off(self):
        """Everyone uploads public images; a private draft moves to public, its old file kept."""
        draft = ImageFactory(creator=self.users["foo_member"], is_draft=True, audience=self.foo)

        with self.settings(**PRIVATE_UPLOADS_OFF):
            self.login("foo_member")
            gallery = self.client.get(reverse("gallery.gallery"))
            rejected = self.upload("foo_member", knowledge_base=str(self.foo.pk))
            accepted = self.upload("foo_member")

        self.assertEqual(200, gallery.status_code)
        self.assertFalse(pq(gallery.content)('select[name="knowledge_base"]'))
        self.assertEqual(400, rejected.status_code)
        self.assertEqual(200, accepted.status_code)
        image = Image.objects.get()
        self.assertEqual((draft.pk, Audience.objects.default()), (image.pk, image.audience))
        self.assertEqual(({image.file.name}, {draft.file.name}), self.stored())

    @parameterized.expand(
        [
            ("public_to_private", "public", "foo"),
            ("private_to_public", "foo", "public"),
            ("same_kb", "foo", "foo"),
        ]
    )
    def test_reupload_replaces_the_draft(self, _name, first, second):
        self.upload("foo_member", knowledge_base=self.choice(first))
        old = Image.objects.get()

        response = self.upload("foo_member", knowledge_base=self.choice(second))

        self.assertEqual(200, response.status_code)
        new = Image.objects.get()
        self.assertEqual(old.pk, new.pk)
        self.assertNotEqual(old.file.name, new.file.name)
        self.assertEqual((self.audience(second), True), (new.audience, new.is_draft))
        names = {new.file.name}
        self.assertEqual((set(), names) if second == "foo" else (names, set()), self.stored())

    def test_rejected_upload_keeps_the_draft(self):
        self.upload("foo_member", knowledge_base=self.choice("foo"))
        old = Image.objects.get()
        stored = self.stored()

        with self.settings(IMAGE_MAX_PIXELS=1):
            response = self.upload("foo_member", knowledge_base=self.choice("public"))

        self.assertEqual(400, response.status_code)
        draft = Image.objects.get()
        self.assertEqual(
            (old.pk, old.file.name, self.foo), (draft.pk, draft.file.name, draft.audience)
        )
        self.assertEqual(stored, self.stored())

    @parameterized.expand([("finalize", "gallery.upload"), ("edit_media", "gallery.edit_media")])
    def test_revoked_member_cannot_finalize_a_draft(self, _name, url_name):
        # A taken title: a 403 shows the rights check comes before the title check.
        ImageFactory(audience=self.foo, title="Foo title", locale="en-US")
        draft = ImageFactory(creator=self.users["foo_member"], is_draft=True, audience=self.foo)
        self.users["foo_member"].groups.clear()
        args = [draft.pk] if url_name == "gallery.edit_media" else []

        response = self.finalize("foo_member", url_name, args, title="Foo title")

        self.assertEqual(403, response.status_code)
        draft.refresh_from_db()
        self.assertIs(True, draft.is_draft)
        self.assertEqual(
            200, self.client.get(reverse("gallery.edit_media", args=[draft.pk])).status_code
        )

    @parameterized.expand([("finalize", "gallery.upload"), ("edit_media", "gallery.edit_media")])
    def test_posted_file_is_ignored(self, _name, url_name):
        draft = ImageFactory(creator=self.users["foo_member"], is_draft=True, audience=self.foo)
        stored = self.stored()
        # Made public since the upload: a replacement would land in public storage.
        self.foo.is_public = True
        self.foo.save()
        args = [draft.pk] if url_name == "gallery.edit_media" else []

        with open(TEST_IMG, "rb") as f:
            response = self.finalize("foo_member", url_name, args, title="Final title", file=f)

        self.assertEqual(302, response.status_code)
        image = Image.objects.get()
        self.assertEqual((None, draft.file.name), (image.is_draft, image.file.name))
        self.assertEqual(stored, self.stored())

    def test_finalize_ignores_a_knowledge_base_choice(self):
        draft = ImageFactory(creator=self.users["foo_member"], is_draft=True, audience=self.foo)

        response = self.finalize("foo_member", title="Final title", knowledge_base="public")

        self.assertEqual(302, response.status_code)
        draft.refresh_from_db()
        self.assertEqual((None, self.foo), (draft.is_draft, draft.audience))

    @parameterized.expand(
        [
            ("same_locale_and_kb", "public", "public", "en-US", False),
            ("other_locale", "public", "public", "de", True),
            ("same_private_kb", "foo", "foo", "en-US", False),
            ("other_kb", "public", "foo", "en-US", True),
        ]
    )
    def test_finalize_title_taken(self, _name, taken_in, draft_kb, locale, saves):
        ImageFactory(audience=self.audience(taken_in), title="Taken title", locale="en-US")
        draft = ImageFactory(
            creator=self.users["foo_member"], is_draft=True, audience=self.audience(draft_kb)
        )

        response = self.finalize("foo_member", title="Taken title", locale=locale)

        draft.refresh_from_db()
        if saves:
            self.assertEqual(302, response.status_code)
            self.assertEqual(
                (None, "Taken title", locale), (draft.is_draft, draft.title, draft.locale)
            )
        else:
            self.assertEqual(200, response.status_code)
            errors = pq(response.content)("#gallery-upload-image .errorlist li")
            self.assertEqual("Image with this Locale and Title already exists.", errors.text())
            self.assertIs(True, draft.is_draft)


class PrivateListingTests(PrivateKnowledgeBases, TestCase):
    def setUp(self):
        super().setUp()
        self.public = ImageFactory(title="Public shot", locale="en-US")
        self.private = ImageFactory(title="Foo shot", locale="en-US", audience=self.foo)
        ImageFactory(title="Foo draft shot", locale="en-US", audience=self.foo, is_draft=True)

    @parameterized.expand(["gallery", "search", "gallery_async", "api_list"])
    def test_listings_public_only(self, listing):
        self.login("staff")
        url = {
            "gallery": reverse("gallery.gallery"),
            "search": urlparams(reverse("gallery.search"), q="shot"),
            "gallery_async": reverse("gallery.async"),
            "api_list": urlparams(reverse("image-list"), locale="en-US"),
        }[listing]

        response = self.client.get(url)

        self.assertEqual(200, response.status_code)
        if listing == "api_list":
            titles = [image["title"] for image in response.json()["results"]]
        else:
            titles = listed_titles(response)
        self.assertEqual(["Public shot"], titles)

    def test_api_detail_public_only(self):
        self.login("staff")

        statuses = [
            self.client.get(reverse("image-detail", args=[image.pk])).status_code
            for image in (self.public, self.private)
        ]

        self.assertEqual([200, 404], statuses)

    @parameterized.expand(
        [
            ("member", "foo_member", "foo", True, True),
            ("non_member", "bar_member", "foo", True, False),
            ("huge_id", "foo_member", "1" * 5000, True, False),
            ("private_uploads_off", "foo_member", "foo", False, False),
        ]
    )
    @override_settings(CACHE_MIDDLEWARE_SECONDS=3600)
    def test_gallery_async_kb_filter(self, _name, viewer, kb, enabled, private):
        self.login(viewer)
        url = urlparams(reverse("gallery.async"), kb=str(self.foo.pk) if kb == "foo" else kb)

        with self.settings(**({} if enabled else PRIVATE_UPLOADS_OFF)):
            response = self.client.get(url)

        self.assertEqual(200, response.status_code)
        self.assertEqual(["Foo shot"] if private else ["Public shot"], listed_titles(response))
        self.assertEqual(private, private_headers(response))


class PrivateMediaPageTests(PrivateKnowledgeBases, TestCase):
    @parameterized.expand(list(MEDIA_PAGES))
    @override_settings(CACHE_MIDDLEWARE_SECONDS=3600, GTM_CONTAINER_ID="GTM-TEST")
    def test_media_pages(self, page):
        creator = self.users["foo_member"]
        private = ImageFactory(audience=self.foo, creator=creator)
        public = ImageFactory(creator=creator)
        urls = {image: reverse(MEDIA_PAGES[page], args=[image.pk]) for image in (private, public)}
        add_permission(self.users["bar_member"], Image, "change_image")
        add_permission(self.users["bar_member"], Image, "delete_image")

        self.login("bar_member")
        self.assertEqual(404, self.client.get(urls[private]).status_code)

        self.login("foo_member")
        for image in (private, public):
            with self.subTest(private=image is private):
                response = self.client.get(urls[image])
                self.assertEqual(200, response.status_code)
                self.assertEqual(image is private, private_headers(response))
                self.assertEqual(image is public, "/gtm-snippet." in response.content.decode())

        # Made public since the upload: its file stays private by name, so a 404 instead of a 500.
        self.foo.is_public = True
        self.foo.save()
        with self.settings(**PRIVATE_UPLOADS_OFF):
            self.assertEqual(404, self.client.get(urls[private]).status_code)
