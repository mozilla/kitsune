from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache

from kitsune.products.tests import ProductFactory, TopicFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import GroupFactory, UserFactory
from kitsune.wiki.facets import _documents_for, documents_for, topics_for
from kitsune.wiki.tests import (
    ApprovedRevisionFactory,
    DocumentFactory,
    RevisionFactory,
    TemplateDocumentFactory,
)


class TestFacetHelpers(TestCase):
    def setUp(self):
        super(TestFacetHelpers, self).setUp()
        # Groups and users
        self.group1 = GroupFactory(name="group1")
        self.group2 = GroupFactory(name="group2")
        self.group3 = GroupFactory(name="group3")
        self.group4 = GroupFactory(name="group4")
        self.user1 = UserFactory(groups=[self.group1, self.group4])
        self.user2 = UserFactory(groups=[self.group2, self.group3])
        self.staff = UserFactory(groups=[GroupFactory(name=settings.STAFF_GROUP)])
        self.anonymous = AnonymousUser()

        # Create products
        self.desktop = ProductFactory(slug="firefox")
        self.mobile = ProductFactory(slug="mobile")

        # Create topics
        self.general_d = TopicFactory(products=[self.desktop], slug="general")
        self.bookmarks_d = TopicFactory(products=[self.desktop], slug="bookmarks")
        self.sync_d = TopicFactory(products=[self.desktop], slug="sync")
        self.general_m = TopicFactory(products=[self.mobile], slug="general")
        self.bookmarks_m = TopicFactory(products=[self.mobile], slug="bookmarks")
        self.sync_m = TopicFactory(products=[self.mobile], slug="sync")

        # Set up documents.
        self.doc1 = DocumentFactory(
            products=[self.desktop], topics=[self.general_d, self.bookmarks_d]
        )
        doc1_revision = ApprovedRevisionFactory(document=self.doc1, is_ready_for_localization=True)

        self.doc1_localized = DocumentFactory(
            locale="de",
            products=[self.desktop],
            topics=[self.general_d, self.bookmarks_d],
            parent=self.doc1,
        )
        ApprovedRevisionFactory(document=self.doc1_localized, based_on=doc1_revision)

        self.doc2 = DocumentFactory(
            display_order=2,
            products=[self.desktop, self.mobile],
            topics=[self.bookmarks_d, self.bookmarks_m, self.sync_d, self.sync_m],
        )
        ApprovedRevisionFactory(document=self.doc2)

        # An archived article shouldn't show up.
        self.doc3 = DocumentFactory(
            is_archived=True, products=[self.desktop], topics=[self.general_d, self.bookmarks_d]
        )
        ApprovedRevisionFactory(document=self.doc3)

        # A template article shouldn't show up either.
        self.doc4 = TemplateDocumentFactory(
            products=[self.desktop], topics=[self.general_d, self.bookmarks_d]
        )
        ApprovedRevisionFactory(document=self.doc4)

        # An article without a current revision shouldn't show up either.
        self.doc5 = DocumentFactory(
            products=[self.desktop, self.mobile],
            topics=[
                self.general_d,
                self.bookmarks_d,
                self.sync_d,
                self.general_m,
                self.bookmarks_m,
                self.sync_m,
            ],
        )
        RevisionFactory(is_approved=False, document=self.doc5)

        # An article restricted to members of "group1".
        self.doc6 = DocumentFactory(
            display_order=3,
            restrict_to_groups=[self.group1],
            products=[self.desktop, self.mobile],
            topics=[
                self.general_d,
                self.bookmarks_d,
                self.sync_d,
                self.general_m,
                self.bookmarks_m,
                self.sync_m,
            ],
        )
        ApprovedRevisionFactory(document=self.doc6)

        # An article restricted to members of "group2" and "group4".
        self.doc7 = DocumentFactory(
            display_order=4,
            restrict_to_groups=[self.group2, self.group4],
            products=[self.desktop, self.mobile],
            topics=[
                self.general_d,
                self.bookmarks_d,
                self.sync_d,
                self.general_m,
                self.bookmarks_m,
                self.sync_m,
            ],
        )
        ApprovedRevisionFactory(document=self.doc7)

        # An article restricted to members of "group2" and "group3".
        self.doc8 = DocumentFactory(
            display_order=5,
            restrict_to_groups=[self.group2, self.group3],
            products=[self.desktop, self.mobile],
            topics=[
                self.general_d,
                self.bookmarks_d,
                self.sync_d,
                self.general_m,
                self.bookmarks_m,
                self.sync_m,
            ],
        )
        doc8_revision = ApprovedRevisionFactory(document=self.doc8, is_ready_for_localization=True)

        self.doc8_localized = DocumentFactory(
            locale="de",
            parent=self.doc8,
            products=[self.desktop, self.mobile],
            topics=[
                self.general_d,
                self.bookmarks_d,
                self.sync_d,
                self.general_m,
                self.bookmarks_m,
                self.sync_m,
            ],
        )
        ApprovedRevisionFactory(document=self.doc8_localized, based_on=doc8_revision)

    def test_topics_for_products(self):
        """Verify topics_for() returns topics for passed products."""
        desktop_topics = topics_for(self.anonymous, product=self.desktop)
        self.assertEqual(
            set(t.slug for t in desktop_topics),
            set((self.general_d.slug, self.bookmarks_d.slug, self.sync_d.slug)),
        )

        mobile_topics = topics_for(self.anonymous, product=self.mobile)
        self.assertEqual(
            set(t.slug for t in mobile_topics),
            set((self.bookmarks_m.slug, self.sync_m.slug)),
        )

        for user in (self.user1, self.user2, self.staff):
            mobile_topics = topics_for(user, product=self.mobile)
            self.assertEqual(
                set(t.slug for t in mobile_topics),
                set((self.general_m.slug, self.bookmarks_m.slug, self.sync_m.slug)),
            )

    def test_documents_for(self):
        """Verify documents_for() returns documents for passed topics."""
        with self.subTest("documents_for-general-anon"):
            docs = _documents_for(self.anonymous, locale="en-US", topics=[self.general_d])
            self.assertEqual([d["id"] for d in docs], [self.doc1.id])

        with self.subTest("documents_for-general-user1"):
            docs = _documents_for(self.user1, locale="en-US", topics=[self.general_d])
            self.assertEqual([d["id"] for d in docs], [self.doc1.id, self.doc6.id, self.doc7.id])

        with self.subTest("documents_for-general-user2"):
            docs = _documents_for(self.user2, locale="en-US", topics=[self.general_d])
            self.assertEqual([d["id"] for d in docs], [self.doc1.id, self.doc7.id, self.doc8.id])

        with self.subTest("documents_for-general-staff"):
            docs = _documents_for(self.staff, locale="en-US", topics=[self.general_d])
            self.assertEqual(
                [d["id"] for d in docs],
                [self.doc1.id, self.doc6.id, self.doc7.id, self.doc8.id],
            )

        with self.subTest("documents_for-bookmarks-anon"):
            docs = _documents_for(self.anonymous, locale="en-US", topics=[self.bookmarks_d])
            self.assertEqual([d["id"] for d in docs], [self.doc1.id, self.doc2.id])

        with self.subTest("documents_for-bookmarks-user1"):
            docs = _documents_for(self.user1, locale="en-US", topics=[self.bookmarks_d])
            self.assertEqual(
                [d["id"] for d in docs], [self.doc1.id, self.doc2.id, self.doc6.id, self.doc7.id]
            )

        with self.subTest("documents_for-bookmarks-user2"):
            docs = _documents_for(self.user2, locale="en-US", topics=[self.bookmarks_d])
            self.assertEqual(
                [d["id"] for d in docs], [self.doc1.id, self.doc2.id, self.doc7.id, self.doc8.id]
            )

        with self.subTest("documents_for-bookmarks-staff"):
            docs = _documents_for(self.staff, locale="en-US", topics=[self.bookmarks_d])
            self.assertEqual(
                [d["id"] for d in docs],
                [self.doc1.id, self.doc2.id, self.doc6.id, self.doc7.id, self.doc8.id],
            )

        with self.subTest("documents_for-sync-anon"):
            docs = _documents_for(self.anonymous, locale="en-US", topics=[self.sync_d])
            self.assertEqual([d["id"] for d in docs], [self.doc2.id])

        with self.subTest("documents_for-sync-user1"):
            docs = _documents_for(self.user1, locale="en-US", topics=[self.sync_d])
            self.assertEqual([d["id"] for d in docs], [self.doc2.id, self.doc6.id, self.doc7.id])

        with self.subTest("documents_for-sync-user2"):
            docs = _documents_for(self.user2, locale="en-US", topics=[self.sync_d])
            self.assertEqual([d["id"] for d in docs], [self.doc2.id, self.doc7.id, self.doc8.id])

        with self.subTest("documents_for-sync-staff"):
            docs = _documents_for(self.staff, locale="en-US", topics=[self.sync_d])
            self.assertEqual(
                [d["id"] for d in docs],
                [self.doc2.id, self.doc6.id, self.doc7.id, self.doc8.id],
            )

        with self.subTest("documents_for-general_bookmarks-anon"):
            docs = _documents_for(
                self.anonymous, locale="en-US", topics=[self.general_d, self.bookmarks_d]
            )
            self.assertEqual([d["id"] for d in docs], [self.doc1.id, self.doc2.id])

        with self.subTest("documents_for-general_bookmarks-user1"):
            docs = _documents_for(
                self.user1, locale="en-US", topics=[self.general_d, self.bookmarks_d]
            )
            self.assertEqual(
                [d["id"] for d in docs], [self.doc1.id, self.doc2.id, self.doc6.id, self.doc7.id]
            )

        with self.subTest("documents_for-general_bookmarks-user2"):
            docs = _documents_for(
                self.user2, locale="en-US", topics=[self.general_d, self.bookmarks_d]
            )
            self.assertEqual(
                [d["id"] for d in docs], [self.doc1.id, self.doc2.id, self.doc7.id, self.doc8.id]
            )

        with self.subTest("documents_for-general_bookmarks-staff"):
            docs = _documents_for(
                self.staff, locale="en-US", topics=[self.general_d, self.bookmarks_d]
            )
            self.assertEqual(
                [d["id"] for d in docs],
                [self.doc1.id, self.doc2.id, self.doc6.id, self.doc7.id, self.doc8.id],
            )

        with self.subTest("documents_for-general_bookmarks_sync_localized-anon"):
            docs = _documents_for(
                self.anonymous, locale="en-US", topics=[self.general_d, self.bookmarks_d]
            )
            self.assertIn(self.doc1.id, [d["id"] for d in docs])
            self.assertIn(self.doc2.id, [d["id"] for d in docs])

        with self.subTest("documents_for-general_bookmarks_sync_localized-user1"):
            docs = _documents_for(
                self.user1, locale="en-US", topics=[self.general_d, self.bookmarks_d]
            )
            doc_ids = [d["id"] for d in docs]
            self.assertIn(self.doc1.id, doc_ids)
            self.assertIn(self.doc2.id, doc_ids)
            self.assertIn(self.doc6.id, doc_ids)
            self.assertIn(self.doc7.id, doc_ids)

        with self.subTest("documents_for-general_bookmarks_sync_localized-user2"):
            docs = _documents_for(
                self.user2, locale="en-US", topics=[self.general_d, self.bookmarks_d]
            )
            doc_ids = [d["id"] for d in docs]
            self.assertIn(self.doc1.id, doc_ids)
            self.assertIn(self.doc2.id, doc_ids)
            self.assertIn(self.doc7.id, doc_ids)
            self.assertIn(self.doc8.id, doc_ids)

        with self.subTest("documents_for-general_bookmarks_sync_localized-staff"):
            docs = _documents_for(
                self.staff, locale="en-US", topics=[self.general_d, self.bookmarks_d]
            )
            doc_ids = [d["id"] for d in docs]
            self.assertIn(self.doc1.id, doc_ids)
            self.assertIn(self.doc2.id, doc_ids)
            self.assertIn(self.doc6.id, doc_ids)
            self.assertIn(self.doc7.id, doc_ids)
            self.assertIn(self.doc8.id, doc_ids)

        with self.subTest("documents_for-general_sync-anon"):
            docs = _documents_for(self.anonymous, locale="en-US", topics=[self.sync_d])
            self.assertEqual([d["id"] for d in docs], [self.doc2.id])

        with self.subTest("documents_for-general_sync-user1"):
            docs = _documents_for(self.user1, locale="en-US", topics=[self.general_d, self.sync_d])
            self.assertEqual(
                [d["id"] for d in docs], [self.doc1.id, self.doc2.id, self.doc6.id, self.doc7.id]
            )

        with self.subTest("documents_for-general_sync-user2"):
            docs = _documents_for(self.user2, locale="en-US", topics=[self.sync_d])
            self.assertEqual([d["id"] for d in docs], [self.doc2.id, self.doc7.id, self.doc8.id])

        with self.subTest("documents_for-general_sync-staff"):
            docs = _documents_for(self.staff, locale="en-US", topics=[self.general_d, self.sync_d])
            self.assertEqual(
                [d["id"] for d in docs],
                [self.doc1.id, self.doc2.id, self.doc6.id, self.doc7.id, self.doc8.id],
            )

    def test_documents_for_caching_1(self):
        """
        Ensure that when we exclude a document, it doesn't affect the result when
        we don't. Note that the cache is automatically cleared between tests.
        """
        docs, _ = documents_for(
            self.anonymous, locale="en-US", topics=[self.bookmarks_d], current_document=self.doc1
        )
        self.assertEqual([d["id"] for d in docs], [self.doc2.id])
        docs, _ = documents_for(self.anonymous, locale="en-US", topics=[self.bookmarks_d])
        self.assertEqual([d["id"] for d in docs], [self.doc1.id, self.doc2.id])

    def test_documents_for_caching_2(self):
        """
        Ensure that when we don't exclude a document, it doesn't affect the result
        when we do. Note that the cache is automatically cleared between tests.
        """
        docs, _ = documents_for(self.anonymous, locale="en-US", topics=[self.bookmarks_d])
        self.assertEqual([d["id"] for d in docs], [self.doc1.id, self.doc2.id])
        docs, _ = documents_for(
            self.anonymous, locale="en-US", topics=[self.bookmarks_d], current_document=self.doc1
        )
        self.assertEqual([d["id"] for d in docs], [self.doc2.id])

    def test_exclude_localized_parent_document(self):
        """
        Test for when we exclude the parent of a localized document.
        """
        with self.subTest("exclude_localized_parent_document-anon"):
            docs, _ = documents_for(
                self.anonymous, locale="de", topics=[self.bookmarks_d], current_document=self.doc1
            )
            self.assertEqual([d["id"] for d in docs], [self.doc1_localized.id])

        with self.subTest("exclude_localized_parent_document-staff"):
            docs, _ = documents_for(
                self.staff, locale="de", topics=[self.bookmarks_d], current_document=self.doc1
            )
            self.assertEqual(
                [d["id"] for d in docs], [self.doc1_localized.id, self.doc8_localized.id]
            )

    def test_exclude_localized_document(self):
        """
        Ensure that when we exclude a localized document, its parent is excluded too.
        """
        with self.subTest("exclude_localized_document-anon"):
            docs, _ = documents_for(
                self.anonymous,
                locale="de",
                topics=[self.bookmarks_d],
                current_document=self.doc1_localized,
            )
            self.assertEqual(len(docs), 0)

        with self.subTest("exclude_localized_document-user2"):
            docs, _ = documents_for(
                self.user2,
                locale="de",
                topics=[self.bookmarks_d],
                current_document=self.doc1_localized,
            )
            self.assertEqual([d["id"] for d in docs], [self.doc8_localized.id])

    def test_documents_for_fallback(self):
        """Verify the fallback in documents_for."""
        with self.subTest("documents_for_fallback-anon"):
            docs, fallbacks = documents_for(
                self.anonymous, locale="es", topics=[self.general_d, self.bookmarks_d]
            )
            self.assertEqual(len(docs), 0)
            self.assertEqual([d["id"] for d in fallbacks], [self.doc1.id, self.doc2.id])

        with self.subTest("documents_for_fallback-user2"):
            docs, fallbacks = documents_for(
                self.user2, locale="de", topics=[self.general_d, self.bookmarks_d]
            )
            self.assertEqual(
                [d["id"] for d in docs], [self.doc1_localized.id, self.doc8_localized.id]
            )
            self.assertEqual([d["id"] for d in fallbacks], [self.doc2.id, self.doc7.id])

        with self.subTest("documents_for_fallback-staff"):
            docs, fallbacks = documents_for(self.staff, locale="de", topics=[self.general_d])
            self.assertEqual(
                [d["id"] for d in docs], [self.doc1_localized.id, self.doc8_localized.id]
            )
            self.assertEqual([d["id"] for d in fallbacks], [self.doc6.id, self.doc7.id])

    def test_topic_change_with_translations(self):
        """Test that when a parent document's topics change, the child translations
        appear in the correct topic listings.

        This test demonstrates the correct behavior where translated documents only
        appear in topic listings based on their parent's topics.
        """
        # Create a parent document in en-US with the first topic
        privacy_topic = TopicFactory(products=[self.desktop], slug="privacy")
        billing_topic = TopicFactory(products=[self.desktop], slug="billing")

        parent_doc = DocumentFactory(products=[self.desktop], topics=[privacy_topic])
        parent_revision = ApprovedRevisionFactory(
            document=parent_doc, is_ready_for_localization=True
        )

        # Create a child translation in a different locale
        child_doc = DocumentFactory(locale="fr", parent=parent_doc)
        ApprovedRevisionFactory(document=child_doc, based_on=parent_revision)

        # Verify the child document appears in the privacy topic listing
        docs_privacy_fr = _documents_for(self.anonymous, locale="fr", topics=[privacy_topic])
        self.assertEqual(len(docs_privacy_fr), 1)
        self.assertEqual(docs_privacy_fr[0]["id"], child_doc.id)

        # Verify the child document doesn't appear in the billing topic listing
        docs_billing_fr = _documents_for(self.anonymous, locale="fr", topics=[billing_topic])
        self.assertEqual(len(docs_billing_fr), 0)

        # Change the parent document's topic
        parent_doc.topics.remove(privacy_topic)
        parent_doc.topics.add(billing_topic)

        # Clear any caches that might interfere with the test
        cache.clear()

        # EXPECTED BEHAVIOR: The child document should now appear in the billing topic listing
        docs_billing_fr_after = _documents_for(self.anonymous, locale="fr", topics=[billing_topic])
        self.assertEqual(len(docs_billing_fr_after), 1)
        self.assertEqual(docs_billing_fr_after[0]["id"], child_doc.id)

        # EXPECTED BEHAVIOR: The child document should no longer appear
        # in the privacy topic listing
        docs_privacy_fr_after = _documents_for(self.anonymous, locale="fr", topics=[privacy_topic])
        self.assertEqual(len(docs_privacy_fr_after), 0)

    def test_documents_for_with_topic_change(self):
        """Test the full documents_for function with topic changes in parent docs.

        This test confirms that translated documents correctly follow their parent's
        topics in the public documents_for function.
        """
        # Create a parent document in en-US with the first topic
        privacy_topic = TopicFactory(products=[self.desktop], slug="privacy")
        billing_topic = TopicFactory(products=[self.desktop], slug="billing")

        parent_doc = DocumentFactory(products=[self.desktop], topics=[privacy_topic])
        parent_revision = ApprovedRevisionFactory(
            document=parent_doc, is_ready_for_localization=True
        )

        # Create a child translation in a different locale
        child_doc = DocumentFactory(locale="fr", parent=parent_doc)
        ApprovedRevisionFactory(document=child_doc, based_on=parent_revision)

        # Test with the public documents_for function
        # Verify the child document appears in the privacy topic listing
        docs_fr, fallbacks = documents_for(
            self.anonymous, locale="fr", topics=[privacy_topic], products=[self.desktop]
        )
        doc_ids = [d["id"] for d in docs_fr]
        self.assertIn(child_doc.id, doc_ids)

        # Verify the child document doesn't appear in the billing topic listing
        docs_fr, fallbacks = documents_for(
            self.anonymous, locale="fr", topics=[billing_topic], products=[self.desktop]
        )
        doc_ids = [d["id"] for d in docs_fr]
        self.assertNotIn(child_doc.id, doc_ids)

        # Change the parent document's topic
        parent_doc.topics.remove(privacy_topic)
        parent_doc.topics.add(billing_topic)

        # Clear any caches that might interfere with the test
        cache.clear()

        # EXPECTED BEHAVIOR: The child document should now appear in the billing topic listing
        docs_fr, fallbacks = documents_for(
            self.anonymous, locale="fr", topics=[billing_topic], products=[self.desktop]
        )
        doc_ids = [d["id"] for d in docs_fr]
        self.assertIn(child_doc.id, doc_ids)

        # EXPECTED BEHAVIOR: The child document should no longer appear in the
        # privacy topic listing
        docs_fr, fallbacks = documents_for(
            self.anonymous, locale="fr", topics=[privacy_topic], products=[self.desktop]
        )
        doc_ids = [d["id"] for d in docs_fr]
        self.assertNotIn(child_doc.id, doc_ids)
