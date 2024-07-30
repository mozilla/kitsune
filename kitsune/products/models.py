from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _lazy

from kitsune.products.managers import NonArchivedManager, ProductManager
from kitsune.sumo.fields import ImagePlusField
from kitsune.sumo.models import ModelBase
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.utils import webpack_static

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
        help_text=("Used everywhere except the home " "page. Must be 96x96."),
    )
    image_offset = models.IntegerField(default=None, null=True, editable=False)
    image_cachebuster = models.CharField(max_length=32, default=None, null=True, editable=False)
    sprite_height = models.IntegerField(default=None, null=True, editable=False)

    # Platforms this Product runs on.
    platforms = models.ManyToManyField("Platform")

    # Override default manager
    objects = models.Manager()
    active = ProductManager()

    class Meta(object):
        ordering = ["display_order"]

    def __str__(self):
        return "%s" % self.title

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
        """Return boolean if a product has subscriptions"""
        return bool(self.codename)

    def questions_enabled(self, locale):
        return self.questions_locales.filter(locale=locale).exists()

    def get_absolute_url(self):
        return reverse("products.product", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if self.is_archived:
            self.topics.update(is_archived=True)
        super().save(*args, **kwargs)


class Topic(BaseProductTopic):
    # We don't use a SlugField here because it isn't unique by itself.
    slug = models.CharField(max_length=255, db_index=True)
    image = ImagePlusField(
        upload_to=settings.TOPIC_IMAGE_PATH,
        null=True,
        blank=True,
        max_length=settings.MAX_FILEPATH_LENGTH,
    )

    # Topics are product-specific
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="topics", null=True, blank=True
    )
    products = models.ManyToManyField(Product, through="ProductTopic", related_name="m2m_topics")

    # Topics can optionally have a parent.
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, related_name="subtopics", null=True, blank=True
    )

    # Whether or not this topic is used in the AAQ.
    in_aaq = models.BooleanField(
        default=False, help_text=_lazy("Whether this topic is shown to users in the AAQ or not.")
    )
    # Whether or not this topic is displayed in navigation menus
    in_nav = models.BooleanField(
        default=False, help_text=_lazy("Whether this topic is shown in navigation menus.")
    )

    class Meta(object):
        ordering = ["product", "display_order"]
        unique_together = ("slug", "product")

    # Override default manager
    objects = models.Manager()
    active = NonArchivedManager()

    def __str__(self):
        if self.product:
            return f"{self.product.title} {self.title}"
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
            path = [cur.slug] + path
        return path

    def documents(self, user=None, **kwargs):
        # Avoid circular imports
        from kitsune.wiki.models import Document

        query = {
            "user": user,
            "topics": self,
            "products": self.product,
            "is_archived": False,
            "category__in": settings.IA_DEFAULT_CATEGORIES,
        }
        query.update(kwargs)
        return Document.objects.visible(**query)

    def get_absolute_url(self):
        if self.parent is None:
            return reverse(
                "products.documents",
                kwargs={
                    "product_slug": self.product.slug,
                    "topic_slug": self.slug,
                },
            )
        else:
            assert self.parent.parent is None
            return reverse(
                "products.subtopics",
                kwargs={
                    "product_slug": self.product.slug,
                    "topic_slug": self.parent.slug,
                    "subtopic_slug": self.slug,
                },
            )


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

    class Meta(object):
        ordering = ["-created"]
        verbose_name_plural = "Topic slug history"

    def save(self, *args, **kwargs):
        # Mark the old topics as archived
        try:
            old_topic = Topic.active.get(slug=self.slug, product=self.topic.product)
            old_topic.is_archived = True
            old_topic.save()
        except Topic.DoesNotExist:
            ...
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

    class Meta(object):
        ordering = ["-max_version"]


class Platform(ModelBase):
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    visible = models.BooleanField(default=False)
    # Dictates the order in which products are displayed in product
    # lists.
    display_order = models.IntegerField()

    def __str__(self):
        return "%s" % self.name
