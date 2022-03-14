from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _lazy

from rest_framework import generics, serializers

from kitsune.products.models import Product, Topic, Platform
from kitsune.sumo.api_utils import LocaleNegotiationMixin, LocalizedCharField, ImageUrlField
from kitsune.wiki.api import DocumentShortSerializer


class ProductSerializer(serializers.ModelSerializer):
    platforms = serializers.SlugRelatedField(
        many=True, slug_field="slug", queryset=Platform.objects.all()
    )
    image = ImageUrlField()

    class Meta:
        model = Product
        fields = ("id", "title", "slug", "description", "platforms", "visible", "image")


class ProductList(generics.ListAPIView):
    """List all documents."""

    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class TopicShortSerializer(serializers.ModelSerializer):
    title = LocalizedCharField(l10n_context="DB: products.Topic.title")

    class Meta:
        model = Topic
        fields = ("title", "slug")


class TopicSerializer(serializers.ModelSerializer):
    parent = serializers.SlugRelatedField(slug_field="slug", queryset=Topic.objects.all())
    path = serializers.ReadOnlyField()
    product = serializers.SlugRelatedField(slug_field="slug", queryset=Product.objects.all())
    title = LocalizedCharField(l10n_context="DB: products.Topic.title")
    subtopics = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = (
            "id",
            "title",
            "slug",
            "description",
            "parent",
            "visible",
            "product",
            "path",
            "subtopics",
            "documents",
        )

    def get_subtopics(self, obj):
        subtopics = obj.subtopics.filter(visible=True)
        return TopicShortSerializer(subtopics, many=True).data

    def get_documents(self, obj):
        locale = self.context.get("locale", settings.WIKI_DEFAULT_LANGUAGE)
        docs = obj.documents(locale=locale)
        return DocumentShortSerializer(docs, many=True).data


class TopicDetail(LocaleNegotiationMixin, generics.RetrieveAPIView):
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer

    def get_object(self):
        queryset = self.get_queryset()
        queryset = queryset.filter(
            slug=self.kwargs.pop("topic"), product__slug=self.kwargs.pop("product")
        )

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
            "subtopics": topics,
            "documents": [],
            "title": _lazy("All Topics"),
            "slug": "",
            "description": _lazy("All Topics"),
            "parent": None,
            "visible": True,
            "product": None,
            "path": "/",
        }


class TopicList(LocaleNegotiationMixin, generics.ListAPIView):
    queryset = Topic.objects.filter(parent=None)
    serializer_class = RootTopicSerializer

    def get_queryset(self):
        queryset = self.queryset.filter(product__slug=self.kwargs["product"])
        visible = bool(self.request.query_params.get("visible", True))
        queryset = queryset.filter(visible=visible)
        return queryset
