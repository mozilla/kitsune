from typing import override

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models

from kitsune.products.managers import (
    CURATED_ARTICLE_Q,
    MAX_QUESTIONS_SHOWN,
    MIN_ITEMS_SHOWN,
    CuratedBlockManager,
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
            forum_config__enabled_locales__locale=locale,
        ).exists()

    def get_absolute_url(self):
        return reverse("products.product", kwargs={"slug": self.slug})


class Topic(BaseProductTopic):
    class ArticleOrdering(models.TextChoices):
        DEFAULT = "default", "Default (display order, then popularity)"
        NEWEST = "newest", "Newest first (most recently added)"

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
    legacy_tag = models.CharField(
        max_length=100,
        blank=True,
        help_text="Legacy Zendesk bucket (accounts/technical/payments). Set on t1 roots.",
    )
    article_ordering = models.CharField(
        max_length=20,
        choices=ArticleOrdering.choices,
        default=ArticleOrdering.DEFAULT,
        help_text="How KB articles are ordered for this topic.",
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

    @property
    def tier_tags(self):
        """Zendesk tier tags derived from the parent chain (e.g. ['t1-foo', 't2-bar'])."""
        return [f"t{i}-{slug}" for i, slug in enumerate(self.path, start=1)]

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

    @override
    def save(self, *args, **kwargs):
        # Check if the is_archived field has changed
        if self._topic_is_archived != self.is_archived:
            for product in self.products.all():
                cache_key = f"hierarchical_topics_v2_{product.slug}"
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


class CuratedBlock(ModelBase):
    """An editor-curated block shown on a product's topic page."""

    class Kind(models.TextChoices):
        CALLOUT = "callout", "Callout"
        ARTICLES = "articles", "Article cards"
        QUESTIONS = "questions", "Forum questions"

    class Variant(models.TextChoices):
        GOOD_TO_KNOW = "good_to_know", "Good to know"
        IMPORTANT = "important", "Important"
        NUMBERED = "numbered", "Numbered"
        FEATURED = "featured", "Featured"
        MANUAL = "manual", "Manual"
        AUTOMATIC = "automatic", "Automatic"

    # Every valid (kind, variant) pair, with the (min, max) number of items it holds.
    ITEM_LIMITS = {
        (Kind.CALLOUT, Variant.GOOD_TO_KNOW): (0, 3),
        (Kind.CALLOUT, Variant.IMPORTANT): (0, 3),
        (Kind.ARTICLES, Variant.NUMBERED): (MIN_ITEMS_SHOWN, 6),
        (Kind.ARTICLES, Variant.FEATURED): (MIN_ITEMS_SHOWN, 6),
        (Kind.QUESTIONS, Variant.MANUAL): (MIN_ITEMS_SHOWN, MAX_QUESTIONS_SHOWN),
        (Kind.QUESTIONS, Variant.AUTOMATIC): (0, 0),
    }

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="curated_blocks")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="curated_blocks")
    kind = models.CharField(max_length=20, choices=Kind.choices)
    variant = models.CharField(max_length=20, choices=Variant.choices)
    message = models.TextField(blank=True, help_text="Callouts only. Plain text.")
    show_until = models.DateTimeField(
        null=True, blank=True, help_text="The block stops showing after this time."
    )
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    updated_at = models.DateTimeField(auto_now=True)

    objects = CuratedBlockManager()

    class Meta:
        verbose_name = "Curated block"
        constraints = [
            models.UniqueConstraint(
                fields=["topic", "product", "kind"], name="unique_curated_block_per_kind"
            ),
        ]

    def __str__(self):
        return f"{self.get_kind_display()} ({self.get_variant_display()}): {self.topic} / {self.product}"

    def clean(self):
        super().clean()
        errors = {}

        if (
            self.kind in self.Kind.values
            and self.variant in self.Variant.values
            and (self.kind, self.variant) not in self.ITEM_LIMITS
        ):
            errors["variant"] = (
                f"'{self.get_variant_display()}' is not a variant of "
                f"{self.get_kind_display()} blocks."
            )

        if self.kind in self.Kind.values:
            message = self.message or ""
            has_message = bool(message.strip())
            if self.kind == self.Kind.CALLOUT and not has_message:
                errors["message"] = "A message is required for callouts."
            elif self.kind != self.Kind.CALLOUT and has_message:
                errors["message"] = "Only callouts have a message."
            elif '"""' in message or "\\" in message or message.endswith('"'):
                errors["message"] = (
                    "The message cannot contain a backslash or three double quotes in a row, "
                    "or end with a double quote."
                )

        if (
            self.topic_id is not None
            and self.product_id is not None
            and not ProductTopic.objects.filter(
                product_id=self.product_id, topic_id=self.topic_id
            ).exists()
        ):
            errors["topic"] = f"'{self.topic}' is not one of the topics of '{self.product}'."

        if errors:
            raise ValidationError(errors)

    def clean_items(self, items):
        """Validate the complete list of items this block would hold.

        Counts and item types depend on the final set of items, so this runs once they
        are known (unsaved items are fine). Raises a ValidationError listing every problem.
        """
        items = list(items)
        limits = self.ITEM_LIMITS.get((self.kind, self.variant))
        if limits is None or self.product_id is None:
            return

        if self.variant == self.Variant.AUTOMATIC:
            if items:
                raise ValidationError("Automatic question blocks cannot have items.")
            return

        low, high = limits
        errors = []
        if not low <= len(items) <= high:
            expected = f"at most {high}" if low == 0 else f"between {low} and {high}"
            errors.append(f"Add {expected} items (got {len(items)}).")

        wants_questions = self.kind == self.Kind.QUESTIONS
        label = "question" if wants_questions else "article"
        target_ids = []
        mismatched = False
        for item in items:
            target_id = item.question_id if wants_questions else item.document_id
            other_id = item.document_id if wants_questions else item.question_id
            if target_id is None or other_id is not None:
                mismatched = True
            if target_id is not None:
                target_ids.append(target_id)
        if mismatched:
            errors.append(f"Only {label}s can be added to this block.")
        if len(set(target_ids)) != len(target_ids):
            errors.append(f"Each {label} can only be added once.")

        if wants_questions:
            eligible = set(
                self.product.questions.filter(
                    pk__in=target_ids, is_spam=False, is_archived=False
                ).values_list("pk", flat=True)
            )
            requirement = "belong to this product and be neither spam nor archived"
        else:
            eligible = set(
                self.product.document_set.filter(CURATED_ARTICLE_Q, pk__in=target_ids).values_list(
                    "pk", flat=True
                )
            )
            requirement = (
                "be a published English source article of this product, not a template, "
                "redirect, restricted or archived article"
            )
        for item in items:
            target = item.question if wants_questions else item.document
            if target is not None and target.pk not in eligible:
                errors.append(f"'{target.title}' must {requirement}.")

        if errors:
            raise ValidationError(errors)


class CuratedBlockItem(ModelBase):
    """An article or question placed in a curated block."""

    block = models.ForeignKey(CuratedBlock, on_delete=models.CASCADE, related_name="items")
    position = models.PositiveSmallIntegerField(default=0)
    document = models.ForeignKey(
        "wiki.Document",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="curated_block_items",
        limit_choices_to=CURATED_ARTICLE_Q,
    )
    question = models.ForeignKey(
        "questions.Question",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="curated_block_items",
        limit_choices_to={"is_spam": False, "is_archived": False},
    )

    class Meta:
        ordering = ["position", "id"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(document__isnull=False, question__isnull=True)
                    | models.Q(document__isnull=True, question__isnull=False)
                ),
                name="curated_block_item_has_one_target",
                violation_error_message="Choose either an article or a question.",
            ),
        ]

    def __str__(self):
        return f"{self.position}: {self.document or self.question}"


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
    # Retained until the next release for compatibility with older application instances.
    hybrid_support_groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name="hybrid_support_configs",
        help_text=(
            "Groups that can choose between forums and Zendesk when both are enabled. "
            "Note: when Zendesk is enabled, each group listed here also becomes an "
            "'organization root' — Zendesk tickets submitted by any of its members "
            "(or members of its subgroups) are visible to everyone in that subtree. "
            "Group must not be a tree root, and cannot overlap (as ancestor or "
            "descendant) with any group already listed in another product's "
            "hybrid_support_groups."
        ),
    )
    group_default_support_type = models.CharField(
        max_length=20,
        choices=SUPPORT_TYPE_CHOICES,
        null=True,
        blank=True,
        help_text="Default support type for organization members (if not set, uses default_support_type)",
    )
    subscription_only = models.BooleanField(
        default=False,
        help_text=(
            "If enabled, only users with an active product subscription can access support. "
            "Unsubscribed users are redirected to another product's AAQ if one is configured, "
            "otherwise the support widget is hidden."
        ),
    )
    unsubscribed_redirect_product = models.ForeignKey(
        "Product",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="redirect_target_for",
        help_text=(
            "When subscription_only is enabled, redirect unsubscribed users to this product's AAQ. "
            "If not set, the support widget is hidden for unsubscribed users."
        ),
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

    def clean(self):
        super().clean()
        if not self.is_active:
            return

        # Ensure that at least one support channel is configured.
        if self.forum_config_id is None and self.zendesk_config_id is None:
            raise ValidationError(
                "No support channel has been configured. "
                "Assign a Zendesk and/or forum configuration."
            )

        # Check that a selected forum config has at least one enabled locale.
        if self.forum_config_id is not None:
            from kitsune.questions.models import AAQConfig

            if not AAQConfig.objects.filter(
                pk=self.forum_config_id,
                enabled_locales__isnull=False,
            ).exists():
                raise ValidationError("The selected forum configuration has no enabled locales.")

        if not self.subscription_only and self.unsubscribed_redirect_product_id:
            raise ValidationError(
                {
                    "unsubscribed_redirect_product": (
                        "Redirect product should only be set when subscription_only is enabled."
                    )
                }
            )

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


class SupportOrganization(ModelBase):
    """Support options for a group under a product's support configuration.

    The group and all of its subgroups form one organization; the options apply to every
    member. Each option here is an addition to the support the configuration already
    provides.
    """

    config = models.ForeignKey(
        ProductSupportConfig, on_delete=models.CASCADE, related_name="support_organizations"
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="support_organizations",
        help_text=(
            "Includes all subgroups. Cannot be a top-level group or nested with another "
            "configured group."
        ),
    )
    include_live_chat = models.BooleanField(
        default=False,
        help_text="Members can start live chats with support agents. Requires Zendesk support.",
    )

    class Meta:
        verbose_name = "Support organization"
        constraints = [
            models.UniqueConstraint(
                fields=["config", "group"], name="unique_support_organization_per_config"
            ),
        ]

    def __str__(self):
        return f"{self.group.name} ({self.config.product})"

    def clean(self):
        super().clean()
        # Local import: products.models -> groups.models -> wiki.parser -> wiki.models
        # -> products.models.
        from kitsune.groups.models import GroupProfile

        # Inline admin rows validate against a parent config that may not be saved yet,
        # so work from the related object rather than from config_id.
        try:
            config = self.config
        except ProductSupportConfig.DoesNotExist:
            return
        if self.group_id is None:
            return

        if self.include_live_chat and config.zendesk_config_id is None:
            raise ValidationError(
                {
                    "include_live_chat": (
                        "Live chat requires Zendesk support on the product configuration."
                    )
                }
            )

        try:
            profile = GroupProfile.objects.get(group_id=self.group_id)
        except GroupProfile.DoesNotExist:
            raise ValidationError({"group": f"'{self.group.name}' has no group profile."})

        if profile.is_root():
            raise ValidationError(
                {
                    "group": (
                        f"'{self.group.name}' is a top-level group. Configure one of its "
                        f"subgroups instead."
                    )
                }
            )

        chain_group_ids = (
            GroupProfile.objects.get_ancestors(profile)
            | GroupProfile.objects.get_descendants(profile)
        ).values_list("group_id", flat=True)

        same_config = SupportOrganization.objects.filter(
            config_id=config.pk, group_id__in=chain_group_ids
        ).exclude(pk=self.pk)
        if same_config.exists():
            names = ", ".join(sorted(org.group.name for org in same_config))
            raise ValidationError(
                {
                    "group": (
                        f"'{self.group.name}' is nested with {names}, which is already "
                        f"configured. Configure one of them, not both."
                    )
                }
            )

        # Until the hybrid_support_groups M2M is removed, other products' groups are
        # recorded in both places; check both.
        other_configs = ProductSupportConfig.objects.exclude(pk=config.pk)
        external_names = sorted(
            set(
                Group.objects.filter(pk__in=chain_group_ids)
                .filter(
                    models.Q(hybrid_support_configs__in=other_configs)
                    | models.Q(support_organizations__config__in=other_configs)
                )
                .values_list("name", flat=True)
            )
        )
        if external_names:
            raise ValidationError(
                {
                    "group": (
                        f"'{self.group.name}' is nested with {', '.join(external_names)}, "
                        f"which is already configured for another product."
                    )
                }
            )


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
    brand_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="Zendesk brand ID to associate tickets with for this product",
    )
    enable_urgency_field = models.BooleanField(
        default=False, help_text="Show the urgency selector in the support form"
    )
    enable_os_field = models.BooleanField(
        default=False, help_text="Show operating system selector in the support form"
    )
    enable_deployment_fields = models.BooleanField(
        default=False,
        help_text="Show deployment-related fields (update channel and policy distribution) in the support form",
    )
    skip_spam_moderation = models.BooleanField(
        default=False, help_text="Skip AI-based spam and product checking for this product"
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
    form_title = models.CharField(
        max_length=255, help_text="User-facing topic text shown in the dropdown"
    )
    topic = models.ForeignKey(
        Topic,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="zendesk_topics",
        help_text="Linked taxonomy topic. Source of truth for tier_tags and legacy_tag.",
    )
    legacy_tag = models.CharField(max_length=100, blank=True, help_text="Legacy Zendesk tag")
    tier_tags = models.JSONField(
        default=list,
        help_text="List of tier tags (e.g., ['t1-billing-and-subscriptions'])",
    )
    automation_tags = models.JSONField(
        default=list,
        blank=True,
        help_text="List of automation tags for Zendesk workflows.",
    )
    segmentation_tag = models.CharField(
        max_length=100, blank=True, null=True, help_text="Segmentation tag for analytics"
    )

    class Meta:
        verbose_name = "Zendesk topic"
        ordering = ["slug"]

    def __str__(self):
        return f"{self.form_title} ({self.slug})"

    @property
    def tags_dict(self):
        """Returns tags in the format expected by ZendeskForm.

        Derives legacy and tier tags from the linked Topic when available;
        falls back to stored fields for ZendeskTopics not yet linked.
        """
        if self.topic_id is not None:
            root = self.topic
            while root.parent_id is not None:
                root = root.parent
            return {
                "legacy": root.legacy_tag,
                "tiers": self.topic.tier_tags,
                "automation": self.automation_tags,
                "segmentation": self.segmentation_tag,
            }
        return {
            "legacy": self.legacy_tag,
            "tiers": self.tier_tags,
            "automation": self.automation_tags,
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
        return f"{self.zendesk_config.name}: {self.zendesk_topic.form_title} (order {self.display_order})"
