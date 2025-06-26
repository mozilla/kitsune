from django.db import models
from taggit.managers import TaggableManager
from taggit.models import GenericTaggedItemBase, TagBase


class SumoTagManager(models.Manager):

    def segmentation_tags(self):
        return self.filter(is_archived=False, slug__startswith="seg-")

    def non_segmentation_tags(self):
        return self.exclude(slug__startswith="seg-").filter(is_archived=False)

    def active(self):
        return self.filter(is_archived=False)


class BigVocabTaggableManager(TaggableManager):
    """TaggableManager for choosing among a predetermined set of tags

    Taggit's seems hard-coupled to taggit's own plain-text-input widget.

    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("through", SumoTaggedItem)
        super().__init__(*args, **kwargs)


class SumoTag(TagBase):
    is_archived = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = SumoTagManager()

    class Meta:
        ordering = ["name", "-updated"]


class SumoTaggedItem(GenericTaggedItemBase):
    tag = models.ForeignKey(SumoTag, related_name="tagged_items", on_delete=models.CASCADE)
