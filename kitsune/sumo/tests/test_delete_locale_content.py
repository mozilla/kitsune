from io import StringIO

from django.conf import settings
from django.core.management import CommandError, call_command
from django.test import override_settings

from kitsune.community.models import DeletedContribution
from kitsune.gallery.models import Image
from kitsune.gallery.tests import ImageFactory
from kitsune.inproduct.models import Redirect
from kitsune.inproduct.tests import RedirectFactory
from kitsune.questions.models import Question
from kitsune.questions.tests import AnswerFactory
from kitsune.sumo.tests import TestCase
from kitsune.wiki.models import Document, Locale
from kitsune.wiki.tests import ApprovedRevisionFactory, LocaleFactory


# "zz" has never been a supported locale.
@override_settings(REMOVED_LOCALES=("zz",))
class DeleteLocaleContentTests(TestCase):
    def setUp(self):
        ApprovedRevisionFactory(document__locale="zz")
        AnswerFactory(question__locale="zz")
        LocaleFactory(locale="zz")
        ImageFactory(locale="zz")
        self.rule = RedirectFactory(locale="zz", topic="some-topic")
        self.kept = ApprovedRevisionFactory(document__locale="de").document

    def run_command(self, *args):
        out = StringIO()
        call_command("delete_locale_content", *args, stdout=out)
        return out.getvalue()

    @override_settings(REMOVED_LOCALES=("zz", "de"))
    def test_refuses_supported_locales(self):
        with self.assertRaises(CommandError):
            self.run_command()
        self.assertTrue(Document.objects.filter(locale="zz").exists())

    def test_dry_run_deletes_nothing(self):
        out = self.run_command("--dry-run")
        self.assertIn(str(self.rule), out)
        self.assertTrue(Document.objects.filter(locale="zz").exists())
        self.assertTrue(Question.objects.filter(locale="zz").exists())
        self.assertFalse(DeletedContribution.objects.exists())

    def test_deletes_content_and_records_contributions(self):
        self.run_command()
        self.assertFalse(Document.objects.filter(locale="zz").exists())
        self.assertFalse(Question.objects.filter(locale="zz").exists())
        self.assertFalse(Locale.objects.filter(locale="zz").exists())
        self.assertFalse(Image.objects.filter(locale="zz").exists())
        self.assertTrue(Document.objects.filter(pk=self.kept.pk).exists())
        self.assertTrue(Redirect.objects.filter(pk=self.rule.pk).exists())
        # One each for the edit, the article, and the answer.
        self.assertEqual(3, DeletedContribution.objects.filter(locale="zz").count())


class RemovedLocalesSettingTests(TestCase):
    def test_removed_locales_are_unsupported_and_redirect(self):
        for locale in settings.REMOVED_LOCALES:
            with self.subTest(locale=locale):
                self.assertNotIn(locale, settings.SUMO_LANGUAGES)
                self.assertIn(locale, settings.NON_SUPPORTED_LOCALES)
