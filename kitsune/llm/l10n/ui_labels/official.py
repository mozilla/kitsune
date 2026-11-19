"""
Find the official label for a label in a locale: the translation its owner shows.

An owner can have several translations for a label's text. These rules settle
which one is the official label, in this order:

- The translated article already has one of them, and the label's spot doesn't
  name another one: keep it.
- Only one translation: use it.
- The label's spot, which an LLM chose from the article: use its translation.
- Still unclear: leave the label, and say what the choices are.

A Spanish article may have the official label of another variant of Spanish for
the same string. That is kept too.
"""

from typing import NamedTuple

from kitsune.llm.l10n.ui_labels.owners import OWNERS, LabelOwner
from kitsune.llm.l10n.ui_labels.strings.catalogs import get_owners_shipping, get_translations
from kitsune.llm.l10n.ui_labels.strings.locales import SPANISH_VARIANTS
from kitsune.llm.l10n.ui_labels.strings.spots import get_strings_with_text
from kitsune.llm.l10n.ui_labels.text import normalize
from kitsune.llm.models import UISpotList

# Why a label has no official label.
NO_OWNER = "no owner"  # It belongs to something we don't know, or it isn't a label.
NOT_LOADED = "strings not loaded"  # We know the owner, but don't have its strings yet.
NO_STRING = "no string"  # The owner has no string with this text.
NOT_SHIPPED = "not shipped"  # The owner doesn't ship this locale.
NOT_TRANSLATED = "not translated"  # The owner ships the locale, and shows English here.

# Which rule settled it.
KEPT = "kept"
ONLY_ONE = "only one"
SPOT = "spot"
UNCLEAR = "unclear"


class OfficialLabel(NamedTuple):
    """
    What we found for one label in one locale.

    `outcome` is a rule, or the reason there is no official label. `label` is the
    official label to write, when a rule settled one. `labels` are all the
    official labels for the label's text.
    """

    outcome: str
    label: str = ""
    labels: tuple[str, ...] = ()


class OfficialLabels:
    """The official labels for the labels of one English revision, in one locale."""

    def __init__(self, owners: dict[int, LabelOwner], locale: str):
        self.owners = owners
        self.found = get_strings_with_text(
            label_owner.text for label_owner in owners.values() if label_owner.owner in OWNERS
        )
        self.loaded = set(UISpotList.objects.values_list("owner", flat=True))
        self.shipping = get_owners_shipping(locale)
        wanted: dict[str, set[str]] = {}
        for label_owner in owners.values():
            if label_owner.owner in self.shipping and (strings := self._strings(label_owner)):
                wanted.setdefault(label_owner.owner, set()).update(s["id"] for s in strings)
        self.translated = {
            owner: get_translations(owner, locale, ids) for owner, ids in wanted.items()
        }
        # Spanish translators also use the labels of Spanish as other countries speak it.
        self.variants = {
            owner: [get_translations(owner, variant, ids) for variant in SPANISH_VARIANTS]
            for owner, ids in wanted.items()
            if locale == "es"
        }

    def of(self, position: int, written: str | None = None) -> OfficialLabel:
        """
        Find the official label for the label at a position.

        `written` is what the translated article has there now, if anything.
        """
        label_owner = self.owners[position]
        if label_owner.owner not in OWNERS:
            return OfficialLabel(NO_OWNER)
        if label_owner.owner not in self.loaded:
            return OfficialLabel(NOT_LOADED)
        if not (strings := self._strings(label_owner)):
            return OfficialLabel(NO_STRING)
        if label_owner.owner not in self.shipping:
            return OfficialLabel(NOT_SHIPPED)

        translated = self.translated[label_owner.owner]
        labels = _distinct(translated[s["id"]] for s in strings if s["id"] in translated)
        spot_labels = _distinct(translated[i] for i in label_owner.spot or () if i in translated)
        if not labels or (label_owner.spot and not spot_labels):
            return OfficialLabel(NOT_TRANSLATED, labels=labels)
        # The spot wins when the article has another of the locale's official labels.
        # A label of another variant of Spanish isn't one the spot could have named,
        # so it doesn't disagree with the spot.
        spot_says_another = (
            len(spot_labels) == 1
            and written is not None
            and normalize(written) != normalize(spot_labels[0])
            and normalize(written) in map(normalize, labels)
        )
        if (
            written is not None
            and not spot_says_another
            and normalize(written) in map(normalize, (*labels, *self.variant_labels(position)))
        ):
            return OfficialLabel(KEPT, written, labels)
        if len(labels) == 1:
            return OfficialLabel(ONLY_ONE, labels[0], labels)
        if len(spot_labels) == 1:
            return OfficialLabel(SPOT, spot_labels[0], labels)
        return OfficialLabel(UNCLEAR, labels=labels)

    def variant_labels(self, position: int) -> tuple[str, ...]:
        """
        Return the official labels that the other variants of Spanish have for the
        label at a position. A Spanish article may have one of them.
        """
        label_owner = self.owners[position]
        return _distinct(
            variant[string["id"]]
            for variant in self.variants.get(label_owner.owner, ())
            for string in self._strings(label_owner)
            if string["id"] in variant
        )

    def _strings(self, label_owner: LabelOwner) -> list[dict]:
        return self.found.get(label_owner.owner, {}).get(label_owner.text, [])


def _distinct(texts) -> tuple[str, ...]:
    """Return the texts that differ after the usual clean-up, in the order they came."""
    seen: dict[str, str] = {}
    for text in texts:
        seen.setdefault(normalize(text), text)
    return tuple(seen.values())
