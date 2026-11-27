"""What the UI labels feature saves: the products' strings, and what an LLM said about labels."""

from django.db import models

from kitsune.sumo.models import ModelBase


class UIStringSource(ModelBase):
    """A repository of product UI strings, and how its last sync went."""

    name = models.CharField(max_length=64, unique=True)
    commit = models.CharField(max_length=40, blank=True)
    fingerprint = models.CharField(
        max_length=64,
        blank=True,
        help_text="Changes when the strings must be read again: a new commit, a new "
        "version of our parsers, or a change in the locales an owner ships.",
    )
    synced_at = models.DateTimeField(
        null=True, blank=True, help_text="When the last sync that succeeded finished."
    )
    error = models.TextField(
        blank=True,
        help_text="Why the last sync failed, or where it found no strings but expected some.",
    )

    class Meta:
        verbose_name = "UI string source"
        verbose_name_plural = "UI string sources"

    def __str__(self):
        return self.name


class UIStringCatalog(ModelBase):
    """
    The UI strings one owner shows in one locale, as its users see them.

    A row exists only for English and for the locales the owner ships. An owner
    whose strings come from several sources has one row per source.
    """

    owner = models.CharField(max_length=32)
    source = models.ForeignKey(UIStringSource, on_delete=models.CASCADE, related_name="+")
    locale = models.CharField(
        max_length=16,
        help_text="A SUMO locale, or the owner's own code for an extra variant like es-MX.",
    )
    strings = models.JSONField(default=dict, help_text="Map of string ID to text.")
    comments = models.JSONField(
        default=dict, help_text="Map of string ID to its source comment. English only."
    )
    terms = models.TextField(
        blank=True,
        help_text="The Fluent terms these files define, like brand names, for reading "
        "the owner's strings in other sources.",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "locale", "source"], name="unique_ui_string_catalog"
            )
        ]

    def __str__(self):
        return f"{self.owner} [{self.locale}]"


class UISpotList(ModelBase):
    """
    An owner's English texts, each with the strings that have it and their spots.

    Strings with the same text that are translated the same way in every locale
    the owner ships share a spot: choosing any of them gives the same label. The
    list is rebuilt after each sync of the owner's strings.
    """

    owner = models.CharField(max_length=32, unique=True)
    strings_by_text = models.JSONField(
        default=dict,
        help_text="Map of an English text, without its case and trailing punctuation, "
        "to its strings: each with its ID, its exact text, and the number of its spot.",
    )
    built_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.owner


class UILabelOwners(ModelBase):
    """
    What an LLM said about the labels of an English revision: the owner of each,
    and its spot.

    The LLM reads the whole article to answer, because a change anywhere can
    change what a label means, so each revision has its own answers.
    """

    revision = models.OneToOneField(
        "wiki.Revision", on_delete=models.CASCADE, primary_key=True, related_name="+"
    )
    owners = models.JSONField(
        help_text="Map of a label's position to its kind, its text, its owner, the reason "
        'when the owner is "unknown", and its spot.'
    )
    answer_version = models.CharField(
        max_length=64,
        help_text="Which version of the question, and which model, gave these answers.",
    )

    class Meta:
        verbose_name = verbose_name_plural = "UI label owners"

    def __str__(self):
        return f"Label owners of revision {self.revision_id}"


class UILabelPairs(ModelBase):
    """
    What an LLM said about the labels of a translation: which label each one
    stands for in the English revision the translation was made from.
    """

    revision = models.OneToOneField(
        "wiki.Revision", on_delete=models.CASCADE, primary_key=True, related_name="+"
    )
    pairs = models.JSONField(
        help_text="Map of a translated label's position to its English label's position."
    )
    explanation = models.TextField(
        blank=True, help_text="What the LLM said about its pairs, for looking into a wrong one."
    )
    answer_version = models.CharField(
        max_length=64,
        help_text="Which version of the question, and which model, gave this answer.",
    )

    class Meta:
        verbose_name = verbose_name_plural = "UI label pairs"

    def __str__(self):
        return f"Label pairs of revision {self.revision_id}"
