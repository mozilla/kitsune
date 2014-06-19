from rest_framework import generics, serializers
from django.shortcuts import get_object_or_404

from kitsune.products.models import Product, Topic
from kitsune.sumo.api import (CORSMixin, LocaleNegotiationMixin,
                              LocalizedCharField)


class ProductSerializer(serializers.ModelSerializer):
    platforms = serializers.SlugRelatedField(many=True, slug_field='slug')

    class Meta:
        model = Product
        fields = ('id', 'title', 'slug', 'description', 'platforms', 'visible')


class ProductList(CORSMixin, generics.ListAPIView):
    """List all documents."""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class TopicSerializer(serializers.ModelSerializer):
    parent = serializers.SlugRelatedField(slug_field='slug')
    path = serializers.Field(source='path')
    product = serializers.SlugRelatedField(slug_field='slug')
    title = LocalizedCharField(source='title',
                               l10n_context='DB: products.Topic.title')

    class Meta:
        model = Topic
        fields = ('id', 'title', 'slug', 'description', 'parent', 'visible',
                  'product', 'path')


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


class TopicList(CORSMixin, LocaleNegotiationMixin, generics.ListAPIView):
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer

    def get_queryset(self):
        queryset = self.queryset.filter(product__slug=self.kwargs['product'])
        visible = self.request.QUERY_PARAMS.get('visible', True)
        queryset = queryset.filter(visible=visible)
        return queryset
