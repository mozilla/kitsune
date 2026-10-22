from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser, User
from django.db import IntegrityError
from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone

from kitsune.groups.models import GroupProfile
from kitsune.groups.tests import DepartmentFactory, EnterpriseCompanyFactory
from kitsune.products.models import ProductSupportConfig, SupportContract
from kitsune.products.routing import (
    ENTERPRISE_SUPPORT,
    PRODUCT_SUPPORT,
    SupportForm,
    route_support,
)
from kitsune.products.tests import (
    ProductFactory,
    ProductSupportConfigFactory,
    SupportContractFactory,
    SupportCoverageFactory,
    SupportOrganizationFactory,
    ZendeskConfigFactory,
)
from kitsune.questions.tests import AAQConfigFactory, QuestionLocaleFactory
from kitsune.users.tests import GroupFactory, UserFactory


class SupportRoutingTests(TestCase):
    """Product support routing."""

    def setUp(self):
        self.factory = RequestFactory()
        self.product = ProductFactory(slug="test-product")
        self.user = UserFactory()

    def test_no_config_returns_none(self):
        """No config means no product support channel or switching."""
        request = self.factory.get("/")
        request.user = self.user

        route = route_support(request, self.product)

        self.assertIsNone(route.product_support.support_type)
        self.assertFalse(route.product_support.can_switch)
        self.assertEqual(route.aaq_action, SupportForm())
        for action in (
            ProductSupportConfig.SUPPORT_TYPE_FORUM,
            PRODUCT_SUPPORT,
            ENTERPRISE_SUPPORT,
            None,
            "invalid",
        ):
            with self.subTest(action=action):
                self.assertFalse(route.allows(action))

    def test_forum_only_routing(self):
        """Forum-only products cannot switch channels."""
        aaq_config = AAQConfigFactory(enabled_locales=[QuestionLocaleFactory(locale="en-US")])
        ProductSupportConfigFactory(
            product=self.product,
            forum_config=aaq_config,
            zendesk_config=None,
            is_active=True,
        )

        request = self.factory.get("/")
        request.user = self.user

        product_support = route_support(request, self.product).product_support

        self.assertEqual(product_support.support_type, ProductSupportConfig.SUPPORT_TYPE_FORUM)
        self.assertFalse(product_support.can_switch)

    def test_zendesk_only_routing(self):
        """Zendesk-only products cannot switch channels."""
        zendesk_config = ZendeskConfigFactory()
        ProductSupportConfigFactory(
            product=self.product,
            forum_config=None,
            zendesk_config=zendesk_config,
            is_active=True,
        )

        request = self.factory.get("/")
        request.user = self.user

        product_support = route_support(request, self.product).product_support

        self.assertEqual(product_support.support_type, ProductSupportConfig.SUPPORT_TYPE_ZENDESK)
        self.assertFalse(product_support.can_switch)

    def test_hybrid_no_organizations_default_forum(self):
        """Hybrid product with no organizations defaults to forum, allows switching."""
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

        product_support = route_support(request, self.product).product_support

        self.assertEqual(product_support.support_type, ProductSupportConfig.SUPPORT_TYPE_FORUM)
        self.assertTrue(product_support.can_switch)

    def test_hybrid_no_organizations_default_zendesk(self):
        """Hybrid product with no organizations defaults to Zendesk, allows switching."""
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

        product_support = route_support(request, self.product).product_support

        self.assertEqual(product_support.support_type, ProductSupportConfig.SUPPORT_TYPE_ZENDESK)
        self.assertTrue(product_support.can_switch)

    def test_hybrid_no_organizations_honors_requested_type(self):
        """Hybrid product with no organizations honors requested_type query param."""
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

        product_support = route_support(request, self.product).product_support

        self.assertEqual(product_support.support_type, ProductSupportConfig.SUPPORT_TYPE_ZENDESK)
        self.assertTrue(product_support.can_switch)

    def test_hybrid_with_organizations_nonmember(self):
        """Hybrid with organizations: a nonmember is locked to default."""
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
        SupportOrganizationFactory(config=config, group=group)

        request = self.factory.get("/", {"support_type": "zendesk"})
        request.user = self.user  # User NOT in group

        product_support = route_support(request, self.product).product_support

        self.assertEqual(product_support.support_type, ProductSupportConfig.SUPPORT_TYPE_FORUM)
        self.assertFalse(product_support.can_switch)

    def test_hybrid_with_organizations_member_can_switch(self):
        """Hybrid with organizations: a member can switch."""
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
        SupportOrganizationFactory(config=config, group=group)

        # Add user to group
        self.user.groups.add(group)

        request = self.factory.get("/", {"support_type": "zendesk"})
        request.user = self.user

        product_support = route_support(request, self.product).product_support

        self.assertEqual(product_support.support_type, ProductSupportConfig.SUPPORT_TYPE_ZENDESK)
        self.assertTrue(product_support.can_switch)

    def test_hybrid_organization_member_default_override(self):
        """Hybrid organization members use group_default_support_type over default."""
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
        SupportOrganizationFactory(config=config, group=group)

        # Add user to group
        self.user.groups.add(group)

        request = self.factory.get("/")  # No requested_type
        request.user = self.user

        product_support = route_support(request, self.product).product_support

        # Should use group_default_support_type (Zendesk), not default (Forum)
        self.assertEqual(product_support.support_type, ProductSupportConfig.SUPPORT_TYPE_ZENDESK)
        self.assertTrue(product_support.can_switch)

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

        product_support = route_support(request, self.product).product_support

        # Should fall back to default since invalid type is ignored
        self.assertEqual(product_support.support_type, ProductSupportConfig.SUPPORT_TYPE_FORUM)
        self.assertTrue(product_support.can_switch)

    def test_anonymous_user_hybrid_no_organizations(self):
        """Anonymous user on hybrid product with no organizations can switch."""
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

        product_support = route_support(request, self.product).product_support

        self.assertEqual(product_support.support_type, ProductSupportConfig.SUPPORT_TYPE_FORUM)
        self.assertTrue(product_support.can_switch)

    def test_anonymous_user_hybrid_with_organizations(self):
        """Anonymous user on hybrid with organizations is locked to default."""
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
        SupportOrganizationFactory(config=config, group=group)

        request = self.factory.get("/")
        request.user = AnonymousUser()

        product_support = route_support(request, self.product).product_support

        self.assertEqual(product_support.support_type, ProductSupportConfig.SUPPORT_TYPE_FORUM)
        self.assertFalse(product_support.can_switch)

    def test_single_channel_forms_ignore_unavailable_channel_choices(self):
        for support_type, requested_type, action in (
            ("forum", "zendesk", "forum"),
            ("zendesk", "forum", PRODUCT_SUPPORT),
        ):
            with self.subTest(support_type=support_type):
                product = ProductFactory()
                ProductSupportConfigFactory(
                    product=product,
                    forum_config=(
                        AAQConfigFactory(enabled_locales=[QuestionLocaleFactory(locale="en-US")])
                        if support_type == "forum"
                        else None
                    ),
                    zendesk_config=ZendeskConfigFactory() if support_type == "zendesk" else None,
                )
                request = self.factory.get("/", {"support_type": requested_type})
                request.user = self.user
                route = route_support(request, product)
                self.assertEqual(route.aaq_action, SupportForm(action))
                self.assertEqual(route.aaq_action.support_type, support_type)
                self.assertTrue(route.allows(action))
                other_action = PRODUCT_SUPPORT if action == "forum" else "forum"
                self.assertFalse(route.allows(other_action))
                self.assertFalse(route.allows(ENTERPRISE_SUPPORT))
                self.assertFalse(route.allows("zendesk"))

    def test_no_support_channels_constraint(self):
        """Database constraint prevents config with neither forum nor Zendesk."""
        with self.assertRaises(IntegrityError) as context:
            ProductSupportConfigFactory(
                product=self.product,
                forum_config=None,
                zendesk_config=None,
                is_active=True,
            )

        self.assertIn("at_least_one_support_channel", str(context.exception))


class SubtreeSupportRoutingTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = UserFactory()
        self.product = ProductFactory()
        config = ProductSupportConfigFactory(
            product=self.product,
            forum_config=AAQConfigFactory(),
            zendesk_config=ZendeskConfigFactory(),
            default_support_type=ProductSupportConfig.SUPPORT_TYPE_FORUM,
            group_default_support_type=ProductSupportConfig.SUPPORT_TYPE_ZENDESK,
            is_active=True,
        )
        self.root = GroupProfile.objects.add_root(
            create_kwargs={"group": GroupFactory(), "slug": "firefox-enterprise"}
        )
        self.parent = GroupProfile.objects.add_child(
            self.root, create_kwargs={"group": GroupFactory(), "slug": "division"}
        )
        self.company = GroupProfile.objects.add_child(
            self.parent, create_kwargs={"group": GroupFactory(), "slug": "company"}
        )
        team = GroupProfile.objects.add_child(
            self.company, create_kwargs={"group": GroupFactory(), "slug": "team"}
        )
        self.descendant = GroupProfile.objects.add_child(
            team, create_kwargs={"group": GroupFactory(), "slug": "subteam"}
        )
        SupportOrganizationFactory(config=config, group=self.company.group)

    def test_deep_descendant_uses_group_default(self):
        self.user.groups.add(self.descendant.group)
        request = self.factory.get("/")
        request.user = self.user

        product_support = route_support(request, self.product).product_support
        self.assertEqual(product_support.support_type, ProductSupportConfig.SUPPORT_TYPE_ZENDESK)
        self.assertTrue(product_support.can_switch)

    def test_deep_descendant_can_override_group_default(self):
        self.user.groups.add(self.descendant.group)
        request = self.factory.get("/", {"support_type": "forum"})
        request.user = self.user

        product_support = route_support(request, self.product).product_support
        self.assertEqual(product_support.support_type, ProductSupportConfig.SUPPORT_TYPE_FORUM)
        self.assertTrue(product_support.can_switch)

    def test_members_outside_company_cannot_use_organization_support(self):
        sibling = GroupProfile.objects.add_child(
            self.parent, create_kwargs={"group": GroupFactory(), "slug": "unmapped-company"}
        )
        unrelated = GroupProfile.objects.add_root(
            create_kwargs={"group": GroupFactory(), "slug": "unrelated"}
        )
        for profile in (self.root, self.parent, sibling, unrelated):
            with self.subTest(group=profile.slug):
                self.user.groups.set([profile.group])
                request = self.factory.get("/", {"support_type": "zendesk"})
                request.user = self.user

                product_support = route_support(request, self.product).product_support
                self.assertEqual(
                    product_support.support_type, ProductSupportConfig.SUPPORT_TYPE_FORUM
                )
                self.assertFalse(product_support.can_switch)


class SubscriptionRoutingTests(TestCase):
    """Subscription-only product support routing."""

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

        product_support = route_support(request, self.product).product_support

        self.assertEqual(product_support.support_type, ProductSupportConfig.SUPPORT_TYPE_ZENDESK)
        self.assertFalse(product_support.can_switch)

    def test_non_subscriber_with_redirect_returns_redirect_sentinel(self):
        """Non-subscribed user is returned SUPPORT_TYPE_REDIRECT when redirect product is set."""
        redirect_product = ProductFactory(slug="firefox")
        self.config.unsubscribed_redirect_product = redirect_product
        self.config.save()

        request = self.factory.get("/")
        request.user = self.user  # has no subscription

        product_support = route_support(request, self.product).product_support

        self.assertEqual(product_support.support_type, ProductSupportConfig.SUPPORT_TYPE_REDIRECT)
        self.assertFalse(product_support.can_switch)

    def test_non_subscriber_without_redirect_returns_hide_sentinel(self):
        """Non-subscribed user is returned SUPPORT_TYPE_HIDE when no redirect product is set."""
        request = self.factory.get("/")
        request.user = self.user  # has no subscription, no redirect product configured

        product_support = route_support(request, self.product).product_support

        self.assertEqual(product_support.support_type, ProductSupportConfig.SUPPORT_TYPE_HIDE)
        self.assertFalse(product_support.can_switch)

    def test_anonymous_user_returns_hide_sentinel(self):
        """Anonymous users on a subscription_only product are treated as non-subscribers."""
        request = self.factory.get("/")
        request.user = AnonymousUser()

        product_support = route_support(request, self.product).product_support

        self.assertEqual(product_support.support_type, ProductSupportConfig.SUPPORT_TYPE_HIDE)
        self.assertFalse(product_support.can_switch)

    def test_subscription_only_false_bypasses_check(self):
        """When subscription_only is False, all users pass through to normal routing."""
        self.config.subscription_only = False
        self.config.save()

        request = self.factory.get("/")
        request.user = self.user  # no subscription, but subscription_only is off

        product_support = route_support(request, self.product).product_support

        self.assertEqual(product_support.support_type, ProductSupportConfig.SUPPORT_TYPE_ZENDESK)
        self.assertFalse(product_support.can_switch)


class EnterpriseSupportRoutingTests(TestCase):
    def setUp(self):
        self.company = EnterpriseCompanyFactory()
        self.department = DepartmentFactory(company=self.company)
        self.user = UserFactory()
        self.user.groups.add(self.company.group)
        self.product = ProductFactory()
        self.today = timezone.localdate()
        self.contract = SupportContractFactory(
            company=self.company,
            starts_on=self.today - timedelta(days=1),
            ends_on=self.today + timedelta(days=1),
        )
        self.coverage = SupportCoverageFactory(contract=self.contract, product=self.product)

    def route(self, user=None, product=None, **params):
        request = RequestFactory().get("/", params)
        request.user = user if user is not None else self.user
        return route_support(request, product if product is not None else self.product)

    def test_company_and_department_members_are_covered(self):
        for group in (self.company.group, self.department.group):
            with self.subTest(group=group):
                self.user.groups.set([group])
                enterprise_support = self.route().enterprise_support
                self.assertTrue(enterprise_support.eligible)
                self.assertEqual(enterprise_support.coverage, self.coverage)
                self.assertIsNone(enterprise_support.reason)

    def test_root_members_and_leaders_are_not_company_members(self):
        root = GroupProfile.objects.get_ancestors(self.company).get(depth=1)
        for groups, leaders in (([], []), ([root.group], []), ([], [self.user])):
            with self.subTest(groups=groups, leaders=leaders):
                self.user.groups.set(groups)
                self.company.leaders.set(leaders)
                enterprise_support = self.route().enterprise_support
                self.assertFalse(enterprise_support.eligible)
                self.assertEqual(enterprise_support.reason, "no_company")

    @override_settings(ENTERPRISE_GROUP_SLUG="missing-enterprise-root")
    def test_missing_enterprise_root(self):
        self.assertEqual(self.route().enterprise_support.reason, "no_company")

    def test_unavailable_user_or_product(self):
        for user, product, reason in (
            (AnonymousUser(), self.product, "not_authenticated"),
            (UserFactory(is_active=False), self.product, "inactive_user"),
            (self.user, ProductFactory(is_archived=True), "product_unavailable"),
        ):
            with self.subTest(reason=reason):
                enterprise_support = self.route(user=user, product=product).enterprise_support
                self.assertFalse(enterprise_support.eligible)
                self.assertEqual(enterprise_support.reason, reason)

    def test_membership_in_two_companies_is_ambiguous(self):
        other_company = EnterpriseCompanyFactory()
        User.groups.through.objects.bulk_create(
            [User.groups.through(user_id=self.user.pk, group_id=other_company.group_id)]
        )

        enterprise_support = self.route().enterprise_support
        self.assertFalse(enterprise_support.eligible)
        self.assertEqual(enterprise_support.reason, "ambiguous_company")

    def test_contract_dates_are_inclusive(self):
        for day, eligible in (
            (self.contract.starts_on - timedelta(days=1), False),
            (self.contract.starts_on, True),
            (self.contract.ends_on, True),
            (self.contract.ends_on + timedelta(days=1), False),
        ):
            with (
                self.subTest(day=day),
                patch("kitsune.products.routing.timezone.localdate", return_value=day),
            ):
                enterprise_support = self.route().enterprise_support
                self.assertEqual(enterprise_support.eligible, eligible)
                self.assertEqual(enterprise_support.reason, None if eligible else "no_coverage")

    def test_suspended_and_cancelled_contracts_are_not_effective(self):
        for status in (SupportContract.Status.SUSPENDED, SupportContract.Status.CANCELLED):
            with self.subTest(status=status):
                self.contract.status = status
                self.contract.save()
                enterprise_support = self.route().enterprise_support
                self.assertFalse(enterprise_support.eligible)
                self.assertEqual(enterprise_support.reason, "no_coverage")

    def test_coverage_is_product_specific(self):
        enterprise_support = self.route(product=ProductFactory()).enterprise_support
        self.assertFalse(enterprise_support.eligible)
        self.assertEqual(enterprise_support.reason, "no_coverage")

    def test_overlapping_coverage_is_ambiguous(self):
        other_contract = SupportContractFactory(
            company=self.company,
            starts_on=self.contract.starts_on,
            ends_on=self.contract.ends_on,
        )
        SupportCoverageFactory(contract=other_contract, product=self.product)

        enterprise_support = self.route().enterprise_support
        self.assertFalse(enterprise_support.eligible)
        self.assertEqual(enterprise_support.reason, "ambiguous_coverage")

    def test_coverage_needs_no_product_support_config(self):
        route = self.route()
        self.assertEqual(route.enterprise_support.coverage, self.coverage)
        self.assertTrue(route.enterprise_support.eligible)
        self.assertIsNone(route.product_support.support_type)

    def test_coverage_ignores_subscription_gate(self):
        config = ProductSupportConfigFactory(
            product=self.product,
            zendesk_config=ZendeskConfigFactory(),
            subscription_only=True,
        )
        for redirect, support_type in (
            (None, ProductSupportConfig.SUPPORT_TYPE_HIDE),
            (ProductFactory(), ProductSupportConfig.SUPPORT_TYPE_REDIRECT),
        ):
            with self.subTest(support_type=support_type):
                config.unsubscribed_redirect_product = redirect
                config.save()
                route = self.route()
                self.assertEqual(route.enterprise_support.coverage, self.coverage)
                self.assertTrue(route.enterprise_support.eligible)
                self.assertEqual(route.product_support.support_type, support_type)
                self.assertFalse(route.product_support.has_ticket)

    def test_preferred_ticket_uses_eligible_legs(self):
        config = ProductSupportConfigFactory(
            product=self.product, zendesk_config=ZendeskConfigFactory()
        )
        for covered, product_support, expected in (
            (True, True, ENTERPRISE_SUPPORT),
            (False, True, PRODUCT_SUPPORT),
            (True, False, ENTERPRISE_SUPPORT),
            (False, False, None),
        ):
            with self.subTest(covered=covered, product_support=product_support):
                self.user.groups.set([self.company.group] if covered else [])
                config.is_active = product_support
                config.save()
                route = self.route()
                self.assertEqual(route.enterprise_support.eligible, covered)
                self.assertEqual(route.product_support.has_ticket, product_support)
                self.assertEqual(route.preferred_ticket, expected)

    def test_hybrid_form_defaults_and_explicit_channels(self):
        config = ProductSupportConfigFactory(
            product=self.product,
            forum_config=AAQConfigFactory(),
            zendesk_config=ZendeskConfigFactory(),
        )
        for default, requested, expected in (
            ("forum", None, SupportForm(ENTERPRISE_SUPPORT, can_switch=True)),
            ("zendesk", None, SupportForm(ENTERPRISE_SUPPORT, can_switch=True)),
            ("forum", "invalid", SupportForm(ENTERPRISE_SUPPORT, can_switch=True)),
            ("zendesk", "forum", SupportForm("forum", can_switch=True)),
            ("forum", "zendesk", SupportForm(ENTERPRISE_SUPPORT, can_switch=True)),
        ):
            with self.subTest(default=default, requested=requested):
                config.default_support_type = default
                config.save()
                route = self.route(**({"support_type": requested} if requested else {}))
                self.assertEqual(route.aaq_action, expected)
                self.assertTrue(route.allows("forum"))
                self.assertFalse(route.allows(PRODUCT_SUPPORT))
                self.assertTrue(route.allows(ENTERPRISE_SUPPORT, str(self.coverage.pk)))

    def test_ticket_weights_prefer_enterprise_without_changing_forum_access(self):
        ProductSupportConfigFactory(
            product=self.product,
            forum_config=AAQConfigFactory(),
            zendesk_config=ZendeskConfigFactory(),
            default_support_type=ProductSupportConfig.SUPPORT_TYPE_FORUM,
        )
        for weights in (
            {ENTERPRISE_SUPPORT: 20, PRODUCT_SUPPORT: 10},
            {ENTERPRISE_SUPPORT: 10, PRODUCT_SUPPORT: 10},
        ):
            with (
                self.subTest(weights=weights),
                patch.dict("kitsune.products.routing.TICKET_WEIGHTS", weights),
            ):
                route = self.route()
                self.assertEqual(route.preferred_ticket, ENTERPRISE_SUPPORT)
                self.assertTrue(route.enterprise_support.eligible)
                self.assertTrue(route.product_support.has_ticket)
                self.assertEqual(
                    route.product_support.support_type, ProductSupportConfig.SUPPORT_TYPE_FORUM
                )
                self.assertTrue(route.product_support.can_switch)
                self.assertEqual(
                    route.aaq_action, SupportForm(ENTERPRISE_SUPPORT, can_switch=True)
                )
                self.assertFalse(route.allows(PRODUCT_SUPPORT))
                self.assertTrue(route.allows(ENTERPRISE_SUPPORT, str(self.coverage.pk)))
                forum_route = self.route(support_type="forum")
                self.assertEqual(forum_route.aaq_action, SupportForm("forum", can_switch=True))

    def test_repeated_product_support_routing_needs_no_queries(self):
        ProductSupportConfigFactory(product=self.product, zendesk_config=ZendeskConfigFactory())
        request = RequestFactory().get("/")
        request.user = self.user
        product_support = route_support(request, self.product).product_support
        self.assertEqual(product_support.support_type, ProductSupportConfig.SUPPORT_TYPE_ZENDESK)

        with self.assertNumQueries(0):
            self.assertEqual(
                route_support(request, self.product).product_support.support_type,
                ProductSupportConfig.SUPPORT_TYPE_ZENDESK,
            )

    def test_anonymous_enterprise_support_needs_no_queries(self):
        with self.assertNumQueries(0):
            enterprise_support = self.route(user=AnonymousUser()).enterprise_support
            self.assertFalse(enterprise_support.eligible)
            self.assertEqual(enterprise_support.reason, "not_authenticated")
