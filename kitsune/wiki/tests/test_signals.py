from unittest.mock import call, patch

from django.test import TestCase

from kitsune.users.tests import GroupFactory
from kitsune.wiki.tests import DocumentFactory


class RenderOnRestrictToGroupsChangeTests(TestCase):
    @patch("kitsune.wiki.tasks.render_document_cascade")
    def test_adding_group_triggers_render_cascade(self, mock_task):
        doc = DocumentFactory()
        group = GroupFactory()
        with self.captureOnCommitCallbacks(execute=True):
            doc.restrict_to_groups.add(group)
        mock_task.delay.assert_called_once_with(doc.id)

    @patch("kitsune.wiki.tasks.render_document_cascade")
    def test_removing_group_triggers_render_cascade(self, mock_task):
        doc = DocumentFactory()
        group = GroupFactory()
        with self.captureOnCommitCallbacks(execute=True):
            doc.restrict_to_groups.add(group)
        mock_task.delay.reset_mock()

        with self.captureOnCommitCallbacks(execute=True):
            doc.restrict_to_groups.remove(group)
        mock_task.delay.assert_called_once_with(doc.id)

    @patch("kitsune.wiki.tasks.render_document_cascade")
    def test_clearing_groups_triggers_render_cascade(self, mock_task):
        doc = DocumentFactory()
        group = GroupFactory()
        with self.captureOnCommitCallbacks(execute=True):
            doc.restrict_to_groups.add(group)
        mock_task.delay.reset_mock()

        with self.captureOnCommitCallbacks(execute=True):
            doc.restrict_to_groups.clear()
        mock_task.delay.assert_called_once_with(doc.id)

    @patch("kitsune.wiki.tasks.render_document_cascade")
    def test_setting_groups_triggers_render_cascade(self, mock_task):
        doc = DocumentFactory()
        group1 = GroupFactory()
        group2 = GroupFactory()
        with self.captureOnCommitCallbacks(execute=True):
            doc.restrict_to_groups.set([group1, group2])
        mock_task.delay.assert_called_once_with(doc.id)

    @patch("kitsune.wiki.tasks.render_document_cascade")
    def test_translations_are_re_rendered(self, mock_task):
        parent = DocumentFactory()
        translation = DocumentFactory(parent=parent, locale="de")
        group = GroupFactory()
        mock_task.delay.reset_mock()

        with self.captureOnCommitCallbacks(execute=True):
            parent.restrict_to_groups.add(group)
        mock_task.delay.assert_has_calls(
            [call(parent.id), call(translation.id)],
            any_order=True,
        )
        assert mock_task.delay.call_count == 2


class ReverseRestrictToGroupsChangeTests(TestCase):
    """Changes made from the Group side must cascade the documents, not the group.

    On the reverse side the signal's "instance" is a Group, so dispatching on "instance.id"
    would re-render whichever document happened to share that id.
    """

    @patch("kitsune.wiki.tasks.render_document_cascade")
    def test_adding_documents_from_the_group_side_cascades_those_documents(self, mock_task):
        doc = DocumentFactory()
        group = GroupFactory()

        with self.captureOnCommitCallbacks(execute=True):
            group.restricted_documents.add(doc)

        mock_task.delay.assert_called_once_with(doc.id)

    @patch("kitsune.wiki.tasks.render_document_cascade")
    def test_removing_documents_from_the_group_side_cascades_those_documents(self, mock_task):
        doc = DocumentFactory()
        group = GroupFactory()
        with self.captureOnCommitCallbacks(execute=True):
            group.restricted_documents.add(doc)
        mock_task.delay.reset_mock()

        with self.captureOnCommitCallbacks(execute=True):
            group.restricted_documents.remove(doc)

        mock_task.delay.assert_called_once_with(doc.id)

    @patch("kitsune.wiki.tasks.render_document_cascade")
    def test_clearing_from_the_group_side_still_finds_the_documents(self, mock_task):
        doc = DocumentFactory()
        group = GroupFactory()
        with self.captureOnCommitCallbacks(execute=True):
            group.restricted_documents.add(doc)
        mock_task.delay.reset_mock()

        with self.captureOnCommitCallbacks(execute=True):
            group.restricted_documents.clear()

        # post_clear cannot report the unlinked documents, so they are read in pre_clear.
        mock_task.delay.assert_called_once_with(doc.id)

    @patch("kitsune.wiki.tasks.render_document_cascade")
    def test_translations_are_cascaded_from_the_group_side_too(self, mock_task):
        parent = DocumentFactory()
        translation = DocumentFactory(parent=parent, locale="de")
        group = GroupFactory()

        with self.captureOnCommitCallbacks(execute=True):
            group.restricted_documents.add(parent)

        mock_task.delay.assert_has_calls([call(parent.id), call(translation.id)], any_order=True)
        assert mock_task.delay.call_count == 2

    @patch("kitsune.wiki.tasks.render_document_cascade")
    def test_nothing_is_dispatched_before_commit(self, mock_task):
        doc = DocumentFactory()
        group = GroupFactory()

        with self.captureOnCommitCallbacks(execute=False):
            group.restricted_documents.add(doc)

        mock_task.delay.assert_not_called()
