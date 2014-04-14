import io
import os

from django.conf import settings
from django.db import models
from PIL import Image
from uuid import uuid4

from kitsune.sumo.models import ModelBase


HOT_TOPIC_SLUG = 'hot'


class Product(ModelBase):
    title = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField()
    description = models.TextField()
    image = models.ImageField(upload_to=settings.PRODUCT_IMAGE_PATH, null=True,
                              blank=True,
                              max_length=settings.MAX_FILEPATH_LENGTH,
                              # no l10n in admin
                              help_text=u'The image must be 96x96.')
    image_offset = models.IntegerField(default=None, null=True, editable=False)
    image_cachebuster = models.CharField(max_length=32, default=None,
                                         null=True, editable=False)
    sprite_height = models.IntegerField(default=None, null=True,
                                        editable=False)

    # Dictates the order in which products are displayed in product
    # lists.
    display_order = models.IntegerField()

    # Whether or not this product is visible in the KB ui to users.
    visible = models.BooleanField(default=False)

    # Whether or not this product is enabled in questions
    questions_enabled = models.BooleanField(default=False)

    # Platforms this Product runs on.
    platforms = models.ManyToManyField('Platform')

    class Meta(object):
        ordering = ['display_order']

    def __unicode__(self):
        return u'%s' % self.title

    @property
    def image_url(self):
        if self.image:
            return self.image.url
        return os.path.join(
            settings.STATIC_URL, 'img', 'product_placeholder.png')

    def sprite_url(self, retina=True):
        fn = 'logo-sprite-2x.png' if retina else 'logo-sprite.png'
        url = os.path.join(settings.MEDIA_URL, settings.PRODUCT_IMAGE_PATH, fn)
        return '%s?%s' % (url, self.image_cachebuster)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None, regenerate_sprite=True):
        super(Product, self).save(force_insert=force_insert,
                                  force_update=force_update, using=using,
                                  update_fields=update_fields)

        if regenerate_sprite:
            cachebust = uuid4().hex
            logos = []
            offset = 0;
            products = Product.objects.order_by('id').all()

            for product in products:
                if product.image:
                    product.image_offset = offset
                    offset += 1
                    logo_file = io.BytesIO(product.image.file.read())
                    logos.append(Image.open(logo_file))
                else:
                    product.image_offset = None

                product.image_cachebuster = cachebust

            for product in products:
                product.sprite_height = 148 * len(logos)
                product.save(regenerate_sprite=False)

            if len(logos):
                large_sprite = Image.new(mode='RGBA',
                                         size=(296, 296 * len(logos)),
                                         color=(0, 0, 0, 0))

                small_sprite = Image.new(mode='RGBA',
                                         size=(148, 148 * len(logos)),
                                         color=(0, 0, 0, 0))

                for offset, logo in enumerate(logos):
                    large_sprite.paste(logo, (100, 100 + (296 * offset)))

                    small_logo = logo.resize((48, 48), Image.ANTIALIAS)
                    small_sprite.paste(small_logo, (50, 50 + (148 * offset)))

                large_sprite.save(os.path.join(
                    settings.MEDIA_ROOT, settings.PRODUCT_IMAGE_PATH,
                    'logo-sprite-2x.png'))

                small_sprite.save(os.path.join(
                    settings.MEDIA_ROOT, settings.PRODUCT_IMAGE_PATH,
                    'logo-sprite.png'))


# Note: This is the "new" Topic class
class Topic(ModelBase):
    title = models.CharField(max_length=255, db_index=True)
    # We don't use a SlugField here because it isn't unique by itself.
    slug = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    image = models.ImageField(upload_to=settings.TOPIC_IMAGE_PATH, null=True,
                              blank=True,
                              max_length=settings.MAX_FILEPATH_LENGTH)

    # Topics are product-specific
    product = models.ForeignKey(Product, related_name='topics')

    # Topics can optionally have a parent.
    parent = models.ForeignKey('self', related_name='subtopics',
                               null=True, blank=True)

    # Dictates the order in which topics are displayed in topic lists.
    display_order = models.IntegerField()

    # Whether or not this topic is visible in the ui to users.
    visible = models.BooleanField(default=False)

    class Meta(object):
        ordering = ['product', 'display_order']
        unique_together = ('slug', 'product')

    def __unicode__(self):
        return u'[%s] %s' % (self.product.title, self.title)

    @property
    def image_url(self):
        if self.image:
            return self.image.url
        return os.path.join(
            settings.STATIC_URL, 'img', 'topic_placeholder.png')


class Version(ModelBase):
    name = models.CharField(max_length=255)
    # We don't use a SlugField here because we want to allow dots.
    slug = models.CharField(max_length=255, db_index=True)
    min_version = models.FloatField()
    max_version = models.FloatField()
    product = models.ForeignKey('Product', related_name='versions')
    visible = models.BooleanField()
    default = models.BooleanField()

    class Meta(object):
        ordering = ['-max_version']


class Platform(ModelBase):
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    visible = models.BooleanField()
    # Dictates the order in which products are displayed in product
    # lists.
    display_order = models.IntegerField()

    def __unicode__(self):
        return u'%s' % self.name
