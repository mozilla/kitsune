from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.db import IntegrityError, transaction

from kitsune.groups.models import GroupProfile
from kitsune.groups.tests import DepartmentFactory, EnterpriseCompanyFactory, GroupProfileFactory
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import GroupFactory, UserFactory
from kitsune.wiki.config import DEFAULT_AUDIENCE_SLUG
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
