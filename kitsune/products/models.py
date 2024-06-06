from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _lazy

from kitsune.sumo.fields import ImagePlusField
from kitsune.sumo.models import ModelBase
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.utils import webpack_static

HOT_TOPIC_SLUG = "hot"


class ProductQuerySet(models.QuerySet):
    def with_question_forums(self, request):
        return self.filter(questions_locales__locale=request.LANGUAGE_CODE).filter(codename="")


class Product(ModelBase):
    title = models.CharField(max_length=255, db_index=True)
    codename = models.CharField(max_length=255, blank=True, default="")
    slug = models.SlugField()
    description = models.TextField()
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

    # Dictates the order in which products are displayed in product
    # lists.
    display_order = models.IntegerField()

    # Whether or not this product is visible in the KB ui to users.
    visible = models.BooleanField(default=False)

    # Platforms this Product runs on.
    platforms = models.ManyToManyField("Platform")

    class Meta(object):
        ordering = ["display_order"]

    objects = ProductQuerySet.as_manager()

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


# Note: This is the "new" Topic class
class Topic(ModelBase):
    title = models.CharField(max_length=255, db_index=True)
    # We don't use a SlugField here because it isn't unique by itself.
    slug = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    image = ImagePlusField(
        upload_to=settings.TOPIC_IMAGE_PATH,
        null=True,
        blank=True,
        max_length=settings.MAX_FILEPATH_LENGTH,
    )

    # Topics are product-specific
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="topics")

    # Topics can optionally have a parent.
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, related_name="subtopics", null=True, blank=True
    )

    # Dictates the order in which topics are displayed in topic lists.
    display_order = models.IntegerField()

    # Whether or not this topic is visible in the ui to users.
    visible = models.BooleanField(default=False)
    # Whether or not this topic is used in the AAQ.
    in_aaq = models.BooleanField(
        default=False, help_text=_lazy("Whether this topic is shown to users in the AAQ or not.")
    )

    class Meta(object):
        ordering = ["product", "display_order"]
        unique_together = ("slug", "product")

    def __str__(self):
        return "[%s] %s" % (self.product.title, self.title)

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
