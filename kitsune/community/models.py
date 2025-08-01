from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import models
from pydantic import BaseModel, Field

from kitsune.products.models import Product
from kitsune.sumo.models import LocaleField


class AnswerMetadata(BaseModel):
    content: str = Field(min_length=1, description="The answer content")
    question_title: str = Field(min_length=1, description="Title of its question")
    is_solution: bool = Field(description="Whether the answer was the solution")


class RevisionMetadata(BaseModel):
    is_approved: bool = Field(description="Whether the revision was approved")
    document_title: str = Field(min_length=1, description="Title of its document")


class DocumentMetadata(BaseModel):
    title: str = Field(min_length=1, description="The document title")


class DeletedContribution(models.Model):
    created = models.DateTimeField(auto_now_add=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
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

    def validate_metadata(self):
        """Validate metadata using Pydantic models."""

        from kitsune.questions.models import Answer
        from kitsune.wiki.models import Document, Revision

        if self.content_type == ContentType.objects.get_for_model(Answer):
            AnswerMetadata(**self.metadata)
        elif self.content_type == ContentType.objects.get_for_model(Revision):
            RevisionMetadata(**self.metadata)
        elif self.content_type == ContentType.objects.get_for_model(Document):
            DocumentMetadata(**self.metadata)

    def save(self, *args, **kwargs):
        self.validate_metadata()
        super().save(*args, **kwargs)
