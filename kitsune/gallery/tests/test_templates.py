from urllib.parse import parse_qs, urlparse

from django.test import override_settings
from parameterized import parameterized
from pyquery import PyQuery as pq

from kitsune.gallery.models import Image
from kitsune.gallery.tests import ImageFactory, PrivateKnowledgeBases, private_headers
from kitsune.products.tests import ProductFactory
from kitsune.sumo.templatetags.jinja_helpers import urlparams
from kitsune.sumo.tests import TestCase, get, post
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import UserFactory
from kitsune.wiki.tests import ApprovedRevisionFactory


class GalleryPageCase(TestCase):
    def tearDown(self):
        Image.objects.all().delete()
        super().tearDown()

    def test_gallery_images(self):
        """Test that all images show up on images gallery page.

        Also, Make sure they don't show up on videos page.

        """
        img = ImageFactory()
        response = get(self.client, "gallery.gallery")
        self.assertEqual(200, response.status_code)
        doc = pq(response.content)
        imgs = doc("#media-list li img")
        self.assertEqual(1, len(imgs))
        self.assertEqual(img.thumbnail_url_if_set(), imgs[0].attrib["src"])

    def test_gallery_locale(self):
        """Test that images only show for their set locale."""
        ImageFactory(locale="es")
        url = reverse("gallery.gallery")
        response = self.client.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        doc = pq(response.content)
        imgs = doc("#media-list li img")
        self.assertEqual(0, len(imgs))

        locale_url = reverse("gallery.gallery", locale="es")
        response = self.client.get(locale_url, follow=True)
        self.assertEqual(200, response.status_code)
        doc = pq(response.content)
        imgs = doc("#media-list li img")
        self.assertEqual(1, len(imgs))


class GalleryAsyncCase(TestCase):
    def tearDown(self):
        Image.objects.all().delete()
        super().tearDown()

    def test_gallery_image_list(self):
        """Test for ajax endpoint without search parameter."""
        img = ImageFactory()
        url = urlparams(reverse("gallery.async"), type="image")
        response = self.client.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        doc = pq(response.content)
        imgs = doc("#media-list li img")
        self.assertEqual(1, len(imgs))
        self.assertEqual(img.thumbnail_url_if_set(), imgs[0].attrib["src"])

    def test_gallery_image_search(self):
        """Test for ajax endpoint with search parameter."""
        img = ImageFactory()
        url = urlparams(reverse("gallery.async"), type="image", q="foobar")
        response = self.client.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        doc = pq(response.content)
        imgs = doc("#media-list li img")
        self.assertEqual(0, len(imgs))

        url = urlparams(reverse("gallery.async"), type="image", q=img.title)
        response = self.client.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        doc = pq(response.content)
        imgs = doc("#media-list li img")
        self.assertEqual(1, len(imgs))
        self.assertEqual(img.thumbnail_url_if_set(), imgs[0].attrib["src"])


class GalleryUploadTestCase(TestCase):
    def setUp(self):
        super().setUp()

        self.u = UserFactory()
        self.client.login(username=self.u.username, password="testpass")

    def tearDown(self):
        Image.objects.all().delete()
        super().tearDown()

    def test_image_draft_shows(self):
        """The image draft is loaded for this user."""
        img = ImageFactory(is_draft=True, creator=self.u)
        response = get(self.client, "gallery.gallery")
        self.assertEqual(200, response.status_code)
        doc = pq(response.content)
        assert doc(".file.preview img").attr("src").endswith(img.file.name)
        self.assertEqual(1, doc(".file.preview img").length)

    def test_image_draft_post(self):
        """Posting to the page saves the field values for the image draft."""
        ImageFactory(is_draft=True, creator=self.u)
        response = post(
            self.client,
            "gallery.gallery",
            {"description": "??", "title": "test"},
        )
        self.assertEqual(200, response.status_code)
        doc = pq(response.content)
        self.assertEqual("??", doc("#gallery-upload-modal textarea").html().strip())
        self.assertEqual("test", doc('#gallery-upload-modal input[name="title"]').val())

    def test_modal_locale_selected(self):
        """Locale value is selected for upload modal."""
        response = get(self.client, "gallery.gallery", locale="fr")
        doc = pq(response.content)
        self.assertEqual("fr", doc('#gallery-upload-image option[selected="selected"]').val())


class MediaPageCase(TestCase):
    def tearDown(self):
        Image.objects.all().delete()
        super().tearDown()

    def test_image_media_page(self):
        """Test the media page."""
        img = ImageFactory()
        response = self.client.get(img.get_absolute_url(), follow=True)
        self.assertEqual(200, response.status_code)
        doc = pq(response.content)
        self.assertEqual(img.title, doc("h1").text())
        self.assertEqual(img.description, doc("#media-object div.description").text())
        self.assertEqual(img.file.url, doc("#media-view img")[0].attrib["src"])


class KnowledgeBaseChoiceTests(PrivateKnowledgeBases, TestCase):
    def gallery_page(self, viewer, **params):
        self.login(viewer)
        response = self.client.get(urlparams(reverse("gallery.gallery"), **params))
        self.assertEqual(200, response.status_code)
        return response, pq(response.content)("#gallery-upload-image")

    @override_settings(CACHE_MIDDLEWARE_SECONDS=3600, GTM_CONTAINER_ID="GTM-TEST")
    def test_upload_form_choice_visibility(self):
        foo, bar = str(self.foo.pk), str(self.bar.pk)
        cases = [
            ("foo_member", {}, ["", "public", foo], ""),
            ("foo_member", {"kb": foo}, ["", "public", foo], foo),
            ("foo_member", {"kb": bar}, ["", "public", foo], ""),
            ("staff", {}, ["", "public", bar, foo], ""),
        ]
        for viewer, params, options, selected in cases:
            with self.subTest(viewer=viewer, params=params):
                response, form = self.gallery_page(viewer, **params)

                select = form.find('select[name="knowledge_base"]')
                self.assertEqual(
                    options, [option.get("value") for option in select.find("option")]
                )
                self.assertEqual(selected, select.val())
                self.assertIsNone(select.attr("disabled"))
                fields = form.find('select[name="knowledge_base"], input[type="file"]')
                self.assertEqual(
                    ["knowledge_base", "file"], [field.get("name") for field in fields]
                )
                self.assertTrue(private_headers(response))
                self.assertNotIn("/gtm-snippet.", response.content.decode())

        response, form = self.gallery_page("no_access")

        self.assertTrue(form.find('input[type="file"]'))
        self.assertFalse(form.find('select[name="knowledge_base"]'))
        self.assertFalse(private_headers(response))
        self.assertIn("/gtm-snippet.", response.content.decode())

    def test_draft_choice_is_locked(self):
        ImageFactory(creator=self.users["foo_member"], is_draft=True, audience=self.foo)

        _response, form = self.gallery_page("foo_member", kb=str(self.bar.pk))

        select = form.find('select[name="knowledge_base"]')
        self.assertEqual(str(self.foo.pk), select.val())
        self.assertIsNotNone(select.attr("disabled"))


class EditorGalleryUrlTests(PrivateKnowledgeBases, TestCase):
    @parameterized.expand(
        [
            ("edit", ["foo"], True),
            ("edit", ["foo", "bar"], False),
            ("edit", [], False),
            ("translate", ["foo"], True),
        ]
    )
    def test_editor_gallery_url_preselects(self, page, knowledge_bases, preselects):
        audiences = [getattr(self, name) for name in knowledge_bases]
        revision = ApprovedRevisionFactory(
            document__products=[ProductFactory()], document__audiences=audiences or None
        )
        slug = revision.document.slug
        url = {
            "edit": reverse("wiki.edit_document", args=[slug]),
            "translate": reverse("wiki.translate", args=[slug], locale="de"),
        }[page]
        self.login("staff")

        response = self.client.get(url)

        self.assertEqual(200, response.status_code)
        gallery_url = pq(response.content)("div.editor").attr("data-media-gallery-url")
        kb = parse_qs(urlparse(gallery_url).query).get("kb")
        self.assertEqual([str(self.foo.pk)] if preselects else None, kb)
