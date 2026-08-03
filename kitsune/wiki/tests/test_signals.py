from unittest.mock import call, patch

from django.contrib.auth.models import Group
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


class RenderOnRestrictingGroupDeletionTests(TestCase):
    """Deleting a group must cascade the documents it was restricting.

    Django's delete collector removes the "restrict_to_groups" rows as a fast delete,
    without sending "m2m_changed", so nothing else notices that the documents are no
    longer restricted the way their cached HTML assumes.
    """

    @patch("kitsune.wiki.tasks.render_document_cascade")
    def test_deleting_a_restricting_group_cascades_its_documents(self, mock_task):
        group = GroupFactory()
        with self.captureOnCommitCallbacks(execute=True):
            doc = DocumentFactory(restrict_to_groups=[group])
        mock_task.delay.reset_mock()

        with self.captureOnCommitCallbacks(execute=True):
            group.delete()

        mock_task.delay.assert_called_once_with(doc.id)

    @patch("kitsune.wiki.tasks.render_document_cascade")
    def test_documents_restricted_to_other_groups_are_left_alone(self, mock_task):
        doomed = GroupFactory()
        survivor = GroupFactory()
        with self.captureOnCommitCallbacks(execute=True):
            restricted = DocumentFactory(restrict_to_groups=[doomed])
            DocumentFactory(restrict_to_groups=[survivor])
        mock_task.delay.reset_mock()

        with self.captureOnCommitCallbacks(execute=True):
            doomed.delete()

        mock_task.delay.assert_called_once_with(restricted.id)

    @patch("kitsune.wiki.tasks.render_document_cascade")
    def test_documents_still_restricted_afterwards_are_cascaded_too(self, mock_task):
        """A document keeping one of its two groups still renders differently.

        The parser allows an include only when the container's groups are a subset of
        the included document's groups, so shrinking the set changes the outcome even
        though the document stays restricted.
        """
        doomed = GroupFactory()
        survivor = GroupFactory()
        with self.captureOnCommitCallbacks(execute=True):
            doc = DocumentFactory(restrict_to_groups=[doomed, survivor])
        mock_task.delay.reset_mock()

        with self.captureOnCommitCallbacks(execute=True):
            doomed.delete()

        mock_task.delay.assert_called_once_with(doc.id)

    @patch("kitsune.wiki.tasks.render_document_cascade")
    def test_translations_are_cascaded_when_a_restricting_group_is_deleted(self, mock_task):
        group = GroupFactory()
        with self.captureOnCommitCallbacks(execute=True):
            parent = DocumentFactory(restrict_to_groups=[group])
            translation = DocumentFactory(parent=parent, locale="de")
        mock_task.delay.reset_mock()

        with self.captureOnCommitCallbacks(execute=True):
            group.delete()

        mock_task.delay.assert_has_calls([call(parent.id), call(translation.id)], any_order=True)
        assert mock_task.delay.call_count == 2

    @patch("kitsune.wiki.tasks.render_document_cascade")
    def test_deleting_a_group_restricting_nothing_dispatches_nothing(self, mock_task):
        group = GroupFactory()
        with self.captureOnCommitCallbacks(execute=True):
            DocumentFactory()
        mock_task.delay.reset_mock()

        with self.captureOnCommitCallbacks(execute=True):
            group.delete()

        mock_task.delay.assert_not_called()

    @patch("kitsune.wiki.tasks.render_document_cascade")
    def test_queryset_deletion_cascades_documents(self, mock_task):
        """Bulk deletes bypass Group.delete(), so the cascade has to hang off a signal."""
        group = GroupFactory()
        with self.captureOnCommitCallbacks(execute=True):
            doc = DocumentFactory(restrict_to_groups=[group])
        mock_task.delay.reset_mock()

        with self.captureOnCommitCallbacks(execute=True):
            Group.objects.filter(pk=group.pk).delete()

        mock_task.delay.assert_called_once_with(doc.id)

    @patch("kitsune.wiki.tasks.render_document_cascade")
    def test_nothing_is_dispatched_before_commit(self, mock_task):
        group = GroupFactory()
        with self.captureOnCommitCallbacks(execute=True):
            DocumentFactory(restrict_to_groups=[group])
        mock_task.delay.reset_mock()

        with self.captureOnCommitCallbacks(execute=False):
            group.delete()

        mock_task.delay.assert_not_called()
