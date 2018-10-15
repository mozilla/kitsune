# Pruned and mnodified version of django-badger/badger/models.py
# https://github.com/mozilla/django-badger/blob/master/badger/models.py

import hashlib
import json
import os.path
import random
import re

from cStringIO import StringIO
from PIL import Image
from time import time
from urlparse import urljoin

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
from django.utils.deconstruct import deconstructible
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext_lazy as _

from kitsune.kbadge.signals import badge_will_be_awarded, badge_was_awarded


IMG_MAX_SIZE = getattr(settings, "BADGER_IMG_MAX_SIZE", (256, 256))

# Set up a file system for badge uploads that can be kept separate from the
# rest of /media if necessary. Lots of hackery to ensure sensible defaults.
UPLOADS_ROOT = getattr(settings, 'BADGER_MEDIA_ROOT',
                       os.path.join(getattr(settings, 'MEDIA_ROOT', 'media/'), 'uploads'))
UPLOADS_URL = getattr(settings, 'BADGER_MEDIA_URL',
                      urljoin(getattr(settings, 'MEDIA_URL', '/media/'), 'uploads/'))
BADGE_UPLOADS_FS = FileSystemStorage(location=UPLOADS_ROOT,
                                     base_url=UPLOADS_URL)

MK_UPLOAD_TMPL = '%(base)s/%(h1)s/%(h2)s/%(hash)s_%(field_fn)s_%(now)s_%(rand)04d.%(ext)s'

DEFAULT_HTTP_PROTOCOL = getattr(settings, "DEFAULT_HTTP_PROTOCOL", "http")


def _document_django_model(cls):
    """Adds meta fields to the docstring for better autodoccing"""
    fields = cls._meta.fields
    doc = cls.__doc__

    if not doc.endswith('\n\n'):
        doc = doc + '\n\n'

    for f in fields:
        doc = doc + '    :arg {0}:\n'.format(f.name)

    cls.__doc__ = doc
    return cls


def scale_image(img_upload, img_max_size):
    """Crop and scale an image file."""
    try:
        img = Image.open(img_upload)
    except IOError:
        return None

    src_width, src_height = img.size
    src_ratio = float(src_width) / float(src_height)
    dst_width, dst_height = img_max_size
    dst_ratio = float(dst_width) / float(dst_height)

    if dst_ratio < src_ratio:
        crop_height = src_height
        crop_width = crop_height * dst_ratio
        x_offset = int(float(src_width - crop_width) / 2)
        y_offset = 0
    else:
        crop_width = src_width
        crop_height = crop_width / dst_ratio
        x_offset = 0
        y_offset = int(float(src_height - crop_height) / 2)

    img = img.crop((x_offset, y_offset,
                    x_offset + int(crop_width), y_offset + int(crop_height)))
    img = img.resize((dst_width, dst_height), Image.ANTIALIAS)

    # If the mode isn't RGB or RGBA we convert it. If it's not one
    # of those modes, then we don't know what the alpha channel should
    # be so we convert it to "RGB".
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    new_img = StringIO()
    img.save(new_img, "PNG")
    img_data = new_img.getvalue()

    return ContentFile(img_data)


# Taken from http://stackoverflow.com/a/4019144
def slugify(txt):
    """A custom version of slugify that retains non-ascii characters. The
    purpose of this function in the application is to make URLs more readable
    in a browser, so there are some added heuristics to retain as much of the
    title meaning as possible while excluding characters that are troublesome
    to read in URLs. For example, question marks will be seen in the browser
    URL as %3F and are thereful unreadable. Although non-ascii characters will
    also be hex-encoded in the raw URL, most browsers will display them as
    human-readable glyphs in the address bar -- those should be kept in the
    slug."""
    # remove trailing whitespace
    txt = txt.strip()
    # remove spaces before and after dashes
    txt = re.sub('\s*-\s*', '-', txt, re.UNICODE)
    # replace remaining spaces with dashes
    txt = re.sub('[\s/]', '-', txt, re.UNICODE)
    # replace colons between numbers with dashes
    txt = re.sub('(\d):(\d)', r'\1-\2', txt, re.UNICODE)
    # replace double quotes with single quotes
    txt = re.sub('"', "'", txt, re.UNICODE)
    # remove some characters altogether
    txt = re.sub(r'[?,:!@#~`+=$%^&\\*()\[\]{}<>]', '', txt, re.UNICODE)
    return txt


def get_permissions_for(self, user):
    """Mixin method to collect permissions for a model instance"""
    pre = 'allows_'
    pre_len = len(pre)
    methods = (m for m in dir(self) if m.startswith(pre))
    perms = dict(
        (m[pre_len:], getattr(self, m)(user))
        for m in methods
    )
    return perms


# We need to do this in django 1.7 because migrations serialize the fields.
# See https://code.djangoproject.com/ticket/22999
@deconstructible
class UploadTo(object):
    """upload_to builder for file upload fields"""
    def __init__(self, field_fn, ext, tmpl=MK_UPLOAD_TMPL):
        self.field_fn = field_fn
        self.ext = ext
        self.tmpl = tmpl

    def __call__(self, instance, filename):
        base, slug = instance.get_upload_meta()
        slug_hash = (hashlib.md5(slug.encode('utf-8', 'ignore'))
                            .hexdigest())
        return self.tmpl % dict(now=int(time()), rand=random.randint(0, 1000),
                                slug=slug[:50], base=base, field_fn=self.field_fn,
                                pk=instance.pk,
                                hash=slug_hash, h1=slug_hash[0], h2=slug_hash[1],
                                ext=self.ext)


class JSONField(models.TextField):
    """JSONField is a generic textfield that neatly serializes/unserializes
    JSON objects seamlessly
    see: http://djangosnippets.org/snippets/1478/
    """

    # Used so to_python() is called
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        """Convert our string value to JSON after we load it from the DB"""
        if not value:
            return dict()
        try:
            if (isinstance(value, basestring) or
                    type(value) is unicode):
                return json.loads(value)
        except ValueError:
            return dict()
        return value

    def get_db_prep_save(self, value, connection):
        """Convert our JSON object to a string before we save"""
        if not value:
            return '{}'
        if isinstance(value, dict):
            value = json.dumps(value, cls=DjangoJSONEncoder)
        if isinstance(value, basestring) or value is None:
            return value
        return smart_unicode(value)


class SearchManagerMixin(object):
    """Quick & dirty manager mixin for search"""

    # See: http://www.julienphalip.com/blog/2008/08/16/adding-search-django-site-snap/
    def _normalize_query(self, query_string,
                         findterms=re.compile(r'"([^"]+)"|(\S+)').findall,
                         normspace=re.compile(r'\s{2,}').sub):
        """
        Splits the query string in invidual keywords, getting rid of unecessary spaces
        and grouping quoted words together.
        Example::

            foo._normalize_query('  some random  words "with   quotes  " and   spaces')
            ['some', 'random', 'words', 'with quotes', 'and', 'spaces']

        """
        return [normspace(' ', (t[0] or t[1]).strip()) for t in findterms(query_string)]

    # See: http://www.julienphalip.com/blog/2008/08/16/adding-search-django-site-snap/
    def _get_query(self, query_string, search_fields):
        """
        Returns a query, that is a combination of Q objects. That
        combination aims to search keywords within a model by testing
        the given search fields.

        """
        query = None  # Query to search for every search term
        terms = self._normalize_query(query_string)
        for term in terms:
            or_query = None  # Query to search for a given term in each field
            for field_name in search_fields:
                q = Q(**{"%s__icontains" % field_name: term})
                if or_query is None:
                    or_query = q
                else:
                    or_query = or_query | q
            if query is None:
                query = or_query
            else:
                query = query & or_query
        return query

    def search(self, query_string, sort='title'):
        """Quick and dirty keyword search on submissions"""
        # TODO: Someday, replace this with something like Sphinx or another real
        # search engine
        strip_qs = query_string.strip()
        if not strip_qs:
            return self.all_sorted(sort).order_by('-modified')
        else:
            query = self._get_query(strip_qs, self.search_fields)
            return self.all_sorted(sort).filter(query).order_by('-modified')

    def all_sorted(self, sort=None):
        """Apply to .all() one of the sort orders supported for views"""
        queryset = self.all()
        if sort == 'title':
            return queryset.order_by('title')
        else:
            return queryset.order_by('-created')


class BadgeException(Exception):
    """General Badger model exception"""


class BadgeException(BadgeException):
    """Badge model exception"""


class BadgeAwardNotAllowedException(BadgeException):
    """Attempt to award a badge not allowed."""


class BadgeAlreadyAwardedException(BadgeException):
    """Attempt to award a unique badge twice."""


class BadgeDeferredAwardManagementNotAllowedException(BadgeException):
    """Attempt to manage deferred awards not allowed."""


class BadgeManager(models.Manager, SearchManagerMixin):
    """Manager for Badge model objects"""
    search_fields = ('title', 'slug', 'description', )

    def allows_add_by(self, user):
        if user.is_anonymous():
            return False
        if getattr(settings, "BADGER_ALLOW_ADD_BY_ANYONE", False):
            return True
        if user.has_perm('badger.add_badge'):
            return True
        return False

    def allows_grant_by(self, user):
        if user.is_anonymous():
            return False
        if user.has_perm('badger.grant_deferredaward'):
            return True
        return False


@_document_django_model
class Badge(models.Model):
    """Representation of a badge"""
    objects = BadgeManager()

    title = models.CharField(max_length=255, blank=False, unique=True,
                             help_text='Short, descriptive title')
    slug = models.SlugField(blank=False, unique=True,
                            help_text='Very short name, for use in URLs and links')
    description = models.TextField(blank=True,
                                   help_text='Longer description of the badge and its criteria')
    image = models.ImageField(blank=True, null=True,
                              storage=BADGE_UPLOADS_FS, upload_to=UploadTo('image', 'png'),
                              help_text='Upload an image to represent the badge')
    # TODO: Rename? Eventually we'll want a globally-unique badge. That is, one
    # unique award for one person for the whole site.
    unique = models.BooleanField(default=True,
                                 help_text=('Should awards of this badge be limited to '
                                            'one-per-person?'))

    creator = models.ForeignKey(User, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, blank=False)
    modified = models.DateTimeField(auto_now=True, blank=False)

    class Meta:
        db_table = 'badger_badge'
        unique_together = ('title', 'slug')
        ordering = ['-modified', '-created']

    get_permissions_for = get_permissions_for

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('kbadge.badge_detail', args=(self.slug,))

    def get_upload_meta(self):
        return ("badge", self.slug)

    def clean(self):
        if self.image:
            scaled_file = scale_image(self.image.file, IMG_MAX_SIZE)
            if not scaled_file:
                raise ValidationError(_(u'Cannot process image'))
            self.image.file = scaled_file

    def save(self, **kwargs):
        """Save the submission, updating slug and screenshot thumbnails"""
        if not self.slug:
            self.slug = slugify(self.title)

        super(Badge, self).save(**kwargs)

    def delete(self, **kwargs):
        """Make sure deletes cascade to awards"""
        self.award_set.all().delete()
        super(Badge, self).delete(**kwargs)

    def allows_detail_by(self, user):
        # TODO: Need some logic here, someday.
        return True

    def allows_edit_by(self, user):
        if user.is_anonymous():
            return False
        if user.has_perm('badger.change_badge'):
            return True
        if user == self.creator:
            return True
        return False

    def allows_delete_by(self, user):
        if user.is_anonymous():
            return False
        if user.has_perm('badger.change_badge'):
            return True
        if user == self.creator:
            return True
        return False

    def allows_award_to(self, user):
        """Is award_to() allowed for this user?"""
        if user is None:
            return True
        if user.is_anonymous():
            return False
        if user.is_staff or user.is_superuser:
            return True
        if user == self.creator:
            return True

        # TODO: List of delegates for whom awarding is allowed

        return False

    def award_to(self, awardee=None, email=None, awarder=None,
                 description='', raise_already_awarded=False):
        """Award this badge to the awardee on the awarder's behalf"""
        # If no awarder given, assume this is on the badge creator's behalf.
        if not awarder:
            awarder = self.creator

        if not self.allows_award_to(awarder):
            raise BadgeAwardNotAllowedException()

        # If we have an email, but no awardee, try looking up the user.
        if email and not awardee:
            qs = User.objects.filter(email=email)

            if qs:
                awardee = qs.latest('date_joined')

        if self.unique and self.is_awarded_to(awardee):
            if raise_already_awarded:
                raise BadgeAlreadyAwardedException()
            else:
                return Award.objects.filter(user=awardee, badge=self)[0]

        return Award.objects.create(user=awardee, badge=self,
                                    creator=awarder,
                                    description=description)

    def is_awarded_to(self, user):
        """Has this badge been awarded to the user?"""
        return Award.objects.filter(user=user, badge=self).count() > 0


class AwardManager(models.Manager):
    def get_query_set(self):
        return super(AwardManager, self).get_query_set().exclude(hidden=True)


@_document_django_model
class Award(models.Model):
    """Representation of a badge awarded to a user"""

    admin_objects = models.Manager()
    objects = AwardManager()

    description = models.TextField(blank=True,
                                   help_text='Explanation and evidence for the badge award')
    badge = models.ForeignKey(Badge)
    image = models.ImageField(blank=True, null=True,
                              storage=BADGE_UPLOADS_FS,
                              upload_to=UploadTo('image', 'png'))
    user = models.ForeignKey(User, related_name="award_user")
    creator = models.ForeignKey(User, related_name="award_creator",
                                blank=True, null=True)
    hidden = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True, blank=False)
    modified = models.DateTimeField(auto_now=True, blank=False)

    get_permissions_for = get_permissions_for

    class Meta:
        db_table = 'badger_award'
        ordering = ['-modified', '-created']

    def __unicode__(self):
        by = self.creator and (u' by %s' % self.creator) or u''
        return u'Award of %s to %s%s' % (self.badge, self.user, by)

    @models.permalink
    def get_absolute_url(self):
        return ('kbadge.award_detail', (self.badge.slug, self.pk))

    def get_upload_meta(self):
        u = self.user.username
        return ("award/%s/%s/%s" % (u[0], u[1], u), self.badge.slug)

    def allows_detail_by(self, user):
        # TODO: Need some logic here, someday.
        return True

    def allows_delete_by(self, user):
        if user.is_anonymous():
            return False
        if user == self.user:
            return True
        if user == self.creator:
            return True
        if user.has_perm('badger.change_award'):
            return True
        return False

    def save(self, *args, **kwargs):

        # Signals and some bits of logic only happen on a new award.
        is_new = not self.pk

        if is_new:
            # Bail if this is an attempt to double-award a unique badge
            if self.badge.unique and self.badge.is_awarded_to(self.user):
                raise BadgeAlreadyAwardedException()

            # Only fire will-be-awarded signal on a new award.
            badge_will_be_awarded.send(sender=self.__class__, award=self)

        super(Award, self).save(*args, **kwargs)

        if is_new:
            # Only fire was-awarded signal on a new award.
            # TODO: we might not need this as there are no more notifications
            badge_was_awarded.send(sender=self.__class__, award=self)

    def delete(self):
        super(Award, self).delete()
