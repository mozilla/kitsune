from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

import requests
from django.contrib.auth.models import AnonymousUser, Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, connections
from django.http import Http404
from django.test import TransactionTestCase, override_settings
from pyquery import PyQuery as pq
from waffle.testutils import override_switch
from zenpy.lib.exception import APIException, RatelimitBudgetExceeded

from kitsune.customercare.models import ZendeskOrganization
from kitsune.customercare.zendesk import ZendeskProvisioningConflict
from kitsune.groups.models import GroupProfile
from kitsune.groups.onboarding import (
    can_onboard_enterprise,
    configure_enterprise_company,
    create_enterprise_company,
    get_enterprise_company,
    get_enterprise_root,
    get_enterprise_support_config,
)
from kitsune.groups.tests import GroupProfileFactory
from kitsune.products.models import SupportOrganization
from kitsune.products.tests import (
    ProductFactory,
    ProductSupportConfigFactory,
    SupportOrganizationFactory,
    ZendeskConfigFactory,
)
from kitsune.questions.tests import AAQConfigFactory
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import GroupFactory, UserFactory


@override_settings(
    ENTERPRISE_GROUP_SLUG="enterprise-root",
    READ_ONLY=False,
    ZENDESK_CHAT_WIDGET_KEY="test-widget",
    ZENDESK_CHAT_SIGNING_KEY_ID="test-key",
    ZENDESK_CHAT_SIGNING_SECRET="test-secret",
)
@override_switch("zendesk-chat", active=True)
class EnterpriseCompanyTests(TestCase):
    def setUp(self):
        super().setUp()
        self.root = GroupProfileFactory(
            slug="enterprise-root",
            visibility=GroupProfile.Visibility.PRIVATE,
            isolation_enabled=True,
        )
        self.actor = UserFactory(is_staff=True)
        self.root.leaders.add(self.actor)
        self.product = ProductFactory(slug=self.root.slug)
        self.config = ProductSupportConfigFactory(
            product=self.product, zendesk_config=ZendeskConfigFactory()
        )

    def _child(self, parent=None, **kwargs):
        return GroupProfile.objects.add_child(
            parent or self.root, create_kwargs={"group": GroupFactory(), **kwargs}
        )

    def _create(self, **kwargs):
        return create_enterprise_company(
            **{
                "actor": self.actor,
                "name": "Example Company",
                "include_live_chat": False,
                **kwargs,
            }
        )

    def _assert_rejected_creation(self, exception=ValidationError, **kwargs):
        models = (Group, GroupProfile, SupportOrganization, ZendeskOrganization)
        before = [model.objects.count() for model in models]
        with self.assertRaises(exception) as raised:
            self._create(**kwargs)
        self.assertEqual([model.objects.count() for model in models], before)
        self.root.refresh_from_db()
        self.assertEqual(self.root.numchild, GroupProfile.objects.get_children(self.root).count())
        return raised.exception

    def test_creation_inherits_tree_policy_without_enrolling_actor(self):
        self.root.visibility = GroupProfile.Visibility.MODERATED
        self.root.save()
        allowed_group = GroupFactory()
        self.root.visible_to_groups.add(allowed_group)
        with patch(
            "kitsune.groups.onboarding.ZendeskClient.validate_organization",
            side_effect=AssertionError("Unlinked company creation must remain local"),
        ):
            company = self._create(name="  Café Software  ", include_live_chat=True)

        self.assertEqual(company.group.name, "Café Software")
        self.assertEqual(company.slug, "cafe-software")
        self.assertEqual(company.depth, 2)
        self.assertEqual(GroupProfile.objects.get_parent(company), self.root)
        self.assertEqual(company.visibility, GroupProfile.Visibility.MODERATED)
        self.assertQuerySetEqual(company.visible_to_groups.all(), [allowed_group])
        self.assertFalse(company.group.user_set.exists())
        self.assertFalse(company.leaders.exists())
        self.assertFalse(self.config.hybrid_support_groups.exists())
        organization = SupportOrganization.objects.get(group=company.group, config=self.config)
        self.assertTrue(organization.include_live_chat)
        mapping = ZendeskOrganization.objects.get(group_profile=company)
        self.assertIsNone(mapping.zendesk_id)
        self.assertIsNotNone(mapping.external_id)

    def test_only_active_staff_root_moderators_can_mutate(self):
        company = self._child()
        root_leader = UserFactory()
        inactive_leader = UserFactory(is_staff=True, is_active=False)
        company_leader = UserFactory(is_staff=True)
        root_member = UserFactory(is_staff=True)
        company.leaders.add(company_leader)
        self.root.leaders.add(root_leader, inactive_leader)
        self.root.group.user_set.add(root_member)
        for actor in (
            None,
            AnonymousUser(),
            root_leader,
            inactive_leader,
            company_leader,
            root_member,
            UserFactory(is_staff=True),
            UserFactory(is_superuser=True, is_staff=False),
        ):
            with self.subTest(actor=actor):
                self.assertFalse(can_onboard_enterprise(actor, self.root))
                self._assert_rejected_creation(PermissionDenied, actor=actor)
                with self.assertRaises(PermissionDenied):
                    configure_enterprise_company(
                        actor=actor, company=company, include_live_chat=True
                    )
        self.assertFalse(SupportOrganization.objects.filter(group=company.group).exists())
        self.assertFalse(ZendeskOrganization.objects.filter(group_profile=company).exists())

    def test_staff_superuser_needs_no_root_membership(self):
        actor = UserFactory(is_staff=True, is_superuser=True)
        company = self._create(actor=actor)
        self.assertFalse(company.group.user_set.filter(pk=actor.pk).exists())
        self.assertFalse(self.root.leaders.filter(pk=actor.pk).exists())
        self.assertFalse(self.root.group.user_set.filter(pk=actor.pk).exists())

    def test_company_scope_uses_saved_exact_parent_not_supplied_attributes(self):
        company = self._child()
        department = self._child(company)
        other_root = GroupProfileFactory()
        other_company = self._child(other_root)
        other_company.path = company.path
        other_company.depth = company.depth
        for candidate in (self.root, department, other_root, other_company):
            with self.subTest(company=candidate.pk):
                with self.assertRaises(Http404):
                    get_enterprise_company(self.root, pk=candidate.pk)
                with self.assertRaises(Http404):
                    configure_enterprise_company(
                        actor=self.actor, company=candidate, include_live_chat=False
                    )
        self.assertFalse(SupportOrganization.objects.exists())
        self.assertFalse(ZendeskOrganization.objects.exists())

    def test_company_lookup_respects_sibling_visibility(self):
        company = self._child()
        sibling = self._child()
        member = UserFactory(groups=[company.group])
        self.assertEqual(get_enterprise_company(self.root, viewer=member, pk=company.pk), company)
        with self.assertRaises(Http404):
            get_enterprise_company(self.root, viewer=member, pk=sibling.pk)

    def test_missing_and_nested_root_configuration_refused(self):
        nested = self._child(slug="nested-root")
        for slug in ("missing-root", nested.slug):
            with self.subTest(slug=slug), override_settings(ENTERPRISE_GROUP_SLUG=slug):
                with self.assertRaises(ValidationError) as raised:
                    get_enterprise_root()
                self.assertEqual(raised.exception.code, "configuration_error")
                error = self._assert_rejected_creation()
                self.assertEqual(error.code, "configuration_error")

    def test_unsafe_root_does_not_weaken_authorization_or_allow_writes(self):
        for changes in (
            {"visibility": GroupProfile.Visibility.PUBLIC},
            {"visibility": GroupProfile.Visibility.PRIVATE, "isolation_enabled": False},
        ):
            with self.subTest(changes=changes):
                GroupProfile.objects.filter(pk=self.root.pk).update(**changes)
                root = get_enterprise_root()
                self.assertTrue(can_onboard_enterprise(self.actor, root))
                error = self._assert_rejected_creation()
                self.assertEqual(error.code, "configuration_error")
                self._assert_rejected_creation(PermissionDenied, actor=UserFactory())

    def test_missing_archived_or_ambiguous_product_refused(self):
        self.product.slug = "unrelated-product"
        self.product.save()
        self._assert_rejected_creation()
        self.product.slug = self.root.slug
        self.product.is_archived = True
        self.product.save()
        self._assert_rejected_creation()
        self.product.is_archived = False
        self.product.save()
        ProductFactory(slug=self.product.slug)
        error = self._assert_rejected_creation()
        self.assertEqual(error.code, "configuration_error")

    def test_inactive_missing_and_forum_only_support_refused(self):
        self.config.is_active = False
        self.config.save()
        self._assert_rejected_creation()
        self.config.is_active = True
        self.config.zendesk_config = None
        self.config.forum_config = AAQConfigFactory()
        self.config.save()
        self._assert_rejected_creation()
        self.config.delete()
        self._assert_rejected_creation()

    def test_subscription_only_support_refused_without_changing_configuration(self):
        self.config.subscription_only = True
        self.config.save()
        error = self._assert_rejected_creation()
        self.assertEqual(error.code, "configuration_error")
        self.config.refresh_from_db()
        self.assertTrue(self.config.subscription_only)

    def test_support_configuration_full_validation_precedes_creation(self):
        self.config.unsubscribed_redirect_product = ProductFactory()
        self.config.save()
        error = self._assert_rejected_creation()
        self.assertEqual(error.code, "configuration_error")

    def test_ticket_form_requires_positive_numeric_id(self):
        zendesk = self.config.zendesk_config
        for ticket_form_id in ("", " ", "0", "-12", "1.5", "invalid", "１２"):
            with self.subTest(ticket_form_id=ticket_form_id):
                zendesk.ticket_form_id = ticket_form_id
                zendesk.save()
                error = self._assert_rejected_creation()
                self.assertEqual(error.code, "configuration_error")

    def test_live_chat_requires_switch_and_each_deployment_setting(self):
        with override_switch("zendesk-chat", active=False):
            self._assert_rejected_creation(include_live_chat=True)
            self.assertEqual(get_enterprise_support_config(include_live_chat=False), self.config)
        for key in (
            "ZENDESK_CHAT_WIDGET_KEY",
            "ZENDESK_CHAT_SIGNING_KEY_ID",
            "ZENDESK_CHAT_SIGNING_SECRET",
        ):
            with self.subTest(setting=key), override_settings(**{key: ""}):
                self._assert_rejected_creation(include_live_chat=True)
                self.assertEqual(
                    get_enterprise_support_config(include_live_chat=False), self.config
                )

    def test_invalid_names_and_generated_slugs_leave_no_company(self):
        for name in ("", " \t", "x" * 151, "x" * 81, "!!!", "中文"):
            with self.subTest(name=name):
                error = self._assert_rejected_creation(name=name)
                self.assertEqual(set(error.message_dict), {"name"})
                self.assertEqual(error.error_dict["name"][0].code, "invalid")
        company = self._create(name="x" * 80)
        self.assertEqual(company.slug, "x" * 80)

    def test_case_insensitive_group_name_conflict_does_not_suffix_identity(self):
        GroupFactory(name="EXAMPLE COMPANY")
        error = self._assert_rejected_creation(name="Example Company")
        self.assertEqual(error.error_dict["name"][0].code, "company_conflict")

    def test_slug_conflict_does_not_suffix_identity(self):
        GroupProfileFactory(slug="example-company")
        error = self._assert_rejected_creation(name="Example Company")
        self.assertEqual(error.error_dict["name"][0].code, "company_conflict")

    @override_settings(READ_ONLY=True)
    def test_read_only_refuses_creation_and_settings(self):
        company = self._child()
        organization = SupportOrganizationFactory(config=self.config, group=company.group)
        self._assert_rejected_creation(PermissionDenied)
        with self.assertRaises(PermissionDenied):
            configure_enterprise_company(actor=self.actor, company=company, include_live_chat=True)
        organization.refresh_from_db()
        self.assertFalse(organization.include_live_chat)
        self.assertFalse(ZendeskOrganization.objects.filter(group_profile=company).exists())

    def test_settings_reuse_company_and_preserve_unrelated_support(self):
        company = self._child()
        member = UserFactory(groups=[company.group])
        company.leaders.add(member)
        other_config = ProductSupportConfigFactory(zendesk_config=ZendeskConfigFactory())
        unrelated = SupportOrganizationFactory(
            config=other_config, group=company.group, include_live_chat=True
        )
        identity = (company.group_id, company.slug, company.path)
        first = configure_enterprise_company(
            actor=self.actor, company=company, include_live_chat=True
        )
        mapping = ZendeskOrganization.objects.get(group_profile=company)
        second = configure_enterprise_company(
            actor=self.actor, company=company, include_live_chat=False
        )
        self.assertEqual(first.pk, second.pk)
        self.assertFalse(second.include_live_chat)
        company.refresh_from_db()
        self.assertEqual((company.group_id, company.slug, company.path), identity)
        self.assertQuerySetEqual(company.group.user_set.all(), [member])
        self.assertQuerySetEqual(company.leaders.all(), [member])
        unrelated.refresh_from_db()
        self.assertTrue(unrelated.include_live_chat)
        mapping.refresh_from_db()
        self.assertEqual(company.zendesk_organization.pk, mapping.pk)
        self.assertFalse(self.config.hybrid_support_groups.exists())

    def test_overlapping_support_configuration_rolls_back_creation(self):
        SupportOrganizationFactory(config=self.config, group=self.root.group)
        error = self._assert_rejected_creation()
        self.assertEqual(error.code, "configuration_error")

    def test_existing_department_support_prevents_parent_support(self):
        company = self._child()
        department = self._child(company)
        SupportOrganizationFactory(config=self.config, group=department.group)
        with self.assertRaises(ValidationError):
            configure_enterprise_company(actor=self.actor, company=company, include_live_chat=True)
        self.assertFalse(SupportOrganization.objects.filter(group=company.group).exists())
        self.assertFalse(ZendeskOrganization.objects.filter(group_profile=company).exists())

    def test_canonical_remote_id_cannot_be_linked_to_second_company(self):
        with patch(
            "kitsune.groups.onboarding.ZendeskClient.validate_organization", return_value="123"
        ):
            first = self._create(zendesk_organization_id="00123")
            error = self._assert_rejected_creation(
                name="Second Company", zendesk_organization_id="123"
            )
        self.assertEqual(first.zendesk_organization.zendesk_id, "123")
        self.assertEqual(error.error_dict["zendesk_organization_id"][0].code, "company_conflict")
        self.assertEqual(ZendeskOrganization.objects.get(zendesk_id="123").group_profile, first)

    def test_link_can_be_set_once_and_cannot_be_cleared_or_reassigned(self):
        company = self._create()
        mapping = company.zendesk_organization
        external_id = mapping.external_id
        with patch(
            "kitsune.groups.onboarding.ZendeskClient.validate_organization", return_value="123"
        ):
            configure_enterprise_company(
                actor=self.actor,
                company=company,
                include_live_chat=True,
                zendesk_organization_id="00123",
            )
        with patch(
            "kitsune.groups.onboarding.ZendeskClient.validate_organization", return_value="456"
        ):
            with self.assertRaises(ValidationError) as raised:
                configure_enterprise_company(
                    actor=self.actor,
                    company=company,
                    include_live_chat=False,
                    zendesk_organization_id="456",
                )
        self.assertEqual(
            raised.exception.error_dict["zendesk_organization_id"][0].code, "company_conflict"
        )
        self.assertTrue(SupportOrganization.objects.get(group=company.group).include_live_chat)
        configure_enterprise_company(
            actor=self.actor, company=company, include_live_chat=False, zendesk_organization_id=""
        )
        mapping.refresh_from_db()
        self.assertEqual(mapping.zendesk_id, "123")
        self.assertEqual(mapping.external_id, external_id)
        with patch(
            "kitsune.groups.onboarding.ZendeskClient.validate_organization",
            side_effect=AssertionError("An unchanged link must not require Zendesk availability"),
        ):
            organization = configure_enterprise_company(
                actor=self.actor,
                company=company,
                include_live_chat=True,
                zendesk_organization_id="123",
            )
        self.assertTrue(organization.include_live_chat)

    def test_canonical_id_replay_preserves_company_mapping(self):
        company = self._create()
        mapping = company.zendesk_organization
        mapping.zendesk_id = "123"
        mapping.save()
        external_id = mapping.external_id
        with patch(
            "kitsune.groups.onboarding.ZendeskClient.validate_organization", return_value="123"
        ):
            organization = configure_enterprise_company(
                actor=self.actor,
                company=company,
                include_live_chat=True,
                zendesk_organization_id="00123",
            )
        mapping.refresh_from_db()
        self.assertEqual(mapping.zendesk_id, "123")
        self.assertEqual(mapping.external_id, external_id)
        self.assertEqual(organization.group, company.group)
        self.assertTrue(organization.include_live_chat)

    def test_remote_failures_are_safe_and_leave_no_partial_company(self):
        for error, code in (
            (ZendeskProvisioningConflict("resource_missing"), "resource_missing"),
            (APIException("private-provider-response"), "zendesk_unavailable"),
            (requests.Timeout("private-provider-response"), "zendesk_unavailable"),
            (RatelimitBudgetExceeded("private-provider-response"), "zendesk_unavailable"),
        ):
            with (
                self.subTest(error=type(error)),
                patch(
                    "kitsune.groups.onboarding.ZendeskClient.validate_organization",
                    side_effect=error,
                ),
            ):
                raised = self._assert_rejected_creation(zendesk_organization_id="123")
                self.assertEqual(raised.error_dict["zendesk_organization_id"][0].code, code)
                self.assertNotIn("private-provider-response", str(raised))

    def test_failed_remote_validation_preserves_existing_settings(self):
        company = self._child()
        organization = SupportOrganizationFactory(config=self.config, group=company.group)
        with patch(
            "kitsune.groups.onboarding.ZendeskClient.validate_organization",
            side_effect=requests.Timeout("private-provider-response"),
        ):
            with self.assertRaises(ValidationError):
                configure_enterprise_company(
                    actor=self.actor,
                    company=company,
                    include_live_chat=True,
                    zendesk_organization_id="123",
                )
        organization.refresh_from_db()
        self.assertFalse(organization.include_live_chat)
        self.assertFalse(ZendeskOrganization.objects.filter(group_profile=company).exists())

    def test_unrelated_integrity_errors_are_not_misreported_as_conflicts(self):
        with patch(
            "kitsune.groups.onboarding.SupportOrganization.save",
            side_effect=IntegrityError("unrelated constraint"),
        ):
            self._assert_rejected_creation(IntegrityError)


@override_settings(
    ENTERPRISE_GROUP_SLUG="enterprise-concurrency-root",
    ES_LIVE_INDEXING=False,
    READ_ONLY=False,
)
class EnterpriseCompanyConcurrencyTests(TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.root = GroupProfileFactory(
            slug="enterprise-concurrency-root",
            visibility=GroupProfile.Visibility.PRIVATE,
            isolation_enabled=True,
        )
        self.actor = UserFactory(is_staff=True)
        self.root.leaders.add(self.actor)
        self.config = ProductSupportConfigFactory(
            product=ProductFactory(slug=self.root.slug),
            zendesk_config=ZendeskConfigFactory(),
        )

    def test_simultaneous_case_insensitive_company_names_have_one_winner(self):
        barrier = Barrier(2, timeout=10)

        def create(name):
            try:
                barrier.wait()
                try:
                    return create_enterprise_company(
                        actor=self.actor, name=name, include_live_chat=False
                    ).pk
                except ValidationError as error:
                    return error.error_dict["name"][0].code
            finally:
                connections.close_all()

        # Release the fixture connection so both workers can use the bounded pool.
        connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(create, ("Concurrent Company", "CONCURRENT COMPANY")))
        self.assertEqual(results.count("company_conflict"), 1)
        company = GroupProfile.objects.get(group__name__iexact="Concurrent Company")
        self.assertIn(company.pk, results)
        self.assertEqual(GroupProfile.objects.get_parent(company), self.root)
        self.assertEqual(SupportOrganization.objects.get(config=self.config).group, company.group)
        self.assertEqual(ZendeskOrganization.objects.get().group_profile, company)

    def test_simultaneous_canonical_links_cannot_share_remote_organization(self):
        companies = [
            GroupProfile.objects.add_child(self.root, create_kwargs={"group": GroupFactory()})
            for _ in range(2)
        ]
        barrier = Barrier(2, timeout=10)
        original_save = ZendeskOrganization.save

        def save_mapping(mapping, *args, **kwargs):
            if mapping.zendesk_id is not None:
                # Both transactions must pass the ownership lookup before either writes.
                barrier.wait()
            return original_save(mapping, *args, **kwargs)

        def configure(entry):
            company, organization_id = entry
            try:
                try:
                    configure_enterprise_company(
                        actor=self.actor,
                        company=company,
                        include_live_chat=False,
                        zendesk_organization_id=organization_id,
                    )
                    return company.pk
                except ValidationError as error:
                    return error.error_dict["zendesk_organization_id"][0].code
            finally:
                connections.close_all()

        connections.close_all()
        with (
            patch(
                "kitsune.groups.onboarding.ZendeskClient.validate_organization", return_value="123"
            ),
            patch.object(ZendeskOrganization, "save", save_mapping),
            ThreadPoolExecutor(max_workers=2) as pool,
        ):
            results = list(pool.map(configure, zip(companies, ("00123", "123"), strict=True)))
        self.assertEqual(results.count("company_conflict"), 1)
        mapping = ZendeskOrganization.objects.get(zendesk_id="123")
        self.assertIn(mapping.group_profile_id, results)
        loser = next(company for company in companies if company.pk != mapping.group_profile_id)
        self.assertFalse(ZendeskOrganization.objects.filter(group_profile=loser).exists())
        self.assertFalse(SupportOrganization.objects.filter(group=loser.group).exists())


@override_settings(ENTERPRISE_GROUP_SLUG="enterprise-root")
class EnterpriseCompanyViewTests(TestCase):
    def setUp(self):
        super().setUp()
        self.root = GroupProfileFactory(
            slug="enterprise-root", visibility=GroupProfile.Visibility.PRIVATE
        )
        self.actor = UserFactory(is_staff=True)
        self.root.leaders.add(self.actor)
        self.config = ProductSupportConfigFactory(
            product=ProductFactory(slug=self.root.slug),
            zendesk_config=ZendeskConfigFactory(),
        )
        self.company = GroupProfile.objects.add_child(
            self.root, create_kwargs={"group": GroupFactory(name="Existing Enterprise Company")}
        )
        self.client.force_login(self.actor)
        self.create_url = reverse("groups.manage_company", args=[self.root.slug])
        self.settings_url = reverse("groups.manage_company", args=[self.company.slug])

    def test_create_company_from_root(self):
        root_page = self.client.get(reverse("groups.profile", args=[self.root.slug]))
        self.assertEqual(
            pq(root_page.content)("#enterprise-onboarding a").attr("href"), self.create_url
        )
        response = self.client.post(
            self.create_url,
            {
                "name": "New Enterprise Company",
                "creating": "false",
                "company": self.company.pk,
            },
        )
        company = GroupProfile.objects.get(slug="new-enterprise-company")
        self.assertRedirects(response, company.get_absolute_url())
        self.assertEqual(GroupProfile.objects.get_parent(company), self.root)
        self.assertEqual(company.depth, 2)
        self.assertEqual(company.visibility, GroupProfile.Visibility.PRIVATE)
        self.assertFalse(company.group.user_set.exists())
        self.assertFalse(company.leaders.exists())
        self.assertFalse(
            SupportOrganization.objects.get(
                group=company.group, config=self.config
            ).include_live_chat
        )
        self.assertIsNone(company.zendesk_organization.zendesk_id)

    def test_creation_requires_name_even_with_forged_edit_mode(self):
        before = GroupProfile.objects.count()
        response = self.client.post(
            self.create_url, {"creating": "false", "company": self.company.pk}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(pq(response.content)("#enterprise-company-form .form-error")), 1)
        self.assertEqual(GroupProfile.objects.count(), before)
        self.assertFalse(SupportOrganization.objects.filter(config=self.config).exists())

    def test_nonstaff_root_leader_keeps_member_controls_but_cannot_onboard(self):
        self.actor.is_staff = False
        self.actor.save()
        for profile in (self.root, self.company):
            page = self.client.get(reverse("groups.profile", args=[profile.slug]))
            self.assertEqual(page.status_code, 200)
            self.assertEqual(len(pq(page.content)("#enterprise-onboarding")), 0)
            self.assertEqual(len(pq(page.content)("#add-users-form")), 1)
        for url in (self.create_url, self.settings_url):
            self.assertEqual(self.client.get(url).status_code, 403)
            self.assertEqual(self.client.post(url, {"name": "Denied Company"}).status_code, 403)
        self.assertFalse(Group.objects.filter(name="Denied Company").exists())

    def test_staff_without_root_leadership_cannot_onboard(self):
        company_leader = UserFactory(is_staff=True)
        self.company.leaders.add(company_leader)
        self.client.force_login(company_leader)
        page = self.client.get(reverse("groups.profile", args=[self.company.slug]))
        self.assertEqual(page.status_code, 200)
        self.assertEqual(len(pq(page.content)("#enterprise-onboarding")), 0)
        self.assertEqual(self.client.post(self.settings_url, {}).status_code, 403)

    def test_anonymous_uses_login_redirect(self):
        self.client.logout()
        for url in (self.create_url, self.settings_url):
            self.assertEqual(self.client.get(url).status_code, 302)

    def test_other_root_and_department_cannot_be_targeted(self):
        other_root = GroupProfileFactory()
        department = GroupProfile.objects.add_child(
            self.company, create_kwargs={"group": GroupFactory()}
        )
        before = GroupProfile.objects.count()
        for profile in (other_root, department):
            url = reverse("groups.manage_company", args=[profile.slug])
            self.assertEqual(self.client.get(url).status_code, 404)
            self.assertEqual(self.client.post(url, {"name": "Forged Company"}).status_code, 404)
        self.assertEqual(GroupProfile.objects.count(), before)
        self.assertFalse(SupportOrganization.objects.filter(config=self.config).exists())
        self.assertFalse(Group.objects.filter(name="Forged Company").exists())

    def test_duplicate_company_redisplays_form_without_partial_rows(self):
        before = GroupProfile.objects.count()
        response = self.client.post(self.create_url, {"name": self.company.group.name.upper()})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(pq(response.content)("#enterprise-company-form .form-error")), 1)
        self.assertEqual(pq(response.content)("#id_name").val(), self.company.group.name.upper())
        self.assertEqual(GroupProfile.objects.count(), before)

    def test_missing_configuration_is_actionable_without_creating_company(self):
        self.config.is_active = False
        self.config.save()
        response = self.client.post(self.create_url, {"name": "Unconfigured Company"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(pq(response.content)("#enterprise-company-form [role=alert]")), 1)
        self.assertFalse(Group.objects.filter(name="Unconfigured Company").exists())

    def test_existing_company_can_get_support_without_being_recreated(self):
        response = self.client.post(self.settings_url, {"zendesk_organization_id": ""})
        self.assertRedirects(response, self.company.get_absolute_url())
        support = SupportOrganization.objects.get(group=self.company.group, config=self.config)
        self.assertFalse(support.include_live_chat)
        self.assertFalse(self.company.group.user_set.exists())
        page = self.client.get(self.company.get_absolute_url())
        self.assertEqual(
            pq(page.content)("#enterprise-onboarding a").attr("href"), self.settings_url
        )

    def test_saved_organization_link_is_readonly_even_for_forged_post(self):
        ZendeskOrganization.objects.create(group_profile=self.company, zendesk_id="123")
        page = self.client.get(self.settings_url)
        self.assertEqual(len(pq(page.content)("#id_name")), 0)
        self.assertIn("disabled", pq(page.content)("#id_zendesk_organization_id")[0].attrib)
        self.assertEqual(pq(page.content)("#id_zendesk_organization_id").val(), "123")
        original_name = self.company.group.name
        original_slug = self.company.slug
        response = self.client.post(
            self.settings_url,
            {
                "name": "Forged Company",
                "creating": "true",
                "company": self.root.pk,
                "zendesk_organization_id": "456",
            },
        )
        self.assertRedirects(response, self.company.get_absolute_url())
        self.assertEqual(
            ZendeskOrganization.objects.get(group_profile=self.company).zendesk_id, "123"
        )
        self.company.refresh_from_db()
        self.assertEqual(self.company.group.name, original_name)
        self.assertEqual(self.company.slug, original_slug)
        self.assertFalse(Group.objects.filter(name="Forged Company").exists())

    def test_company_mutations_require_csrf(self):
        self.client.handler.enforce_csrf_checks = True
        self.assertEqual(
            self.client.post(self.create_url, {"name": "Missing CSRF Company"}).status_code, 403
        )
        self.assertEqual(self.client.post(self.settings_url, {}).status_code, 403)
        self.assertFalse(Group.objects.filter(name="Missing CSRF Company").exists())
