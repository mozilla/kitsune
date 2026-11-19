"""
Compare the labels in translated articles with the official labels. Nothing here
changes an article.

A translation is checked when it was made from its English article's latest
revision that is ready for localization. Any other is out of date, and machine
translation or a translator will redo it anyway.

A translated label is compared with the official label of the English label it
stands for. One that can't be paired with an English label usually has nothing to
be compared with: the English label has no official label, like an operating
system's label that a translator translated.
"""

from collections.abc import Iterator
from typing import NamedTuple

from django.conf import settings
from django.db.models import QuerySet

from kitsune.llm.l10n.ui_labels.labels import find_labels
from kitsune.llm.l10n.ui_labels.official import UNCLEAR, OfficialLabels
from kitsune.llm.l10n.ui_labels.owners import LabelOwner
from kitsune.llm.l10n.ui_labels.owners.lookup import get_owners
from kitsune.llm.l10n.ui_labels.pairing import get_pairs
from kitsune.llm.l10n.ui_labels.text import loosen
from kitsune.wiki.models import Document

MATCHES = "matches the official label"
IN_ENGLISH = "left in English"
DIFFERS = "differs from the official label"
SEVERAL = "unclear: several official labels"
NO_OFFICIAL_LABEL = "no official label: {reason}"
NOT_PAIRED = "not paired with an English label"
OUT_OF_DATE = "translation out of date, not checked"


class Finding(NamedTuple):
    """
    What the check found: for one label of a translation, or for a whole
    translation that is out of date.

    `official` is the official label, or the choices when it's unclear which.
    """

    locale: str
    article: str
    result: str
    label: str = ""
    english: str = ""
    owner: str = ""
    official: str = ""


def get_english_articles() -> QuerySet[Document]:
    """Return the English articles that have labels and can be translated."""
    return Document.objects.filter(
        locale=settings.WIKI_DEFAULT_LANGUAGE,
        is_archived=False,
        is_localizable=True,
        latest_localizable_revision__content__regex=r"\{(menu|button|pref) ",
    ).order_by("id")


def check_article(article: Document, locales: list[str] | None = None) -> list[Finding]:
    """Check an English article's translations, asking the LLM for whatever isn't saved yet."""
    english = article.latest_localizable_revision
    owners = get_owners(english)
    translations = article.translations.filter(current_revision__isnull=False)
    if locales:
        translations = translations.filter(locale__in=locales)
    findings: list[Finding] = []
    for translation in translations.select_related("current_revision"):
        if translation.current_revision.based_on_id == english.id:
            # Pairing reads the English revision through `based_on`. This saves a query
            # for each translation.
            translation.current_revision.based_on = english
            findings += check_translation(translation, owners)
        else:
            findings.append(Finding(translation.locale, article.slug, OUT_OF_DATE))
    return findings


def check_translation(translation: Document, owners: dict[int, LabelOwner]) -> Iterator[Finding]:
    """
    Compare each label of a translated article with the official label of the English
    label it stands for. The owners are those of the English revision it was made from.
    """
    revision = translation.current_revision
    official_labels = OfficialLabels(owners, translation.locale)
    pairs = get_pairs(revision, official_labels)
    for position, use in find_labels(revision.content).items():
        if position not in pairs:
            yield Finding(translation.locale, translation.parent.slug, NOT_PAIRED, use.markup)
            continue
        label_owner = owners[pairs[position]]
        found = official_labels.of(pairs[position], use.text)
        if not found.label:
            no_label = NO_OFFICIAL_LABEL.format(reason=found.outcome)
            result = SEVERAL if found.outcome == UNCLEAR else no_label
        elif loosen(use.text) == loosen(found.label):
            # A label that differs only in case or its last punctuation mark is a match.
            result = MATCHES
        else:
            result = IN_ENGLISH if loosen(use.text) == loosen(label_owner.text) else DIFFERS
        yield Finding(
            translation.locale,
            translation.parent.slug,
            result,
            use.markup,
            label_owner.text,
            label_owner.owner,
            found.label or " | ".join(found.labels),
        )
