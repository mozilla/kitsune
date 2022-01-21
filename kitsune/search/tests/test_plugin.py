from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse


class OpenSearchTestCase(TestCase):
    """Test the SUMO OpenSearch plugin."""

    def test_host(self):
        response = self.client.get(reverse("search.plugin", locale="fr"))
        self.assertEqual(response.status_code, 200)
        # FIXME: This is silly. The better test would be to parse out
        # the content and then go through and make sure all the urls
        # were correct.
        assert b"en-US" not in response.content

    def test_plugin_expires_and_mimetype(self):
        response = self.client.get(reverse("search.plugin", locale="en-US"))
        self.assertEqual(response.status_code, 200)
        # Verify that it has the Expires: HTTP header
        assert "expires" in response
        # Verify the mimetype is correct
        self.assertEqual(response["content-type"], "application/opensearchdescription+xml")

    def test_plugin_uses_correct_locale(self):
        response = self.client.get(reverse("search.plugin", locale="en-US"))
        assert b"/en-US/search" in response.content

        response = self.client.get(reverse("search.plugin", locale="fr"))
        assert b"/fr/search" in response.content

    # FIXME: test plugin results
