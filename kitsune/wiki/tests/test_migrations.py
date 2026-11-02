from importlib import import_module

from django.apps import apps

from kitsune.sumo.tests import TestCase
from kitsune.users.tests import GroupFactory
from kitsune.wiki.config import PUBLIC_AUDIENCE_SLUG, REDIRECT_HTML
from kitsune.wiki.models import Audience, Document, DocumentAudience
from kitsune.wiki.tests import (
    ApprovedRevisionFactory,
    AudienceFactory,
    DocumentFactory,
    TemplateDocumentFactory,
)

audience_migration = import_module("kitsune.wiki.migrations.0027_assign_audiences")


class WikiAudienceMigrationTests(TestCase):
    def restricted_original(self, *groups):
        document = DocumentFactory(audiences=[])
        document.restrict_to_groups.add(*groups)
        return document

    def stub(self, *targets):
        stub = DocumentFactory(
            html=f'{REDIRECT_HTML}href="/kb/target">Target</a></p>', audiences=[]
        )
        for target in targets:
            stub.add_link_to(target, "link")
        return stub

    def assert_audiences(self, expected):
        for label, (document, audiences) in expected.items():
            with self.subTest(label):
                self.assertEqual(set(document.audiences.all()), audiences)

    def test_forward_maps_originals(self):
        g1, g2, stray = GroupFactory(), GroupFactory(), GroupFactory()
        one_group = self.restricted_original(g1)
        two_groups = self.restricted_original(g1, g2)
        translation = DocumentFactory(parent=two_groups, locale="de")
        translation.restrict_to_groups.add(stray)
        assigned = AudienceFactory()
        already_assigned = DocumentFactory(audiences=[assigned])
        already_assigned.restrict_to_groups.add(g2)
        unrestricted = {
            "approved en-US original": ApprovedRevisionFactory(
                document=DocumentFactory(audiences=[])
            ).document,
            "archived original": DocumentFactory(is_archived=True, audiences=[]),
            "de original": DocumentFactory(locale="de", audiences=[]),
            "template": TemplateDocumentFactory(audiences=[]),
        }

        audience_migration.forward(apps, None)

        public = Audience.objects.get(slug=PUBLIC_AUDIENCE_SLUG)
        audience_of = {group: Audience.objects.get(groups=group) for group in (g1, g2)}
        self.assert_audiences(
            {
                **{label: (document, {public}) for label, document in unrestricted.items()},
                "one group": (one_group, {audience_of[g1]}),
                "two groups": (two_groups, {audience_of[g1], audience_of[g2]}),
                "translation": (translation, set()),
                "already assigned": (already_assigned, {assigned}),
            }
        )
        for group, audience in audience_of.items():
            with self.subTest(group=group.name):
                self.assertEqual(list(audience.groups.values_list("id", flat=True)), [group.id])
                self.assertEqual(audience.name, group.name)
        self.assertFalse(Audience.objects.filter(groups=stray).exists())

    def test_forward_names_and_slugs(self):
        cases = [
            ("Public", "Public (restricted)", "public-restricted"),
            ("Public (restricted)", "Public (restricted) 2", "public-restricted-2"),
            ("public", "public", "public-2"),
            ("Foo Bar", "Foo Bar", "foo-bar"),
            ("foo bar", "foo bar", "foo-bar-2"),
            ("!!!", "!!!", "audience"),
            ("x" * 150, "x" * 150, "x" * 80),
            ("x" * 149 + "y", "x" * 149 + "y", "x" * 78 + "-2"),
        ]
        for group_name, _name, _slug in cases:
            self.restricted_original(GroupFactory(name=group_name))

        audience_migration.forward(apps, None)

        for group_name, name, slug in cases:
            with self.subTest(group_name=group_name):
                audience = Audience.objects.get(groups__name=group_name)
                self.assertEqual((audience.name, audience.slug), (name, slug))

    def test_forward_maps_stubs_to_their_final_target(self):
        group = GroupFactory()
        target = self.restricted_original(group)
        second_in_chain = self.stub(target)
        first_in_chain = self.stub(second_in_chain)
        to_translation = self.stub(DocumentFactory(parent=target, locale="de"))
        two_links = self.stub(target, DocumentFactory(audiences=[]))
        unlinked = self.stub()
        dead_end = self.stub()
        dead_end.restrict_to_groups.add(group)
        to_dead_end = self.stub(dead_end)
        cycle_start = self.stub()
        cycle_end = self.stub(cycle_start)
        cycle_start.add_link_to(cycle_end, "link")

        audience_migration.forward(apps, None)

        restricted = {Audience.objects.get(groups=group)}
        public = {Audience.objects.get(slug=PUBLIC_AUDIENCE_SLUG)}
        self.assert_audiences(
            {
                "first in a chain": (first_in_chain, restricted),
                "second in a chain": (second_in_chain, restricted),
                "to a translation": (to_translation, restricted),
                "two links, lowest id followed": (two_links, restricted),
                "without a link": (unlinked, public),
                "without a link, own restriction": (dead_end, restricted),
                "chain ending at a linkless stub": (to_dead_end, public),
                "cycle start": (cycle_start, public),
                "cycle end": (cycle_end, public),
            }
        )

    def test_backward_removes_audience_data_only(self):
        g1, g2 = GroupFactory(), GroupFactory()
        original = self.restricted_original(g1, g2)
        DocumentFactory(parent=original, locale="de").restrict_to_groups.add(g1)
        DocumentFactory(audiences=[])
        restrictions = Document.restrict_to_groups.through.objects
        before = set(restrictions.values_list("document_id", "group_id"))

        audience_migration.forward(apps, None)
        audience_migration.backward(apps, None)

        self.assertFalse(DocumentAudience.objects.exists())
        self.assertFalse(Audience.objects.exists())
        self.assertEqual(set(restrictions.values_list("document_id", "group_id")), before)
