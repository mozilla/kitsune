from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework import generics, serializers, status

from kitsune.sumo.api import GenericAPIException, LocaleNegotiationMixin
from kitsune.wiki.models import Document
from kitsune.wiki.config import REDIRECT_HTML


class DocumentShortSerializer(serializers.ModelSerializer):
    products = serializers.SlugRelatedField(many=True, slug_field='slug')
    topics = serializers.SlugRelatedField(many=True, slug_field='slug')

    class Meta:
        model = Document
        fields = ('title', 'slug')


class DocumentDetailSerializer(DocumentShortSerializer):
    summary = serializers.CharField(source='summary', read_only=True)
    url = serializers.CharField(source='get_absolute_url', read_only=True)

    class Meta:
        model = Document
        fields = ('id', 'title', 'slug', 'url', 'locale', 'products', 'topics',
                  'summary', 'html')


class DocumentList(LocaleNegotiationMixin, generics.ListAPIView):
    """List all documents."""
    queryset = Document.objects.all()
    serializer_class = DocumentShortSerializer
    paginate_by = 100

    def get_queryset(self):
        queryset = self.queryset

        queryset = queryset.filter(category__in=settings.IA_DEFAULT_CATEGORIES,
                                   current_revision__isnull=False)

        locale = self.get_locale()
        product = self.request.QUERY_PARAMS.get('product')
        topic = self.request.QUERY_PARAMS.get('topic')
        is_template = bool(self.request.QUERY_PARAMS.get('is_template', False))
        is_archived = bool(self.request.QUERY_PARAMS.get('is_archived', False))
        is_redirect = bool(self.request.QUERY_PARAMS.get('is_redirect', False))

        if locale is not None:
            queryset = queryset.filter(locale=locale)

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
            raise GenericAPIException(status.HTTP_400_BAD_REQUEST,
                                      'topic requires product')

        queryset = queryset.filter(is_template=is_template)
        queryset = queryset.filter(is_archived=is_archived)

        redirect_filter = Q(html__startswith=REDIRECT_HTML)
        if is_redirect:
            queryset = queryset.filter(redirect_filter)
        else:
            queryset = queryset.filter(~redirect_filter)

        return queryset


class DocumentDetail(LocaleNegotiationMixin, generics.RetrieveAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentDetailSerializer

    def get_object(self):
        queryset = self.get_queryset()
        queryset = queryset.filter(locale=self.get_locale())

        obj = get_object_or_404(queryset, **self.kwargs)
        self.check_object_permissions(self.request, obj)
        return obj
