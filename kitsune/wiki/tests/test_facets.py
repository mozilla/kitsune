from django.contrib.auth.models import AnonymousUser

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
        self.staff = UserFactory(is_staff=True)
        self.anonymous = AnonymousUser()

        # Create products
        self.desktop = ProductFactory(slug="firefox")
        self.mobile = ProductFactory(slug="mobile")

        # Create topics
        self.general_d = TopicFactory(product=self.desktop, slug="general")
        self.bookmarks_d = TopicFactory(product=self.desktop, slug="bookmarks")
        self.sync_d = TopicFactory(product=self.desktop, slug="sync")
        self.general_m = TopicFactory(product=self.mobile, slug="general")
        self.bookmarks_m = TopicFactory(product=self.mobile, slug="bookmarks")
        self.sync_m = TopicFactory(product=self.mobile, slug="sync")

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
        doc3 = DocumentFactory(
            is_archived=True, products=[self.desktop], topics=[self.general_d, self.bookmarks_d]
        )
        ApprovedRevisionFactory(document=doc3)

        # A template article shouldn't show up either.
        doc4 = TemplateDocumentFactory(
            products=[self.desktop], topics=[self.general_d, self.bookmarks_d]
        )
        ApprovedRevisionFactory(document=doc4)

        # An article without a current revision shouldn't show up either.
        doc5 = DocumentFactory(
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
        RevisionFactory(is_approved=False, document=doc5)

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
            self.assertEqual([d["id"] for d in docs], [self.doc1.id])

        with self.subTest("documents_for-general_bookmarks-user1"):
            docs = _documents_for(
                self.user1, locale="en-US", topics=[self.general_d, self.bookmarks_d]
            )
            self.assertEqual([d["id"] for d in docs], [self.doc1.id, self.doc6.id, self.doc7.id])

        with self.subTest("documents_for-general_bookmarks-user2"):
            docs = _documents_for(
                self.user2, locale="en-US", topics=[self.general_d, self.bookmarks_d]
            )
            self.assertEqual([d["id"] for d in docs], [self.doc1.id, self.doc7.id, self.doc8.id])

        with self.subTest("documents_for-general_bookmarks-staff"):
            docs = _documents_for(
                self.staff, locale="en-US", topics=[self.general_d, self.bookmarks_d]
            )
            self.assertEqual(
                [d["id"] for d in docs],
                [self.doc1.id, self.doc6.id, self.doc7.id, self.doc8.id],
            )

        with self.subTest("documents_for-general_bookmarks_sync_localized-anon"):
            docs = _documents_for(
                self.anonymous, locale="de", topics=[self.general_d, self.bookmarks_d]
            )
            self.assertEqual([d["id"] for d in docs], [self.doc1_localized.id])

        with self.subTest("documents_for-general_bookmarks_sync_localized-user1"):
            docs = _documents_for(
                self.user1, locale="de", topics=[self.general_d, self.bookmarks_d]
            )
            self.assertEqual([d["id"] for d in docs], [self.doc1_localized.id])

        with self.subTest("documents_for-general_bookmarks_sync_localized-user2"):
            docs = _documents_for(
                self.user2, locale="de", topics=[self.general_d, self.bookmarks_d]
            )
            self.assertEqual(
                [d["id"] for d in docs], [self.doc1_localized.id, self.doc8_localized.id]
            )

        with self.subTest("documents_for-general_bookmarks_sync_localized-staff"):
            docs = _documents_for(
                self.staff, locale="de", topics=[self.general_d, self.bookmarks_d]
            )
            self.assertEqual(
                [d["id"] for d in docs], [self.doc1_localized.id, self.doc8_localized.id]
            )

        with self.subTest("documents_for-general_sync-anon"):
            docs = _documents_for(
                self.anonymous, locale="en-US", topics=[self.general_d, self.sync_d]
            )
            self.assertEqual(len(docs), 0)

        with self.subTest("documents_for-general_sync-user1"):
            docs = _documents_for(self.user1, locale="en-US", topics=[self.general_d, self.sync_d])
            self.assertEqual([d["id"] for d in docs], [self.doc6.id, self.doc7.id])

        with self.subTest("documents_for-general_sync-user2"):
            docs = _documents_for(self.user2, locale="en-US", topics=[self.general_d, self.sync_d])
            self.assertEqual([d["id"] for d in docs], [self.doc7.id, self.doc8.id])

        with self.subTest("documents_for-general_sync-staff"):
            docs = _documents_for(self.staff, locale="en-US", topics=[self.general_d, self.sync_d])
            self.assertEqual([d["id"] for d in docs], [self.doc6.id, self.doc7.id, self.doc8.id])

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
            self.assertEqual([d["id"] for d in fallbacks], [self.doc1.id])

        with self.subTest("documents_for_fallback-user2"):
            docs, fallbacks = documents_for(
                self.user2, locale="de", topics=[self.general_d, self.bookmarks_d]
            )
            self.assertEqual(
                [d["id"] for d in docs], [self.doc1_localized.id, self.doc8_localized.id]
            )
            self.assertEqual([d["id"] for d in fallbacks], [self.doc7.id])

        with self.subTest("documents_for_fallback-staff"):
            docs, fallbacks = documents_for(self.staff, locale="de", topics=[self.general_d])
            self.assertEqual(
                [d["id"] for d in docs], [self.doc1_localized.id, self.doc8_localized.id]
            )
            self.assertEqual([d["id"] for d in fallbacks], [self.doc6.id, self.doc7.id])
