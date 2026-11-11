from io import StringIO

from django.core.management import CommandError, call_command

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


class DeleteLocaleContentTests(TestCase):
    def setUp(self):
        # "zz" has never been a supported locale.
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

    def test_refuses_supported_locales(self):
        with self.assertRaises(CommandError):
            self.run_command("zz", "de")
        self.assertTrue(Document.objects.filter(locale="zz").exists())

    def test_dry_run_deletes_nothing(self):
        out = self.run_command("zz", "--dry-run")
        self.assertIn(str(self.rule), out)
        self.assertTrue(Document.objects.filter(locale="zz").exists())
        self.assertTrue(Question.objects.filter(locale="zz").exists())
        self.assertFalse(DeletedContribution.objects.exists())

    def test_deletes_content_and_records_contributions(self):
        self.run_command("zz")
        self.assertFalse(Document.objects.filter(locale="zz").exists())
        self.assertFalse(Question.objects.filter(locale="zz").exists())
        self.assertFalse(Locale.objects.filter(locale="zz").exists())
        self.assertFalse(Image.objects.filter(locale="zz").exists())
        self.assertTrue(Document.objects.filter(pk=self.kept.pk).exists())
        self.assertTrue(Redirect.objects.filter(pk=self.rule.pk).exists())
        # One each for the edit, the article, and the answer.
        self.assertEqual(3, DeletedContribution.objects.filter(locale="zz").count())
