from django.db.models import Q

from rest_framework import generics, serializers

from kitsune.gallery.models import Image
from kitsune.sumo.api import (
    LocaleNegotiationMixin, InequalityFilterBackend, DateTimeUTCField, ImageUrlField)


class ImageShortSerializer(serializers.ModelSerializer):
    url = ImageUrlField(source='file')

    class Meta(object):
        model = Image
        fields = ('id', 'title', 'url', 'locale', 'width', 'height')


class ImageDetailSerializer(ImageShortSerializer):
    created = DateTimeUTCField(read_only=True)
    updated = DateTimeUTCField(read_only=True)
    updated_by = serializers.SlugRelatedField(slug_field='username')

    class Meta(ImageShortSerializer.Meta):
        fields = ImageShortSerializer.Meta.fields + (
            'created', 'updated', 'updated_by', 'description', 'is_draft',
            'creator')


class ImageList(LocaleNegotiationMixin, generics.ListAPIView):
    """List all image ids."""
    queryset = Image.objects.all()
    serializer_class = ImageShortSerializer
    paginate_by = 100
    filter_fields = ['height', 'width']
    filter_backends = [InequalityFilterBackend]

    def get_queryset(self):
        not_is_draft = Q(is_draft=None) | Q(is_draft=False)
        queryset = self.queryset.filter(not_is_draft)

        # locale may come from the Accept-language header, but it can be
        # overridden via the query string.
        locale = self.get_locale()
        locale = self.request.QUERY_PARAMS.get('locale', locale)
        if locale is not None:
            queryset = queryset.filter(locale=locale)

        return queryset


class ImageDetail(generics.RetrieveAPIView):
    queryset = Image.objects.all()
    serializer_class = ImageDetailSerializer
