import time

from django.contrib.admin.sites import AdminSite
from django.db.models import ProtectedError
from django.test import RequestFactory
from django.urls import reverse

from kitsune.sumo.tests import TestCase
from kitsune.users.tests import GroupFactory, UserFactory
from kitsune.wiki.admin import AudienceAdmin, DocumentAdmin
from kitsune.wiki.models import Audience, Document
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
        self.public = Audience.objects.public()

    def test_public_cannot_be_deleted(self):
        other = AudienceFactory()
        self.assertFalse(self.admin.has_delete_permission(self.request, self.public))
        self.assertTrue(self.admin.has_delete_permission(self.request, other))

        self.client.post(
            reverse("admin:wiki_audience_changelist"),
            {
                "action": "delete_selected",
                "_selected_action": [self.public.pk, other.pk],
                "post": "yes",
            },
        )
        self.assertTrue(Audience.objects.filter(pk=self.public.pk).exists())

        self.admin.delete_queryset(self.request, Audience.objects.all())
        self.assertQuerySetEqual(Audience.objects.all(), [self.public])

    def test_public_rejects_groups_and_slugs_are_read_only(self):
        group = GroupFactory()
        other = AudienceFactory()

        response = self.client.post(
            reverse("admin:wiki_audience_change", args=[self.public.pk]),
            {"name": self.public.name, "groups": [group.pk]},
        )
        self.client.post(
            reverse("admin:wiki_audience_change", args=[other.pk]),
            {"name": other.name, "groups": [group.pk]},
        )

        self.assertIn("groups", response.context["adminform"].form.errors)
        self.assertFalse(self.public.groups.exists())
        self.assertTrue(other.groups.filter(pk=group.pk).exists())
        self.assertNotIn("slug", self.admin.get_readonly_fields(self.request))
        for audience in (self.public, other):
            with self.subTest(audience=audience.slug):
                self.assertIn("slug", self.admin.get_readonly_fields(self.request, audience))

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
