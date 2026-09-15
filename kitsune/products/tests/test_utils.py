from django.contrib.auth.models import AnonymousUser
from django.test import override_settings

from kitsune.groups.models import GroupProfile
from kitsune.groups.tests import GroupProfileFactory
from kitsune.products.models import ProductSupportConfig
from kitsune.products.tests import (
    ProductFactory,
    ProductSupportConfigFactory,
    SupportOrganizationFactory,
    TopicFactory,
    ZendeskConfigFactory,
)
from kitsune.products.utils import (
    get_products,
    get_taxonomy,
    is_enterprise_user,
    should_show_enterprise_banner,
)
from kitsune.questions.tests import AAQConfigFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import GroupFactory, UserFactory


class GetTaxonomyTests(TestCase):
    def setUp(self):
        p1 = ProductFactory(title="product1", slug="p1")
        p2 = ProductFactory(title="product2", slug="p2")
        self.p3 = p3 = ProductFactory(title="product3", slug="mozilla-account", visible=False)
        p4 = ProductFactory(title="product4", slug="p4", visible=False)
        p5 = ProductFactory(title="product5", slug="p5", is_archived=True)

        TopicFactory(
            title="topic1",
            description="Something brief about t1...",
            metadata={
                "description": "Details about t1...",
                "example-questions-assigned-to-this-topic": [
                    "Can you tell me about topic1?",
                    "Is there a setting for topic1?",
                ],
            },
            products=[p1, p2, p3, p4],
        )
        t2 = TopicFactory(
            title="topic2",
            description="Something brief about t2...",
            metadata={
                "description": "Details about t2...",
                "example-questions-assigned-to-this-topic": [
                    "Can you tell me about topic2?",
                    "Is there a setting for topic2?",
                ],
            },
            products=[p2, p3, p4],
        )
        t3 = TopicFactory(
            title="topic3",
            description="Something brief about t3...",
            metadata={"description": "Details about t3..."},
            products=[p2, p3, p4],
        )
        TopicFactory(
            title="topic4",
            description="Something brief about t4...",
            metadata={
                "description": "Details about t4...",
                "example-questions-assigned-to-this-topic": [
                    "Can you tell me about topic4?",
                    "Is there a setting for topic4?",
                ],
            },
            parent=t2,
            products=[p2, p3, p4],
        )
        t5 = TopicFactory(
            title="topic5",
            description="Something brief about t5...",
            metadata={},
            parent=t3,
            products=[p2, p3, p4],
        )
        t6 = TopicFactory(
            title="topic6",
            description="Something brief about t6...",
            metadata={
                "description": "Details about t6...",
                "example-questions-assigned-to-this-topic": [
                    "Can you tell me about topic6?",
                    "Is there a setting for topic6?",
                ],
            },
            parent=t3,
            products=[p3, p4],
        )
        TopicFactory(
            title="topic7",
            description="Something brief about t7...",
            metadata={"description": "Details about t7..."},
            parent=t5,
            products=[p2, p3, p4],
        )
        TopicFactory(
            title="topic8",
            description="Something brief about t8...",
            metadata={},
            parent=t6,
            products=[p3, p4],
        )
        TopicFactory(
            title="topic9",
            description="Something brief about t9...",
            metadata={
                "description": "Details about t9...",
                "example-questions-assigned-to-this-topic": [
                    "Can you tell me about topic9?",
                    "Is there a setting for topic9?",
                ],
            },
            parent=t6,
            products=[p3, p4],
        )
        TopicFactory(
            title="topic10",
            description="Something brief about t10...",
            metadata={"description": "Details about t10..."},
            products=[p4, p5],
        )

    def test_all_products_with_defaults(self):
        self.assertEqual(
            get_taxonomy(),
            """topics:
- title: topic1
  description: Something brief about t1...
  products:
  - title: product1
  - title: product2
  - title: product3
  subtopics: []
- title: topic2
  description: Something brief about t2...
  products:
  - title: product2
  - title: product3
  subtopics:
  - title: topic4
    description: Something brief about t4...
    products:
    - title: product2
    - title: product3
    subtopics: []
- title: topic3
  description: Something brief about t3...
  products:
  - title: product2
  - title: product3
  subtopics:
  - title: topic5
    description: Something brief about t5...
    products:
    - title: product2
    - title: product3
    subtopics:
    - title: topic7
      description: Something brief about t7...
      products:
      - title: product2
      - title: product3
      subtopics: []
  - title: topic6
    description: Something brief about t6...
    products:
    - title: product3
    subtopics:
    - title: topic8
      description: Something brief about t8...
      products:
      - title: product3
      subtopics: []
    - title: topic9
      description: Something brief about t9...
      products:
      - title: product3
      subtopics: []
""",
        )

    def test_all_products_as_json(self):
        self.assertEqual(
            get_taxonomy(output_format="json"),
            """{
  "topics": [
    {
      "title": "topic1",
      "description": "Something brief about t1...",
      "products": [
        {
          "title": "product1"
        },
        {
          "title": "product2"
        },
        {
          "title": "product3"
        }
      ],
      "subtopics": []
    },
    {
      "title": "topic2",
      "description": "Something brief about t2...",
      "products": [
        {
          "title": "product2"
        },
        {
          "title": "product3"
        }
      ],
      "subtopics": [
        {
          "title": "topic4",
          "description": "Something brief about t4...",
          "products": [
            {
              "title": "product2"
            },
            {
              "title": "product3"
            }
          ],
          "subtopics": []
        }
      ]
    },
    {
      "title": "topic3",
      "description": "Something brief about t3...",
      "products": [
        {
          "title": "product2"
        },
        {
          "title": "product3"
        }
      ],
      "subtopics": [
        {
          "title": "topic5",
          "description": "Something brief about t5...",
          "products": [
            {
              "title": "product2"
            },
            {
              "title": "product3"
            }
          ],
          "subtopics": [
            {
              "title": "topic7",
              "description": "Something brief about t7...",
              "products": [
                {
                  "title": "product2"
                },
                {
                  "title": "product3"
                }
              ],
              "subtopics": []
            }
          ]
        },
        {
          "title": "topic6",
          "description": "Something brief about t6...",
          "products": [
            {
              "title": "product3"
            }
          ],
          "subtopics": [
            {
              "title": "topic8",
              "description": "Something brief about t8...",
              "products": [
                {
                  "title": "product3"
                }
              ],
              "subtopics": []
            },
            {
              "title": "topic9",
              "description": "Something brief about t9...",
              "products": [
                {
                  "title": "product3"
                }
              ],
              "subtopics": []
            }
          ]
        }
      ]
    }
  ]
}""",
        )

    def test_all_products_with_metadata(self):
        self.assertEqual(
            get_taxonomy(
                include_metadata=["description", "example-questions-assigned-to-this-topic"]
            ),
            """topics:
- title: topic1
  description: Details about t1...
  example-questions-assigned-to-this-topic:
  - Can you tell me about topic1?
  - Is there a setting for topic1?
  products:
  - title: product1
  - title: product2
  - title: product3
  subtopics: []
- title: topic2
  description: Details about t2...
  example-questions-assigned-to-this-topic:
  - Can you tell me about topic2?
  - Is there a setting for topic2?
  products:
  - title: product2
  - title: product3
  subtopics:
  - title: topic4
    description: Details about t4...
    example-questions-assigned-to-this-topic:
    - Can you tell me about topic4?
    - Is there a setting for topic4?
    products:
    - title: product2
    - title: product3
    subtopics: []
- title: topic3
  description: Details about t3...
  products:
  - title: product2
  - title: product3
  subtopics:
  - title: topic6
    description: Details about t6...
    example-questions-assigned-to-this-topic:
    - Can you tell me about topic6?
    - Is there a setting for topic6?
    products:
    - title: product3
    subtopics:
    - title: topic9
      description: Details about t9...
      example-questions-assigned-to-this-topic:
      - Can you tell me about topic9?
      - Is there a setting for topic9?
      products:
      - title: product3
      subtopics: []
""",
        )

    def test_specific_product_with_metadata(self):
        expected = """topics:
- title: topic1
  description: Details about t1...
  example-questions-assigned-to-this-topic:
  - Can you tell me about topic1?
  - Is there a setting for topic1?
  subtopics: []
- title: topic2
  description: Details about t2...
  example-questions-assigned-to-this-topic:
  - Can you tell me about topic2?
  - Is there a setting for topic2?
  subtopics:
  - title: topic4
    description: Details about t4...
    example-questions-assigned-to-this-topic:
    - Can you tell me about topic4?
    - Is there a setting for topic4?
    subtopics: []
- title: topic3
  description: Details about t3...
  subtopics:
  - title: topic6
    description: Details about t6...
    example-questions-assigned-to-this-topic:
    - Can you tell me about topic6?
    - Is there a setting for topic6?
    subtopics:
    - title: topic9
      description: Details about t9...
      example-questions-assigned-to-this-topic:
      - Can you tell me about topic9?
      - Is there a setting for topic9?
      subtopics: []
"""
        self.assertEqual(
            get_taxonomy(
                self.p3,
                include_metadata=["description", "example-questions-assigned-to-this-topic"],
            ),
            expected,
        )
        self.assertEqual(
            get_taxonomy(
                "mozilla-account",
                include_metadata=["description", "example-questions-assigned-to-this-topic"],
            ),
            expected,
        )
        self.assertEqual(
            get_taxonomy(
                "product3",
                include_metadata=["description", "example-questions-assigned-to-this-topic"],
            ),
            expected,
        )


class GetProductsTests(TestCase):
    def setUp(self):
        ProductFactory(
            title="product1",
            description="All about product1...",
            metadata={
                "description": "Detailed description of product1...",
            },
            display_order=1,
            slug="p1",
        )
        ProductFactory(
            title="product2",
            description="All about product2...",
            metadata={
                "description": "Detailed description of product2...",
            },
            display_order=2,
            slug="p2",
        )
        ProductFactory(
            title="product3",
            description="All about product3...",
            metadata={
                "description": "Detailed description of product3...",
            },
            display_order=3,
            slug="mozilla-account",
            visible=False,
        )
        ProductFactory(
            title="product4",
            description="All about product4...",
            metadata={
                "description": "Detailed description of product4...",
            },
            display_order=4,
            slug="p4",
            visible=False,
        )
        ProductFactory(
            title="product5",
            description="All about product5...",
            metadata={
                "description": "Detailed description of product5...",
            },
            display_order=5,
            slug="p5",
            is_archived=True,
        )

    def test_get_products(self):
        expected = """products:
- title: product1
  description: All about product1...
- title: product2
  description: All about product2...
- title: product3
  description: All about product3...
"""
        self.assertEqual(get_products(), expected)

    def test_get_products_as_json(self):
        expected = """{
  "products": [
    {
      "title": "product1",
      "description": "All about product1..."
    },
    {
      "title": "product2",
      "description": "All about product2..."
    },
    {
      "title": "product3",
      "description": "All about product3..."
    }
  ]
}"""
        self.assertEqual(get_products(output_format="JSON"), expected)

    def test_get_products_with_metadata(self):
        expected = """products:
- title: product1
  description: Detailed description of product1...
- title: product2
  description: Detailed description of product2...
- title: product3
  description: Detailed description of product3...
"""
        self.assertEqual(get_products(include_metadata=["description"]), expected)

    def test_get_products_with_metadata_as_json(self):
        expected = """{
  "products": [
    {
      "title": "product1",
      "description": "Detailed description of product1..."
    },
    {
      "title": "product2",
      "description": "Detailed description of product2..."
    },
    {
      "title": "product3",
      "description": "Detailed description of product3..."
    }
  ]
}"""
        self.assertEqual(
            get_products(include_metadata=["description"], output_format="JSON"), expected
        )


class IsEnterpriseUserTests(TestCase):
    def setUp(self):
        super().setUp()
        self.root = GroupProfileFactory(
            slug="firefox-enterprise", visibility=GroupProfile.Visibility.MODERATED
        )
        self.company = self.root.add_child(group=GroupFactory(), slug="company3")
        self.team = self.company.add_child(group=GroupFactory(), slug="company3-team")
        self.user = UserFactory(groups=[self.team.group])

    def test_root_membership_is_enterprise(self):
        user = UserFactory(groups=[self.root.group])

        self.assertTrue(is_enterprise_user(user))

    def test_unmapped_company_and_deep_descendant_need_no_support_config(self):
        company_member = UserFactory(groups=[self.company.group])

        self.assertTrue(is_enterprise_user(company_member))
        self.assertTrue(is_enterprise_user(self.user))
        self.assertFalse(should_show_enterprise_banner(self.user))

    def test_unrelated_tree_is_not_enterprise(self):
        other_root = GroupProfileFactory()
        other_team = other_root.add_child(group=GroupFactory(), slug="other-team")
        user = UserFactory(groups=[other_team.group])

        self.assertFalse(is_enterprise_user(user))

    def test_anonymous_is_not_enterprise(self):
        self.assertFalse(is_enterprise_user(AnonymousUser()))
        self.assertFalse(is_enterprise_user(None))

    def test_missing_enterprise_root_is_not_enterprise(self):
        self.root.slug = "other-enterprise"
        self.root.save(update_fields=["slug"])

        self.assertFalse(is_enterprise_user(self.user))

    @override_settings(ENTERPRISE_GROUP_SLUG="partner-support")
    def test_configured_enterprise_tree_overrides_default(self):
        root = GroupProfileFactory(slug="partner-support")
        team = root.add_child(group=GroupFactory(), slug="partner-team")
        user = UserFactory(groups=[team.group])

        self.assertTrue(is_enterprise_user(user))
        self.assertFalse(is_enterprise_user(self.user))

    def test_leadership_does_not_grant_membership(self):
        leader = UserFactory()
        self.root.leaders.add(leader)

        self.assertTrue(self.root.can_view(leader))
        self.assertFalse(is_enterprise_user(leader))

    def test_visibility_grant_does_not_grant_membership(self):
        audit_group = GroupFactory()
        auditor = UserFactory(groups=[audit_group])
        self.root.visible_to_groups.add(audit_group)

        self.assertTrue(self.root.can_view(auditor))
        self.assertFalse(is_enterprise_user(auditor))


class EnterpriseBannerCacheInvalidationTests(TestCase):
    def setUp(self):
        super().setUp()
        self.root = GroupProfileFactory(slug="firefox-enterprise")
        self.company = self.root.add_child(group=GroupFactory(), slug="company3")
        self.team = self.company.add_child(group=GroupFactory(), slug="company3-team")
        self.user = UserFactory(groups=[self.team.group])
        self.product = ProductFactory(slug="firefox-enterprise")
        self.config = ProductSupportConfigFactory(
            product=self.product,
            is_active=True,
            default_support_type=ProductSupportConfig.SUPPORT_TYPE_ZENDESK,
            zendesk_config=ZendeskConfigFactory(),
        )

    def test_active_support_shows_banner_only_to_enterprise_members(self):
        self.assertTrue(should_show_enterprise_banner(self.user))
        self.assertFalse(should_show_enterprise_banner(UserFactory()))
        self.assertFalse(should_show_enterprise_banner(AnonymousUser()))
        self.assertFalse(should_show_enterprise_banner(None))

    def test_default_route_change_hides_banner_not_identity(self):
        self.config.forum_config = AAQConfigFactory()
        self.config.save()
        self.assertTrue(should_show_enterprise_banner(self.user))

        self.config.default_support_type = ProductSupportConfig.SUPPORT_TYPE_FORUM
        self.config.save()

        self.assertTrue(is_enterprise_user(self.user))
        self.assertFalse(should_show_enterprise_banner(self.user))

    def test_group_default_takes_precedence_for_banner(self):
        self.config.forum_config = AAQConfigFactory()
        self.config.default_support_type = ProductSupportConfig.SUPPORT_TYPE_FORUM
        self.config.group_default_support_type = ProductSupportConfig.SUPPORT_TYPE_ZENDESK
        self.config.save()
        self.assertTrue(should_show_enterprise_banner(self.user))

        self.config.default_support_type = ProductSupportConfig.SUPPORT_TYPE_ZENDESK
        self.config.group_default_support_type = ProductSupportConfig.SUPPORT_TYPE_FORUM
        self.config.save()

        self.assertTrue(is_enterprise_user(self.user))
        self.assertFalse(should_show_enterprise_banner(self.user))

    def test_group_membership_changes_update_banner(self):
        self.assertTrue(should_show_enterprise_banner(self.user))

        self.team.group.user_set.remove(self.user)
        self.assertFalse(should_show_enterprise_banner(self.user))

        self.team.group.user_set.add(self.user)
        self.assertTrue(should_show_enterprise_banner(self.user))

        self.team.group.user_set.clear()
        self.assertFalse(should_show_enterprise_banner(self.user))

    def test_company_move_updates_descendant_banner(self):
        other_root = GroupProfileFactory()
        self.assertTrue(should_show_enterprise_banner(self.user))

        self.company.move(other_root, "last-child")
        self.assertFalse(is_enterprise_user(self.user))
        self.assertFalse(should_show_enterprise_banner(self.user))

        self.company.refresh_from_db()
        self.root.refresh_from_db()
        self.company.move(self.root, "last-child")
        self.assertTrue(is_enterprise_user(self.user))
        self.assertTrue(should_show_enterprise_banner(self.user))

    def test_config_creation_updates_unmapped_descendant_banner(self):
        self.config.delete()
        self.assertTrue(is_enterprise_user(self.user))
        self.assertFalse(should_show_enterprise_banner(self.user))

        ProductSupportConfigFactory(
            product=self.product,
            zendesk_config=ZendeskConfigFactory(),
        )

        self.assertTrue(should_show_enterprise_banner(self.user))

    def test_config_activation_updates_unmapped_descendant_banner(self):
        self.assertTrue(should_show_enterprise_banner(self.user))

        self.config.is_active = False
        self.config.save()
        self.assertTrue(is_enterprise_user(self.user))
        self.assertFalse(should_show_enterprise_banner(self.user))
        with self.assertNumQueries(0):
            self.assertFalse(should_show_enterprise_banner(self.user))

        self.config.is_active = True
        self.config.save()
        self.assertTrue(should_show_enterprise_banner(self.user))

    def test_removing_zendesk_from_hybrid_config_hides_banner_not_identity(self):
        self.config.forum_config = AAQConfigFactory()
        self.config.save()
        self.assertTrue(should_show_enterprise_banner(self.user))

        self.config.zendesk_config = None
        self.config.save()

        self.assertTrue(is_enterprise_user(self.user))
        self.assertFalse(should_show_enterprise_banner(self.user))

    def test_zendesk_deletion_hides_banner_not_identity(self):
        self.config.forum_config = AAQConfigFactory()
        self.config.save()
        self.assertTrue(should_show_enterprise_banner(self.user))

        self.config.zendesk_config.delete()

        self.assertTrue(is_enterprise_user(self.user))
        self.assertFalse(should_show_enterprise_banner(self.user))

    def test_product_rename_updates_unmapped_descendant_banner(self):
        self.assertTrue(should_show_enterprise_banner(self.user))

        self.product.slug = "other-product"
        self.product.save()
        self.assertTrue(is_enterprise_user(self.user))
        self.assertFalse(should_show_enterprise_banner(self.user))

        self.product.slug = "firefox-enterprise"
        self.product.save()
        self.assertTrue(should_show_enterprise_banner(self.user))

    def test_organization_changes_do_not_revoke_identity_or_banner(self):
        organization = SupportOrganizationFactory(config=self.config, group=self.company.group)
        self.assertTrue(is_enterprise_user(self.user))
        self.assertTrue(should_show_enterprise_banner(self.user))

        organization.group = GroupFactory()
        organization.save()
        self.assertTrue(is_enterprise_user(self.user))
        self.assertTrue(should_show_enterprise_banner(self.user))

        organization.delete()
        self.assertTrue(is_enterprise_user(self.user))
        self.assertTrue(should_show_enterprise_banner(self.user))
