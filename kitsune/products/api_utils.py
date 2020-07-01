from django.core.exceptions import ValidationError
from rest_framework import serializers


class TopicField(serializers.SlugRelatedField):
    def __init__(self, slug_field="slug", product_field="product", **kwargs):
        super(TopicField, self).__init__(slug_field=slug_field, **kwargs)
        self.product_field = product_field
        self.error_messages["missing_product"] = "A product must be specified to select a topic."

    def to_internal_value(self, topic_slug):
        product_slug = self.parent.initial_data.get("product")
        if product_slug is None:
            raise ValidationError(self.error_messages["missing_product"])

        return self.queryset.get(**{self.slug_field: topic_slug, "product__slug": product_slug})
