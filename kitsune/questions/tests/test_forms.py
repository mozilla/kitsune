import json

from django.conf import settings
from django.contrib.auth.models import AnonymousUser

from kitsune.products.tests import ProductFactory, TopicFactory
from kitsune.questions.forms import NewQuestionForm, WatchQuestionForm
from kitsune.questions.tests import AAQConfigFactory, QuestionLocaleFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory


class WatchQuestionFormTests(TestCase):
    """Tests for WatchQuestionForm."""

    def test_anonymous_watch_with_email(self):
        form = WatchQuestionForm(
            AnonymousUser(), data={"email": "wo@ot.com", "event_type": "reply"}
        )
        assert form.is_valid()
        self.assertEqual("wo@ot.com", form.cleaned_data["email"])

    def test_anonymous_watch_without_email(self):
        form = WatchQuestionForm(AnonymousUser(), data={"event_type": "reply"})
        assert not form.is_valid()
        self.assertEqual("Please provide an email.", form.errors["email"][0])

    def test_registered_watch_with_email(self):
        form = WatchQuestionForm(UserFactory(), data={"email": "wo@ot.com", "event_type": "reply"})
        assert form.is_valid()
        assert not form.cleaned_data["email"]

    def test_registered_watch_without_email(self):
        form = WatchQuestionForm(UserFactory(), data={"event_type": "reply"})
        assert form.is_valid()


class TestNewQuestionForm(TestCase):
    """Tests for the NewQuestionForm"""

    def setUp(self):
        super().setUp()
        self.locale = QuestionLocaleFactory(locale=settings.LANGUAGE_CODE)
        self.product = ProductFactory(slug="firefox")
        self.aaq_config = AAQConfigFactory(
            product=self.product,
            enabled_locales=[self.locale],
            is_active=True,
            extra_fields=["troubleshooting", "ff_version", "os"],
        )

    def test_metadata_keys(self):
        """Test metadata_field_keys property."""
        # Test the default form
        form = NewQuestionForm()
        expected = ["useragent"]
        actual = form.metadata_field_keys
        self.assertEqual(expected, actual)

        # Test the form with a product
        form = NewQuestionForm(product=self.product)
        expected = ["troubleshooting", "ff_version", "os", "useragent"]
        actual = form.metadata_field_keys
        self.assertEqual(sorted(expected), sorted(actual))

    def test_cleaned_metadata(self):
        """Test the cleaned_metadata property."""
        # Test with no metadata
        topic = TopicFactory(slug="cookies", products=[self.product], in_aaq=True)
        data = {"title": "Lorem", "content": "ipsum", "email": "t@t.com", "category": topic.id}
        form = NewQuestionForm(product=self.product, data=data)
        form.is_valid()
        expected = {}
        actual = form.cleaned_metadata
        self.assertDictEqual(expected, actual)

        # Test with metadata
        data["os"] = "Linux"
        form = NewQuestionForm(product=self.product, data=data)
        form.is_valid()
        expected = {"os": "Linux"}
        actual = form.cleaned_metadata
        self.assertDictEqual(expected, actual)

        # Add an empty metadata value
        data["ff_version"] = ""
        form = NewQuestionForm(product=self.product, data=data)
        form.is_valid()
        expected = {"os": "Linux"}
        actual = form.cleaned_metadata
        self.assertDictEqual(expected, actual)

        # Check for clean troubleshooting data
        data["modifiedPreferences"] = {
            "print.macosx.pagesetup": True,
        }
        data["troubleshooting"] = json.dumps(
            {
                "environmentVariables": {
                    "MOZ_CRASHREPORTER_DATA_DIRECTORY": "/home/ringo/crashs",
                    "MOZ_CRASHREPORTER_PING_DIRECTORY": "/home/ringo/pings",
                },
            }
        )
        form = NewQuestionForm(product=self.product, data=data)
        form.is_valid()
        expected = {
            "os": "Linux",
            "troubleshooting": json.dumps(
                {
                    "environmentVariables": {
                        "MOZ_CRASHREPORTER_DATA_DIRECTORY": "/home/<USERNAME>/crashs",
                        "MOZ_CRASHREPORTER_PING_DIRECTORY": "/home/<USERNAME>/pings",
                    },
                }
            ),
        }
        actual = form.cleaned_metadata
        self.assertDictEqual(actual, expected)
