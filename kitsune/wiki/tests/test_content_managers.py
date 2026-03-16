from django.test import TestCase

from kitsune.wiki.content_managers import AIContentManager
from kitsune.wiki.models import Document
from kitsune.wiki.tests import ApprovedRevisionFactory, DocumentFactory


class AIContentManagerCreateRevisionTests(TestCase):
    def setUp(self):
        self.manager = AIContentManager()
        self.parent_doc = DocumentFactory(locale="en-US")
        ApprovedRevisionFactory(document=self.parent_doc, is_ready_for_localization=True)
        self.parent_doc.refresh_from_db()

    def _make_data(self, title="Titre traduit"):
        return {
            "target_locale": "fr",
            "translated_content": {
                "title": {"translation": title},
            },
            "summary": "Résumé",
            "keywords": "mots-clés",
            "content": "Contenu traduit",
        }

    def test_creates_new_document_with_translated_title_and_parent_slug(self):
        """When no target doc exists, it is created with the translated title and parent slug."""
        self.manager.create_revision(self._make_data(), self.parent_doc)

        target_doc = Document.objects.get(parent=self.parent_doc, locale="fr")
        self.assertEqual(target_doc.title, "Titre traduit")
        self.assertEqual(target_doc.slug, self.parent_doc.slug)

    def test_existing_doc_without_current_revision_gets_title_and_slug_updated(self):
        """When a target doc exists but has no approved revision, title and slug are overwritten."""
        spam_doc = DocumentFactory(
            parent=self.parent_doc,
            locale="fr",
            title="Spammer's bad title",
            slug="bad-slug",
        )
        self.assertIsNone(spam_doc.current_revision)

        self.manager.create_revision(self._make_data(), self.parent_doc)

        spam_doc.refresh_from_db()
        self.assertEqual(spam_doc.title, "Titre traduit")
        self.assertEqual(spam_doc.slug, self.parent_doc.slug)

    def test_existing_doc_with_current_revision_keeps_title_and_slug(self):
        """When a target doc exists and has an approved revision, title and slug are preserved."""
        target_doc = DocumentFactory(
            parent=self.parent_doc,
            locale="fr",
            title="Titre approuvé",
            slug="titre-approuve",
        )
        ApprovedRevisionFactory(document=target_doc)
        target_doc.refresh_from_db()
        self.assertIsNotNone(target_doc.current_revision)

        self.manager.create_revision(self._make_data(), self.parent_doc)

        target_doc.refresh_from_db()
        self.assertEqual(target_doc.title, "Titre approuvé")
        self.assertEqual(target_doc.slug, "titre-approuve")
