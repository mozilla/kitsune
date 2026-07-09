from datetime import timedelta
from unittest import mock

from django.test import TestCase, override_settings
from django.utils import timezone

from kitsune.wiki.content_managers import AIContentManager
from kitsune.wiki.models import RevisionTranslationRecord
from kitsune.wiki.strategies import (
    AITranslationStrategy,
    HybridTranslationStrategy,
    TranslationMethod,
    TranslationRequest,
    TranslationResult,
    TranslationStrategy,
    TranslationTrigger,
)
from kitsune.wiki.tasks import cleanup_old_translation_records
from kitsune.wiki.tests import RevisionFactory


class LogOperationTests(TestCase):
    """Tests for TranslationStrategy._log_operation (recording LLM explanations)."""

    def setUp(self):
        self.strategy = TranslationStrategy()
        self.source_revision = RevisionFactory()
        self.target_revision = RevisionFactory()
        self.explanation = {
            "content": "Translated the body.",
            "summary": "Translated the summary.",
            "keywords": "Translated the keywords.",
            "title": "Translated the title.",
        }

    def _request(self, trigger=TranslationTrigger.TRANSLATE):
        return TranslationRequest(
            revision=self.source_revision,
            trigger=trigger,
            target_locale="fr",
            method=TranslationMethod.AI,
        )

    def _result(self, **kwargs):
        defaults = {
            "success": True,
            "method": TranslationMethod.AI,
            "revision": self.target_revision,
            "metadata": {"explanation": self.explanation},
        }
        defaults.update(kwargs)
        return TranslationResult(**defaults)

    def test_records_explanation_for_successful_ai_translation(self):
        self.strategy._log_operation(self._request(), self._result())

        record = RevisionTranslationRecord.objects.get(revision=self.target_revision)
        self.assertEqual(record.locale, "fr")
        self.assertEqual(record.explanation, self.explanation)
        self.assertEqual(record.trigger, "translate")
        self.assertEqual(record.method, "ai")

    def test_stores_enum_trigger_as_its_value(self):
        # An enum member subclasses str, so it persists as its underlying value.
        self.strategy._log_operation(
            self._request(trigger=TranslationTrigger.STALE_TRANSLATION_UPDATE), self._result()
        )

        record = RevisionTranslationRecord.objects.get(revision=self.target_revision)
        self.assertEqual(record.trigger, "stale_translation_update")

    def test_stores_string_trigger_unchanged(self):
        # After an async round-trip through the celery task, the trigger arrives as a
        # plain string rather than a TranslationTrigger member.
        self.strategy._log_operation(self._request(trigger="initial_translation"), self._result())

        record = RevisionTranslationRecord.objects.get(revision=self.target_revision)
        self.assertEqual(record.trigger, "initial_translation")

    def test_no_record_without_explanation(self):
        self.strategy._log_operation(self._request(), self._result(metadata={}))

        self.assertFalse(RevisionTranslationRecord.objects.exists())

    def test_no_record_for_failed_operation(self):
        self.strategy._log_operation(self._request(), self._result(success=False))

        self.assertFalse(RevisionTranslationRecord.objects.exists())

    def test_no_record_without_revision(self):
        self.strategy._log_operation(self._request(), self._result(revision=None))

        self.assertFalse(RevisionTranslationRecord.objects.exists())

    def test_is_idempotent_and_updates_existing_record(self):
        self.strategy._log_operation(self._request(), self._result())

        new_explanation = {"content": "Revised explanation."}
        self.strategy._log_operation(
            self._request(), self._result(metadata={"explanation": new_explanation})
        )

        records = RevisionTranslationRecord.objects.filter(revision=self.target_revision)
        self.assertEqual(records.count(), 1)
        self.assertEqual(records.get().explanation, new_explanation)


class AIAndHybridStrategyLogTests(TestCase):
    """The AI and hybrid strategies record the LLM explanation for the translated revision."""

    TRANSLATED_CONTENT = {
        "content": {"translation": "Contenu", "explanation": "Explained content."},
        "summary": {"translation": "Résumé", "explanation": "Explained summary."},
        "keywords": {"translation": "mots", "explanation": "Explained keywords."},
        "title": {"translation": "Titre", "explanation": "Explained title."},
    }

    @mock.patch("kitsune.wiki.strategies.llm_translate")
    def test_ai_translate_records_explanation(self, mock_translate):
        mock_translate.return_value = self.TRANSLATED_CONTENT
        target_revision = RevisionFactory()
        strategy = AITranslationStrategy()
        l10n_request = TranslationRequest(
            revision=RevisionFactory(),
            trigger=TranslationTrigger.TRANSLATE,
            target_locale="fr",
            method=TranslationMethod.AI,
        )

        with (
            mock.patch.object(
                strategy.content_manager, "create_revision", return_value=target_revision
            ),
            mock.patch.object(
                strategy.content_manager, "publish_revision", return_value=target_revision
            ),
        ):
            result = strategy.translate(l10n_request)

        self.assertTrue(result.success)
        record = RevisionTranslationRecord.objects.get(revision=target_revision)
        self.assertEqual(record.locale, "fr")
        self.assertEqual(record.method, "ai")
        self.assertEqual(record.trigger, "translate")
        self.assertEqual(record.explanation["content"], "Explained content.")
        self.assertEqual(record.explanation["title"], "Explained title.")

    @mock.patch("kitsune.wiki.strategies.llm_translate")
    def test_hybrid_translate_records_hybrid_method(self, mock_translate):
        # The hybrid strategy delegates to AITranslationStrategy.translate, but the
        # recorded method must reflect the request (hybrid), not the AI strategy that
        # ran it.
        mock_translate.return_value = self.TRANSLATED_CONTENT
        target_revision = RevisionFactory()
        l10n_request = TranslationRequest(
            revision=RevisionFactory(),
            trigger=TranslationTrigger.TRANSLATE,
            target_locale="es",
            method=TranslationMethod.HYBRID,
        )

        # The inner AITranslationStrategy builds its own AIContentManager, so patch at
        # the class. publish_revision is never reached because hybrid passes publish=False.
        with mock.patch.object(AIContentManager, "create_revision", return_value=target_revision):
            result = HybridTranslationStrategy().translate(l10n_request)

        self.assertTrue(result.success)
        record = RevisionTranslationRecord.objects.get(revision=target_revision)
        self.assertEqual(record.locale, "es")
        self.assertEqual(record.method, "hybrid")


class CleanupOldTranslationRecordsTests(TestCase):
    """Tests for the cleanup_old_translation_records purge task."""

    def _create_record(self, created):
        record = RevisionTranslationRecord.objects.create(
            revision=RevisionFactory(),
            locale="fr",
            explanation={"content": "explanation"},
            trigger="translate",
            method="ai",
        )
        # created is auto_now_add, so set it explicitly via a queryset update.
        RevisionTranslationRecord.objects.filter(pk=record.pk).update(created=created)
        return record

    @override_settings(TRANSLATION_RECORD_RETENTION_DAYS=180)
    def test_deletes_only_records_older_than_retention(self):
        now = timezone.now()
        old = self._create_record(now - timedelta(days=181))
        recent = self._create_record(now - timedelta(days=179))

        cleanup_old_translation_records()

        self.assertFalse(RevisionTranslationRecord.objects.filter(pk=old.pk).exists())
        self.assertTrue(RevisionTranslationRecord.objects.filter(pk=recent.pk).exists())
