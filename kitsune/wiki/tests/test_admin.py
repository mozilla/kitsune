import time

from django.contrib.admin.sites import AdminSite
from django.db.models import ProtectedError
from django.test import RequestFactory
from django.urls import reverse

from kitsune.gallery.tests import ImageFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import GroupFactory, UserFactory
from kitsune.wiki.admin import AudienceAdmin, DocumentAdmin
from kitsune.wiki.models import Audience, AudienceFeaturedDocument, Document, DocumentAudience
from kitsune.wiki.tests import AudienceFactory, DocumentFactory, TranslatedRevisionFactory


class ArchiveTests(TestCase):
    """Tests for the archival bit flipping in the admin UI"""

    def test_inheritance(self):
        """Make sure parent/child equality of is_archived is maintained."""
        self.assertEqual(Document.objects.filter(is_archived=True).count(), 0)
        # Set up a child and a parent and an orphan (all false) and something
        # true.
        TranslatedRevisionFactory()
        TranslatedRevisionFactory()
        DocumentFactory()
        DocumentFactory(is_archived=True)

        # Batch-clear the archival bits:
        DocumentAdmin._set_archival(Document.objects.all(), True)

        # Assert the child of the parent and the parent of the child (along
        # with everything else) became (or stayed) true:
        self.assertEqual(Document.objects.filter(is_archived=True).count(), 6)
        # We didn't lose any, and they're all true.


class AudienceAdminTests(TestCase):
    def setUp(self):
        self.superuser = UserFactory(is_staff=True, is_superuser=True)
        # Admin requests need an OIDC-backed session with an unexpired ID token.
        self.client.force_login(self.superuser, backend="kitsune.users.auth.SumoOIDCAuthBackend")
        session = self.client.session
        session["oidc_id_token_expiration"] = time.time() + 3600
        session.save()
        self.request = RequestFactory().get("/")
        self.request.user = self.superuser
        self.admin = AudienceAdmin(Audience, AdminSite())
        self.default = Audience.objects.default()

    def change(self, audience, featured=(), **data):
        featured_forms = {
            "featured-TOTAL_FORMS": len(featured),
            "featured-INITIAL_FORMS": 0,
            "featured-MIN_NUM_FORMS": 0,
            "featured-MAX_NUM_FORMS": 3,
        }
        for index, document in enumerate(featured):
            featured_forms[f"featured-{index}-document"] = document.pk
            featured_forms[f"featured-{index}-order"] = index
        return self.client.post(
            reverse("admin:wiki_audience_change", args=[audience.pk]),
            {"name": audience.name, "color": audience.color, **featured_forms, **data},
        )

    def test_default_cannot_be_deleted(self):
        other = AudienceFactory()
        self.assertFalse(self.admin.has_delete_permission(self.request, self.default))
        self.assertTrue(self.admin.has_delete_permission(self.request, other))

        self.client.post(
            reverse("admin:wiki_audience_changelist"),
            {
                "action": "delete_selected",
                "_selected_action": [self.default.pk, other.pk],
                "post": "yes",
            },
        )
        self.assertTrue(Audience.objects.filter(pk=self.default.pk).exists())

        self.admin.delete_queryset(self.request, Audience.objects.all())
        self.assertQuerySetEqual(Audience.objects.all(), [self.default])

    def test_public_kbs_reject_groups_and_the_default_stays_public(self):
        group = GroupFactory()
        public_kb = AudienceFactory(is_public=True)
        private_kb = AudienceFactory()

        rejected = {
            "default": self.change(self.default, groups=[group.pk]),
            "public kb": self.change(public_kb, is_public="on", groups=[group.pk]),
            "made public with groups": self.change(private_kb, is_public="on", groups=[group.pk]),
        }
        self.change(private_kb, groups=[group.pk])
        self.change(self.default)

        for label, response in rejected.items():
            with self.subTest(label):
                self.assertIn("groups", response.context["adminform"].form.errors)
        self.assertFalse(Audience.objects.filter(groups=group).exclude(pk=private_kb.pk).exists())
        self.assertTrue(private_kb.groups.filter(pk=group.pk).exists())
        self.assertTrue(Audience.objects.get(pk=self.default.pk).is_public)
        self.assertEqual(self.admin.get_readonly_fields(self.request), ())
        self.assertEqual(
            self.admin.get_readonly_fields(self.request, self.default), ("slug", "is_public")
        )
        self.assertEqual(self.admin.get_readonly_fields(self.request, private_kb), ("slug",))

    def test_publishing_a_kb_with_content_needs_confirmation(self):
        kbs = {
            "articles": AudienceFactory(),
            "images": AudienceFactory(),
            "empty": AudienceFactory(),
            "already public": AudienceFactory(is_public=True),
        }
        DocumentFactory(audiences=[kbs["articles"]])
        ImageFactory(audience=kbs["images"], file="")
        ImageFactory(audience=kbs["already public"], file="")

        for label, kb in kbs.items():
            with self.subTest(label):
                response = self.change(kb, is_public="on")
                if label in ("articles", "images"):
                    self.assertIn("confirm_publish", response.context["adminform"].form.errors)
                    self.assertFalse(Audience.objects.get(pk=kb.pk).is_public)
                    response = self.change(kb, is_public="on", confirm_publish="on")
                self.assertEqual(302, response.status_code)
                self.assertTrue(Audience.objects.get(pk=kb.pk).is_public)

    def test_featured_articles_must_belong_to_the_kb(self):
        kb = AudienceFactory()
        inside = [DocumentFactory(audiences=[kb]) for _ in range(4)]
        elsewhere = DocumentFactory(audiences=[AudienceFactory()])
        translation = DocumentFactory(parent=inside[0], locale="de")
        DocumentAudience.objects.create(document=translation, audience=kb)

        for label, document in (("another kb", elsewhere), ("translation", translation)):
            with self.subTest(label):
                response = self.change(kb, featured=[document])
                formset = response.context["inline_admin_formsets"][0].formset
                self.assertIn("document", formset.errors[0])
                self.assertFalse(kb.featured.exists())

        too_many = self.change(kb, featured=inside)
        formset = too_many.context["inline_admin_formsets"][0].formset
        self.assertTrue(formset.non_form_errors())
        self.assertFalse(kb.featured.exists())

        self.change(kb, featured=inside[:3])
        self.assertEqual(
            list(kb.featured.values_list("document", flat=True)), [d.pk for d in inside[:3]]
        )
        self.assertEqual(AudienceFeaturedDocument.objects.count(), 3)

    def test_assigned_audience_cannot_be_deleted(self):
        audience = AudienceFactory()
        DocumentFactory(audiences=[audience])

        with self.assertRaises(ProtectedError):
            audience.delete()

    def test_no_audience_filter(self):
        public_original = DocumentFactory()
        unassigned = DocumentFactory(audiences=[])
        DocumentFactory(parent=public_original, locale="de")

        response = self.client.get(reverse("admin:wiki_document_changelist"), {"audience": "none"})

        self.assertEqual(list(response.context["cl"].result_list), [unassigned])
