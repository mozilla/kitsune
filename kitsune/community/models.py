from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import models

from kitsune.products.models import Product
from kitsune.sumo.models import LocaleField


class DeletedContribution(models.Model):
    created = models.DateTimeField(auto_now_add=True)

    # Contribution-related fields
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    # Use "metadata" to store any additional information needed for specific content types.
    metadata = models.JSONField(null=True, default=None)
    contributor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="deleted_contributions"
    )
    contribution_timestamp = models.DateTimeField()
    locale = LocaleField()
    products = models.ManyToManyField(Product)

    class Meta:
        indexes = [
            models.Index(fields=["locale"]),
            models.Index(fields=["contribution_timestamp"]),
        ]
