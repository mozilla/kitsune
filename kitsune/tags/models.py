from taggit.managers import TaggableManager

from kitsune.tags.forms import TagField


class BigVocabTaggableManager(TaggableManager):
    """TaggableManager for choosing among a predetermined set of tags

    Taggit's seems hard-coupled to taggit's own plain-text-input widget.

    """

    def formfield(self, form_class=TagField, **kwargs):
        """Swap in our custom TagField."""
        return super(BigVocabTaggableManager, self).formfield(form_class, **kwargs)
