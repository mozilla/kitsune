import json
import logging
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from testfixtures import LogCapture


class TestDockerflowIntegration(TestCase):
    """Tests for around Dockerflow integration."""

    def test_lbheartbeat_view(self):
        response = self.client.get("/__lbheartbeat__")
        self.assertEqual(response.status_code, 200)

    def test_heartbeat_checks(self):
        response = self.client.get("/__heartbeat__")

        self.assertEqual("application/json", response["content-type"])
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        # Django system checks raise warnings
        self.assertEqual("warning", content["status"])

    def test_request_summary_log(self):
        log_capture = LogCapture(attributes=("name", "levelname", "getMessage", "path", "errno"))

        self.client.get(reverse("search", locale="en-US"))

        log_capture.check(
            ("request.summary", "INFO", "", "/en-US/search/", 0),
        )
