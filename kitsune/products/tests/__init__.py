from datetime import timedelta

import factory
import factory.django
import factory.fuzzy
from django.template.defaultfilters import slugify
from django.utils import timezone

from kitsune.groups.tests import EnterpriseCompanyFactory
from kitsune.products.models import (
    CuratedBlock,
    CuratedBlockItem,
    Platform,
    Product,
    ProductSupportConfig,
    SupportContract,
    SupportCoverage,
    Topic,
    Version,
    ZendeskConfig,
    ZendeskTopic,
    ZendeskTopicConfiguration,
)
from kitsune.sumo.tests import FuzzyUnicode


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    title = FuzzyUnicode()
    slug = factory.LazyAttribute(lambda o: slugify(o.title))
    description = FuzzyUnicode()
    display_order = factory.fuzzy.FuzzyInteger(10)
    visible = True

    image = factory.django.ImageField()
    image_offset = 0
    image_cachebuster = FuzzyUnicode()
    sprite_height = 100


class TopicFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Topic

    title = FuzzyUnicode()
    slug = factory.LazyAttribute(lambda o: slugify(o.title))
    description = FuzzyUnicode()
    image = factory.django.ImageField()
    display_order = factory.fuzzy.FuzzyInteger(10)
    visible = True
    in_aaq = factory.fuzzy.FuzzyChoice([True, False])
    is_archived = False

    @factory.post_generation
    def products(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing
            return

        if extracted is not None:
            for t in extracted:
                self.products.add(t)


class VersionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Version

    min_version = factory.fuzzy.FuzzyDecimal(100)
    max_version = factory.LazyAttribute(lambda obj: obj.min_version + 1)
    name = factory.LazyAttribute(lambda obj: "Version %d" % obj.min_version)
    slug = factory.LazyAttribute(lambda obj: "v%d" % obj.min_version)
    visible = True
    default = factory.fuzzy.FuzzyChoice([False, True])
    product = factory.SubFactory(ProductFactory)


class PlatformFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Platform

    name = FuzzyUnicode()
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    visible = True
    display_order = factory.fuzzy.FuzzyInteger(10)


class ZendeskConfigFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ZendeskConfig

    name = FuzzyUnicode()
    ticket_form_id = "360000417171"
    enable_os_field = False


class ZendeskTopicFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ZendeskTopic

    slug = FuzzyUnicode()
    form_title = FuzzyUnicode()
    legacy_tag = ""
    tier_tags: list[str] = []
    automation_tags: list[str] = []
    segmentation_tag = ""


class ZendeskTopicConfigurationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ZendeskTopicConfiguration

    zendesk_config = factory.SubFactory(ZendeskConfigFactory)
    zendesk_topic = factory.SubFactory(ZendeskTopicFactory)
    display_order = factory.fuzzy.FuzzyInteger(10)
    loginless_only = False


class ProductSupportConfigFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductSupportConfig

    product = factory.SubFactory(ProductFactory)
    is_active = True
    default_support_type = ProductSupportConfig.SUPPORT_TYPE_ZENDESK


class CuratedBlockFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CuratedBlock

    product = factory.SubFactory(ProductFactory)
    topic = factory.LazyAttribute(lambda o: TopicFactory(products=[o.product]))
    kind = CuratedBlock.Kind.CALLOUT
    variant = CuratedBlock.Variant.GOOD_TO_KNOW
    message = factory.LazyAttribute(
        lambda o: "Heads up." if o.kind == CuratedBlock.Kind.CALLOUT else ""
    )


class CuratedBlockItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CuratedBlockItem

    block = factory.SubFactory(CuratedBlockFactory)
    position = factory.Sequence(lambda n: n)


def make_article(product, **document_fields):
    """Return an approved, localizable KB article of `product`."""
    # Avoid cycles: wiki.tests -> products.tests.
    from kitsune.wiki.tests import ApprovedRevisionFactory

    revision = ApprovedRevisionFactory(
        document__products=[product],
        is_ready_for_localization=True,
        **{f"document__{name}": value for name, value in document_fields.items()},
    )
    return revision.document


class SupportContractFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SupportContract

    company = factory.SubFactory(EnterpriseCompanyFactory)
    name = factory.Sequence(lambda n: f"Support agreement {n}")
    status = SupportContract.Status.ACTIVE
    starts_on = factory.LazyFunction(lambda: timezone.localdate() - timedelta(days=30))
    ends_on = factory.LazyFunction(lambda: timezone.localdate() + timedelta(days=30))


class SupportCoverageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SupportCoverage

    contract = factory.SubFactory(SupportContractFactory)
    product = factory.SubFactory(ProductFactory)
    zendesk_config = factory.SubFactory(ZendeskConfigFactory)
    zendesk_product_value = factory.LazyAttribute(lambda coverage: coverage.product.slug)
