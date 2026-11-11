import io
import posixpath
from unittest import mock

from parameterized import parameterized
from PIL import Image as PILImage

from kitsune.gallery import views
from kitsune.gallery.storage import PRIVATE_MEDIA_URL
from kitsune.gallery.tests import (
    PRIVATE_UPLOADS_OFF,
    ImageFactory,
    PrivateKnowledgeBases,
    header_tokens,
    private_headers,
    thumbnailed_image,
)
from kitsune.sumo.tests import TestCase, template_used

UNKNOWN_NAME = "private/uploads/gallery/images/nope.png"
# Nothing sends an ETag or Last-Modified, so no 304 can answer before authorization.
CONDITIONAL_HEADERS = {
    "HTTP_IF_NONE_MATCH": "*",
    "HTTP_IF_MODIFIED_SINCE": "Wed, 01 Jan 2200 00:00:00 GMT",
}


class PrivateMediaTests(PrivateKnowledgeBases, TestCase):
    """
    The images are created by the user without access: the draft's creator may read it, a
    finalized image's creator may not.
    """

    def setUp(self):
        super().setUp()
        self.finalized = self.private_image(creator=self.users["no_access"])
        self.draft = self.private_image(creator=self.users["no_access"], is_draft=True)

    def private_image(self, filename="shot.png", **kwargs):
        return thumbnailed_image(
            audience=self.foo, file__filename=filename, file__format="PNG", **kwargs
        )

    def fetch(self, url, viewer="anonymous", **extra):
        """Requests the url as the viewer, and reads a streamed body so its file gets closed."""
        self.login(viewer)
        response = self.client.get(url, **extra)
        response.body = (
            b"".join(response.streaming_content) if response.streaming else response.content
        )
        return response

    def assert_404(self, response):
        self.assertEqual(404, response.status_code)
        self.assertTrue(template_used(response, "handlers/404.html"))
        self.assertTrue(private_headers(response))

    def test_status_matrix(self):
        cases = [
            ("finalized", "staff", 200),
            ("finalized", "foo_member", 200),
            ("draft", "no_access", 200),
            ("finalized", "bar_member", 404),
            ("finalized", "anonymous", 404),
            ("finalized", "no_access", 404),
            ("draft", "bar_member", 404),
            ("draft", "anonymous", 404),
        ]

        for image, viewer, status in cases:
            with self.subTest(image=image, viewer=viewer):
                url = getattr(self, image).file.url

                response = self.fetch(url, viewer, **CONDITIONAL_HEADERS)

                self.assertEqual(status, response.status_code)
                if status == 404:
                    self.assert_404(response)

    def test_authorizes_before_reading(self):
        url = self.finalized.file.url

        with mock.patch.object(views, "private_storage") as private_storage:
            self.assert_404(self.fetch(url, "bar_member"))
            self.assert_404(self.fetch(url, "anonymous"))
            self.assert_404(self.fetch(PRIVATE_MEDIA_URL + UNKNOWN_NAME, "staff"))

        private_storage.return_value.open.assert_not_called()

    def test_missing_bytes_are_404(self):
        field_file = self.finalized.file
        (self.private_root / field_file.name).unlink()

        self.assert_404(self.fetch(field_file.url, "foo_member"))

    def test_unknown_names_are_404(self):
        public = ImageFactory(file__filename="pub.png", file__format="PNG")
        stored = self.finalized.file.name
        names = {
            "alias_of_stored_name": stored.replace("/images/", "/images/../images/"),
            "nul_byte_before_the_extension": stored.replace(".png", "%00.png"),
        }

        for label, name in names.items():
            with self.subTest(name=label):
                self.assert_404(self.fetch(PRIVATE_MEDIA_URL + name, "staff"))

        # Without the private/ prefix the route doesn't match, and no private file is named so.
        self.assertEqual(
            404, self.fetch(PRIVATE_MEDIA_URL + public.file.name, "staff").status_code
        )

    def test_private_uploads_off_is_404(self):
        url = self.finalized.file.url
        self.assertEqual(200, self.fetch(url, "staff").status_code)

        with self.settings(**PRIVATE_UPLOADS_OFF):
            self.assert_404(self.fetch(url, "staff"))

    def test_headers_on_success(self):
        field_file = self.finalized.file

        response = self.fetch(field_file.url, "foo_member")

        self.assertEqual(200, response.status_code)
        self.assertEqual({"private", "max-age=600"}, header_tokens(response, "Cache-Control"))
        self.assertLessEqual({"cookie", "authorization"}, header_tokens(response, "Vary"))
        headers = {
            "Content-Type": "image/png",
            "X-Content-Type-Options": "nosniff",
            "Cross-Origin-Resource-Policy": "same-origin",
            "Content-Disposition": f'inline; filename="{posixpath.basename(field_file.name)}"',
            "ETag": None,
            "Last-Modified": None,
        }
        for header, value in headers.items():
            with self.subTest(header=header):
                self.assertEqual(value, response.get(header))
        self.assertEqual((self.private_root / field_file.name).read_bytes(), response.body)

    def test_404_identical(self):
        url = self.finalized.file.url

        for viewer in ("bar_member", "anonymous"):
            with self.subTest(viewer=viewer):
                denied = self.fetch(url, viewer)
                missing = self.fetch(PRIVATE_MEDIA_URL + UNKNOWN_NAME, viewer)

                self.assert_404(denied)
                self.assert_404(missing)
                self.assertEqual(denied["Content-Type"], missing["Content-Type"])
                self.assertEqual(set(denied.headers), set(missing.headers))

    @parameterized.expand([(".gif", "image/gif"), (".JPG", "image/jpeg"), (".svg", None)])
    def test_content_type_follows_extension(self, extension, content_type):
        image = self.private_image(filename=f"photo{extension}")

        response = self.fetch(image.file.url, "staff")
        thumbnail = self.fetch(image.thumbnail.url, "staff")

        if content_type is None:
            self.assert_404(response)
        else:
            self.assertEqual((200, content_type), (response.status_code, response["Content-Type"]))
        # Thumbnails are PNG whatever the source's name.
        self.assertEqual((200, "image/png"), (thumbnail.status_code, thumbnail["Content-Type"]))

    def test_thumbnail_of_an_animated_gif_is_png(self):
        image = thumbnailed_image(
            audience=self.foo, file__from_path="kitsune/upload/tests/media/animated.gif"
        )

        response = self.fetch(image.thumbnail.url, "foo_member")

        self.assertTrue(image.thumbnail.name.endswith(".png"))
        self.assertEqual("image/png", response["Content-Type"])
        self.assertEqual("PNG", PILImage.open(io.BytesIO(response.body)).format)

    def test_image_of_a_kb_made_public_is_readable_by_anyone(self):
        url = self.finalized.file.url
        self.foo.is_public = True
        self.foo.save()

        self.assertEqual(200, self.fetch(url, "anonymous").status_code)
