"""
Put the official labels into a machine translation.

`TranslationLabels` knows which official label each label of an English article
gets in one locale. The translator uses it twice:

- Before the LLM translates, for what to tell it: the official label of each
  label that has one, and the {pref}s that hold config text and must stay as
  they are.
- After, to check the translation. A label the LLM left in English gets its
  official label, and what couldn't be settled is listed for staff.

When a product shows several official labels for a label and nothing says which
one this label means, the one that the article's earlier translation already has is kept.
"""

import re
from collections import defaultdict
from typing import NamedTuple

from kitsune.llm.l10n.ui_labels.labels import find_label_uses, find_labels
from kitsune.llm.l10n.ui_labels.official import KEPT, NO_OWNER, ONLY_ONE, SPOT, OfficialLabels
from kitsune.llm.l10n.ui_labels.owners import CONFIG
from kitsune.llm.l10n.ui_labels.owners.lookup import get_owners
from kitsune.llm.l10n.ui_labels.pairing import get_text_pairs
from kitsune.llm.l10n.ui_labels.text import loosen
from kitsune.wiki.models import Document

# Locales where an ending attached to a label depends on how the label sounds. The 를
# in "{menu Settings}를" would have to become 을 after 설정.
ENDING_LOCALES = {"ko", "tr", "ta", "te"}
ENDING = re.compile(r"['’-]?[^\W\d_]")
# An official label with any of these in it would break the label it is written into.
BREAKS_MARKUP = re.compile(r"[{}\[\]<>\n]")

# Why a label gets its official label, in words for staff.
WHY_CHOSEN = {
    KEPT: "kept from the earlier translation",
    ONLY_ONE: "the only translation",
    SPOT: "one of {count} official labels, chosen by spot {spot}",
}

# What a check can find, in words for staff.
CHECK_FINDINGS = {
    "corrected": "Changed to the official label by the check",
    "endings": "Left as written, because an ending is attached",
    "missing": "Have an official label that the translation doesn't use",
    "config_changed": "Config text that the translation changed",
}


class CheckedTranslation(NamedTuple):
    """
    A translation after its labels were checked, and what the check found.

    `corrected` are the labels that got their official label. `endings` were left
    because an ending is attached. `missing` are English labels with an official
    label that the check finds no label for in the translation, like one written in
    other words. `config_changed` are config {pref}s that the translation no longer
    has as they were.
    """

    content: str
    corrected: list[str]
    endings: list[str]
    missing: list[str]
    config_changed: list[str]


class TranslationLabels:
    """What one machine translation of an English article needs to know about its labels."""

    def __init__(self, article: Document, locale: str):
        english = article.latest_localizable_revision
        translation = article.translated_to(locale)
        owners = get_owners(english)
        all_uses = dict(enumerate(find_label_uses(english.content)))

        self.locale = locale
        self.official_labels = OfficialLabels(owners, locale)
        self.uses = {position: use for position, use in all_uses.items() if position in owners}
        # How many labels got no answer about their owner, and so no official label.
        self.unanswered = len(find_labels(english.content).keys() - owners.keys())
        earlier = translation.current_revision if translation else None
        written = self._written(earlier.content if earlier else "")
        self.found = {
            position: self.official_labels.of(position, written.get(position))
            for position in self.uses
        }
        self.chosen = {
            position: found.label
            for position, found in self.found.items()
            if found.label and not BREAKS_MARKUP.search(found.label)
        }
        self.config_prefs = list(
            dict.fromkeys(
                use.markup
                for position, use in all_uses.items()
                if use.category == "config"
                or (position in owners and owners[position].owner == CONFIG)
            )
        )

    @property
    def for_prompt(self) -> list[tuple[str, str]]:
        """
        Return each label and its official label, both as markup, for the LLM.

        A label whose uses in one article don't all get the same official label, like
        "General" for Firefox and then for Windows, is left out. The check settles
        each use.
        """
        chosen = defaultdict(set)
        for position, use in self.uses.items():
            chosen[use.kind, use.text].add(self.chosen.get(position, ""))
        return [
            (f"{{{kind} {text}}}", f"{{{kind} {official}}}")
            for (kind, text), (official, *others) in chosen.items()
            if official and not others
        ]

    def check(self, translation: str) -> CheckedTranslation:
        """
        Give its official label to each label that the translation has in English,
        or with an official label that belongs to another spot.
        """
        translated = find_labels(translation)
        pairs = get_text_pairs(self.uses, translated, self.official_labels)
        content, corrected, endings = translation, [], []
        # From the last label to the first, so the places of the earlier ones still hold.
        for position, english in sorted(pairs.items(), reverse=True):
            use, official = translated[position], self.chosen.get(english)
            if not official or self.official_labels.of(english, use.text).outcome == KEPT:
                continue
            if self.locale in ENDING_LOCALES and ENDING.match(
                content, content.index("}", use.end) + 1
            ):
                endings.append(use.markup)
                continue
            content = content[: use.start] + official + content[use.end :]
            corrected.append(f"{use.markup} → {{{use.kind} {official}}}")
        paired = set(pairs.values())
        return CheckedTranslation(
            content,
            corrected[::-1],
            endings[::-1],
            [self.uses[position].markup for position in self.chosen if position not in paired],
            [pref for pref in self.config_prefs if pref not in translation],
        )

    def explain(self, checked: CheckedTranslation) -> str:
        """
        Say where each official label came from and what the check did, for the
        explanation that staff can read.
        """
        total = len(self.uses) + self.unanswered
        lines = [f"UI labels: {len(self.chosen)} of {total} have an official label."]
        if self.unanswered:
            lines.append(f"{self.unanswered} got no answer about their owner and were left alone.")
        lines += dict.fromkeys(self._reason(position) for position in self.uses)
        for name, meaning in CHECK_FINDINGS.items():
            if labels := getattr(checked, name):
                lines.append(f"{meaning}: {', '.join(dict.fromkeys(labels))}.")
        return "\n".join(lines)

    def _reason(self, position: int) -> str:
        """Say in a line which official label a label gets and why, or why it gets none."""
        label_owner, found = self.official_labels.owners[position], self.found[position]
        markup = self.uses[position].markup
        owner = label_owner.owner + (
            f": {label_owner.unknown_reason}" if label_owner.unknown_reason else ""
        )
        if position in self.chosen:
            why = WHY_CHOSEN[found.outcome].format(
                count=len(found.labels), spot=(label_owner.spot or [""])[0]
            )
            return f"{markup} → {found.label} ({owner}, {why})"
        if found.outcome == NO_OWNER:
            return f"{markup} has no official label ({owner})"
        if found.label:
            return f"{markup} has an official label we can't write, {found.label!r} ({owner})"
        choices = f": {' | '.join(found.labels)}" if found.labels else ""
        return f"{markup} has no official label ({owner}, {found.outcome}{choices})"

    def _written(self, earlier: str) -> dict[int, str]:
        """
        Return what the earlier translation has for each English label that pairs by text.

        An official label that two different English labels share, like "Erweiterungen" for
        "Add-ons" and "Extensions" in German, is left out. We can't tell whose it is.
        """
        shared_by = defaultdict(set)
        for position, use in self.uses.items():
            for official in self.official_labels.of(position).labels:
                shared_by[loosen(official)].add(loosen(use.text))
        translated = find_labels(earlier)
        return {
            english: translated[position].text
            for position, english in get_text_pairs(
                self.uses, translated, self.official_labels
            ).items()
            if len(shared_by[loosen(translated[position].text)]) < 2
        }
