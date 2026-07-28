"""Task 3 — shared content exclusions, retrieval eligibility predicates, access metadata.

The security-critical guarantee here is that the bulk ``eligible_documents()`` queryset
selects exactly the documents for which the object predicate ``is_retrieval_indexable``
is true, so incremental, backfill, and reconciliation paths cannot diverge.
"""

from kitsune.products.tests import ProductFactory, TopicFactory
from kitsune.retrieval.eligibility import (
    access_group_ids_for,
    eligible_documents,
    family_document_ids,
    family_documents,
    family_id_for,
    is_publicly_accessible,
    is_retrieval_content_eligible,
    is_retrieval_indexable,
    visibility_for,
)
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import GroupFactory
from kitsune.wiki.config import (
    ADMINISTRATION_CATEGORY,
    CANNED_RESPONSES_CATEGORY,
    REDIRECT_HTML,
    TROUBLESHOOTING_CATEGORY,
)
from kitsune.wiki.indexing import is_indexable_content, is_public_indexing_allowed
from kitsune.wiki.models import Document
from kitsune.wiki.tests import (
    ApprovedRevisionFactory,
    DocumentFactory,
    TemplateDocumentFactory,
)


def _reload(doc):
    # is_restricted is a cached_property and the current_revision/category can be
    # set through save() side effects, so always assert against fresh DB state.
    return Document.objects.get(pk=doc.pk)


def _approved(**kwargs):
    doc = DocumentFactory(**kwargs)
    ApprovedRevisionFactory(document=doc)
    return _reload(doc)


def _translation(parent, locale="de", *, approved=True):
    doc = DocumentFactory(parent=parent, locale=locale)
    if approved:
        ApprovedRevisionFactory(document=doc)
    return _reload(doc)


def _make_redirect(doc):
    # html is editable=False and normally produced by rendering; set it directly so
    # the predicate sees the exact REDIRECT_HTML prefix it checks.
    Document.objects.filter(pk=doc.pk).update(html=REDIRECT_HTML + '<a href="/x">x</a></p>')
    return _reload(doc)


def _stale_template_translation(*, approved=True):
    """Reproduce the real stale ``is_template`` row created by parent propagation."""
    parent = TemplateDocumentFactory()
    translation = TemplateDocumentFactory(parent=parent, locale="de")
    if approved:
        ApprovedRevisionFactory(document=translation)

    parent.title = "Former template"
    parent.category = TROUBLESHOOTING_CATEGORY
    parent.save()
    return _reload(translation)


class SharedContentExclusionsTests(TestCase):
    """``is_indexable_content`` / ``is_public_indexing_allowed`` in wiki.indexing."""

    def test_normal_document_is_indexable_content(self):
        self.assertTrue(is_indexable_content(_approved()))

    def test_is_indexable_content_is_revision_agnostic(self):
        # No current revision, but still indexable *content*; the revision gate
        # lives in the retrieval predicate, not the shared rule.
        self.assertTrue(is_indexable_content(DocumentFactory()))

    def test_is_indexable_content_is_access_agnostic(self):
        restricted = DocumentFactory(restrict_to_groups=[GroupFactory()])
        self.assertTrue(is_indexable_content(_reload(restricted)))

    def test_redirect_is_not_indexable_content(self):
        self.assertFalse(is_indexable_content(_make_redirect(_approved())))

    def test_redirect_marker_is_allowed_when_not_at_the_start(self):
        doc = _approved()
        Document.objects.filter(pk=doc.pk).update(html=f"<p>Prefix</p>{REDIRECT_HTML}")
        self.assertTrue(is_indexable_content(_reload(doc)))

    def test_template_is_not_indexable_content(self):
        self.assertFalse(is_indexable_content(_reload(TemplateDocumentFactory())))

    def test_archived_is_not_indexable_content(self):
        self.assertFalse(is_indexable_content(_reload(DocumentFactory(is_archived=True))))

    def test_translation_inherits_archived_exclusion(self):
        parent = DocumentFactory(is_archived=True)
        translation = _translation(_reload(parent))
        self.assertTrue(translation.is_archived)
        self.assertFalse(is_indexable_content(translation))

    def test_canned_response_category_is_not_indexable_content(self):
        doc = DocumentFactory(category=CANNED_RESPONSES_CATEGORY)
        self.assertFalse(is_indexable_content(_reload(doc)))

    def test_administration_category_is_not_indexable_content(self):
        doc = DocumentFactory(category=ADMINISTRATION_CATEGORY)
        self.assertFalse(is_indexable_content(_reload(doc)))

    def test_parent_category_propagation_leaves_stale_template_translation_fail_closed(self):
        translation = _stale_template_translation()
        self.assertTrue(translation.is_template)
        self.assertEqual(translation.category, TROUBLESHOOTING_CATEGORY)
        self.assertFalse(is_indexable_content(translation))

    def test_public_indexing_allowed_for_normal_document(self):
        self.assertTrue(is_public_indexing_allowed(_approved()))

    def test_public_indexing_not_allowed_when_restricted(self):
        restricted = DocumentFactory(restrict_to_groups=[GroupFactory()])
        ApprovedRevisionFactory(document=restricted)
        self.assertFalse(is_public_indexing_allowed(_reload(restricted)))

    def test_public_indexing_not_allowed_when_excluded_content(self):
        self.assertFalse(is_public_indexing_allowed(_reload(TemplateDocumentFactory())))


class RetrievalPredicateTests(TestCase):
    """The three retrieval predicates in retrieval.eligibility."""

    def test_content_eligible_requires_current_revision(self):
        self.assertFalse(is_retrieval_content_eligible(DocumentFactory()))
        self.assertTrue(is_retrieval_content_eligible(_approved()))

    def test_content_eligible_is_access_agnostic(self):
        restricted = DocumentFactory(restrict_to_groups=[GroupFactory()])
        ApprovedRevisionFactory(document=restricted)
        self.assertTrue(is_retrieval_content_eligible(_reload(restricted)))

    def test_content_eligible_excludes_content_type_exclusions(self):
        template = TemplateDocumentFactory()
        ApprovedRevisionFactory(document=template)
        self.assertFalse(is_retrieval_content_eligible(_reload(template)))

    def test_publicly_accessible_for_unrestricted(self):
        self.assertTrue(is_publicly_accessible(_approved()))

    def test_not_publicly_accessible_when_restricted(self):
        restricted = DocumentFactory(restrict_to_groups=[GroupFactory()])
        self.assertFalse(is_publicly_accessible(_reload(restricted)))

    def test_translation_inherits_parent_restriction(self):
        parent = DocumentFactory(restrict_to_groups=[GroupFactory()])
        ApprovedRevisionFactory(document=parent)
        translation = _translation(_reload(parent))
        self.assertFalse(is_publicly_accessible(translation))

    def test_translation_of_public_parent_is_accessible(self):
        parent = _approved()
        self.assertTrue(is_publicly_accessible(_translation(parent)))

    def test_retrieval_indexable_is_content_eligible_and_public(self):
        self.assertTrue(is_retrieval_indexable(_approved()))

    def test_retrieval_indexable_false_when_restricted(self):
        restricted = DocumentFactory(restrict_to_groups=[GroupFactory()])
        ApprovedRevisionFactory(document=restricted)
        self.assertFalse(is_retrieval_indexable(_reload(restricted)))

    def test_retrieval_indexable_false_without_revision(self):
        self.assertFalse(is_retrieval_indexable(DocumentFactory()))


class EligibleDocumentsQuerysetTests(TestCase):
    """The queryset must be provably equal to the object predicate over a mixed corpus."""

    def test_queryset_equals_predicate_over_mixed_corpus(self):
        eligible = _approved()
        eligible_translation = _translation(eligible)

        restricted = DocumentFactory(restrict_to_groups=[GroupFactory()])
        ApprovedRevisionFactory(document=restricted)
        restricted_translation = _translation(_reload(restricted))

        no_revision = DocumentFactory()
        template = TemplateDocumentFactory()
        ApprovedRevisionFactory(document=template)
        archived = DocumentFactory(is_archived=True)
        ApprovedRevisionFactory(document=archived)
        archived_translation = _translation(_reload(archived))
        canned = DocumentFactory(category=CANNED_RESPONSES_CATEGORY)
        ApprovedRevisionFactory(document=canned)
        administration = DocumentFactory(category=ADMINISTRATION_CATEGORY)
        ApprovedRevisionFactory(document=administration)
        redirect = _make_redirect(_approved())
        stale_template_translation = _stale_template_translation()

        expected = {doc.pk for doc in Document.objects.all() if is_retrieval_indexable(doc)}
        actual = set(eligible_documents().values_list("pk", flat=True))
        self.assertEqual(actual, expected)

        # Guard against a vacuous match: the corpus must exercise both sides.
        self.assertEqual({eligible.pk, eligible_translation.pk}, expected)
        for excluded in (
            restricted,
            restricted_translation,
            no_revision,
            template,
            archived,
            archived_translation,
            canned,
            administration,
            redirect,
            stale_template_translation,
        ):
            self.assertNotIn(excluded.pk, actual)

    def test_queryset_prefetches_original_owned_metadata(self):
        product = ProductFactory()
        topic = TopicFactory(products=[product])
        parent = _approved(products=[product], topics=[topic])
        translation = _translation(parent)

        documents = {
            document.pk: document
            for document in eligible_documents().filter(pk__in=[parent.pk, translation.pk])
        }

        with self.assertNumQueries(0):
            for document in documents.values():
                original = document.original
                self.assertEqual([product], list(original.products.all()))
                self.assertEqual([topic], list(original.topics.all()))
                self.assertEqual([], access_group_ids_for(document))


class FamilyHelperTests(TestCase):
    def test_family_id_is_parent_or_self(self):
        parent = _approved()
        translation = _translation(parent)
        self.assertEqual(family_id_for(parent), parent.pk)
        self.assertEqual(family_id_for(translation), parent.pk)

    def test_family_documents_and_ids_span_the_whole_family(self):
        parent = _approved()
        t1 = _translation(parent, "de")
        t2 = _translation(parent, "fr")
        expected = {parent.pk, t1.pk, t2.pk}
        self.assertEqual(set(family_document_ids(t1)), expected)
        self.assertEqual({doc.pk for doc in family_documents(t2)}, expected)


class AccessMetadataTests(TestCase):
    def test_access_group_ids_are_sorted(self):
        g1 = GroupFactory()
        g2 = GroupFactory()
        # Add out of id order to prove the helper sorts.
        higher, lower = sorted((g1, g2), key=lambda g: g.id, reverse=True)
        doc = DocumentFactory(restrict_to_groups=[higher, lower])
        self.assertEqual(access_group_ids_for(_reload(doc)), sorted([g1.id, g2.id]))

    def test_visibility_reflects_restriction(self):
        restricted = DocumentFactory(restrict_to_groups=[GroupFactory()])
        self.assertEqual(visibility_for(_reload(restricted)), "group_restricted")
        self.assertEqual(visibility_for(_approved()), "public")

    def test_public_document_has_no_access_group_ids(self):
        self.assertEqual(access_group_ids_for(_approved()), [])

    def test_translation_inherits_access_metadata_from_original(self):
        g1 = GroupFactory()
        g2 = GroupFactory()
        parent = DocumentFactory(restrict_to_groups=[g1, g2])
        ApprovedRevisionFactory(document=parent)
        translation = _translation(_reload(parent))
        self.assertEqual(access_group_ids_for(translation), sorted([g1.id, g2.id]))
        self.assertEqual(visibility_for(translation), "group_restricted")
