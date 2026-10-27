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
    SupportAction,
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
from kitsune.products.utils import get_professional_support_products, get_support_company
from kitsune.questions.tests import AAQConfigFactory, QuestionLocaleFactory
from kitsune.sumo.utils import get_aaq_context
from kitsune.users.tests import UserFactory


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
        self.assertEqual(route.aaq_action, SupportAction())
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

    def test_single_channel_forms_ignore_unavailable_channel_choices(self):
        for support_type, requested_type, action in (
            ("forum", "zendesk", "forum"),
            ("zendesk", "forum", PRODUCT_SUPPORT),
        ):
            with self.subTest(support_type=support_type):
                product = ProductFactory()
                config = ProductSupportConfigFactory(
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
                self.assertEqual(
                    route.aaq_action, SupportAction(action, zendesk_config=config.zendesk_config)
                )
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
                patch("kitsune.products.models.timezone.localdate", return_value=day),
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
        enterprise = SupportAction(
            ENTERPRISE_SUPPORT,
            can_switch=True,
            zendesk_config=self.coverage.zendesk_config,
            coverage=self.coverage,
        )
        for default, requested, expected in (
            ("forum", None, enterprise),
            ("zendesk", None, enterprise),
            ("forum", "invalid", enterprise),
            ("zendesk", "forum", SupportAction("forum", can_switch=True)),
            ("forum", "zendesk", enterprise),
        ):
            with self.subTest(default=default, requested=requested):
                config.default_support_type = default
                config.save()
                route = self.route(**({"support_type": requested} if requested else {}))
                self.assertEqual(route.aaq_action, expected)
                self.assertTrue(route.allows("forum"))
                self.assertFalse(route.allows(PRODUCT_SUPPORT))
                self.assertTrue(route.allows(ENTERPRISE_SUPPORT, str(self.coverage.pk)))

    def test_support_organizations_do_not_change_ticket_access(self):
        config = ProductSupportConfigFactory(
            product=self.product,
            forum_config=AAQConfigFactory(),
            zendesk_config=ZendeskConfigFactory(),
            default_support_type=ProductSupportConfig.SUPPORT_TYPE_ZENDESK,
        )
        organization = SupportOrganizationFactory(
            config=config, group=EnterpriseCompanyFactory().group, include_live_chat=True
        )
        product_ticket = SupportAction(
            PRODUCT_SUPPORT, can_switch=True, zendesk_config=config.zendesk_config
        )
        enterprise = SupportAction(
            ENTERPRISE_SUPPORT,
            can_switch=True,
            zendesk_config=self.coverage.zendesk_config,
            coverage=self.coverage,
        )
        user = UserFactory()
        for change in ("added", "removed"):
            if change == "removed":
                organization.delete()
            with self.subTest(organization=change):
                self.assertEqual(self.route(user=user).aaq_action, product_ticket)
                self.assertEqual(self.route().aaq_action, enterprise)

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
                self.assertEqual(route.aaq_action.action, ENTERPRISE_SUPPORT)
                self.assertTrue(route.aaq_action.can_switch)
                self.assertFalse(route.allows(PRODUCT_SUPPORT))
                self.assertTrue(route.allows(ENTERPRISE_SUPPORT, str(self.coverage.pk)))
                forum_route = self.route(support_type="forum")
                self.assertEqual(forum_route.aaq_action, SupportAction("forum", can_switch=True))

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


class SupportPresentationTests(TestCase):
    """Pages present the router's decision for each persona."""

    def setUp(self):
        today = timezone.localdate()
        self.current = {
            "starts_on": today - timedelta(days=1),
            "ends_on": today + timedelta(days=1),
        }
        self.company = EnterpriseCompanyFactory()
        self.vpn = ProductFactory(slug="vpn")
        ProductSupportConfigFactory(
            product=self.vpn, zendesk_config=ZendeskConfigFactory(), subscription_only=True
        )
        self.forum_product = ProductFactory(slug="forum-product")
        ProductSupportConfigFactory(
            product=self.forum_product,
            forum_config=AAQConfigFactory(enabled_locales=[QuestionLocaleFactory(locale="en-US")]),
            default_support_type=ProductSupportConfig.SUPPORT_TYPE_FORUM,
        )
        self.unconfigured = ProductFactory(slug="unconfigured")
        self.archived = ProductFactory(is_archived=True)
        contract = SupportContractFactory(company=self.company, **self.current)
        for product in (self.vpn, self.forum_product, self.unconfigured, self.archived):
            SupportCoverageFactory(contract=contract, product=product)

    def user(self, *groups, subscribed=False):
        user = UserFactory()
        user.groups.set([group.group for group in groups])
        if subscribed:
            user.profile.products.add(self.vpn)
        return user

    def request_for(self, user):
        request = RequestFactory().get("/")
        request.user = user
        return request

    def presented(self, product, support_type, *, can_switch=False, is_enterprise=False):
        return {
            "product_slug": product.slug,
            "multiple_products": False,
            "has_public_forum": product == self.forum_product,
            "current_support_type": support_type,
            "can_switch": can_switch,
            "is_enterprise": is_enterprise,
        }

    def test_presented_support_and_professional_products_follow_the_router(self):
        expired_company = EnterpriseCompanyFactory()
        SupportCoverageFactory(
            product=self.vpn,
            contract__company=expired_company,
            contract__starts_on=self.current["starts_on"] - timedelta(days=30),
            contract__ends_on=self.current["starts_on"],
        )
        forum_company = EnterpriseCompanyFactory()
        SupportCoverageFactory(
            product=self.forum_product,
            contract__company=forum_company,
            contract__starts_on=self.current["starts_on"],
            contract__ends_on=self.current["ends_on"],
        )
        renewed_company = EnterpriseCompanyFactory()
        expired = {
            "starts_on": self.current["starts_on"] - timedelta(days=30),
            "ends_on": self.current["starts_on"],
        }
        for period in (expired, self.current):
            SupportCoverageFactory(
                product=self.vpn,
                contract=SupportContractFactory(company=renewed_company, **period),
            )
        leader = self.user()
        self.company.leaders.add(leader)

        vpn_hidden = {"current_support_type": ProductSupportConfig.SUPPORT_TYPE_HIDE}
        vpn_product = self.presented(self.vpn, "zendesk")
        vpn_enterprise = self.presented(self.vpn, "zendesk", is_enterprise=True)
        forum = self.presented(self.forum_product, "forum")
        forum_enterprise = self.presented(
            self.forum_product, "zendesk", can_switch=True, is_enterprise=True
        )
        unconfigured_enterprise = self.presented(self.unconfigured, "zendesk", is_enterprise=True)
        covered_products = [self.vpn, self.forum_product, self.unconfigured]
        covered_contexts = (vpn_enterprise, forum_enterprise, unconfigured_enterprise)
        for persona, user, products, contexts in (
            ("anonymous", AnonymousUser(), [], (vpn_hidden, forum, {})),
            ("uncovered", self.user(), [], (vpn_hidden, forum, {})),
            ("subscriber", self.user(subscribed=True), [], (vpn_product, forum, {})),
            ("company member", self.user(self.company), covered_products, covered_contexts),
            (
                "department member",
                self.user(DepartmentFactory(company=self.company)),
                covered_products,
                covered_contexts,
            ),
            ("root member", self.user(self.company.get_parent()), [], (vpn_hidden, forum, {})),
            ("company leader", leader, [], (vpn_hidden, forum, {})),
            (
                "expired subscriber",
                self.user(expired_company, subscribed=True),
                [],
                (vpn_product, forum, {}),
            ),
            (
                "other product subscriber",
                self.user(forum_company, subscribed=True),
                [self.forum_product],
                (vpn_product, forum_enterprise, {}),
            ),
            (
                "renewed company member",
                self.user(renewed_company),
                [self.vpn],
                (vpn_enterprise, forum, {}),
            ),
        ):
            with self.subTest(persona=persona):
                request = RequestFactory().get("/")
                request.user = user
                request.LANGUAGE_CODE = "en-US"
                professional_products = get_professional_support_products(request)
                self.assertCountEqual(professional_products, products)
                for product, context in zip(
                    (self.vpn, self.forum_product, self.unconfigured), contexts, strict=True
                ):
                    self.assertEqual(get_aaq_context(request, product), context)
                for product in (self.vpn, self.forum_product, self.unconfigured, self.archived):
                    self.assertEqual(
                        product in professional_products,
                        route_support(request, product).enterprise_support.eligible,
                    )

    def test_professional_products_deny_ambiguity_and_inactive_users(self):
        member = self.user(self.company)
        with self.assertNumQueries(2):
            self.assertCountEqual(
                get_professional_support_products(self.request_for(member)),
                [self.vpn, self.forum_product, self.unconfigured],
            )

        overlapping = SupportContractFactory(company=self.company, **self.current)
        SupportCoverageFactory(contract=overlapping, product=self.vpn)
        self.assertCountEqual(
            get_professional_support_products(self.request_for(member)),
            [self.forum_product, self.unconfigured],
        )

        inactive = UserFactory(is_active=False)
        inactive.groups.add(self.company.group)
        User.groups.through.objects.bulk_create(
            [User.groups.through(user_id=member.pk, group_id=EnterpriseCompanyFactory().group_id)]
        )
        for user in (inactive, member):
            with self.subTest(user=user):
                self.assertEqual(get_professional_support_products(self.request_for(user)), [])

    def test_support_company_is_resolved_once_per_request(self):
        request = self.request_for(self.user(DepartmentFactory(company=self.company)))
        with self.assertNumQueries(1):
            self.assertEqual(get_support_company(request), self.company)
        with self.assertNumQueries(0):
            self.assertEqual(get_support_company(request), self.company)
            self.assertIsNone(get_support_company(self.request_for(AnonymousUser())))
