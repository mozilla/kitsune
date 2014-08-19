from django.db.models import Q

from rest_framework import generics, serializers

from kitsune.gallery.models import Image
from kitsune.sumo.api import CORSMixin, LocaleNegotiationMixin


class ImageShortSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField('get_url')

    class Meta(object):
        model = Image
        fields = ('id', 'title', 'url', 'locale')

    def get_url(self, obj):
        return obj.get_absolute_url()


class ImageDetailSerializer(ImageShortSerializer):
    updated_by = serializers.SlugRelatedField(slug_field='username')

    class Meta(ImageShortSerializer.Meta):
        fields = ImageShortSerializer.Meta.fields + (
            'created', 'updated', 'updated_by', 'description', 'is_draft',
            'creator')


class ImageList(CORSMixin, LocaleNegotiationMixin, generics.ListAPIView):
    """List all image ids."""
    queryset = Image.objects.all()
    serializer_class = ImageShortSerializer
    paginate_by = 100

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


class ImageDetail(CORSMixin, generics.RetrieveAPIView):
    queryset = Image.objects.all()
    serializer_class = ImageDetailSerializer
