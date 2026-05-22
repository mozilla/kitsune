from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from kitsune.groups.models import GroupProfile
from kitsune.products.admin import ProductSupportConfigForm
from kitsune.products.models import ProductSupportConfig
from kitsune.products.tests import (
    ProductFactory,
    ProductSupportConfigFactory,
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
