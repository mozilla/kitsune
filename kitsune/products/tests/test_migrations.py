from importlib import import_module

from django.apps import apps
from django.db import connection

from kitsune.groups.tests import GroupProfileFactory
from kitsune.products.models import ProductSupportConfig
from kitsune.products.tests import (
    ProductFactory,
    ProductSupportConfigFactory,
    ZendeskConfigFactory,
)
from kitsune.questions.tests import AAQConfigFactory
from kitsune.sumo.tests import TestCase

enterprise_migration = import_module(
    "kitsune.products.migrations.0054_enterprise_root_and_forum_only_config"
)


class EnterpriseRootAndConfigMigrationTests(TestCase):
    def test_root_is_renamed_both_ways_unless_the_new_slug_is_taken(self):
        root = GroupProfileFactory(slug="firefox-enterprise")
        for direction, slug in (
            (enterprise_migration.forward, "professional-support"),
            (enterprise_migration.backward, "firefox-enterprise"),
        ):
            direction(apps, None)
            root.refresh_from_db()
            self.assertEqual(root.slug, slug)

        GroupProfileFactory(slug="professional-support")
        enterprise_migration.forward(apps, None)
        root.refresh_from_db()
        self.assertEqual(root.slug, "firefox-enterprise")

    def test_firefox_enterprise_support_becomes_forum_only(self):
        hybrid = ProductSupportConfigFactory(
            product=ProductFactory(slug="firefox-enterprise"),
            forum_config=AAQConfigFactory(),
            zendesk_config=ZendeskConfigFactory(),
        )
        ticket_only = ProductSupportConfigFactory(
            product=ProductFactory(slug="firefox-enterprise"),
            zendesk_config=ZendeskConfigFactory(),
        )
        stale = ProductSupportConfigFactory(
            product=ticket_only.product, is_active=False, zendesk_config=ZendeskConfigFactory()
        )
        unrelated = ProductSupportConfigFactory(zendesk_config=ZendeskConfigFactory())
        unrelated_inactive = ProductSupportConfigFactory(
            product=unrelated.product, is_active=False, zendesk_config=ZendeskConfigFactory()
        )
        expected = {
            hybrid.pk: (True, hybrid.forum_config_id, None),
            ticket_only.pk: (False, None, ticket_only.zendesk_config_id),
            unrelated.pk: (True, None, unrelated.zendesk_config_id),
            unrelated_inactive.pk: (False, None, unrelated_inactive.zendesk_config_id),
        }

        for direction in (enterprise_migration.forward, enterprise_migration.backward):
            direction(apps, None)
            configs = ProductSupportConfig.objects.filter(
                pk__in=[*expected, stale.pk]
            ).values_list("pk", "is_active", "forum_config_id", "zendesk_config_id")
            self.assertEqual({pk: tuple(state) for pk, *state in configs}, expected)

    def test_legacy_organization_tables_and_column_stay_without_foreign_keys(self):
        introspection = connection.introspection
        with connection.cursor() as cursor:
            self.assertIn(
                "group_default_support_type",
                {
                    column.name
                    for column in introspection.get_table_description(
                        cursor, ProductSupportConfig._meta.db_table
                    )
                },
            )
            for table in (
                "products_supportorganization",
                "products_productsupportconfig_hybrid_support_groups",
            ):
                with self.subTest(table):
                    constraints = introspection.get_constraints(cursor, table)
                    self.assertTrue(constraints)
                    self.assertFalse(
                        [name for name, info in constraints.items() if info["foreign_key"]]
                    )
