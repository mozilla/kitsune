import hashlib
import itertools
import logging
import time
from datetime import datetime, timedelta
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.urlresolvers import resolve
from django.db import models, IntegrityError
from django.db.models import Q
from django.http import Http404
from django.utils.encoding import smart_str

import waffle
from pyquery import PyQuery
from tidings.models import NotificationsMixin
from django.utils.translation import ugettext_lazy as _lazy, ugettext as _

from kitsune.gallery.models import Image
from kitsune.products.models import Product, Topic
from kitsune.search.es_utils import UnindexMeBro, es_analyzer_for_locale
from kitsune.search.models import (
    SearchMappingType, SearchMixin, register_for_indexing,
    register_mapping_type)
from kitsune.sumo.apps import ProgrammingError
from kitsune.sumo.models import ModelBase, LocaleField
from kitsune.sumo.urlresolvers import reverse, split_path
from kitsune.tags.models import BigVocabTaggableMixin
from kitsune.wiki.config import (
    CATEGORIES, SIGNIFICANCES, TYPO_SIGNIFICANCE, MEDIUM_SIGNIFICANCE,
    MAJOR_SIGNIFICANCE, REDIRECT_HTML, REDIRECT_CONTENT, REDIRECT_TITLE,
    REDIRECT_SLUG, CANNED_RESPONSES_CATEGORY, ADMINISTRATION_CATEGORY,
    TEMPLATES_CATEGORY, DOC_HTML_CACHE_KEY, TEMPLATE_TITLE_PREFIX)
from kitsune.wiki.permissions import DocumentPermissionMixin


log = logging.getLogger('k.wiki')


class TitleCollision(Exception):
    """An attempt to create two pages of the same title in one locale"""


class SlugCollision(Exception):
    """An attempt to create two pages of the same slug in one locale"""


class _NotDocumentView(Exception):
    """A URL not pointing to the document view was passed to from_url()."""


class Document(NotificationsMixin, ModelBase, BigVocabTaggableMixin,
               SearchMixin, DocumentPermissionMixin):
    """A localized knowledgebase document, not revision-specific."""
    title = models.CharField(max_length=255, db_index=True)
    slug = models.CharField(max_length=255, db_index=True)

    # Is this document a template or not?
    is_template = models.BooleanField(default=False, editable=False,
                                      db_index=True)
    # Is this document localizable or not?
    is_localizable = models.BooleanField(default=True, db_index=True)

    # TODO: validate (against settings.SUMO_LANGUAGES?)
    locale = LocaleField(default=settings.WIKI_DEFAULT_LANGUAGE, db_index=True)

    # Latest approved revision. L10n dashboard depends on this being so (rather
    # than being able to set it to earlier approved revisions). (Remove "+" to
    # enable reverse link.)
    current_revision = models.ForeignKey('Revision', null=True,
                                         related_name='current_for+')

    # Latest revision which both is_approved and is_ready_for_localization,
    # This may remain non-NULL even if is_localizable is changed to false.
    latest_localizable_revision = models.ForeignKey(
        'Revision', null=True, related_name='localizable_for+')

    # The Document I was translated from. NULL iff this doc is in the default
    # locale or it is nonlocalizable. TODO: validate against
    # settings.WIKI_DEFAULT_LANGUAGE.
    parent = models.ForeignKey('self', related_name='translations',
                               null=True, blank=True)

    # Cached HTML rendering of approved revision's wiki markup:
    html = models.TextField(editable=False)

    # A document's category must always be that of its parent. If it has no
    # parent, it can do what it wants. This invariant is enforced in save().
    category = models.IntegerField(choices=CATEGORIES, db_index=True)

    # A document's is_archived flag must match that of its parent. If it has no
    # parent, it can do what it wants. This invariant is enforced in save().
    is_archived = models.BooleanField(
        default=False, db_index=True, verbose_name='is obsolete',
        help_text=_lazy(
            u'If checked, this wiki page will be hidden from basic searches '
            u'and dashboards. When viewed, the page will warn that it is no '
            u'longer maintained.'))

    # Enable discussion (kbforum) on this document.
    allow_discussion = models.BooleanField(
        default=True, help_text=_lazy(
            u'If checked, this document allows discussion in an associated '
            u'forum. Uncheck to hide/disable the forum.'))

    # List of users that have contributed to this document.
    contributors = models.ManyToManyField(User)

    # List of products this document applies to.
    products = models.ManyToManyField(Product)

    # List of product-specific topics this document applies to.
    topics = models.ManyToManyField(Topic)

    # Needs change fields.
    needs_change = models.BooleanField(default=False, help_text=_lazy(
        u'If checked, this document needs updates.'), db_index=True)
    needs_change_comment = models.CharField(max_length=500, blank=True)

    # A 24 character length gives years before having to alter max_length.
    share_link = models.CharField(max_length=24, default='')

    # Dictates the order in which articles are displayed.
    display_order = models.IntegerField(default=1, db_index=True)

    # List of related documents
    related_documents = models.ManyToManyField('self', blank=True)

    # firefox_versions,
    # operating_systems:
    #    defined in the respective classes below. Use them as in
    #    test_firefox_versions.

    # TODO: Rethink indexes once controller code is near complete. Depending on
    # how MySQL uses indexes, we probably don't need individual indexes on
    # title and locale as well as a combined (title, locale) one.
    class Meta(object):
        ordering = ['display_order', 'id']
        unique_together = (('parent', 'locale'), ('title', 'locale'),
                           ('slug', 'locale'))
        permissions = [('archive_document', 'Can archive document'),
                       ('edit_needs_change', 'Can edit needs_change')]

    def _collides(self, attr, value):
        """Return whether there exists a doc in this locale whose `attr` attr
        is equal to mine."""
        return Document.objects.filter(
            locale=self.locale, **{attr: value}).exclude(id=self.id).exists()

    def _raise_if_collides(self, attr, exception):
        """Raise an exception if a page of this title/slug already exists."""
        if self.id is None or hasattr(self, 'old_' + attr):
            # If I am new or my title/slug changed...
            if self._collides(attr, getattr(self, attr)):
                raise exception

    def clean(self):
        """Translations can't be localizable."""
        self._clean_is_localizable()
        self._clean_category()
        self._clean_template_status()
        self._ensure_inherited_attr('is_archived')

    def _clean_is_localizable(self):
        """is_localizable == allowed to have translations. Make sure that isn't
        violated.

        For default language (en-US), is_localizable means it can have
        translations. Enforce:
            * is_localizable=True if it has translations
            * if has translations, unable to make is_localizable=False

        For non-default langauges, is_localizable must be False.

        """
        if self.locale != settings.WIKI_DEFAULT_LANGUAGE:
            self.is_localizable = False

        # Can't save this translation if parent not localizable
        if self.parent and not self.parent.is_localizable:
            raise ValidationError('"%s": parent "%s" is not localizable.' % (
                                  unicode(self), unicode(self.parent)))

        # Can't make not localizable if it has translations
        # This only applies to documents that already exist, hence self.pk
        if self.pk and not self.is_localizable and self.translations.exists():
            raise ValidationError(
                u'"{0}": document has {1} translations but is not localizable.'
                .format(unicode(self), self.translations.count()))

    def _ensure_inherited_attr(self, attr):
        """Make sure my `attr` attr is the same as my parent's if I have one.

        Otherwise, if I have children, make sure their `attr` attr is the same
        as mine.

        """
        if self.parent:
            # We always set the child according to the parent rather than vice
            # versa, because we do not expose an Archived checkbox in the
            # translation UI.
            setattr(self, attr, getattr(self.parent, attr))
        else:  # An article cannot have both a parent and children.
            # Make my children the same as me:
            if self.id:
                self.translations.all().update(**{attr: getattr(self, attr)})

    def _clean_category(self):
        """Make sure a doc's category is valid."""
        if (not self.parent and
                self.category not in (id for id, name in CATEGORIES)):
            # All we really need to do here is make sure category != '' (which
            # is what it is when it's missing from the DocumentForm). The extra
            # validation is just a nicety.
            raise ValidationError(_('Please choose a category.'))

        self._ensure_inherited_attr('category')

    def _clean_template_status(self):
        if (self.category == TEMPLATES_CATEGORY and
                not self.title.startswith(TEMPLATE_TITLE_PREFIX)):
            raise ValidationError(_(u'Documents in the Template category must have titles that '
                                    u'start with "{prefix}". (Current title is "{title}")')
                                  .format(prefix=TEMPLATE_TITLE_PREFIX, title=self.title))

        if self.title.startswith(TEMPLATE_TITLE_PREFIX) and self.category != TEMPLATES_CATEGORY:
            raise ValidationError(_(u'Documents with titles that start with "{prefix}" must be in '
                                    u'the templates category. (Current category is "{category}". '
                                    u'Current title is "{title}".)')
                                  .format(prefix=TEMPLATE_TITLE_PREFIX,
                                          category=self.get_category_display(),
                                          title=self.title))

    def _attr_for_redirect(self, attr, template):
        """Return the slug or title for a new redirect.

        `template` is a Python string template with "old" and "number" tokens
        used to create the variant.

        """
        def unique_attr():
            """Return a variant of getattr(self, attr) such that there is no
            Document of my locale with string attribute `attr` equal to it.

            Never returns the original attr value.

            """
            # "My God, it's full of race conditions!"
            i = 1
            while True:
                new_value = template % dict(old=getattr(self, attr), number=i)
                if not self._collides(attr, new_value):
                    return new_value
                i += 1

        old_attr = 'old_' + attr
        if hasattr(self, old_attr):
            # My slug (or title) is changing; we can reuse it for the redirect.
            return getattr(self, old_attr)
        else:
            # Come up with a unique slug (or title):
            return unique_attr()

    def save(self, *args, **kwargs):
        slug_changed = hasattr(self, 'old_slug')
        title_changed = hasattr(self, 'old_title')

        self.is_template = (
            self.title.startswith(TEMPLATE_TITLE_PREFIX) or
            self.category == TEMPLATES_CATEGORY or
            (self.parent.category if self.parent else None) == TEMPLATES_CATEGORY)
        treat_as_template = (
            self.is_template or
            (self.old_title if title_changed else '').startswith(TEMPLATE_TITLE_PREFIX))

        self._raise_if_collides('slug', SlugCollision)
        self._raise_if_collides('title', TitleCollision)

        # These are too important to leave to a (possibly omitted) is_valid
        # call:
        self._clean_is_localizable()
        self._ensure_inherited_attr('is_archived')
        # Everything is validated before save() is called, so the only thing
        # that could cause save() to exit prematurely would be an exception,
        # which would cause a rollback, which would negate any category changes
        # we make here, so don't worry:
        self._clean_category()
        self._clean_template_status()

        if slug_changed:
            # Clear out the share link so it gets regenerated.
            self.share_link = ''

        super(Document, self).save(*args, **kwargs)

        # Make redirects if there's an approved revision and title or slug
        # changed. Allowing redirects for unapproved docs would (1) be of
        # limited use and (2) require making Revision.creator nullable.
        #
        # Having redirects for templates doesn't really make sense, and
        # none of the rest of the KB really deals with it, so don't bother.
        if self.current_revision and (slug_changed or title_changed) and not treat_as_template:
            try:
                doc = Document.objects.create(
                    locale=self.locale,
                    title=self._attr_for_redirect('title', REDIRECT_TITLE),
                    slug=self._attr_for_redirect('slug', REDIRECT_SLUG),
                    category=self.category,
                    is_localizable=False)
                Revision.objects.create(
                    document=doc,
                    content=REDIRECT_CONTENT % self.title,
                    is_approved=True,
                    reviewer=self.current_revision.creator,
                    creator=self.current_revision.creator)
            except TitleCollision:
                pass

        if slug_changed:
            del self.old_slug
        if title_changed:
            del self.old_title

        self.parse_and_calculate_links()
        self.clear_cached_html()

    def __setattr__(self, name, value):
        """Trap setting slug and title, recording initial value."""
        # Public API: delete the old_title or old_slug attrs after changing
        # title or slug (respectively) to suppress redirect generation.
        if name != '_state' and not self._state.adding:
            # I have been saved and so am worthy of a redirect.
            if name in ('slug', 'title'):
                old_name = 'old_' + name
                if not hasattr(self, old_name):
                    # Avoid recursive call to __setattr__ when
                    # ``getattr(self, name)`` needs to refresh the
                    # database.
                    setattr(self, old_name, None)
                    # Normal articles are compared case-insensitively
                    if getattr(self, name).lower() != value.lower():
                        setattr(self, old_name, getattr(self, name))
                    else:
                        delattr(self, old_name)

                    # Articles that have a changed title are checked
                    # case-sensitively for the title prefix changing.
                    ttp = TEMPLATE_TITLE_PREFIX
                    if name == 'title' and self.title.startswith(ttp) != value.startswith(ttp):
                        # Save original value:
                        setattr(self, old_name, getattr(self, name))

                elif value == getattr(self, old_name):
                    # They changed the attr back to its original value.
                    delattr(self, old_name)
        super(Document, self).__setattr__(name, value)

    @property
    def content_parsed(self):
        if not self.current_revision:
            return ''
        return self.current_revision.content_parsed

    @property
    def summary(self):
        if not self.current_revision:
            return ''
        return self.current_revision.summary

    @property
    def language(self):
        return settings.LANGUAGES_DICT[self.locale.lower()]

    @property
    def related_products(self):
        related_pks = [d.pk for d in self.related_documents.all()]
        related_pks.append(self.pk)
        return Product.objects.filter(document__in=related_pks).distinct()

    @property
    def is_hidden_from_search_engines(self):
        return (self.is_template or self.is_archived or
                self.category in (ADMINISTRATION_CATEGORY,
                                  CANNED_RESPONSES_CATEGORY))

    def get_absolute_url(self):
        return reverse('wiki.document', locale=self.locale, args=[self.slug])

    @classmethod
    def from_url(cls, url, required_locale=None, id_only=False,
                 check_host=True):
        """Return the approved Document the URL represents, None if there isn't
        one.

        Return None if the URL is a 404, the URL doesn't point to the right
        view, or the indicated document doesn't exist.

        To limit the universe of discourse to a certain locale, pass in a
        `required_locale`. To fetch only the ID of the returned Document, set
        `id_only` to True.

        If the URL has a host component, we assume it does not point to this
        host and thus does not point to a Document, because that would be a
        needlessly verbose way to specify an internal link. However, if you
        pass check_host=False, we assume the URL's host is the one serving
        Documents, which comes in handy for analytics whose metrics return
        host-having URLs.

        """
        try:
            components = _doc_components_from_url(
                url, required_locale=required_locale, check_host=check_host)
        except _NotDocumentView:
            return None
        if not components:
            return None
        locale, path, slug = components

        doc = cls.objects
        if id_only:
            doc = doc.only('id')
        try:
            doc = doc.get(locale=locale, slug=slug)
        except cls.DoesNotExist:
            try:
                doc = doc.get(locale=settings.WIKI_DEFAULT_LANGUAGE, slug=slug)
                translation = doc.translated_to(locale)
                if translation:
                    return translation
                return doc
            except cls.DoesNotExist:
                return None
        return doc

    def redirect_url(self, source_locale=settings.LANGUAGE_CODE):
        """If I am a redirect, return the URL to which I redirect.

        Otherwise, return None.

        """
        # If a document starts with REDIRECT_HTML and contains any <a> tags
        # with hrefs, return the href of the first one. This trick saves us
        # from having to parse the HTML every time.
        if self.html.startswith(REDIRECT_HTML):
            anchors = PyQuery(self.html)('a[href]')
            if anchors:
                # Articles with a redirect have a link that has the locale
                # hardcoded into it, and so by simply redirecting to the given
                # link, we end up possibly losing the locale. So, instead,
                # we strip out the locale and replace it with the original
                # source locale only in the case where an article is going
                # from one locale and redirecting it to a different one.
                # This only applies when it's a non-default locale because we
                # don't want to override the redirects that are forcibly
                # changing to (or staying within) a specific locale.
                full_url = anchors[0].get('href')
                (dest_locale, url) = split_path(full_url)
                if (source_locale != dest_locale and
                        dest_locale == settings.LANGUAGE_CODE):
                    return '/' + source_locale + '/' + url
                return full_url

    def redirect_document(self):
        """If I am a redirect to a Document, return that Document.

        Otherwise, return None.

        """
        url = self.redirect_url()
        if url:
            return self.from_url(url)

    def __unicode__(self):
        return '[%s] %s' % (self.locale, self.title)

    def allows_vote(self, request):
        """Return whether we should render the vote form for the document."""

        # If the user isn't authenticated, we show the form even if they
        # may have voted. This is because the page can be cached and we don't
        # want to cache the page without the vote form. Users that already
        # voted will see a "You already voted on this Article." message
        # if they try voting again.
        authed_and_voted = (
            request.user.is_authenticated() and
            self.current_revision and
            self.current_revision.has_voted(request))

        return (not self.is_archived and
                self.current_revision and
                not authed_and_voted and
                not self.redirect_document() and
                self.category != TEMPLATES_CATEGORY and
                not waffle.switch_is_active('hide-voting'))

    def translated_to(self, locale):
        """Return the translation of me to the given locale.

        If there is no such Document, return None.

        """
        if self.locale != settings.WIKI_DEFAULT_LANGUAGE:
            raise NotImplementedError('translated_to() is implemented only on'
                                      'Documents in the default language so'
                                      'far.')
        try:
            return Document.objects.get(locale=locale, parent=self)
        except Document.DoesNotExist:
            return None

    @property
    def original(self):
        """Return the document I was translated from or, if none, myself."""
        return self.parent or self

    def localizable_or_latest_revision(self, include_rejected=False):
        """Return latest ready-to-localize revision if there is one,
        else the latest approved revision if there is one,
        else the latest unrejected (unreviewed) revision if there is one,
        else None.

        include_rejected -- If true, fall back to the latest rejected
            revision if all else fails.

        """
        def latest(queryset):
            """Return the latest item from a queryset (by ID).

            Return None if the queryset is empty.

            """
            try:
                return queryset.order_by('-id')[0:1].get()
            except ObjectDoesNotExist:  # Catching IndexError seems overbroad.
                return None

        rev = self.latest_localizable_revision
        if not rev or not self.is_localizable:
            rejected = Q(is_approved=False, reviewed__isnull=False)

            # Try latest approved revision:
            rev = (latest(self.revisions.filter(is_approved=True)) or
                   # No approved revs. Try unrejected:
                   latest(self.revisions.exclude(rejected)) or
                   # No unrejected revs. Maybe fall back to rejected:
                   (latest(self.revisions) if include_rejected else None))
        return rev

    def is_outdated(self, level=MEDIUM_SIGNIFICANCE):
        """Return whether an update of a given magnitude has occured
        to the parent document since this translation had an approved
        update and such revision is ready for l10n.

        If this is not a translation or has never been approved, return
        False.

        level: The significance of an edit that is "enough". Defaults to
            MEDIUM_SIGNIFICANCE.

        """
        if not (self.parent and self.current_revision):
            return False

        based_on_id = self.current_revision.based_on_id
        more_filters = {'id__gt': based_on_id} if based_on_id else {}

        return self.parent.revisions.filter(
            is_approved=True, is_ready_for_localization=True,
            significance__gte=level, **more_filters).exists()

    def is_majorly_outdated(self):
        """Return whether a MAJOR_SIGNIFICANCE-level update has occurred to the
        parent document since this translation had an approved update and such
        revision is ready for l10n.

        If this is not a translation or has never been approved, return False.

        """
        return self.is_outdated(level=MAJOR_SIGNIFICANCE)

    def is_watched_by(self, user):
        """Return whether `user` is notified of edits to me."""
        from kitsune.wiki.events import EditDocumentEvent
        return EditDocumentEvent.is_notifying(user, self)

    def get_topics(self):
        """Return the list of new topics that apply to this document.

        If the document has a parent, it inherits the parent's topics.
        """
        if self.parent:
            return self.parent.get_topics()

        return Topic.objects.filter(document=self)

    def get_products(self):
        """Return the list of products that apply to this document.

        If the document has a parent, it inherits the parent's products.
        """
        if self.parent:
            return self.parent.get_products()

        return Product.objects.filter(document=self)

    @property
    def recent_helpful_votes(self):
        """Return the number of helpful votes in the last 30 days."""
        start = datetime.now() - timedelta(days=30)
        return HelpfulVote.objects.filter(
            revision__document=self, created__gt=start, helpful=True).count()

    @classmethod
    def get_mapping_type(cls):
        return DocumentMappingType

    def parse_and_calculate_links(self):
        """Calculate What Links Here data for links going out from this.

        Also returns a parsed version of the current html, because that
        is a byproduct of the process, and is useful.
        """
        if not self.current_revision:
            return ''

        # Remove "what links here" reverse links, because they might be
        # stale and re-rendering will re-add them. This cannot be done
        # reliably in the parser's parse() function, because that is
        # often called multiple times per document.
        self.links_from().delete()

        # Also delete the DocumentImage instances for this document.
        DocumentImage.objects.filter(document=self).delete()

        from kitsune.wiki.parser import wiki_to_html, WhatLinksHereParser
        return wiki_to_html(self.current_revision.content,
                            locale=self.locale,
                            doc_id=self.id,
                            parser_cls=WhatLinksHereParser)

    def links_from(self):
        """Get a query set of links that are from this document to another."""
        return DocumentLink.objects.filter(linked_from=self)

    def links_to(self):
        """Get a query set of links that are from another document to this."""
        return DocumentLink.objects.filter(linked_to=self)

    def add_link_to(self, linked_to, kind):
        """Create a DocumentLink to another Document."""
        DocumentLink.objects.get_or_create(linked_from=self,
                                           linked_to=linked_to,
                                           kind=kind)

    @property
    def images(self):
        return Image.objects.filter(documentimage__document=self)

    def add_image(self, image):
        """Create a DocumentImage to connect self to an Image instance."""
        try:
            DocumentImage(document=self, image=image).save()
        except IntegrityError:
            # This DocumentImage already exists, ok.
            pass

    def clear_cached_html(self):
        # Clear out both mobile and desktop templates.
        for mobile, minimal in itertools.product([True, False], repeat=2):
            cache.delete(doc_html_cache_key(self.locale, self.slug, mobile, minimal))


@register_mapping_type
class DocumentMappingType(SearchMappingType):
    seconds_ago_filter = 'current_revision__created__gte'
    list_keys = [
        'topic',
        'product'
    ]

    @classmethod
    def get_model(cls):
        return Document

    @classmethod
    def get_query_fields(cls):
        return ['document_title',
                'document_content',
                'document_summary',
                'document_keywords']

    @classmethod
    def get_localized_fields(cls):
        # This is the same list as `get_query_fields`, but it doesn't
        # have to be, which is why it is typed twice.
        return ['document_title',
                'document_content',
                'document_summary',
                'document_keywords']

    @classmethod
    def get_mapping(cls):
        return {
            'properties': {
                # General fields
                'id': {'type': 'long'},
                'model': {'type': 'string', 'index': 'not_analyzed'},
                'url': {'type': 'string', 'index': 'not_analyzed'},
                'indexed_on': {'type': 'integer'},
                'updated': {'type': 'integer'},

                'product': {'type': 'string', 'index': 'not_analyzed'},
                'topic': {'type': 'string', 'index': 'not_analyzed'},

                # Document specific fields (locale aware)
                'document_title': {'type': 'string', 'analyzer': 'snowball'},
                'document_keywords': {'type': 'string', 'analyzer': 'snowball'},
                'document_content': {'type': 'string', 'store': 'yes',
                                     'analyzer': 'snowball',
                                     'term_vector': 'with_positions_offsets'},
                'document_summary': {'type': 'string', 'store': 'yes',
                                     'analyzer': 'snowball',
                                     'term_vector': 'with_positions_offsets'},

                # Document specific fields (locale naive)
                'document_locale': {'type': 'string', 'index': 'not_analyzed'},
                'document_current_id': {'type': 'integer'},
                'document_parent_id': {'type': 'integer'},
                'document_category': {'type': 'integer'},
                'document_slug': {'type': 'string', 'index': 'not_analyzed'},
                'document_is_archived': {'type': 'boolean'},
                'document_recent_helpful_votes': {'type': 'integer'},
                'document_display_order': {'type': 'integer'}
            }
        }

    @classmethod
    def extract_document(cls, obj_id, obj=None):
        if obj is None:
            model = cls.get_model()
            obj = model.objects.select_related(
                'current_revision', 'parent').get(pk=obj_id)

        if obj.html.startswith(REDIRECT_HTML):
            # It's possible this document is indexed and was turned
            # into a redirect, so now we want to explicitly unindex
            # it. The way we do that is by throwing an exception
            # which gets handled by the indexing machinery.
            raise UnindexMeBro()

        d = {}
        d['id'] = obj.id
        d['model'] = cls.get_mapping_type_name()
        d['url'] = obj.get_absolute_url()
        d['indexed_on'] = int(time.time())

        d['topic'] = [t.slug for t in obj.get_topics()]
        d['product'] = [p.slug for p in obj.get_products()]

        d['document_title'] = obj.title
        d['document_locale'] = obj.locale
        d['document_parent_id'] = obj.parent.id if obj.parent else None
        d['document_content'] = obj.html
        d['document_category'] = obj.category
        d['document_slug'] = obj.slug
        d['document_is_archived'] = obj.is_archived
        d['document_display_order'] = obj.original.display_order

        d['document_summary'] = obj.summary
        if obj.current_revision is not None:
            d['document_keywords'] = obj.current_revision.keywords
            d['updated'] = int(time.mktime(
                obj.current_revision.created.timetuple()))
            d['document_current_id'] = obj.current_revision.id
            d['document_recent_helpful_votes'] = obj.recent_helpful_votes
        else:
            d['document_summary'] = None
            d['document_keywords'] = None
            d['updated'] = None
            d['document_current_id'] = None
            d['document_recent_helpful_votes'] = 0

        # Don't query for helpful votes if the document doesn't have a current
        # revision, or is a template, or is a redirect, or is in Navigation
        # category (50).
        if (obj.current_revision and
                not obj.is_template and
                not obj.html.startswith(REDIRECT_HTML) and
                not obj.category == 50):
            d['document_recent_helpful_votes'] = obj.recent_helpful_votes
        else:
            d['document_recent_helpful_votes'] = 0

        # Select a locale-appropriate default analyzer for all strings.
        d['_analyzer'] = es_analyzer_for_locale(obj.locale)

        return d

    @classmethod
    def get_indexable(cls, seconds_ago=0):
        # This function returns all the indexable things, but we
        # really need to handle the case where something was indexable
        # and isn't anymore. Given that, this returns everything that
        # has a revision.
        indexable = super(cls, cls).get_indexable(seconds_ago=seconds_ago)
        indexable = indexable.filter(current_revision__isnull=False)
        return indexable

    @classmethod
    def index(cls, document, **kwargs):
        # If there are no revisions or the current revision is a
        # redirect, we want to remove it from the index.
        if (document['document_current_id'] is None or
                document['document_content'].startswith(REDIRECT_HTML)):

            cls.unindex(document['id'], es=kwargs.get('es', None))
            return

        super(cls, cls).index(document, **kwargs)


register_for_indexing('wiki', Document)
register_for_indexing(
    'wiki',
    Document.topics.through,
    m2m=True)
register_for_indexing(
    'wiki',
    Document.products.through,
    m2m=True)


MAX_REVISION_COMMENT_LENGTH = 255


class AbstractRevision(models.Model):
    # **%(class)s** is being used because it will allow  a unique reverse name for the field
    # like created_revisions and created_draftrevisions
    creator = models.ForeignKey(User, related_name='created_%(class)ss')
    created = models.DateTimeField(default=datetime.now)
    # The reverse name should be revisions and draftrevisions
    document = models.ForeignKey(Document, related_name='%(class)ss')
    # Keywords are used mostly to affect search rankings. Moderators may not
    # have the language expertise to translate keywords, so we put them in the
    # Revision so the translators can handle them:
    keywords = models.CharField(max_length=255, blank=True)

    class Meta:
        abstract = True


class Revision(ModelBase, SearchMixin, AbstractRevision):
    """A revision of a localized knowledgebase document"""
    summary = models.TextField()  # wiki markup
    content = models.TextField()  # wiki markup

    reviewed = models.DateTimeField(null=True)
    expires = models.DateTimeField(null=True, blank=True)

    # The significance of the initial revision of a document is NULL.
    significance = models.IntegerField(choices=SIGNIFICANCES, null=True)

    comment = models.CharField(max_length=MAX_REVISION_COMMENT_LENGTH)
    reviewer = models.ForeignKey(User, related_name='reviewed_revisions',
                                 null=True)
    is_approved = models.BooleanField(default=False, db_index=True)

    # The default locale's rev that was the latest ready-for-l10n one when the
    # Edit button was hit to begin creating this revision. If there was none,
    # this is simply the latest of the default locale's revs as of that time.
    # Used to determine whether localizations are out of date.
    based_on = models.ForeignKey('self', null=True, blank=True)
    # TODO: limit_choices_to={'document__locale':
    # settings.WIKI_DEFAULT_LANGUAGE} is a start but not sufficient.

    # Is both approved and marked as ready for translation (which will result
    # in the translation UI considering it when looking for the latest
    # translatable version). If is_approved=False or this revision belongs to a
    # non-default-language Document, this must be False.
    is_ready_for_localization = models.BooleanField(default=False)
    readied_for_localization = models.DateTimeField(null=True)
    readied_for_localization_by = models.ForeignKey(
        User, related_name='readied_for_l10n_revisions', null=True)

    class Meta(object):
        permissions = [('review_revision', 'Can review a revision'),
                       ('mark_ready_for_l10n',
                        'Can mark revision as ready for localization'),
                       ('edit_keywords', 'Can edit keywords')]

    def _based_on_is_clean(self):
        """Return a tuple: (the correct value of based_on, whether the old
        value was correct).

        based_on must be a revision of the English version of the document. If
        based_on is not already set when this is called, the return value
        defaults to something reasonable.

        """
        original = self.document.original
        if self.based_on and self.based_on.document != original:
            # based_on is set and points to the wrong doc. The following is
            # then the most likely helpful value:
            return original.localizable_or_latest_revision(), False
        # Even None is permissible, for example in the case of a brand new doc.
        return self.based_on, True

    def clean(self):
        """Ensure based_on is valid & police is_ready/is_approved invariant."""
        # All of the cleaning herein should be unnecessary unless the user
        # messes with hidden form data.
        try:
            self.document and self.document.original
        except Document.DoesNotExist:
            # For clean()ing forms that don't have a document instance behind
            # them yet
            self.based_on = None
        else:
            based_on, is_clean = self._based_on_is_clean()
            if not is_clean:
                old = self.based_on
                self.based_on = based_on  # Be nice and guess a correct value.
                # TODO(erik): This error message ignores non-translations.
                raise ValidationError(
                    _('A revision must be based on the English article. '
                      'Revision ID %(id)s does not fit this criterion.') %
                    dict(id=old.id))

        if not self.can_be_readied_for_localization():
            self.is_ready_for_localization = False

    def save(self, *args, **kwargs):
        _, is_clean = self._based_on_is_clean()
        if not is_clean:  # No more Mister Nice Guy
            # TODO(erik): This error message ignores non-translations.
            raise ProgrammingError('Revision.based_on must be None or refer '
                                   'to a revision of the default-'
                                   'language document.')

        super(Revision, self).save(*args, **kwargs)

        # When a revision is approved, re-cache the document's html content
        # and update document contributors
        if self.is_approved and (
                not self.document.current_revision or
                self.document.current_revision.id < self.id):
            # Determine if there are new contributors and add them to the list
            contributors = self.document.contributors.all()
            # Exclude all explicitly rejected revisions
            new_revs = self.document.revisions.exclude(
                reviewed__isnull=False, is_approved=False)
            if self.document.current_revision:
                new_revs = new_revs.filter(
                    id__gt=self.document.current_revision.id)
            new_contributors = {r.creator for r in new_revs.select_related('creator')}
            for user in new_contributors:
                if user not in contributors:
                    self.document.contributors.add(user)

            # Update document denormalized fields
            if self.is_ready_for_localization:
                self.document.latest_localizable_revision = self
            self.document.html = self.content_parsed
            self.document.current_revision = self
            self.document.save()
        elif (self.is_ready_for_localization and
              (not self.document.latest_localizable_revision or
               self.id > self.document.latest_localizable_revision.id)):
            # We are marking a newer revision as ready for l10n.
            # Update the denormalized field on the document.
            self.document.latest_localizable_revision = self
            self.document.save()

    def delete(self, *args, **kwargs):
        """Dodge cascading delete of documents and other revisions."""
        def latest_revision(excluded_rev, constraint):
            """Return the largest-ID'd revision meeting the given constraint
            and excluding the given revision, or None if there is none."""
            revs = document.revisions.filter(constraint).exclude(
                pk=excluded_rev.pk).order_by('-id')[:1]
            try:
                # Academic TODO: There's probably a way to keep the QuerySet
                # lazy all the way through the update() call.
                return revs[0]
            except IndexError:
                return None

        Revision.objects.filter(based_on=self).update(based_on=None)
        document = self.document

        # If the current_revision is being deleted, try to update it to the
        # previous approved revision:
        if document.current_revision == self:
            new_current = latest_revision(self, Q(is_approved=True))
            document.update(
                current_revision=new_current,
                html=new_current.content_parsed if new_current else '')

        # Likewise, step the latest_localizable_revision field backward if
        # we're deleting that revision:
        if document.latest_localizable_revision == self:
            document.update(latest_localizable_revision=latest_revision(
                self, Q(is_approved=True, is_ready_for_localization=True)))

        super(Revision, self).delete(*args, **kwargs)

    def has_voted(self, request):
        """Did the user already vote for this revision?"""
        if request.user.is_authenticated():
            qs = HelpfulVote.objects.filter(revision=self,
                                            creator=request.user)
        elif request.anonymous.has_id:
            anon_id = request.anonymous.anonymous_id
            qs = HelpfulVote.objects.filter(revision=self,
                                            anonymous_id=anon_id)
        else:
            return False

        return qs.exists()

    def __unicode__(self):
        return u'[%s] %s #%s: %s' % (self.document.locale,
                                     self.document.title,
                                     self.id, self.content[:50])

    def __repr__(self):
        return '<Revision [{!r}] {!r} #{!r}: {!r:.50}>'.format(
            self.document.locale,
            self.document.title,
            self.id,
            self.content)

    @property
    def content_parsed(self):
        from kitsune.wiki.parser import wiki_to_html
        return wiki_to_html(self.content, locale=self.document.locale,
                            doc_id=self.document.id)

    def can_be_readied_for_localization(self):
        """Return whether this revision has the prerequisites necessary for the
        user to mark it as ready for localization."""
        # If not is_approved, can't be is_ready. TODO: think about using a
        # single field with more states.
        # Also, if significance is trivial, it shouldn't be translated.
        return (self.is_approved and
                self.significance > TYPO_SIGNIFICANCE and
                self.document.locale == settings.WIKI_DEFAULT_LANGUAGE)

    def get_absolute_url(self):
        return reverse('wiki.revision', locale=self.document.locale,
                       args=[self.document.slug, self.id])

    @property
    def previous(self):
        """Get the revision that came before this in the document's history."""
        older_revs = Revision.objects.filter(document=self.document,
                                             id__lt=self.id,
                                             is_approved=True)
        older_revs = older_revs.order_by('-created')
        try:
            return older_revs[0]
        except IndexError:
            return None

    @classmethod
    def get_mapping_type(cls):
        return RevisionMetricsMappingType


class DraftRevision(ModelBase, SearchMixin, AbstractRevision):
    based_on = models.ForeignKey(Revision)
    content = models.TextField(blank=True)
    locale = LocaleField(blank=False, db_index=True)
    slug = models.CharField(max_length=255, blank=True)
    summary = models.TextField(blank=True)
    title = models.CharField(max_length=255, blank=True)


@register_mapping_type
class RevisionMetricsMappingType(SearchMappingType):
    seconds_ago_filter = 'created__gte'

    @classmethod
    def get_model(cls):
        return Revision

    @classmethod
    def get_index_group(cls):
        return 'metrics'

    @classmethod
    def get_mapping(cls):
        return {
            'properties': {
                'id': {'type': 'long'},
                'model': {'type': 'string', 'index': 'not_analyzed'},
                'url': {'type': 'string', 'index': 'not_analyzed'},
                'indexed_on': {'type': 'integer'},
                'created': {'type': 'date'},
                'reviewed': {'type': 'date'},

                'locale': {'type': 'string', 'index': 'not_analyzed'},
                'product': {'type': 'string', 'index': 'not_analyzed'},
                'is_approved': {'type': 'boolean'},
                'creator_id': {'type': 'long'},
                'reviewer_id': {'type': 'long'},
            }
        }

    @classmethod
    def extract_document(cls, obj_id, obj=None):
        """Extracts indexable attributes from an Answer."""
        fields = ['id', 'created', 'creator_id', 'reviewed', 'reviewer_id',
                  'is_approved', 'document_id']
        composed_fields = ['document__locale', 'document__slug']
        all_fields = fields + composed_fields

        if obj is None:
            model = cls.get_model()
            obj_dict = model.objects.values(*all_fields).get(pk=obj_id)
        else:
            obj_dict = dict([(field, getattr(obj, field))
                             for field in fields])
            obj_dict['document__locale'] = obj.document.locale
            obj_dict['document__slug'] = obj.document.slug

        d = {}
        d['id'] = obj_dict['id']
        d['model'] = cls.get_mapping_type_name()

        # We do this because get_absolute_url is an instance method
        # and we don't want to create an instance because it's a DB
        # hit and expensive. So we do it by hand. get_absolute_url
        # doesn't change much, so this is probably ok.
        d['url'] = reverse('wiki.revision', kwargs={
            'revision_id': obj_dict['id'],
            'document_slug': obj_dict['document__slug']})

        d['indexed_on'] = int(time.time())

        d['created'] = obj_dict['created']
        d['reviewed'] = obj_dict['reviewed']

        d['locale'] = obj_dict['document__locale']
        d['is_approved'] = obj_dict['is_approved']
        d['creator_id'] = obj_dict['creator_id']
        d['reviewer_id'] = obj_dict['reviewer_id']

        doc = Document.objects.get(id=obj_dict['document_id'])
        d['product'] = [p.slug for p in doc.get_products()]

        return d


register_for_indexing('revisions', Revision)


class HelpfulVote(ModelBase):
    """Helpful or Not Helpful vote on Revision."""
    revision = models.ForeignKey(Revision, related_name='poll_votes')
    helpful = models.BooleanField(default=False)
    created = models.DateTimeField(default=datetime.now, db_index=True)
    creator = models.ForeignKey(User, related_name='poll_votes', null=True)
    anonymous_id = models.CharField(max_length=40, db_index=True)
    user_agent = models.CharField(max_length=1000)

    def add_metadata(self, key, value):
        HelpfulVoteMetadata.objects.create(vote=self, key=key, value=value)


class HelpfulVoteMetadata(ModelBase):
    """Metadata for article votes."""
    vote = models.ForeignKey(HelpfulVote, related_name='metadata')
    key = models.CharField(max_length=40, db_index=True)
    value = models.CharField(max_length=1000)


class ImportantDate(ModelBase):
    """Important date that shows up globally on metrics graphs."""
    text = models.CharField(max_length=100)
    date = models.DateField(db_index=True)


# Note: This model should probably be called LocaleTeam.
# It's a pain to change it now because of table names, FK column names,
# the M2M tables, etc.
class Locale(ModelBase):
    """A localization team."""
    locale = LocaleField(unique=True)
    leaders = models.ManyToManyField(
        User, blank=True, related_name='locales_leader')
    reviewers = models.ManyToManyField(
        User, blank=True, related_name='locales_reviewer')
    editors = models.ManyToManyField(
        User, blank=True, related_name='locales_editor')

    class Meta:
        ordering = ['locale']

    def get_absolute_url(self):
        return reverse('wiki.locale_details', args=[self.locale])

    def __unicode__(self):
        return self.locale


class DocumentLink(ModelBase):
    """Model a link between documents.

    If article A contains [[Link:B]], then `linked_to` is B,
    `linked_from` is A, and kind is 'link'.
    """
    linked_to = models.ForeignKey(Document,
                                  related_name='documentlink_from_set')
    linked_from = models.ForeignKey(Document,
                                    related_name='documentlink_to_set')
    kind = models.CharField(max_length=16)

    class Meta:
        unique_together = ('linked_from', 'linked_to', 'kind')

    def __unicode__(self):
        return (u'<DocumentLink: %s from %s to %s>' %
                (self.kind, self.linked_from, self.linked_to))


class DocumentImage(ModelBase):
    """Model to keep track of what documents include what images."""
    document = models.ForeignKey(Document)
    image = models.ForeignKey(Image)

    class Meta:
        unique_together = ('document', 'image')

    def __unicode__(self):
        return u'<DocumentImage: {doc} includes {img}>'.format(
            doc=self.document, img=self.image)


def _doc_components_from_url(url, required_locale=None, check_host=True):
    """Return (locale, path, slug) if URL is a Document, False otherwise.

    If URL doesn't even point to the document view, raise _NotDocumentView.

    """
    # Extract locale and path from URL:
    parsed = urlparse(url)  # Never has errors AFAICT
    if check_host and parsed.netloc:
        return False
    locale, path = split_path(parsed.path)
    if required_locale and locale != required_locale:
        return False
    path = '/' + path

    try:
        view, view_args, view_kwargs = resolve(path)
    except Http404:
        return False

    import kitsune.wiki.views  # Views import models; models import views.
    if view != kitsune.wiki.views.document:
        raise _NotDocumentView
    return locale, path, view_kwargs['document_slug']


def points_to_document_view(url, required_locale=None):
    """Return whether a URL reverses to the document view.

    To limit the universe of discourse to a certain locale, pass in a
    `required_locale`.

    """
    try:
        return not not _doc_components_from_url(
            url, required_locale=required_locale)
    except _NotDocumentView:
        return False


def user_num_documents(user):
    """Count the number of documents a user has contributed to. """
    return (Document.objects
            .filter(revisions__creator=user)
            .exclude(html__startswith='<p>REDIRECT <a').distinct().count())


def user_documents(user):
    """Return the documents a user has contributed to."""
    return (Document.objects
            .filter(revisions__creator=user)
            .exclude(html__startswith='<p>REDIRECT <a').distinct())


def user_redirects(user):
    """Return the redirects a user has contributed to."""
    return (Document.objects
            .filter(revisions__creator=user)
            .filter(html__startswith='<p>REDIRECT <a').distinct())


def doc_html_cache_key(locale, slug, mobile, minimal):
    """Returns the cache key for the document html."""
    cache_key = DOC_HTML_CACHE_KEY.format(
        locale=locale, slug=slug, mobile=str(mobile), minimal=str(minimal))
    return hashlib.sha1(smart_str(cache_key)).hexdigest()
