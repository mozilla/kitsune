from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers
from tower import ugettext_lazy as _lazy

from kitsune.products.models import Product, Topic
from kitsune.sumo.api_utils import LocaleNegotiationMixin, LocalizedCharField, ImageUrlField
from kitsune.wiki.api import DocumentShortSerializer


class TopicField(serializers.SlugRelatedField):

    def __init__(self, slug_field='slug', product_field='product', **kwargs):
        super(TopicField, self).__init__(slug_field=slug_field, **kwargs)
        self.product_field = product_field
        self.error_messages['missing_product'] = (
            'A product must be specified to select a topic.')

    def from_native(self, topic_slug, product_slug):
        """
        Given a topic slug and product slug, get the right topic.

        This is like ``SlugRelatedField.from_native``, except it has been
        modified to deal with a product slug.
        """
        if self.queryset is None:
            raise Exception('Writable related fields must include a '
                            '`queryset` argument')

        try:
            return self.queryset.get(**{
                self.slug_field: topic_slug,
                'product__slug': product_slug
            })
        except ObjectDoesNotExist:
            raise ValidationError(self.error_messages['does_not_exist'] %
                                  (self.slug_field, topic_slug))
        except (TypeError, ValueError):
            msg = self.error_messages['invalid']
            raise ValidationError(msg)

    def field_from_native(self, data, files, field_name, into):
        """
        Update into with the topic object specified by the slug in data.

        This is like ``SlugRelatedField.field_from_native``, except it has
        been modified to also pass data['product']`` to ``from_native`` to
        disambiguate the topic from other topics with the same slug.
        """
        if self.read_only:
            return

        try:
            if self.many:
                try:
                    # Form data
                    value = data.getlist(field_name)
                    if value == [''] or value == []:
                        raise KeyError
                except AttributeError:
                    # Non-form data
                    value = data[field_name]
            else:
                value = data[field_name]
        except KeyError:
            if self.partial:
                return
            value = self.get_default_value()

        try:
            product_slug = data[self.product_field]
        except KeyError:
            if self.required or value not in self.null_values:
                raise ValidationError(self.error_messages['missing_product'])

        source = self.source or field_name

        if value in self.null_values:
            if self.required:
                raise ValidationError(self.error_messages['required'])
            into[source] = None
        elif self.many:
            into[source] = [self.from_native(item, product_slug)
                            for item in value]
        else:
            into[source] = self.from_native(value, product_slug)


class ProductSerializer(serializers.ModelSerializer):
    platforms = serializers.SlugRelatedField(many=True, slug_field='slug')
    image = ImageUrlField()

    class Meta:
        model = Product
        fields = ('id', 'title', 'slug', 'description', 'platforms', 'visible', 'image')


class ProductList(generics.ListAPIView):
    """List all documents."""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class TopicShortSerializer(serializers.ModelSerializer):
    title = LocalizedCharField(source='title',
                               l10n_context='DB: products.Topic.title')

    class Meta:
        model = Topic
        fields = ('title', 'slug')


class TopicSerializer(serializers.ModelSerializer):
    parent = serializers.SlugRelatedField(slug_field='slug')
    path = serializers.Field(source='path')
    product = serializers.SlugRelatedField(slug_field='slug')
    title = LocalizedCharField(source='title',
                               l10n_context='DB: products.Topic.title')
    subtopics = serializers.SerializerMethodField('get_subtopics')
    documents = serializers.SerializerMethodField('get_documents')

    class Meta:
        model = Topic
        fields = ('id', 'title', 'slug', 'description', 'parent', 'visible',
                  'product', 'path', 'subtopics', 'documents')

    def get_subtopics(self, obj):
        subtopics = obj.subtopics.filter(visible=True)
        return TopicShortSerializer(subtopics, many=True).data

    def get_documents(self, obj):
        locale = self.context.get('locale', settings.WIKI_DEFAULT_LANGUAGE)
        docs = obj.documents(locale=locale)
        return DocumentShortSerializer(docs, many=True).data


class TopicDetail(LocaleNegotiationMixin, generics.RetrieveAPIView):
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer

    def get_object(self):
        queryset = self.get_queryset()
        queryset = queryset.filter(
            slug=self.kwargs.pop('topic'),
            product__slug=self.kwargs.pop('product'))

        obj = get_object_or_404(queryset, **self.kwargs)
        self.check_object_permissions(self.request, obj)
        return obj


class RootTopicSerializer(TopicShortSerializer):
    """
    Wrap a list of topics in something that looks like a topic.

    This makes topic browsers on clients a lot simpler.
    """

    @property
    def data(self):
        topics = super(RootTopicSerializer, self).data
        return {
            'subtopics': topics,
            'documents': [],
            'title': _lazy('All Topics'),
            'slug': '',
            'description': _lazy('All Topics'),
            'parent': None,
            'visible': True,
            'product': None,
            'path': '/',
        }


class TopicList(LocaleNegotiationMixin, generics.ListAPIView):
    queryset = Topic.objects.filter(parent=None)
    serializer_class = RootTopicSerializer

    def get_queryset(self):
        queryset = self.queryset.filter(product__slug=self.kwargs['product'])
        visible = bool(self.request.query_params.get('visible', True))
        queryset = queryset.filter(visible=visible)
        return queryset
