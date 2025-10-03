from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers, status

from kitsune.products.models import Product, Topic
from kitsune.sumo.api_utils import GenericAPIException, LocaleNegotiationMixin
from kitsune.sumo.i18n import normalize_language
from kitsune.wiki.config import REDIRECT_HTML
from kitsune.wiki.models import Document


class DocumentShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ("id", "title", "slug")


class DocumentDetailSerializer(DocumentShortSerializer):
    summary = serializers.CharField(read_only=True)
    url = serializers.CharField(source="get_absolute_url", read_only=True)
    products = serializers.SlugRelatedField(
        many=True, slug_field="slug", queryset=Product.active.all()
    )
    topics = serializers.SlugRelatedField(
        many=True, slug_field="slug", queryset=Topic.active.all()
    )

    class Meta:
        model = Document
        fields = ("id", "title", "slug", "url", "locale", "products", "topics", "summary", "html")


class DocumentList(LocaleNegotiationMixin, generics.ListAPIView):
    """List all documents."""

    serializer_class = DocumentShortSerializer

    def get_queryset(self):
        locales = self.request.query_params.get("locales")
        if locales:
            # Multiple locales are separated by commas.
            locales = locales.replace(",", " ").split()
        elif locale := normalize_language(self.get_locale()):
            locales = [locale]

        categories = self.request.query_params.get("categories")
        if categories:
            # Multiple categories are separated by commas.
            categories = categories.replace(",", " ").split()
        else:
            categories = settings.IA_DEFAULT_CATEGORIES

        product = self.request.query_params.get("product")
        topic = self.request.query_params.get("topic")
        is_template = bool(self.request.query_params.get("is_template", False))
        is_archived = bool(self.request.query_params.get("is_archived", False))
        is_redirect = bool(self.request.query_params.get("is_redirect", False))
        title_query = self.request.query_params.get("q")

        queryset = Document.objects.visible(self.request.user, category__in=categories)

        if locales:
            queryset = queryset.filter(locale__in=locales)

        if product is not None:
            if locale == settings.WIKI_DEFAULT_LANGUAGE:
                queryset = queryset.filter(products__slug=product)
            else:
                # Localized articles inherit product from the parent.
                queryset = queryset.filter(parent__products__slug=product)

            if topic is not None:
                if locale == settings.WIKI_DEFAULT_LANGUAGE:
                    queryset = queryset.filter(topics__slug=topic)
                else:
                    # Localized articles inherit topic from the parent.
                    queryset = queryset.filter(parent__topics__slug=topic)
        elif topic is not None:
            raise GenericAPIException(status.HTTP_400_BAD_REQUEST, "topic requires product")

        queryset = queryset.filter(is_template=is_template)
        queryset = queryset.filter(is_archived=is_archived)

        redirect_filter = Q(html__startswith=REDIRECT_HTML)
        if is_redirect:
            queryset = queryset.filter(redirect_filter)
        else:
            queryset = queryset.filter(~redirect_filter)

        if title_query:
            queryset = queryset.filter(title__icontains=title_query)

        return queryset


class DocumentDetail(LocaleNegotiationMixin, generics.RetrieveAPIView):
    serializer_class = DocumentDetailSerializer

    def get_object(self):
        locale = normalize_language(self.get_locale())
        queryset = Document.objects.visible(self.request.user, locale=locale)
        obj = get_object_or_404(queryset, **self.kwargs)
        self.check_object_permissions(self.request, obj)
        return obj
