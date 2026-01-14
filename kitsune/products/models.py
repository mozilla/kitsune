from django.conf import settings
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.db import models

from kitsune.products.managers import (
    NonArchivedManager,
    ProductManager,
    ProductSupportConfigManager,
)
from kitsune.sumo.fields import ImagePlusField
from kitsune.sumo.models import ModelBase
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.utils import PrettyJSONEncoder, webpack_static

HOT_TOPIC_SLUG = "hot"


class BaseProductTopic(ModelBase):
    """Abstract base class for Product and Topic."""

    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    # Whether or not is visible in the ui to users.
    visible = models.BooleanField(default=False)
    # whether or not is archived
    is_archived = models.BooleanField(default=False)
    # Dictates the display order in lists
    display_order = models.IntegerField()
    metadata = models.JSONField(
        default=dict,
        encoder=PrettyJSONEncoder,
        help_text="Data useful for things like LLM prompts.",
    )

    class Meta:
        abstract = True


class Product(BaseProductTopic):
    codename = models.CharField(max_length=255, blank=True, default="")
    slug = models.SlugField()
    image = ImagePlusField(
        upload_to=settings.PRODUCT_IMAGE_PATH,
        null=True,
        blank=True,
        max_length=settings.MAX_FILEPATH_LENGTH,
        # no l10n in admin
        help_text="Used on the the home page. Must be 484x244.",
    )
    image_alternate = ImagePlusField(
        upload_to=settings.PRODUCT_IMAGE_PATH,
        null=True,
        blank=True,
        max_length=settings.MAX_FILEPATH_LENGTH,
        help_text="Used everywhere except the home page. Must be 96x96.",
    )
    image_offset = models.IntegerField(default=None, null=True, editable=False)
    image_cachebuster = models.CharField(max_length=32, default=None, null=True, editable=False)
    sprite_height = models.IntegerField(default=None, null=True, editable=False)

    # Platforms this Product runs on.
    platforms = models.ManyToManyField("Platform")

    pinned_article_config = models.ForeignKey(
        "wiki.PinnedArticleConfig",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products",
        verbose_name="Pinned article configuration",
        help_text="Pinned article configuration for this product's landing page.",
    )

    # Override default manager
    objects = models.Manager()
    active = ProductManager()

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return "{}".format(self.title)

    @property
    def image_url(self):
        if self.image:
            return self.image.url
        return webpack_static("products/img/product_placeholder.png")

    @property
    def image_alternate_url(self):
        if self.image_alternate:
            return self.image_alternate.url
        return webpack_static("products/img/product_placeholder_alternate.png")

    @property
    def has_ticketing_support(self):
        """Return boolean if a product has Zendesk ticketing support"""
        return self.support_configs.filter(
            is_active=True,
            zendesk_config__isnull=False,
        ).exists()

    def questions_enabled(self, locale):
        """Check if product has an active public forum in the given locale."""
        return self.support_configs.filter(
            is_active=True,
            forum_config__is_active=True,
            forum_config__enabled_locales__locale=locale,
        ).exists()

    def get_absolute_url(self):
        return reverse("products.product", kwargs={"slug": self.slug})


class Topic(BaseProductTopic):
    # We don't use a SlugField here because it isn't unique by itself.
    slug = models.CharField(max_length=255, db_index=True)
    image = ImagePlusField(
        upload_to=settings.TOPIC_IMAGE_PATH,
        null=True,
        blank=True,
        max_length=settings.MAX_FILEPATH_LENGTH,
    )

    products = models.ManyToManyField(Product, through="ProductTopic", related_name="m2m_topics")

    # Topics can optionally have a parent.
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, related_name="subtopics", null=True, blank=True
    )

    # Whether or not this topic is used in the AAQ.
    in_aaq = models.BooleanField(
        default=False, help_text="Whether this topic is shown to users in the AAQ or not."
    )
    # Whether or not this topic is displayed in navigation menus
    in_nav = models.BooleanField(
        default=False, help_text="Whether this topic is shown in navigation menus."
    )

    class Meta:
        ordering = ["title", "display_order"]

    # Override default manager
    objects = models.Manager()
    active = NonArchivedManager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._topic_is_archived = self.is_archived

    def __str__(self):
        return self.title

    @property
    def image_url(self):
        if self.image:
            return self.image.url
        return webpack_static("products/img/topic_placeholder.png")

    @property
    def path(self):
        path = [self.slug]
        cur = self
        while cur.parent:
            cur = cur.parent
            path = [cur.slug, *path]
        return path

    def documents(self, user=None, **kwargs):
        # Avoid circular imports
        from kitsune.wiki.models import Document

        query = {
            "user": user,
            "topics": self,
            "products__in": self.products,
            "is_archived": False,
            "category__in": settings.IA_DEFAULT_CATEGORIES,
        }
        query.update(kwargs)
        return Document.objects.visible(**query)

    def get_absolute_url(self, product_slug=None):
        kwargs = {"topic_slug": self.slug}
        named_url = "products.topic_documents"
        if product_slug:
            kwargs.update({"product_slug": product_slug})
            named_url = "products.documents"

            if self.parent:
                assert self.parent.parent is None
                kwargs.update({"topic_slug": self.parent.slug, "subtopic_slug": self.slug})
                named_url = "products.subtopics"
        return reverse(named_url, kwargs=kwargs)

    def save(self, *args, **kwargs):
        # Check if the is_archived field has changed
        if self._topic_is_archived != self.is_archived:
            for product in self.products.all():
                cache_key = f"hierarchical_topics_{product.slug}"
                cache.delete(cache_key)

        # Ensure that the "metadata" field is a dict.
        if self.metadata is None:
            self.metadata = {}
        elif not isinstance(self.metadata, dict):
            raise ValueError('The "metadata" field must be a dict.')

        super().save(*args, **kwargs)
        self._topic_is_archived = self.is_archived


class ProductTopic(ModelBase):
    """Through model for Product and Topic to add additional metadata."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["product", "topic"], name="unique_product_topic")
        ]


class TopicSlugHistory(ModelBase):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="slug_history")
    slug = models.SlugField(max_length=255, unique=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]
        verbose_name_plural = "Topic slug history"

    def save(self, *args, **kwargs):
        # Mark the old topics as archived
        old_topics = Topic.active.filter(slug=self.slug)
        for old_topic in old_topics:
            old_topic.is_archived = True
            old_topic.save()
        super().save(*args, **kwargs)


class Version(ModelBase):
    name = models.CharField(max_length=255)
    # We don't use a SlugField here because we want to allow dots.
    slug = models.CharField(max_length=255, db_index=True)
    min_version = models.FloatField()
    max_version = models.FloatField()
    product = models.ForeignKey("Product", on_delete=models.CASCADE, related_name="versions")
    visible = models.BooleanField(default=False)
    default = models.BooleanField(default=False)

    class Meta:
        ordering = ["-max_version"]


class Platform(ModelBase):
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    visible = models.BooleanField(default=False)
    # Dictates the order in which products are displayed in product
    # lists.
    display_order = models.IntegerField()

    def __str__(self):
        return "{}".format(self.name)


class ProductSupportConfig(ModelBase):
    """Configuration for product support routing (forums and/or Zendesk).

    This model acts as a routing layer that determines which support channel(s)
    are available for a product and handles group-based access control for hybrid support.
    """

    SUPPORT_TYPE_FORUM = "forum"
    SUPPORT_TYPE_ZENDESK = "zendesk"
    SUPPORT_TYPE_CHOICES = [
        (SUPPORT_TYPE_FORUM, "Community Forums"),
        (SUPPORT_TYPE_ZENDESK, "Zendesk Support"),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="support_configs")
    forum_config = models.ForeignKey(
        "questions.AAQConfig",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="support_configs",
        help_text="Select forum configuration to enable community support",
    )
    zendesk_config = models.ForeignKey(
        "ZendeskConfig",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="support_configs",
        help_text="Select Zendesk configuration to enable Zendesk support",
    )
    is_active = models.BooleanField(
        default=False, help_text="Only one configuration can be active per product"
    )
    default_support_type = models.CharField(
        max_length=20,
        choices=SUPPORT_TYPE_CHOICES,
        default=SUPPORT_TYPE_FORUM,
        help_text="Default support channel for users (used when only one channel or no group access)",
    )
    hybrid_support_groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name="hybrid_support_configs",
        help_text="Groups that can choose between forums and Zendesk when both are enabled",
    )
    group_default_support_type = models.CharField(
        max_length=20,
        choices=SUPPORT_TYPE_CHOICES,
        null=True,
        blank=True,
        help_text="Default support type for users in hybrid groups (if not set, uses default_support_type)",
    )

    objects = ProductSupportConfigManager()

    class Meta:
        verbose_name = "Product support configuration"
        constraints = [
            models.UniqueConstraint(
                fields=["product", "is_active"], name="unique_active_support_config"
            ),
            models.CheckConstraint(
                check=models.Q(forum_config__isnull=False)
                | models.Q(zendesk_config__isnull=False),
                name="at_least_one_support_channel",
            ),
        ]

    def __str__(self):
        return f"{self.product} Support Configuration"

    @property
    def is_hybrid(self):
        """Returns True if both forum and Zendesk support are enabled."""
        return bool(self.forum_config) and bool(self.zendesk_config)

    @property
    def enable_forum_support(self):
        """Returns True if forum support is enabled (forum_config is set)."""
        return bool(self.forum_config)

    @property
    def enable_zendesk_support(self):
        """Returns True if Zendesk support is enabled (zendesk_config is set)."""
        return bool(self.zendesk_config)


class ZendeskConfig(ModelBase):
    """Configuration for Zendesk support integration.

    Stores per-product Zendesk settings like form IDs and field preferences.
    Global Zendesk API credentials remain in Django settings.
    """

    name = models.CharField(
        max_length=255, help_text="Descriptive name for this Zendesk configuration"
    )
    ticket_form_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="Zendesk ticket form ID to use for this product (leave blank to use global default)",
    )
    enable_os_field = models.BooleanField(
        default=False, help_text="Show operating system selector in the support form"
    )
    topics = models.ManyToManyField(
        "ZendeskTopic",
        through="ZendeskTopicConfiguration",
        related_name="zendesk_configs",
        help_text="Topics available for this Zendesk configuration",
    )

    class Meta:
        verbose_name = "Zendesk configuration"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ZendeskTopic(ModelBase):
    """Zendesk support topic/category for the support form dropdown.

    Topics are reusable across multiple Zendesk configurations through
    the ZendeskTopicConfiguration through table.
    """

    slug = models.SlugField(
        max_length=100, unique=True, help_text="Globally unique identifier for this topic"
    )
    topic = models.CharField(
        max_length=255, help_text="User-facing topic text shown in the dropdown"
    )
    legacy_tag = models.CharField(max_length=100, blank=True, help_text="Legacy Zendesk tag")
    tier_tags = models.JSONField(
        default=list,
        help_text="List of tier tags (e.g., ['t1-billing-and-subscriptions'])",
    )
    automation_tag = models.CharField(
        max_length=100, blank=True, null=True, help_text="Automation tag for Zendesk workflows"
    )
    segmentation_tag = models.CharField(
        max_length=100, blank=True, null=True, help_text="Segmentation tag for analytics"
    )

    class Meta:
        verbose_name = "Zendesk topic"
        ordering = ["slug"]

    def __str__(self):
        return f"{self.topic} ({self.slug})"

    @property
    def tags_dict(self):
        """Returns tags in the format expected by ZendeskForm."""
        return {
            "legacy": self.legacy_tag,
            "tiers": self.tier_tags,
            "automation": self.automation_tag,
            "segmentation": self.segmentation_tag,
        }


class ZendeskTopicConfiguration(ModelBase):
    """
    Through table connecting ZendeskConfig to ZendeskTopic with config-specific settings.

    This allows topics to be reused across multiple configs with different
    ordering and visibility settings.
    """

    zendesk_config = models.ForeignKey(
        ZendeskConfig, on_delete=models.CASCADE, related_name="topic_configurations"
    )
    zendesk_topic = models.ForeignKey(
        ZendeskTopic, on_delete=models.CASCADE, related_name="configurations"
    )
    display_order = models.IntegerField(
        default=0,
        help_text="Order in which this topic appears in this config (lower numbers first)",
    )
    loginless_only = models.BooleanField(
        default=False, help_text="Only show this topic for loginless flows in this config"
    )

    class Meta:
        verbose_name = "Zendesk topic configuration"
        ordering = ["display_order", "zendesk_topic__slug"]
        constraints = [
            models.UniqueConstraint(
                fields=["zendesk_config", "zendesk_topic"], name="unique_topic_per_config"
            )
        ]

    def __str__(self):
        return (
            f"{self.zendesk_config.name}: {self.zendesk_topic.topic} (order {self.display_order})"
        )
