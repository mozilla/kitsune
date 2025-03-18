from django.conf import settings

from kitsune.sumo.tests import TestCase
from kitsune.users.models import Profile
from kitsune.users.tests import GroupFactory, UserFactory
from kitsune.wiki.handlers import DocumentListener
from kitsune.wiki.models import Document, Revision
from kitsune.wiki.tests import DocumentFactory, HelpfulVoteFactory, RevisionFactory


class TestDocumentListener(TestCase):
    def setUp(self):
        self.user = UserFactory()
        Profile.get_sumo_bot()
        self.listener = DocumentListener()

        self.content_group = GroupFactory(name=settings.SUMO_CONTENT_GROUP)
        self.group_user1 = UserFactory()
        self.group_user2 = UserFactory()
        self.content_group.user_set.add(self.group_user1, self.group_user2)

    def test_document_contributor_replacement(self):
        """Test that sole contributor is replaced with content group members."""
        document = DocumentFactory()
        document.contributors.add(self.user)

        self.listener.on_user_deletion(self.user)

        self.assertFalse(document.contributors.filter(id=self.user.id).exists())

        self.assertTrue(document.contributors.filter(id=self.group_user1.id).exists())
        self.assertTrue(document.contributors.filter(id=self.group_user2.id).exists())

    def test_document_multiple_contributors(self):
        """Test that user is removed but other contributors remain."""
        document = DocumentFactory()
        other_contributor = UserFactory()
        document.contributors.add(self.user, other_contributor)

        self.listener.on_user_deletion(self.user)

        self.assertFalse(document.contributors.filter(id=self.user.id).exists())

        self.assertTrue(document.contributors.filter(id=other_contributor.id).exists())

        self.assertFalse(document.contributors.filter(id=self.group_user1.id).exists())
        self.assertFalse(document.contributors.filter(id=self.group_user2.id).exists())

    def test_multiple_documents(self):
        """Test handling multiple documents with different contributor scenarios."""
        doc1 = DocumentFactory()
        doc1.contributors.add(self.user)

        doc2 = DocumentFactory()
        other_contributor = UserFactory()
        doc2.contributors.add(self.user, other_contributor)

        doc3 = DocumentFactory()
        doc3.contributors.add(other_contributor)

        self.listener.on_user_deletion(self.user)

        self.assertFalse(doc1.contributors.filter(id=self.user.id).exists())
        self.assertTrue(doc1.contributors.filter(id=self.group_user1.id).exists())
        self.assertTrue(doc1.contributors.filter(id=self.group_user2.id).exists())

        self.assertFalse(doc2.contributors.filter(id=self.user.id).exists())
        self.assertTrue(doc2.contributors.filter(id=other_contributor.id).exists())
        self.assertFalse(doc2.contributors.filter(id=self.group_user1.id).exists())

        self.assertTrue(doc3.contributors.filter(id=other_contributor.id).exists())
        self.assertEqual(doc3.contributors.count(), 1)

    def test_anonymize_votes(self):
        """Test that revision votes are anonymized."""
        v1 = HelpfulVoteFactory(creator=self.user)
        v2 = HelpfulVoteFactory(creator=UserFactory())

        self.listener.on_user_deletion(self.user)

        v1.refresh_from_db()
        v2.refresh_from_db()

        self.assertIs(v1.creator, None)
        self.assertTrue(v1.anonymous_id)
        # The rest should remain untouched.
        self.assertTrue(v2.creator)
        self.assertFalse(v2.anonymous_id)

    def test_non_approved_revision_handling(self):
        """Test handling of non-approved revisions when a user is deleted."""
        doc_to_delete = DocumentFactory(current_revision=None)
        RevisionFactory(document=doc_to_delete, creator=self.user, is_approved=False)

        doc_to_keep = DocumentFactory()
        other_user = UserFactory()
        approved_rev = RevisionFactory(document=doc_to_keep, creator=other_user, is_approved=True)
        doc_to_keep.current_revision = approved_rev
        doc_to_keep.save()
        non_approved_rev = RevisionFactory(
            document=doc_to_keep, creator=self.user, is_approved=False
        )

        doc_to_reassign = DocumentFactory()
        approved_user_rev = RevisionFactory(
            document=doc_to_reassign, creator=self.user, is_approved=True
        )
        doc_to_reassign.current_revision = approved_user_rev
        doc_to_reassign.save()

        self.listener.on_user_deletion(self.user)

        self.assertFalse(Document.objects.filter(id=doc_to_delete.id).exists())

        self.assertTrue(Document.objects.filter(id=doc_to_keep.id).exists())
        doc_to_keep.refresh_from_db()

        self.assertTrue(Revision.objects.filter(id=approved_rev.id).exists())

        self.assertFalse(Revision.objects.filter(id=non_approved_rev.id).exists())

        self.assertTrue(Document.objects.filter(id=doc_to_reassign.id).exists())
        doc_to_reassign.refresh_from_db()
        self.assertEqual(
            doc_to_reassign.current_revision.creator.username, settings.SUMO_BOT_USERNAME
        )
