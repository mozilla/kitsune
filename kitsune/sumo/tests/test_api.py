import json

from django.conf import settings

from kitsune.questions.models import QuestionLocale
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse


class TestLocalesAPIView(TestCase):
    def setUp(self):
        QuestionLocale.objects.get_or_create(locale=settings.LANGUAGE_CODE)

    def test_basic(self):
        url = reverse("sumo.locales_api")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)

        # Do some spot checks.
        # NB: These checks will break when we change other parts of SUMO.
        self.assertEqual(
            content["en-US"], {"name": "English", "localized_name": "English", "aaq_enabled": True}
        )

        self.assertEqual(
            content["fr"],
            {"name": "French", "localized_name": "Fran\xe7ais", "aaq_enabled": False},
        )
