from django.core.exceptions import ValidationError
from django.db import IntegrityError

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
