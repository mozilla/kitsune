from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.forms.models import inlineformset_factory

from kitsune.groups.models import GroupProfile
from kitsune.products.admin import ProductSupportConfigForm, SupportOrganizationInlineFormSet
from kitsune.products.models import ProductSupportConfig, SupportOrganization
from kitsune.products.tests import (
    ProductFactory,
    ProductSupportConfigFactory,
    SupportOrganizationFactory,
    TopicFactory,
    ZendeskConfigFactory,
)
from kitsune.questions.tests import AAQConfigFactory, QuestionLocaleFactory
from kitsune.sumo.tests import TestCase


class TopicModelTests(TestCase):
    def test_path(self):
        """Verify that the path property works."""
        p = ProductFactory(slug="p")
        t1 = TopicFactory(products=[p], slug="t1")
        t2 = TopicFactory(products=[p], slug="t2", parent=t1)
        t3 = TopicFactory(products=[p], slug="t3", parent=t2)

        self.assertEqual(t1.path, [t1.slug])
        self.assertEqual(t2.path, [t1.slug, t2.slug])
        self.assertEqual(t3.path, [t1.slug, t2.slug, t3.slug])

    def test_absolute_url(self):
        p = ProductFactory()
        t = TopicFactory(products=[p])
        expected = f"/en-US/products/{p.slug}/{t.slug}"
        actual = t.get_absolute_url(p.slug)
        self.assertEqual(actual, expected)

    def test_absolute_url_subtopic(self):
        p = ProductFactory()
        t1 = TopicFactory(products=[p])
        t2 = TopicFactory(parent=t1, products=[p])
        expected = f"/en-US/products/{p.slug}/{t1.slug}/{t2.slug}"
        actual = t2.get_absolute_url(p.slug)
        self.assertEqual(actual, expected)

    def test_absolute_url_topics(self):
        t = TopicFactory()
        expected = f"/en-US/topics/{t.slug}"
        actual = t.get_absolute_url()
        self.assertEqual(actual, expected)


class ProductModelTests(TestCase):
    def test_absolute_url(self):
        p = ProductFactory()
        expected = "/en-US/products/{p}".format(p=p.slug)
        actual = p.get_absolute_url()
        self.assertEqual(actual, expected)


class ProductSupportConfigCleanTests(TestCase):
    def test_forum_config_with_no_locales_raises(self):
        """Active config with forum_config that has no enabled locales should fail."""
        aaq_config = AAQConfigFactory()
        product = ProductFactory()
        psc = ProductSupportConfigFactory(
            product=product,
            forum_config=aaq_config,
            is_active=True,
        )
        with self.assertRaises(ValidationError):
            psc.clean()

    def test_forum_config_with_locales_passes(self):
        """Active config with forum_config that has enabled locales should pass."""
        locale = QuestionLocaleFactory(locale="en-US")
        aaq_config = AAQConfigFactory(enabled_locales=[locale])
        product = ProductFactory()
        psc = ProductSupportConfigFactory(
            product=product,
            forum_config=aaq_config,
            is_active=True,
        )
        psc.clean()  # Should not raise

    def test_active_with_zendesk_only_passes(self):
        """Active config with only zendesk_config should pass."""
        zendesk_config = ZendeskConfigFactory()
        product = ProductFactory()
        psc = ProductSupportConfigFactory(
            product=product,
            zendesk_config=zendesk_config,
            is_active=True,
        )
        psc.clean()  # Should not raise

    def test_active_with_both_channels_passes(self):
        """Active config with both channels should pass."""
        locale = QuestionLocaleFactory(locale="en-US")
        aaq_config = AAQConfigFactory(enabled_locales=[locale])
        zendesk_config = ZendeskConfigFactory()
        product = ProductFactory()
        psc = ProductSupportConfigFactory(
            product=product,
            forum_config=aaq_config,
            zendesk_config=zendesk_config,
            is_active=True,
        )
        psc.clean()  # Should not raise

    def test_inactive_skips_validation(self):
        """Inactive config skips all validation."""
        aaq_config = AAQConfigFactory()
        zendesk_config = ZendeskConfigFactory()
        product = ProductFactory()
        psc = ProductSupportConfigFactory(
            product=product,
            forum_config=aaq_config,
            zendesk_config=zendesk_config,
            is_active=False,
        )
        psc.clean()  # Should not raise even though forum_config has no locales

    def test_active_with_no_channels_raises(self):
        """Active config with no support channels should fail validation."""
        product = ProductFactory()
        psc = ProductSupportConfig(product=product, is_active=True)
        with self.assertRaises(ValidationError):
            psc.clean()

    def test_save_with_no_channels_raises_integrity_error(self):
        """Saving with no support channels should fail due to DB constraint."""
        product = ProductFactory()
        with self.assertRaises(IntegrityError):
            ProductSupportConfigFactory(
                product=product,
                forum_config=None,
                zendesk_config=None,
            )


class HybridSupportGroupsValidationTests(TestCase):
    def setUp(self):
        self.Group = Group
        self.GroupProfile = GroupProfile
        self.Form = ProductSupportConfigForm

        zd = ZendeskConfigFactory(name="zd")
        self.config = ProductSupportConfigFactory(product=ProductFactory(), zendesk_config=zd)

        self.root_group = Group.objects.create(name="firefox-enterprise")
        self.root = GroupProfile.add_root(group=self.root_group, slug="firefox-enterprise")
        self.c1_group = Group.objects.create(name="company1")
        self.c1 = self.root.add_child(group=self.c1_group, slug="company1")
        self.c2_group = Group.objects.create(name="company2")
        self.c2 = self.root.add_child(group=self.c2_group, slug="company2")
        self.it_group = Group.objects.create(name="company1.IT")
        self.c1_it = self.c1.add_child(group=self.it_group, slug="company1-it")

    def _build_form(self, *groups):
        return self.Form(
            data={
                "product": str(self.config.product_id),
                "is_active": "on",
                "zendesk_config": str(self.config.zendesk_config_id),
                "default_support_type": self.config.default_support_type,
                "hybrid_support_groups": [str(g.pk) for g in groups],
            },
            instance=self.config,
        )

    def test_root_group_is_rejected(self):
        form = self._build_form(self.root_group)
        self.assertFalse(form.is_valid())
        self.assertIn("hybrid_support_groups", form.errors)

    def test_ancestor_in_another_config_is_rejected(self):
        other_zd = ZendeskConfigFactory(name="other-zd")
        other_config = ProductSupportConfigFactory(
            product=ProductFactory(), zendesk_config=other_zd
        )
        other_config.hybrid_support_groups.add(self.c1_group)

        form = self._build_form(self.it_group)
        self.assertFalse(form.is_valid())
        self.assertIn("hybrid_support_groups", form.errors)

    def test_descendant_in_another_config_is_rejected(self):
        other_zd = ZendeskConfigFactory(name="other-zd")
        other_config = ProductSupportConfigFactory(
            product=ProductFactory(), zendesk_config=other_zd
        )
        other_config.hybrid_support_groups.add(self.it_group)

        form = self._build_form(self.c1_group)
        self.assertFalse(form.is_valid())
        self.assertIn("hybrid_support_groups", form.errors)

    def test_two_groups_in_same_chain_in_one_submission_rejected(self):
        form = self._build_form(self.c1_group, self.it_group)
        self.assertFalse(form.is_valid())
        self.assertIn("hybrid_support_groups", form.errors)

    def test_independent_groups_accepted(self):
        form = self._build_form(self.c1_group, self.c2_group)
        self.assertTrue(form.is_valid(), msg=str(form.errors))

    def test_group_without_groupprofile_skipped(self):
        flat_group = self.Group.objects.create(name="flat-group")
        form = self._build_form(flat_group)
        self.assertTrue(form.is_valid(), msg=str(form.errors))


class SupportOrganizationValidationTests(TestCase):
    def setUp(self):
        self.config = ProductSupportConfigFactory(
            product=ProductFactory(), zendesk_config=ZendeskConfigFactory(name="zd")
        )

        root_group = Group.objects.create(name="firefox-enterprise")
        self.root = GroupProfile.add_root(group=root_group, slug="firefox-enterprise")
        self.c1_group = Group.objects.create(name="company1")
        self.c1 = self.root.add_child(group=self.c1_group, slug="company1")
        self.c2_group = Group.objects.create(name="company2")
        self.c2 = self.root.add_child(group=self.c2_group, slug="company2")
        self.it_group = Group.objects.create(name="company1.IT")
        self.c1_it = self.c1.add_child(group=self.it_group, slug="company1-it")

    def _other_config(self):
        return ProductSupportConfigFactory(
            product=ProductFactory(), zendesk_config=ZendeskConfigFactory(name="other-zd")
        )

    def test_subgroup_organizations_are_valid(self):
        SupportOrganization(config=self.config, group=self.c1_group).full_clean()
        SupportOrganizationFactory(config=self.config, group=self.c1_group)
        SupportOrganization(config=self.config, group=self.c2_group).full_clean()

    def test_tree_root_rejected(self):
        with self.assertRaises(ValidationError) as cm:
            SupportOrganization(config=self.config, group=self.root.group).full_clean()
        self.assertIn("group", cm.exception.message_dict)

    def test_group_without_profile_rejected(self):
        flat_group = Group.objects.create(name="flat-group")
        with self.assertRaises(ValidationError) as cm:
            SupportOrganization(config=self.config, group=flat_group).full_clean()
        self.assertIn("group", cm.exception.message_dict)

    def test_nested_within_saved_group_of_same_config_rejected(self):
        SupportOrganizationFactory(config=self.config, group=self.c1_group)
        with self.assertRaises(ValidationError) as cm:
            SupportOrganization(config=self.config, group=self.it_group).full_clean()
        [message] = cm.exception.message_dict["group"]
        self.assertIn(self.c1_group.name, message)

    def test_nested_within_other_products_m2m_group_rejected(self):
        self._other_config().hybrid_support_groups.add(self.c1_group)
        with self.assertRaises(ValidationError) as cm:
            SupportOrganization(config=self.config, group=self.it_group).full_clean()
        [message] = cm.exception.message_dict["group"]
        self.assertIn(self.c1_group.name, message)

    def test_containing_other_products_organization_rejected(self):
        SupportOrganizationFactory(config=self._other_config(), group=self.it_group)
        with self.assertRaises(ValidationError) as cm:
            SupportOrganization(config=self.config, group=self.c1_group).full_clean()
        [message] = cm.exception.message_dict["group"]
        self.assertIn(self.it_group.name, message)

    def test_same_group_allowed_for_two_products(self):
        SupportOrganizationFactory(config=self._other_config(), group=self.c1_group)
        SupportOrganization(config=self.config, group=self.c1_group).full_clean()

    def test_live_chat_requires_zendesk_support(self):
        forum_only = ProductSupportConfigFactory(
            product=ProductFactory(), forum_config=AAQConfigFactory()
        )
        SupportOrganization(config=forum_only, group=self.c1_group).full_clean()
        with self.assertRaises(ValidationError) as cm:
            SupportOrganization(
                config=forum_only, group=self.c1_group, include_live_chat=True
            ).full_clean()
        self.assertIn("include_live_chat", cm.exception.message_dict)

    def test_group_is_unique_per_config(self):
        SupportOrganizationFactory(config=self.config, group=self.c1_group)
        with self.assertRaises(IntegrityError):
            SupportOrganizationFactory(config=self.config, group=self.c1_group)


class SupportOrganizationInlineFormSetTests(TestCase):
    def setUp(self):
        self.config = ProductSupportConfigFactory(
            product=ProductFactory(), zendesk_config=ZendeskConfigFactory(name="zd")
        )
        root = GroupProfile.add_root(
            group=Group.objects.create(name="firefox-enterprise"), slug="firefox-enterprise"
        )
        self.c1_group = Group.objects.create(name="company1")
        c1 = root.add_child(group=self.c1_group, slug="company1")
        self.c2_group = Group.objects.create(name="company2")
        root.add_child(group=self.c2_group, slug="company2")
        self.it_group = Group.objects.create(name="company1.IT")
        c1.add_child(group=self.it_group, slug="company1-it")

        self.FormSet = inlineformset_factory(
            ProductSupportConfig,
            SupportOrganization,
            formset=SupportOrganizationInlineFormSet,
            fields=("group", "include_live_chat"),
            extra=2,
        )

    def _formset(self, *groups, include_live_chat=False):
        prefix = "support_organizations"
        data = {
            f"{prefix}-TOTAL_FORMS": str(len(groups)),
            f"{prefix}-INITIAL_FORMS": "0",
            f"{prefix}-MIN_NUM_FORMS": "0",
            f"{prefix}-MAX_NUM_FORMS": "1000",
        }
        for i, group in enumerate(groups):
            data[f"{prefix}-{i}-group"] = str(group.pk)
            if include_live_chat:
                data[f"{prefix}-{i}-include_live_chat"] = "on"
        return self.FormSet(data, instance=self.config, prefix=prefix)

    def test_unsaved_forum_only_config_rejects_live_chat(self):
        self.config = ProductSupportConfig(
            product=ProductFactory(), forum_config=AAQConfigFactory()
        )

        formset = self._formset(self.c1_group, include_live_chat=True)

        self.assertFalse(formset.is_valid())
        self.assertIn("include_live_chat", formset.errors[0])

    def test_unsaved_config_checks_group_constraints(self):
        SupportOrganizationFactory(config=self.config, group=self.it_group)
        self.config = ProductSupportConfig(
            product=ProductFactory(), zendesk_config=self.config.zendesk_config
        )
        root_group = Group.objects.get(name="firefox-enterprise")
        flat_group = Group.objects.create(name="flat-group")

        for group in (root_group, flat_group, self.c1_group):
            with self.subTest(group=group.name):
                formset = self._formset(group)

                self.assertFalse(formset.is_valid())
                self.assertIn("group", formset.errors[0])

    def test_unsaved_zendesk_config_accepts_live_chat(self):
        self.config = ProductSupportConfig(
            product=ProductFactory(), zendesk_config=self.config.zendesk_config
        )

        formset = self._formset(self.c1_group, include_live_chat=True)

        self.assertTrue(formset.is_valid(), msg=str(formset.errors))

    def test_unsaved_zendesk_removal_rejects_live_chat(self):
        self.config.forum_config = AAQConfigFactory()
        self.config.zendesk_config = None

        formset = self._formset(self.c1_group, include_live_chat=True)

        self.assertFalse(formset.is_valid())
        self.assertIn("include_live_chat", formset.errors[0])

    def test_nested_rows_submitted_together_rejected(self):
        formset = self._formset(self.c1_group, self.it_group)
        self.assertFalse(formset.is_valid())
        [message] = formset.non_form_errors()
        self.assertIn(self.c1_group.name, message)
        self.assertIn(self.it_group.name, message)

    def test_independent_rows_accepted(self):
        formset = self._formset(self.c1_group, self.c2_group)
        self.assertTrue(formset.is_valid(), msg=str(formset.errors))
