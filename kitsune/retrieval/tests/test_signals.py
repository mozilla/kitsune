from unittest import mock

from django.test import TestCase, override_settings

from kitsune.products.tests import ProductFactory, TopicFactory
from kitsune.users.tests import GroupFactory
from kitsune.wiki.tests import ApprovedRevisionFactory, DocumentFactory


class SignalTestCase(TestCase):
    """Signals are asserted by what they *enqueue*; the sync core has its own suite."""

    def setUp(self):
        super().setUp()
        self.document = DocumentFactory(title="Install Firefox", slug="install-firefox")
        ApprovedRevisionFactory(document=self.document)
        self.document.refresh_from_db()

    def _queued_syncs(self, action):
        """Document ids queued for sync by `action`, once its transaction commits."""
        with mock.patch("kitsune.retrieval.tasks.sync_document.delay") as delay:
            with self.captureOnCommitCallbacks(execute=True):
                action()
        return {call.args[0] for call in delay.call_args_list}

    def _queued_deletes(self, action):
        with mock.patch("kitsune.retrieval.tasks.delete_document.delay") as delay:
            with self.captureOnCommitCallbacks(execute=True):
                action()
        return {call.args for call in delay.call_args_list}


@override_settings(RETRIEVAL_INGESTION_ENABLED=True, RETRIEVAL_LIVE_INDEXING=True)
class DocumentSaveTests(SignalTestCase):
    def test_saving_a_document_queues_its_own_sync(self):
        self.assertIn(self.document.id, self._queued_syncs(self.document.save))

    def test_saving_an_original_refreshes_the_whole_family(self):
        translation = DocumentFactory(parent=self.document, locale="de", slug="de-install")
        ApprovedRevisionFactory(document=translation)

        queued = self._queued_syncs(self.document.save)

        # Translations inherit products, topics, category and access from the original.
        self.assertEqual(queued, {self.document.id, translation.id})

    def test_saving_a_translation_refreshes_the_family_too(self):
        translation = DocumentFactory(parent=self.document, locale="de", slug="de-install")
        ApprovedRevisionFactory(document=translation)

        queued = self._queued_syncs(translation.save)

        self.assertEqual(queued, {self.document.id, translation.id})

    def test_nothing_is_queued_before_the_transaction_commits(self):
        with mock.patch("kitsune.retrieval.tasks.sync_document.delay") as delay:
            with self.captureOnCommitCallbacks(execute=False):
                self.document.save()
            delay.assert_not_called()


@override_settings(RETRIEVAL_INGESTION_ENABLED=True, RETRIEVAL_LIVE_INDEXING=False)
class LiveIndexingOffTests(SignalTestCase):
    """With the pipeline on, live indexing governs freshness only."""

    def test_no_sync_is_queued(self):
        self.assertEqual(self._queued_syncs(self.document.save), set())

    def test_deletion_is_still_queued(self):
        # Eviction is not a freshness optimization.
        identity = ("kb", str(self.document.id), self.document.locale)
        self.assertIn(identity, self._queued_deletes(self.document.delete))


@override_settings(RETRIEVAL_INGESTION_ENABLED=False, RETRIEVAL_LIVE_INDEXING=True)
class IngestionDisabledTests(SignalTestCase):
    """The master switch queues nothing at all, and outranks live indexing to do it.

    Live indexing is deliberately left on here: the point is that the switch above it wins, so
    a half-configured environment cannot start filling a queue nothing is consuming.
    """

    def setUp(self):
        super().setUp()
        self.group = GroupFactory()

    def test_saving_a_document_queues_no_sync(self):
        self.assertEqual(self._queued_syncs(self.document.save), set())

    def test_deleting_a_document_queues_no_eviction(self):
        self.assertEqual(self._queued_deletes(self.document.delete), set())

    def test_taxonomy_changes_queue_nothing(self):
        product = ProductFactory()
        self.assertEqual(self._queued_syncs(lambda: self.document.products.add(product)), set())
        self.assertEqual(self._queued_syncs(product.delete), set())

    def test_access_changes_queue_nothing(self):
        relation = self.document.restrict_to_groups
        self.assertEqual(self._queued_syncs(lambda: relation.add(self.group)), set())
        self.assertEqual(self._queued_syncs(self.group.delete), set())


@override_settings(RETRIEVAL_INGESTION_ENABLED=True, RETRIEVAL_LIVE_INDEXING=True)
class TaxonomyChangeTests(SignalTestCase):
    def setUp(self):
        super().setUp()
        self.product = ProductFactory()
        self.topic = TopicFactory()

    def test_forward_add_remove_and_clear_refresh_the_family(self):
        for field, item in (("products", self.product), ("topics", self.topic)):
            relation = getattr(self.document, field)
            with self.subTest(field=field, action="add"):
                self.assertIn(self.document.id, self._queued_syncs(lambda: relation.add(item)))
            with self.subTest(field=field, action="remove"):
                self.assertIn(self.document.id, self._queued_syncs(lambda: relation.remove(item)))
            relation.add(item)
            with self.subTest(field=field, action="clear"):
                self.assertIn(self.document.id, self._queued_syncs(relation.clear))

    def test_reverse_add_remove_and_clear_refresh_the_family(self):
        for item in (self.product, self.topic):
            relation = item.document_set
            with self.subTest(model=type(item).__name__, action="add"):
                self.assertIn(
                    self.document.id, self._queued_syncs(lambda: relation.add(self.document))
                )
            with self.subTest(model=type(item).__name__, action="remove"):
                self.assertIn(
                    self.document.id, self._queued_syncs(lambda: relation.remove(self.document))
                )
            relation.add(self.document)
            # post_clear cannot report what was removed, so capture it during pre_clear.
            with self.subTest(model=type(item).__name__, action="clear"):
                self.assertIn(self.document.id, self._queued_syncs(relation.clear))

    def test_deletion_refreshes_documents_before_join_rows_disappear(self):
        for field, item in (("products", self.product), ("topics", self.topic)):
            getattr(self.document, field).add(item)
            with self.subTest(model=type(item).__name__):
                self.assertIn(self.document.id, self._queued_syncs(item.delete))


@override_settings(RETRIEVAL_INGESTION_ENABLED=True, RETRIEVAL_LIVE_INDEXING=True)
class RestrictionChangeTests(SignalTestCase):
    """An access change is an ordinary freshness transition (ADR 0006)."""

    def setUp(self):
        super().setUp()
        self.group = GroupFactory()

    def test_restricting_a_document_refreshes_it_so_it_is_evicted(self):
        # Under the public-only policy this makes the document ineligible; the sync core
        # then evicts it. The signal's job is only to notice.
        self.assertIn(
            self.document.id,
            self._queued_syncs(lambda: self.document.restrict_to_groups.add(self.group)),
        )

    def test_widening_access_refreshes_it_so_it_is_indexed(self):
        self.document.restrict_to_groups.add(self.group)
        self.assertIn(
            self.document.id,
            self._queued_syncs(lambda: self.document.restrict_to_groups.remove(self.group)),
        )

    def test_clearing_restrictions_refreshes_the_document(self):
        self.document.restrict_to_groups.add(self.group)
        self.assertIn(self.document.id, self._queued_syncs(self.document.restrict_to_groups.clear))

    def test_changes_from_the_group_side_find_the_documents(self):
        relation = self.group.restricted_documents
        self.assertIn(self.document.id, self._queued_syncs(lambda: relation.add(self.document)))
        self.assertIn(self.document.id, self._queued_syncs(lambda: relation.remove(self.document)))
        relation.add(self.document)
        self.assertIn(self.document.id, self._queued_syncs(relation.clear))

    def test_deleting_a_group_refreshes_the_documents_it_restricted(self):
        self.document.restrict_to_groups.add(self.group)
        self.assertIn(self.document.id, self._queued_syncs(self.group.delete))


@override_settings(RETRIEVAL_INGESTION_ENABLED=True, RETRIEVAL_LIVE_INDEXING=True)
class DocumentDeletionTests(SignalTestCase):
    def test_deleting_a_document_queues_an_eviction_for_its_exact_identity(self):
        identity = ("kb", str(self.document.id), self.document.locale)
        self.assertIn(identity, self._queued_deletes(self.document.delete))

    def test_a_translation_is_evicted_by_its_own_locale(self):
        translation = DocumentFactory(parent=self.document, locale="de", slug="de-install")
        ApprovedRevisionFactory(document=translation)
        identity = ("kb", str(translation.id), "de")

        self.assertIn(identity, self._queued_deletes(translation.delete))
