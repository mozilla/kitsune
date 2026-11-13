from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.db import IntegrityError, transaction
from parameterized import parameterized
from pyquery import PyQuery as pq

from kitsune.groups.models import GroupProfile
from kitsune.groups.tests import DepartmentFactory, EnterpriseCompanyFactory, GroupProfileFactory
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import GroupFactory, UserFactory
from kitsune.wiki.config import DEFAULT_AUDIENCE_SLUG
from kitsune.wiki.forms import DocumentForm
from kitsune.wiki.managers import has_private_kb_access
from kitsune.wiki.models import Audience, Document, DocumentAudience, Revision
from kitsune.wiki.tests import (
    ApprovedRevisionFactory,
    AudienceFactory,
    new_document_data,
)


def _approved(**kwargs):
    revision = ApprovedRevisionFactory(**kwargs)
    return revision.document


class AudienceAccessTests(TestCase):
    def test_access_rule(self):
        agents_group = GroupFactory()
        company = EnterpriseCompanyFactory()
        parent_profile = GroupProfileFactory()
        child_profile = GroupProfile.objects.add_child(
            parent_profile, create_kwargs={"group": GroupFactory(), "slug": "child"}
        )
        deleted_group = GroupFactory()

        public = Audience.objects.default()
        contributors = AudienceFactory(is_public=True)
        agents = AudienceFactory(groups=[agents_group])
        company_audience = AudienceFactory(groups=[company.group])

        documents = {
            "pub": _approved(document__audiences=[public]),
            "public_kb": _approved(document__audiences=[contributors]),
            "public_kb_and_agents": _approved(document__audiences=[contributors, agents]),
            "agents": _approved(document__audiences=[agents]),
            "company": _approved(document__audiences=[company_audience]),
            "both": _approved(document__audiences=[agents, company_audience]),
            "mixed": _approved(document__audiences=[public, agents]),
            "nogroups": _approved(document__audiences=[AudienceFactory()]),
            "gone": _approved(document__audiences=[AudienceFactory(groups=[deleted_group])]),
            "parentgroup": _approved(
                document__audiences=[AudienceFactory(groups=[parent_profile.group])]
            ),
        }
        documents["agents_translation"] = _approved(
            document__parent=documents["agents"],
            document__locale="de",
            based_on=documents["agents"].current_revision,
        )
        deleted_group.delete()

        viewers = {
            "anonymous": AnonymousUser(),
            "agent": UserFactory(groups=[agents_group]),
            "department": UserFactory(groups=[DepartmentFactory(company=company).group]),
            "company": UserFactory(groups=[company.group]),
            "child": UserFactory(groups=[child_profile.group]),
            "nobody": UserFactory(),
            "staff": UserFactory(groups=[GroupFactory(name=settings.STAFF_GROUP)]),
            "superuser": UserFactory(is_superuser=True),
        }
        privileged = {"staff", "superuser"}
        expected = {
            "pub": set(viewers),
            "public_kb": set(viewers),
            "public_kb_and_agents": set(viewers),
            "mixed": set(viewers),
            "agents": {"agent"} | privileged,
            "agents_translation": {"agent"} | privileged,
            "company": {"department", "company"} | privileged,
            "both": {"agent", "department", "company"} | privileged,
            "parentgroup": privileged,
            "nogroups": privileged,
            "gone": privileged,
        }

        for viewer_name, viewer in viewers.items():
            visible_ids = set(Document.objects.visible(viewer).values_list("id", flat=True))
            revision_document_ids = set(
                Revision.objects.visible(viewer).values_list("document_id", flat=True)
            )
            for document_name, document in documents.items():
                with self.subTest(viewer=viewer_name, document=document_name):
                    allowed = viewer_name in expected[document_name]
                    self.assertEqual(document.id in visible_ids, allowed)
                    self.assertEqual(document.id in revision_document_ids, allowed)
                    self.assertEqual(
                        Document.objects.visible(viewer, pk=document.pk).exists(), allowed
                    )
                    try:
                        Document.objects.get_visible(viewer, pk=document.pk)
                    except Document.DoesNotExist:
                        found = False
                    else:
                        found = True
                    self.assertEqual(found, allowed)
                    self.assertEqual(
                        Document.objects.get(pk=document.pk).is_visible_for(viewer), allowed
                    )

    def test_missing_default_fails_closed(self):
        agents_group = GroupFactory()
        formerly_default = _approved()
        agents = _approved(document__audiences=[AudienceFactory(groups=[agents_group])])
        old_default_id = Audience.objects.get(slug=DEFAULT_AUDIENCE_SLUG).pk
        DocumentAudience.objects.filter(audience_id=old_default_id).delete()
        Audience.objects.filter(pk=old_default_id).delete()

        agent = UserFactory(groups=[agents_group])
        self.assertTrue(Document.objects.get(pk=formerly_default.pk).is_restricted)
        self.assertFalse(Document.objects.get(pk=formerly_default.pk).is_visible_for(agent))
        self.assertFalse(Document.objects.visible(AnonymousUser()).exists())
        self.assertQuerySetEqual(Document.objects.visible(agent), [agents])

        author = UserFactory()
        self.client.login(username=author.username, password="testpass")
        response = self.client.post(reverse("wiki.new_document"), new_document_data())

        self.assertEqual(response.status_code, 302)
        new_document = Document.objects.get(slug="a-test-article")
        recreated = Audience.objects.get(slug=DEFAULT_AUDIENCE_SLUG)
        self.assertNotEqual(recreated.pk, old_default_id)
        self.assertTrue(recreated.is_public)
        self.assertQuerySetEqual(new_document.audiences.all(), [recreated])

    def test_default_must_stay_public(self):
        Audience.objects.default()
        with transaction.atomic(), self.assertRaises(IntegrityError):
            Audience.objects.filter(slug=DEFAULT_AUDIENCE_SLUG).update(is_public=False)

    def test_flipping_visibility_changes_access(self):
        kb = AudienceFactory()
        document = _approved(document__audiences=[kb])
        anonymous = AnonymousUser()

        for is_public in (True, False):
            with self.subTest(is_public=is_public):
                kb.is_public = is_public
                kb.save()
                self.assertEqual(Document.objects.visible(anonymous).exists(), is_public)
                self.assertEqual(Document.objects.get(pk=document.pk).is_restricted, not is_public)


class KnowledgeBaseListingTests(TestCase):
    def setUp(self):
        agents_group = GroupFactory()
        company = EnterpriseCompanyFactory()
        legacy_group = GroupFactory()

        default = Audience.objects.default()
        default.is_listed = True
        default.save()
        self.kbs = {
            "default": default,
            "public": AudienceFactory(is_public=True, is_listed=True),
            "agents": AudienceFactory(is_listed=True, groups=[agents_group]),
            "company": AudienceFactory(is_listed=True, groups=[company.group]),
            "empty": AudienceFactory(is_listed=True),
            "legacy": AudienceFactory(groups=[legacy_group]),
        }
        self.viewers = {
            "none": None,
            "anonymous": AnonymousUser(),
            "agent": UserFactory(groups=[agents_group]),
            "department": UserFactory(groups=[DepartmentFactory(company=company).group]),
            "other_department": UserFactory(groups=[DepartmentFactory().group]),
            "company": UserFactory(groups=[company.group]),
            "legacy": UserFactory(groups=[legacy_group]),
            "nobody": UserFactory(),
            "staff": UserFactory(groups=[GroupFactory(name=settings.STAFF_GROUP)]),
            "superuser": UserFactory(is_superuser=True),
        }

    @parameterized.expand(
        [
            ("none", {"public"}, {"public"}, False),
            ("anonymous", {"public"}, {"public"}, False),
            ("agent", {"public", "agents"}, {"public", "agents"}, True),
            ("department", {"public", "company"}, {"public", "company"}, True),
            ("other_department", {"public"}, {"public"}, False),
            ("company", {"public", "company"}, {"public", "company"}, True),
            ("legacy", {"public"}, {"public"}, True),
            ("nobody", {"public"}, {"public"}, False),
            ("staff", {"public"}, {"public", "agents", "company", "empty"}, True),
            ("superuser", {"public"}, {"public", "agents", "company", "empty"}, True),
        ]
    )
    def test_listed_and_browsable_kbs(self, viewer, listed, browsable, private_access):
        user = self.viewers[viewer]

        self.assertEqual(
            set(Audience.objects.listed_for(user)), {self.kbs[name] for name in listed}
        )
        self.assertEqual(
            set(Audience.objects.browsable_by(user)), {self.kbs[name] for name in browsable}
        )
        self.assertEqual(has_private_kb_access(user), private_access)


class PrivateAudienceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        agents_group = GroupFactory()
        second_group = GroupFactory()
        company = EnterpriseCompanyFactory()

        cls.kbs = {
            "listed": AudienceFactory(is_listed=True, groups=[agents_group]),
            "unlisted": AudienceFactory(groups=[agents_group, second_group]),
            "company": AudienceFactory(groups=[company.group]),
            "other_company": AudienceFactory(groups=[EnterpriseCompanyFactory().group]),
            "public": AudienceFactory(is_public=True, is_listed=True, groups=[agents_group]),
            "default": Audience.objects.default(),
        }
        cls.viewers = {
            "anonymous": AnonymousUser(),
            "nobody": UserFactory(),
            "agent": UserFactory(groups=[agents_group, second_group]),
            "department": UserFactory(groups=[DepartmentFactory(company=company).group]),
            "staff": UserFactory(groups=[GroupFactory(name=settings.STAFF_GROUP)]),
            "superuser": UserFactory(is_superuser=True),
        }

    @parameterized.expand(
        [
            ("anonymous", set()),
            ("nobody", set()),
            ("agent", {"listed", "unlisted"}),
            ("department", {"company"}),
            ("staff", {"listed", "unlisted", "company", "other_company"}),
            ("superuser", {"listed", "unlisted", "company", "other_company"}),
        ]
    )
    def test_private_for(self, viewer, expected):
        self.assertCountEqual(
            Audience.objects.private_for(self.viewers[viewer]),
            [self.kbs[name] for name in expected],
        )


class KnowledgeBasePresentationTests(TestCase):
    def test_listing_is_private_first_then_by_name_and_distinct(self):
        groups = [GroupFactory(), GroupFactory()]
        for name in ("Zed", "Aardvark", "Mid"):
            AudienceFactory(name=name, is_public=True, is_listed=True)
        AudienceFactory(name="Yankee", is_listed=True, groups=groups)
        AudienceFactory(name="Bravo", is_listed=True, groups=groups[:1])
        member = UserFactory(groups=groups)

        for lister in (Audience.objects.listed_for, Audience.objects.browsable_by):
            self.assertEqual(
                [kb.name for kb in lister(member)],
                ["Bravo", "Yankee", "Aardvark", "Mid", "Zed"],
            )

    @parameterized.expand(
        [
            ("Northwind Support Team", "", "NS"),
            ("northwind  support", "", "NS"),
            ("Acme", "", "A"),
            ("Northwind Support", "NW", "NW"),
        ]
    )
    def test_monogram(self, name, mark, expected):
        self.assertEqual(Audience(name=name, mark=mark).monogram, expected)


class AudiencesWidgetTests(TestCase):
    def setUp(self):
        self.public = AudienceFactory(name="Product Docs", is_public=True)
        self.private = AudienceFactory(name="Accessibility", is_public=False)

    def _render(self):
        return pq(str(DocumentForm(can_assign_audiences=True)["audiences"]))

    def test_options_grouped_by_visibility(self):
        doc = self._render()
        public_group = doc("optgroup[label='Public']").text()
        private_group = doc("optgroup[label='Private']").text()
        self.assertIn("Product Docs", public_group)
        self.assertNotIn("Accessibility", public_group)
        self.assertIn("Accessibility", private_group)
        self.assertNotIn("Product Docs", private_group)

    def test_options_carry_data_public(self):
        doc = self._render()
        self.assertEqual(doc(f"option[value='{self.public.pk}']").attr("data-public"), "true")
        self.assertEqual(doc(f"option[value='{self.private.pk}']").attr("data-public"), "false")

    def test_empty_group_omitted(self):
        Audience.objects.filter(is_public=False).delete()
        doc = self._render()
        self.assertEqual(len(doc("optgroup[label='Private']")), 0)
        self.assertEqual(len(doc("optgroup[label='Public']")), 1)

    def test_selected_options_stay_selected(self):
        form = DocumentForm(
            new_document_data() | {"audiences": [self.private.pk]}, can_assign_audiences=True
        )
        doc = pq(str(form["audiences"]))
        self.assertEqual(doc(f"option[value='{self.private.pk}']").attr("selected"), "selected")
        self.assertIsNone(doc(f"option[value='{self.public.pk}']").attr("selected"))

    def test_mixed_selection_still_valid(self):
        data = new_document_data() | {"audiences": [self.public.pk, self.private.pk]}
        form = DocumentForm(data, can_assign_audiences=True)
        self.assertNotIn("audiences", form.errors)

    def test_status_region_rendered_for_staff_only(self):
        url = reverse("wiki.new_document")
        staff = UserFactory(groups=[GroupFactory(name=settings.STAFF_GROUP)])
        self.client.login(username=staff.username, password="testpass")
        self.assertEqual(len(pq(self.client.get(url).content)("#kb-audience-status")), 1)

        self.client.logout()
        user = UserFactory()
        self.client.login(username=user.username, password="testpass")
        self.assertEqual(len(pq(self.client.get(url).content)("#kb-audience-status")), 0)
