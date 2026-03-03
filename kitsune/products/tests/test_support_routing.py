from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase

from kitsune.products.managers import ProductSupportConfigManager
from kitsune.products.models import ProductSupportConfig
from kitsune.products.tests import (
    ProductFactory,
    ProductSupportConfigFactory,
    ZendeskConfigFactory,
)
from kitsune.questions.tests import AAQConfigFactory
from kitsune.users.tests import GroupFactory, UserFactory


class SupportRoutingTests(TestCase):
    """Tests for ProductSupportConfig.objects.route_support_request()"""

    def setUp(self):
        self.factory = RequestFactory()
        self.product = ProductFactory(slug="test-product")
        self.user = UserFactory()

    def test_no_config_returns_none(self):
        """When no ProductSupportConfig exists, return (None, False)."""
        request = self.factory.get("/")
        request.user = self.user

        support_type, can_switch = ProductSupportConfig.objects.route_support_request(
            request, self.product
        )

        self.assertIsNone(support_type)
        self.assertFalse(can_switch)

    def test_forum_only_routing(self):
        """Forum-only product returns (SUPPORT_TYPE_FORUM, False)."""
        aaq_config = AAQConfigFactory()
        ProductSupportConfigFactory(
            product=self.product,
            forum_config=aaq_config,
            zendesk_config=None,
            is_active=True,
        )

        request = self.factory.get("/")
        request.user = self.user

        support_type, can_switch = ProductSupportConfig.objects.route_support_request(
            request, self.product
        )

        self.assertEqual(support_type, ProductSupportConfig.SUPPORT_TYPE_FORUM)
        self.assertFalse(can_switch)

    def test_zendesk_only_routing(self):
        """Zendesk-only product returns (SUPPORT_TYPE_ZENDESK, False)."""
        zendesk_config = ZendeskConfigFactory()
        ProductSupportConfigFactory(
            product=self.product,
            forum_config=None,
            zendesk_config=zendesk_config,
            is_active=True,
        )

        request = self.factory.get("/")
        request.user = self.user

        support_type, can_switch = ProductSupportConfig.objects.route_support_request(
            request, self.product
        )

        self.assertEqual(support_type, ProductSupportConfig.SUPPORT_TYPE_ZENDESK)
        self.assertFalse(can_switch)

    def test_hybrid_no_groups_default_forum(self):
        """Hybrid product with no groups defaults to forum, allows switching."""
        aaq_config = AAQConfigFactory()
        zendesk_config = ZendeskConfigFactory()
        ProductSupportConfigFactory(
            product=self.product,
            forum_config=aaq_config,
            zendesk_config=zendesk_config,
            default_support_type=ProductSupportConfig.SUPPORT_TYPE_FORUM,
            is_active=True,
        )

        request = self.factory.get("/")
        request.user = self.user

        support_type, can_switch = ProductSupportConfig.objects.route_support_request(
            request, self.product
        )

        self.assertEqual(support_type, ProductSupportConfig.SUPPORT_TYPE_FORUM)
        self.assertTrue(can_switch)

    def test_hybrid_no_groups_default_zendesk(self):
        """Hybrid product with no groups defaults to Zendesk, allows switching."""
        aaq_config = AAQConfigFactory()
        zendesk_config = ZendeskConfigFactory()
        ProductSupportConfigFactory(
            product=self.product,
            forum_config=aaq_config,
            zendesk_config=zendesk_config,
            default_support_type=ProductSupportConfig.SUPPORT_TYPE_ZENDESK,
            is_active=True,
        )

        request = self.factory.get("/")
        request.user = self.user

        support_type, can_switch = ProductSupportConfig.objects.route_support_request(
            request, self.product
        )

        self.assertEqual(support_type, ProductSupportConfig.SUPPORT_TYPE_ZENDESK)
        self.assertTrue(can_switch)

    def test_hybrid_no_groups_honors_requested_type(self):
        """Hybrid product with no groups honors requested_type query param."""
        aaq_config = AAQConfigFactory()
        zendesk_config = ZendeskConfigFactory()
        ProductSupportConfigFactory(
            product=self.product,
            forum_config=aaq_config,
            zendesk_config=zendesk_config,
            default_support_type=ProductSupportConfig.SUPPORT_TYPE_FORUM,
            is_active=True,
        )

        request = self.factory.get("/", {"support_type": "zendesk"})
        request.user = self.user

        support_type, can_switch = ProductSupportConfig.objects.route_support_request(
            request, self.product
        )

        self.assertEqual(support_type, ProductSupportConfig.SUPPORT_TYPE_ZENDESK)
        self.assertTrue(can_switch)

    def test_hybrid_with_groups_user_not_in_group(self):
        """Hybrid with groups: user NOT in group is locked to default."""
        aaq_config = AAQConfigFactory()
        zendesk_config = ZendeskConfigFactory()
        group = GroupFactory(name="beta-testers")
        config = ProductSupportConfigFactory(
            product=self.product,
            forum_config=aaq_config,
            zendesk_config=zendesk_config,
            default_support_type=ProductSupportConfig.SUPPORT_TYPE_FORUM,
            is_active=True,
        )
        config.hybrid_support_groups.add(group)

        request = self.factory.get("/", {"support_type": "zendesk"})
        request.user = self.user  # User NOT in group

        support_type, can_switch = ProductSupportConfig.objects.route_support_request(
            request, self.product
        )

        self.assertEqual(support_type, ProductSupportConfig.SUPPORT_TYPE_FORUM)
        self.assertFalse(can_switch)

    def test_hybrid_with_groups_user_in_group_can_switch(self):
        """Hybrid with groups: user IN group can switch."""
        aaq_config = AAQConfigFactory()
        zendesk_config = ZendeskConfigFactory()
        group = GroupFactory(name="beta-testers")
        config = ProductSupportConfigFactory(
            product=self.product,
            forum_config=aaq_config,
            zendesk_config=zendesk_config,
            default_support_type=ProductSupportConfig.SUPPORT_TYPE_FORUM,
            is_active=True,
        )
        config.hybrid_support_groups.add(group)

        # Add user to group
        self.user.groups.add(group)

        request = self.factory.get("/", {"support_type": "zendesk"})
        request.user = self.user

        support_type, can_switch = ProductSupportConfig.objects.route_support_request(
            request, self.product
        )

        self.assertEqual(support_type, ProductSupportConfig.SUPPORT_TYPE_ZENDESK)
        self.assertTrue(can_switch)

    def test_hybrid_group_default_override(self):
        """Hybrid with groups: group_default_support_type overrides default."""
        aaq_config = AAQConfigFactory()
        zendesk_config = ZendeskConfigFactory()
        group = GroupFactory(name="beta-testers")
        config = ProductSupportConfigFactory(
            product=self.product,
            forum_config=aaq_config,
            zendesk_config=zendesk_config,
            default_support_type=ProductSupportConfig.SUPPORT_TYPE_FORUM,
            group_default_support_type=ProductSupportConfig.SUPPORT_TYPE_ZENDESK,
            is_active=True,
        )
        config.hybrid_support_groups.add(group)

        # Add user to group
        self.user.groups.add(group)

        request = self.factory.get("/")  # No requested_type
        request.user = self.user

        support_type, can_switch = ProductSupportConfig.objects.route_support_request(
            request, self.product
        )

        # Should use group_default_support_type (Zendesk), not default (Forum)
        self.assertEqual(support_type, ProductSupportConfig.SUPPORT_TYPE_ZENDESK)
        self.assertTrue(can_switch)

    def test_invalid_requested_type_ignored(self):
        """Invalid requested_type query param is ignored."""
        aaq_config = AAQConfigFactory()
        zendesk_config = ZendeskConfigFactory()
        ProductSupportConfigFactory(
            product=self.product,
            forum_config=aaq_config,
            zendesk_config=zendesk_config,
            default_support_type=ProductSupportConfig.SUPPORT_TYPE_FORUM,
            is_active=True,
        )

        request = self.factory.get("/", {"support_type": "invalid"})
        request.user = self.user

        support_type, can_switch = ProductSupportConfig.objects.route_support_request(
            request, self.product
        )

        # Should fall back to default since invalid type is ignored
        self.assertEqual(support_type, ProductSupportConfig.SUPPORT_TYPE_FORUM)
        self.assertTrue(can_switch)

    def test_anonymous_user_hybrid_no_groups(self):
        """Anonymous user on hybrid product with no groups can switch."""
        aaq_config = AAQConfigFactory()
        zendesk_config = ZendeskConfigFactory()
        ProductSupportConfigFactory(
            product=self.product,
            forum_config=aaq_config,
            zendesk_config=zendesk_config,
            default_support_type=ProductSupportConfig.SUPPORT_TYPE_FORUM,
            is_active=True,
        )

        request = self.factory.get("/")
        request.user = AnonymousUser()

        support_type, can_switch = ProductSupportConfig.objects.route_support_request(
            request, self.product
        )

        self.assertEqual(support_type, ProductSupportConfig.SUPPORT_TYPE_FORUM)
        self.assertTrue(can_switch)

    def test_anonymous_user_hybrid_with_groups(self):
        """Anonymous user on hybrid with groups is locked to default."""
        aaq_config = AAQConfigFactory()
        zendesk_config = ZendeskConfigFactory()
        group = GroupFactory(name="beta-testers")
        config = ProductSupportConfigFactory(
            product=self.product,
            forum_config=aaq_config,
            zendesk_config=zendesk_config,
            default_support_type=ProductSupportConfig.SUPPORT_TYPE_FORUM,
            is_active=True,
        )
        config.hybrid_support_groups.add(group)

        request = self.factory.get("/")
        request.user = AnonymousUser()

        support_type, can_switch = ProductSupportConfig.objects.route_support_request(
            request, self.product
        )

        self.assertEqual(support_type, ProductSupportConfig.SUPPORT_TYPE_FORUM)
        self.assertFalse(can_switch)

    def test_no_support_channels_constraint(self):
        """Database constraint prevents config with neither forum nor Zendesk."""
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError) as context:
            ProductSupportConfigFactory(
                product=self.product,
                forum_config=None,
                zendesk_config=None,
                is_active=True,
            )

        self.assertIn("at_least_one_support_channel", str(context.exception))


class SubscriptionRoutingTests(TestCase):
    """Tests for subscription_only routing in route_support_request()."""

    def setUp(self):
        self.factory = RequestFactory()
        self.product = ProductFactory(slug="mozilla-vpn")
        self.zendesk_config = ZendeskConfigFactory()
        self.user = UserFactory()
        self.config = ProductSupportConfigFactory(
            product=self.product,
            forum_config=None,
            zendesk_config=self.zendesk_config,
            is_active=True,
            subscription_only=True,
        )

    def test_subscriber_routes_to_zendesk(self):
        """Subscribed user on a subscription_only product is routed to ZD."""
        self.user.profile.products.add(self.product)

        request = self.factory.get("/")
        request.user = self.user

        support_type, can_switch = ProductSupportConfig.objects.route_support_request(
            request, self.product
        )

        self.assertEqual(support_type, ProductSupportConfig.SUPPORT_TYPE_ZENDESK)
        self.assertFalse(can_switch)

    def test_non_subscriber_with_redirect_returns_redirect_sentinel(self):
        """Non-subscribed user is returned SUPPORT_TYPE_REDIRECT when redirect product is set."""
        redirect_product = ProductFactory(slug="firefox")
        self.config.unsubscribed_redirect_product = redirect_product
        self.config.save()

        request = self.factory.get("/")
        request.user = self.user  # has no subscription

        support_type, can_switch = ProductSupportConfig.objects.route_support_request(
            request, self.product
        )

        self.assertEqual(support_type, ProductSupportConfigManager.SUPPORT_TYPE_REDIRECT)
        self.assertFalse(can_switch)

    def test_non_subscriber_without_redirect_returns_hide_sentinel(self):
        """Non-subscribed user is returned SUPPORT_TYPE_HIDE when no redirect product is set."""
        request = self.factory.get("/")
        request.user = self.user  # has no subscription, no redirect product configured

        support_type, can_switch = ProductSupportConfig.objects.route_support_request(
            request, self.product
        )

        self.assertEqual(support_type, ProductSupportConfigManager.SUPPORT_TYPE_HIDE)
        self.assertFalse(can_switch)

    def test_anonymous_user_returns_hide_sentinel(self):
        """Anonymous users on a subscription_only product are treated as non-subscribers."""
        request = self.factory.get("/")
        request.user = AnonymousUser()

        support_type, can_switch = ProductSupportConfig.objects.route_support_request(
            request, self.product
        )

        self.assertEqual(support_type, ProductSupportConfigManager.SUPPORT_TYPE_HIDE)
        self.assertFalse(can_switch)

    def test_subscription_only_false_bypasses_check(self):
        """When subscription_only is False, all users pass through to normal routing."""
        self.config.subscription_only = False
        self.config.save()

        request = self.factory.get("/")
        request.user = self.user  # no subscription, but subscription_only is off

        support_type, can_switch = ProductSupportConfig.objects.route_support_request(
            request, self.product
        )

        self.assertEqual(support_type, ProductSupportConfig.SUPPORT_TYPE_ZENDESK)
        self.assertFalse(can_switch)
