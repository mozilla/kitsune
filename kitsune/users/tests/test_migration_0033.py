from django.contrib.auth.models import User
from django.test import TestCase
from django.db.models import Q

from kitsune.questions.tests import (
    AnswerFactory,
    QuestionFactory,
    QuestionVoteFactory,
    AnswerVoteFactory,
)
from kitsune.users.tests import ProfileFactory
from kitsune.wiki.tests import RevisionFactory
from kitsune.messages.models import InboxMessage, OutboxMessage
from kitsune.gallery.tests import ImageFactory, VideoFactory
from kitsune.forums.tests import ThreadFactory, PostFactory


class TestDeleteNonMigratedUsersMigrationQuery(TestCase):
    """Test the migration that deletes non-migrated users."""

    def setUp(self):
        # Create users with different combinations of migration status and content creation

        # Case 1: Non-migrated user with no content (should be deleted)
        ProfileFactory(user__username="user1", is_fxa_migrated=False)

        # Case 2: Non-migrated user with a question (should be kept)
        user2 = ProfileFactory(user__username="user2", is_fxa_migrated=False).user
        QuestionFactory(creator=user2)

        # Case 3: Non-migrated user with an answer (should be kept)
        user3 = ProfileFactory(user__username="user3", is_fxa_migrated=False).user
        AnswerFactory(creator=user3)

        # Case 4: Non-migrated user with a revision (should be kept)
        user4 = ProfileFactory(user__username="user4", is_fxa_migrated=False).user
        RevisionFactory(creator=user4)

        # Case 5: Migrated user with no content (should be kept)
        ProfileFactory(user__username="user5", is_fxa_migrated=True)

        # Case 6: Non-migrated user with a question vote (should be kept)
        user6 = ProfileFactory(user__username="user6", is_fxa_migrated=False).user
        QuestionVoteFactory(creator=user6)

        # Case 7: Non-migrated user with an answer vote (should be kept)
        user7 = ProfileFactory(user__username="user7", is_fxa_migrated=False).user
        AnswerVoteFactory(creator=user7)

        # Case 8: Non-migrated user who is a sender of inbox messages (should be kept)
        user8 = ProfileFactory(user__username="user8", is_fxa_migrated=False).user
        InboxMessage.objects.create(to=user2, sender=user8, message="test")

        # Case 9: Non-migrated user with an outbox message (should be kept)
        user9 = ProfileFactory(user__username="user9", is_fxa_migrated=False).user
        outbox_msg = OutboxMessage.objects.create(sender=user9, message="test")
        outbox_msg.to.add(user2)

        # Case 10: Non-migrated user who is a sender of inbox messages (should be kept)
        user10 = ProfileFactory(user__username="user10", is_fxa_migrated=False).user
        InboxMessage.objects.create(to=user2, sender=user10, message="test")

        # Case 11: Non-migrated user with a gallery image (should be kept)
        user11 = ProfileFactory(user__username="user11", is_fxa_migrated=False).user
        ImageFactory(creator=user11)

        # Case 12: Non-migrated user with a gallery video (should be kept)
        user12 = ProfileFactory(user__username="user12", is_fxa_migrated=False).user
        VideoFactory(creator=user12)

        # Case 13: Non-migrated user with a forum thread (should be kept)
        user13 = ProfileFactory(user__username="user13", is_fxa_migrated=False).user
        ThreadFactory(creator=user13)

        # Case 14: Non-migrated user with a forum post (should be kept)
        user14 = ProfileFactory(user__username="user14", is_fxa_migrated=False).user
        thread = ThreadFactory()
        PostFactory(thread=thread, author=user14)

        # Case 15: Non-migrated user who reviewed a revision (should be kept)
        user15 = ProfileFactory(user__username="user15", is_fxa_migrated=False).user
        RevisionFactory(reviewer=user15)

    def test_direct_query_logic(self):
        """Test the query logic of the migration directly without going through apps."""
        # Query using the same logic as the migration but with direct model references
        users_to_delete = User.objects.filter(profile__is_fxa_migrated=False).exclude(
            Q(answer_votes__isnull=False)
            | Q(answers__isnull=False)
            | Q(award_creator__isnull=False)
            | Q(badge__isnull=False)
            | Q(created_revisions__isnull=False)
            | Q(gallery_images__isnull=False)
            | Q(gallery_videos__isnull=False)
            | Q(inboxmessage__isnull=False)
            | Q(outbox__isnull=False)
            | Q(poll_votes__isnull=False)
            | Q(post__isnull=False)
            | Q(question_votes__isnull=False)
            | Q(questions__isnull=False)
            | Q(readied_for_l10n_revisions__isnull=False)
            | Q(reviewed_revisions__isnull=False)
            | Q(thread__isnull=False)
            | Q(wiki_post_set__isnull=False)
            | Q(wiki_thread_set__isnull=False)
        )

        # Only user1 should be in this queryset
        self.assertEqual(users_to_delete.count(), 1)
        self.assertEqual(users_to_delete.first().username, "user1")
