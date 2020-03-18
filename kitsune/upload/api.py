from django.conf import settings
from rest_framework import serializers

from kitsune.upload.models import ImageAttachment


class ImageAttachmentSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    delete_url = serializers.SerializerMethodField()
    thumbnail_size = serializers.SerializerMethodField()

    class Meta:
        model = ImageAttachment
        fields = (
            "file",
            "thumbnail",
            "creator",
            "content_type",
            "object_id",
            "url",
            "thumbnail_url",
            "thumbnail_size",
            "delete_url",
        )

    def get_url(self, obj):
        return obj.get_absolute_url()

    def get_thumbnail_url(self, obj):
        return obj.thumbnail_if_set().url

    def get_delete_url(self, obj):
        return obj.get_delete_url()

    def get_thumbnail_size(self, obj):
        return settings.THUMBNAIL_SIZE
