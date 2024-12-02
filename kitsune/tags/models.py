from django.db import models
from taggit.managers import TaggableManager
from taggit.models import GenericTaggedItemBase, TagBase


class SumoTagManager(models.Manager):

    def segmentation_tags(self):
        return self.filter(is_archived=False, slug__startswith="seg-")

    def active(self):
        return self.filter(is_archived=False)


class BigVocabTaggableManager(TaggableManager):
    """TaggableManager for choosing among a predetermined set of tags

    Taggit's seems hard-coupled to taggit's own plain-text-input widget.

    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("through", SumoTaggedItem)
        super().__init__(*args, **kwargs)

    def formfield(self, form_class=None, **kwargs):
        """Swap in our custom TagField."""
        from kitsune.tags.forms import TagField

        form_class = form_class or TagField
        return super().formfield(form_class, **kwargs)


class SumoTag(TagBase):
    is_archived = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = SumoTagManager()

    class Meta:
        ordering = ["name", "-updated"]


class SumoTaggedItem(GenericTaggedItemBase):
    tag = models.ForeignKey(SumoTag, related_name="tagged_items", on_delete=models.CASCADE)
