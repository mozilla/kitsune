from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers
from rest_framework.decorators import api_view
from tower import ugettext_lazy as _lazy

from kitsune.products.models import Product, Topic
from kitsune.sumo.api import (CORSMixin, LocaleNegotiationMixin,
                              LocalizedCharField)
from kitsune.wiki.api import DocumentShortSerializer
from kitsune.wiki.models import Document


class ProductSerializer(serializers.ModelSerializer):
    platforms = serializers.SlugRelatedField(many=True, slug_field='slug')

    class Meta:
        model = Product
        fields = ('id', 'title', 'slug', 'description', 'platforms', 'visible')


class ProductList(CORSMixin, generics.ListAPIView):
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
    subtopics = TopicShortSerializer(source='subtopics', many=True)
    documents = serializers.SerializerMethodField('get_documents')

    class Meta:
        model = Topic
        fields = ('id', 'title', 'slug', 'description', 'parent', 'visible',
                  'product', 'path', 'subtopics', 'documents')

    def get_documents(self, obj):
        locale = self.context.get('locale', settings.WIKI_DEFAULT_LANGUAGE)
        docs = obj.documents(locale=locale)
        return DocumentShortSerializer(docs, many=True).data


class TopicDetail(CORSMixin, LocaleNegotiationMixin, generics.RetrieveAPIView):
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer

    def get_object(self):
        queryset = self.get_queryset()
        queryset = queryset.filter(
            visible=True,
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


class TopicList(CORSMixin, LocaleNegotiationMixin, generics.ListAPIView):
    queryset = Topic.objects.filter(parent=None)
    serializer_class = RootTopicSerializer

    def get_queryset(self):
        queryset = self.queryset.filter(product__slug=self.kwargs['product'])
        visible = bool(self.request.QUERY_PARAMS.get('visible', True))
        queryset = queryset.filter(visible=visible)
        return queryset
