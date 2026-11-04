from unittest.mock import call, patch

from django.core.cache import cache
from django.test import TestCase, override_settings

from kitsune.wiki.models import Audience, doc_html_cache_key
from kitsune.wiki.tests import AudienceFactory, DocumentFactory


class RenderOnAudiencesChangeTests(TestCase):
    @patch("kitsune.wiki.tasks.render_document_cascade")
    def test_adding_audience_triggers_render_cascade(self, mock_task):
        doc = DocumentFactory(audiences=[])
        audience = AudienceFactory()
        with self.captureOnCommitCallbacks(execute=True):
            doc.audiences.add(audience)
        mock_task.delay.assert_called_once_with(doc.id)

    @patch("kitsune.wiki.tasks.render_document_cascade")
    def test_removing_audience_triggers_render_cascade(self, mock_task):
        audience = AudienceFactory()
        doc = DocumentFactory(audiences=[audience])

        with self.captureOnCommitCallbacks(execute=True):
            doc.audiences.remove(audience)
        mock_task.delay.assert_called_once_with(doc.id)

    @patch("kitsune.wiki.tasks.render_document_cascade")
    def test_clearing_audiences_triggers_render_cascade(self, mock_task):
        doc = DocumentFactory(audiences=[AudienceFactory()])

        with self.captureOnCommitCallbacks(execute=True):
            doc.audiences.clear()
        mock_task.delay.assert_called_once_with(doc.id)

    @patch("kitsune.wiki.tasks.render_document_cascade")
    def test_setting_audiences_triggers_render_cascade(self, mock_task):
        doc = DocumentFactory(audiences=[])
        with self.captureOnCommitCallbacks(execute=True):
            doc.audiences.set([AudienceFactory(), AudienceFactory()])
        mock_task.delay.assert_called_once_with(doc.id)

    @patch("kitsune.wiki.tasks.render_document_cascade")
    def test_translations_are_re_rendered(self, mock_task):
        parent = DocumentFactory(audiences=[])
        translation = DocumentFactory(parent=parent, locale="de")
        audience = AudienceFactory()

        with self.captureOnCommitCallbacks(execute=True):
            parent.audiences.add(audience)
        mock_task.delay.assert_has_calls(
            [call(parent.id), call(translation.id)],
            any_order=True,
        )
        assert mock_task.delay.call_count == 2


class ReverseAudiencesChangeTests(TestCase):
    """Changes made from the Audience side must cascade the documents, not the audience.

    On the reverse side the signal's "instance" is an Audience, so dispatching on
    "instance.id" would re-render whichever document happened to share that id.
    """

    @patch("kitsune.wiki.tasks.render_document_cascade")
    def test_adding_documents_from_the_audience_side_cascades_those_documents(self, mock_task):
        doc = DocumentFactory(audiences=[])
        audience = AudienceFactory()

        with self.captureOnCommitCallbacks(execute=True):
            audience.documents.add(doc)

        mock_task.delay.assert_called_once_with(doc.id)

    @patch("kitsune.wiki.tasks.render_document_cascade")
    def test_removing_documents_from_the_audience_side_cascades_those_documents(self, mock_task):
        audience = AudienceFactory()
        doc = DocumentFactory(audiences=[audience])

        with self.captureOnCommitCallbacks(execute=True):
            audience.documents.remove(doc)

        mock_task.delay.assert_called_once_with(doc.id)

    @patch("kitsune.wiki.tasks.render_document_cascade")
    def test_clearing_from_the_audience_side_still_finds_the_documents(self, mock_task):
        audience = AudienceFactory()
        doc = DocumentFactory(audiences=[audience])

        with self.captureOnCommitCallbacks(execute=True):
            audience.documents.clear()

        # post_clear cannot report the unlinked documents, so they are read in pre_clear.
        mock_task.delay.assert_called_once_with(doc.id)

    @patch("kitsune.wiki.tasks.render_document_cascade")
    def test_translations_are_cascaded_from_the_audience_side_too(self, mock_task):
        parent = DocumentFactory(audiences=[])
        translation = DocumentFactory(parent=parent, locale="de")
        audience = AudienceFactory()

        with self.captureOnCommitCallbacks(execute=True):
            audience.documents.add(parent)

        mock_task.delay.assert_has_calls([call(parent.id), call(translation.id)], any_order=True)
        assert mock_task.delay.call_count == 2

    @patch("kitsune.wiki.tasks.render_document_cascade")
    def test_nothing_is_dispatched_before_commit(self, mock_task):
        doc = DocumentFactory(audiences=[])
        audience = AudienceFactory()

        with self.captureOnCommitCallbacks(execute=False):
            audience.documents.add(doc)

        mock_task.delay.assert_not_called()


class PageCacheOnAudiencesChangeTests(TestCase):
    @patch("kitsune.wiki.tasks.render_document_cascade")
    def test_audience_change_clears_family_page_cache(self, mock_task):
        public = Audience.objects.default()
        doc = DocumentFactory(audiences=[public, AudienceFactory()])
        translation = DocumentFactory(parent=doc, locale="de")
        keys = [
            doc_html_cache_key("en-US", doc.slug),
            # Fallback pages are cached under the request locale.
            doc_html_cache_key("de", doc.slug),
            doc_html_cache_key("de", translation.slug),
        ]

        for side, unpublish in (
            ("forward", lambda: doc.audiences.remove(public)),
            ("reverse", lambda: public.documents.remove(doc)),
        ):
            for committed in (False, True):
                with self.subTest(side, committed=committed):
                    doc.audiences.add(public)
                    cache.set_many(dict.fromkeys(keys, ("<html>", {})))
                    self.assertCountEqual(cache.get_many(keys), keys)

                    with self.captureOnCommitCallbacks(execute=committed):
                        unpublish()

                    self.assertCountEqual(cache.get_many(keys), [] if committed else keys)

    @patch("kitsune.wiki.tasks.render_document_cascade")
    def test_visibility_flip_rerenders_and_clears_page_caches(self, mock_task):
        kb = AudienceFactory(is_public=True)
        doc = DocumentFactory(audiences=[kb])
        translation = DocumentFactory(parent=doc, locale="de")
        keys = [doc_html_cache_key("en-US", doc.slug), doc_html_cache_key("de", translation.slug)]

        for field, value, flipped in (("name", "Renamed", False), ("is_public", False, True)):
            with self.subTest(field):
                mock_task.reset_mock()
                cache.set_many(dict.fromkeys(keys, ("<html>", {})))
                setattr(kb, field, value)

                with self.captureOnCommitCallbacks(execute=True):
                    kb.save()

                self.assertCountEqual(cache.get_many(keys), [] if flipped else keys)
                self.assertEqual(
                    {c.args[0] for c in mock_task.delay.call_args_list},
                    {doc.id, translation.id} if flipped else set(),
                )


class RenderIncludersOnDeleteTests(TestCase):
    """Deleting an include must rerender dependents after the link rows disappear."""

    def setUp(self):
        self.included = DocumentFactory(title="Shared", slug="shared")
        self.includer = DocumentFactory(title="Includer", slug="includer")
        self.includer.add_link_to(self.included, "include")

    @override_settings(RETRIEVAL_LIVE_INDEXING=False)
    @patch("kitsune.retrieval.tasks.delete_document.delay")
    def test_deletion_rerenders_includers_when_retrieval_is_disabled(self, retrieval_delete):
        # Eviction is deliberately not gated on RETRIEVAL_LIVE_INDEXING, and Celery is eager
        # here, so an unmocked delete would reach Elasticsearch — which the wiki CI job has no
        # container for. This test is about the wiki cascade, not about retrieval.
        with patch("kitsune.wiki.tasks.render_document_cascade.delay") as delay:
            with self.captureOnCommitCallbacks(execute=True):
                self.included.delete()

        self.assertIn(self.includer.id, {task.args[0] for task in delay.call_args_list})
