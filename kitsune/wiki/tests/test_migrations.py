from importlib import import_module

from django.apps import apps

from kitsune.sumo.tests import TestCase
from kitsune.wiki.config import DEFAULT_AUDIENCE_SLUG
from kitsune.wiki.models import Audience
from kitsune.wiki.tests import AudienceFactory

visibility_migration = import_module("kitsune.wiki.migrations.0029_knowledge_base_visibility")


class KnowledgeBaseVisibilityMigrationTests(TestCase):
    def test_forward_makes_the_reserved_audience_the_public_default(self):
        Audience.objects.filter(slug=DEFAULT_AUDIENCE_SLUG).delete()
        reserved = Audience.objects.create(slug="public", name="Public")
        # As 0027 maps a group named "Default"; public only to satisfy the later constraint.
        clash = Audience.objects.create(slug="default", name="Default", is_public=True)
        private = AudienceFactory()

        visibility_migration.forward(apps, None)

        self.assertEqual(
            set(Audience.objects.values_list("pk", "slug", "name", "is_public")),
            {
                (reserved.pk, "default", "Default", True),
                (clash.pk, "default-restricted", "Default (restricted)", True),
                (private.pk, private.slug, private.name, False),
            },
        )
