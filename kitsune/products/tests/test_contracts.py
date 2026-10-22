import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from threading import Barrier
from unittest.mock import patch

from django.contrib import admin
from django.db import connections, transaction
from django.db.models.deletion import ProtectedError
from django.test import Client, TransactionTestCase, override_settings
from django.urls import path

from kitsune.customercare.models import ZendeskOrganization
from kitsune.customercare.zendesk import ZendeskClient
from kitsune.groups.tests import DepartmentFactory, EnterpriseCompanyFactory, GroupProfileFactory
from kitsune.products.admin import lock_contract_company
from kitsune.products.models import Product, SupportContract, SupportCoverage, ZendeskConfig
from kitsune.products.tests import ProductFactory, SupportCoverageFactory, ZendeskConfigFactory
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.urls import urlpatterns as sumo_urlpatterns
from kitsune.users.tests import UserFactory, add_permission

urlpatterns = [path("admin/", admin.site.urls), *sumo_urlpatterns]
Status = SupportContract.Status


class ContractAdminFixtures:
    def setUp(self):
        super().setUp()
        self.actor = UserFactory(is_staff=True, is_superuser=True)
        self.company = EnterpriseCompanyFactory()
        self.product = ProductFactory()
        self.config = ZendeskConfigFactory()
        self.add_url = reverse("admin:products_supportcontract_add")

    def admin_client(self):
        client = Client()
        client.force_login(self.actor, backend="kitsune.users.auth.SumoOIDCAuthBackend")
        session = client.session
        session["oidc_id_token_expiration"] = time.time() + 3600
        session.save()
        return client

    def change_url(self, contract):
        return reverse("admin:products_supportcontract_change", args=[contract.pk])

    def covered(self, starts_on="2026-01-01", ends_on="2026-03-31", **kwargs):
        kwargs.setdefault("contract__company", self.company)
        kwargs.setdefault("product", self.product)
        return SupportCoverageFactory(
            contract__starts_on=date.fromisoformat(starts_on),
            contract__ends_on=date.fromisoformat(ends_on),
            **kwargs,
        )

    def coverage_row(self, coverage=None, **changes):
        coverage = coverage or SupportCoverage(
            product=self.product,
            zendesk_config=self.config,
            zendesk_product_value="enterprise_browser",
            includes_chat=True,
        )
        return {
            "id": coverage.pk or "",
            "contract": coverage.contract_id or "",
            "product": coverage.product_id,
            "zendesk_config": coverage.zendesk_config_id,
            "zendesk_product_value": coverage.zendesk_product_value,
            "includes_chat": "on" if coverage.includes_chat else "",
            **changes,
        }

    def contract_data(self, *, contract=None, coverages=None, **changes):
        contract = contract or SupportContract(
            company=self.company,
            name="Annual support",
            starts_on=date(2026, 1, 1),
            ends_on=date(2026, 3, 31),
        )
        if coverages is None:
            rows = contract.coverages.all() if contract.pk else [None]
            coverages = [self.coverage_row(coverage) for coverage in rows]
        data = {
            field: getattr(contract, field) for field in ("name", "status", "starts_on", "ends_on")
        }
        data.update(
            {
                "company": contract.company_id,
                "_save": "Save",
                "coverages-TOTAL_FORMS": str(len(coverages)),
                "coverages-INITIAL_FORMS": str(sum(bool(row["id"]) for row in coverages)),
                "coverages-MIN_NUM_FORMS": "1",
                "coverages-MAX_NUM_FORMS": "1000",
                **changes,
            }
        )
        for index, row in enumerate(coverages):
            data.update({f"coverages-{index}-{key}": value for key, value in row.items()})
        return data

    def assert_overlap_rejected(self, response, contract=None):
        self.assertContains(response, "already covers a selected product")
        if contract is not None:
            ends_on = contract.ends_on
            contract.refresh_from_db()
            self.assertEqual(contract.ends_on, ends_on)


@override_settings(
    ENTERPRISE_GROUP_SLUG="contract-admin-root", ROOT_URLCONF=__name__, READ_ONLY=False
)
class SupportContractAdminTests(ContractAdminFixtures, TestCase):
    def setUp(self):
        super().setUp()
        self.client = self.admin_client()

    def test_create_bundle_with_independent_zendesk_configs(self):
        other_product, other_config = ProductFactory(), ZendeskConfigFactory()
        rows = [
            self.coverage_row(),
            self.coverage_row(
                product=other_product.pk,
                zendesk_config=other_config.pk,
                zendesk_product_value="enterprise_bundle",
                includes_chat="",
            ),
        ]
        response = self.client.post(self.add_url, self.contract_data(coverages=rows))
        self.assertEqual(response.status_code, 302)
        contract = self.company.support_contracts.get()
        self.assertCountEqual(
            contract.coverages.values_list(
                "product_id", "zendesk_config_id", "zendesk_product_value", "includes_chat"
            ),
            [
                (self.product.pk, self.config.pk, "enterprise_browser", True),
                (other_product.pk, other_config.pk, "enterprise_bundle", False),
            ],
        )

    def test_edit_contract_and_coverage_without_moving_company(self):
        coverage = self.covered()
        contract = coverage.contract
        data = self.contract_data(
            contract=contract, company=EnterpriseCompanyFactory().pk, name="Renewed agreement"
        )
        data["coverages-0-zendesk_product_value"] = "renewed_browser"
        self.assertEqual(self.client.post(self.change_url(contract), data).status_code, 302)
        contract.refresh_from_db()
        coverage.refresh_from_db()
        self.assertEqual(contract.company, self.company)
        self.assertEqual(contract.name, "Renewed agreement")
        self.assertEqual(coverage.zendesk_product_value, "renewed_browser")

    def test_invalid_period_and_company_are_field_errors(self):
        for field, changes in (
            ("ends_on", {"starts_on": "2026-04-01", "ends_on": "2026-03-31"}),
            ("company", {"company": "not-a-company"}),
            ("company", {"company": "9" * 100}),
        ):
            with self.subTest(changes=changes):
                response = self.client.post(self.add_url, self.contract_data(**changes))
                self.assertEqual(response.status_code, 200)
                self.assertIn(field, response.context["adminform"].form.errors)
                self.assertFalse(SupportContract.objects.exists())

    def test_company_choices_exclude_root_departments_and_other_trees(self):
        unrelated = GroupProfileFactory()
        for company in (
            self.company.get_root(),
            DepartmentFactory(company=self.company),
            unrelated,
            EnterpriseCompanyFactory(root=unrelated),
        ):
            with self.subTest(company=company.slug):
                response = self.client.post(self.add_url, self.contract_data(company=company.pk))
                self.assertEqual(response.status_code, 200)
                self.assertIn("company", response.context["adminform"].form.errors)
                self.assertFalse(SupportContract.objects.exists())

    def test_missing_enterprise_root_is_a_form_error(self):
        with override_settings(ENTERPRISE_GROUP_SLUG="missing-contract-root"):
            self.assertEqual(self.client.get(self.add_url).status_code, 200)
            response = self.client.post(self.add_url, self.contract_data())
        self.assertEqual(response.status_code, 200)
        self.assertIn("company", response.context["adminform"].form.errors)
        self.assertFalse(SupportContract.objects.exists())

    def test_empty_and_duplicate_coverages_are_rejected(self):
        duplicate = self.coverage_row(zendesk_config=ZendeskConfigFactory().pk)
        for rows in ([], [self.coverage_row(), duplicate]):
            with self.subTest(rows=rows):
                response = self.client.post(self.add_url, self.contract_data(coverages=rows))
                errors = response.context["inline_admin_formsets"][0].formset.non_form_errors()
                self.assertContains(response, errors[0])
                self.assertFalse(SupportContract.objects.exists())
                self.assertFalse(SupportCoverage.objects.exists())

    def test_active_and_suspended_contracts_block_inclusive_overlap(self):
        for existing, new in (
            (Status.ACTIVE, Status.SUSPENDED),
            (Status.SUSPENDED, Status.ACTIVE),
        ):
            company = EnterpriseCompanyFactory()
            self.covered(contract__company=company, contract__status=existing)
            for start, end in (
                ("2025-12-01", "2026-01-01"),
                ("2026-03-31", "2026-04-30"),
                ("2026-02-01", "2026-02-28"),
                ("2025-12-01", "2026-04-30"),
            ):
                with self.subTest(existing=existing, new=new, start=start, end=end):
                    data = self.contract_data(
                        company=company.pk, status=new, starts_on=start, ends_on=end
                    )
                    response = self.client.post(self.add_url, data)
                    self.assert_overlap_rejected(response)
                    self.assertEqual(company.support_contracts.count(), 1)

    def test_editing_dates_cannot_extend_existing_coverage_into_overlap(self):
        contract = self.covered().contract
        self.covered("2026-04-01", "2026-06-30")
        response = self.client.post(
            self.change_url(contract), self.contract_data(contract=contract, ends_on="2026-04-01")
        )
        self.assert_overlap_rejected(response, contract)

    def test_omitted_coverage_cannot_bypass_overlap_validation_on_edit(self):
        contract = self.covered().contract
        self.covered("2026-04-01", "2026-06-30")
        submitted = SupportCoverageFactory(contract=contract)
        data = self.contract_data(
            contract=contract, coverages=[self.coverage_row(submitted)], ends_on="2026-04-01"
        )
        response = self.client.post(self.change_url(contract), data)
        self.assert_overlap_rejected(response, contract)
        self.assertEqual(contract.coverages.count(), 2)

    def test_contract_permission_alone_cannot_bypass_coverage_validation(self):
        contract = self.covered().contract
        self.covered("2026-04-01", "2026-06-30")
        self.actor = UserFactory(is_staff=True)
        add_permission(self.actor, SupportContract, "change_supportcontract")
        response = self.admin_client().post(
            self.change_url(contract), self.contract_data(contract=contract, ends_on="2026-04-01")
        )
        self.assert_overlap_rejected(response, contract)

    def test_add_only_staff_can_create_contract_with_coverage(self):
        self.actor = UserFactory(is_staff=True)
        for model, permission in (
            (SupportContract, "add_supportcontract"),
            (Product, "view_product"),
            (ZendeskConfig, "view_zendeskconfig"),
        ):
            add_permission(self.actor, model, permission)
        client = self.admin_client()
        self.assertContains(client.get(self.add_url), 'name="coverages-0-product"')
        self.assertEqual(client.post(self.add_url, self.contract_data()).status_code, 302)
        self.assertEqual(
            self.company.support_contracts.get().coverages.get().product, self.product
        )

    def test_reactivating_cancelled_contract_rechecks_existing_coverages(self):
        self.covered()
        contract = self.covered(contract__status=Status.CANCELLED).contract
        response = self.client.post(
            self.change_url(contract), self.contract_data(contract=contract, status=Status.ACTIVE)
        )
        self.assert_overlap_rejected(response, contract)
        self.assertEqual(contract.status, Status.CANCELLED)

    def test_cancelled_contracts_do_not_block_in_either_direction(self):
        for existing, new in (
            (Status.CANCELLED, Status.ACTIVE),
            (Status.ACTIVE, Status.CANCELLED),
            (Status.CANCELLED, Status.SUSPENDED),
        ):
            with self.subTest(existing=existing, new=new):
                company = EnterpriseCompanyFactory()
                self.covered(contract__company=company, contract__status=existing)
                response = self.client.post(
                    self.add_url, self.contract_data(company=company.pk, status=new)
                )
                self.assertEqual(response.status_code, 302)
                self.assertEqual(company.support_contracts.count(), 2)

    def test_adjacent_period_and_single_day_contracts_are_allowed(self):
        self.covered()
        response = self.client.post(
            self.add_url, self.contract_data(starts_on="2026-04-01", ends_on="2026-04-01")
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.company.support_contracts.count(), 2)

    def test_overlap_is_allowed_for_other_companies_and_products(self):
        self.covered(contract__company=EnterpriseCompanyFactory())
        self.covered(product=ProductFactory())
        self.assertEqual(self.client.post(self.add_url, self.contract_data()).status_code, 302)
        self.assertEqual(self.company.support_contracts.count(), 2)

    def test_submitted_inline_deletion_preserves_saved_coverage(self):
        coverage = self.covered()
        data = self.contract_data(contract=coverage.contract)
        data["coverages-0-DELETE"] = "on"
        response = self.client.post(self.change_url(coverage.contract), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(coverage.contract.coverages.filter(pk=coverage.pk).exists())

    def test_contract_delete_view_refuses_and_preserves_history(self):
        coverage = self.covered("2025-01-01", "2025-12-31", contract__status=Status.CANCELLED)
        url = reverse("admin:products_supportcontract_delete", args=[coverage.contract_id])
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, {"post": "yes"}).status_code, 403)
        self.assertTrue(self.company.support_contracts.filter(coverages=coverage).exists())

    def test_bulk_contract_deletion_is_not_offered_and_preserves_history(self):
        coverage = self.covered()
        url = reverse("admin:products_supportcontract_changelist")
        self.assertNotContains(self.client.get(url), 'value="delete_selected"')
        response = self.client.post(
            url,
            {
                "action": "delete_selected",
                "_selected_action": [coverage.contract_id],
                "post": "yes",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.company.support_contracts.filter(coverages=coverage).exists())

    def test_contract_creates_only_local_zendesk_identity(self):
        with patch.object(ZendeskClient, "__init__", side_effect=AssertionError):
            response = self.client.post(self.add_url, self.contract_data())
        self.assertEqual(response.status_code, 302)
        self.assertIsNone(ZendeskOrganization.objects.get(group_profile=self.company).zendesk_id)

    def test_company_deletion_preserves_contract_history(self):
        coverage = self.covered(contract__status=Status.CANCELLED)
        with self.assertRaises(ProtectedError), transaction.atomic():
            self.company.delete()
        self.assertTrue(self.company.support_contracts.filter(coverages=coverage).exists())


@override_settings(
    ENTERPRISE_GROUP_SLUG="contract-concurrency-root",
    ROOT_URLCONF=__name__,
    READ_ONLY=False,
    ES_LIVE_INDEXING=False,
)
class SupportContractConcurrencyTests(ContractAdminFixtures, TransactionTestCase):
    def race(self, *submissions):
        clients = [self.admin_client() for _ in submissions]
        barrier = Barrier(len(submissions), timeout=10)

        def synchronize_company(company_id):
            barrier.wait()
            lock_contract_company(company_id)

        def post(item):
            client, (url, data) = item
            try:
                response = client.post(url, data)
                return response.status_code, response.content
            finally:
                connections.close_all()

        connections.close_all()
        with (
            patch("kitsune.products.admin.lock_contract_company", synchronize_company),
            ThreadPoolExecutor(max_workers=len(submissions)) as pool,
        ):
            results = list(pool.map(post, zip(clients, submissions, strict=True)))
        self.assertCountEqual([status for status, content in results], [200, 302])
        rejected = next(body for status, body in results if status == 200)
        self.assertIn(b"already covers a selected product", rejected)

    def test_simultaneous_overlapping_admin_posts_have_one_winner(self):
        submission = (self.add_url, self.contract_data())
        self.race(submission, submission)
        self.assertEqual(self.company.support_contracts.count(), 1)

    def test_overlapping_edit_and_add_have_one_winner_without_posted_edit_company(self):
        contract = self.covered().contract
        data = self.contract_data(contract=contract, ends_on="2026-04-30")
        del data["company"]
        self.race(
            (self.change_url(contract), data),
            (self.add_url, self.contract_data(starts_on="2026-04-01", ends_on="2026-04-30")),
        )
        blocking = self.company.support_contracts.filter(
            status__in=(Status.ACTIVE, Status.SUSPENDED),
            coverages__product=self.product,
            starts_on__lte=date(2026, 4, 15),
            ends_on__gte=date(2026, 4, 15),
        )
        self.assertEqual(blocking.count(), 1)
