from django.db import models

from taggit.managers import TaggableManager

from kitsune.tags.forms import TagField


class BigVocabTaggableManager(TaggableManager):
    """TaggableManager for choosing among a predetermined set of tags

    Taggit's seems hard-coupled to taggit's own plain-text-input widget.

    """
    def formfield(self, form_class=TagField, **kwargs):
        """Swap in our custom TagField."""
        return super(BigVocabTaggableManager, self).formfield(form_class,
                                                              **kwargs)


# taggit adds a "tags" property which isn't a field, but South can't
# tell the difference. So we tell south to ignore everything in this
# module.
#
# Note: If we end up adding models to this module, then we'll need to
# rethink this.
from south.modelsinspector import add_ignored_fields
add_ignored_fields(["^kitsune\.tags\.models"])


class BigVocabTaggableMixin(models.Model):
    """Mixin for taggable models that still allows a caching manager to be the
    default manager

    Mix this in after [your caching] ModelBase.

    """
    tags = BigVocabTaggableManager()

    class Meta:
        abstract = True
