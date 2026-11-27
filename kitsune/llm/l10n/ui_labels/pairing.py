"""
Work out which English label each label of a translation stands for.

A translated label gets its owner and its spot from the English label it stands
for. Most pair up by their text: the translated label is still the English text,
or it's one of the English label's official labels. When that leaves a translated
label over, and an English label that has an official label, an LLM reads both
articles and pairs them.
"""

import logging
import re
from collections import defaultdict

from django.conf import settings
from langchain_core.exceptions import OutputParserException
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate

from kitsune.llm.l10n.config import L10N_LLM_MODEL
from kitsune.llm.l10n.ui_labels.labels import (
    LabelUse,
    find_label_uses,
    find_labels,
    number_labels,
)
from kitsune.llm.l10n.ui_labels.official import OfficialLabels
from kitsune.llm.l10n.ui_labels.text import loosen
from kitsune.llm.models import UILabelPairs
from kitsune.llm.utils import build_chain_with_retry, get_llm
from kitsune.wiki.models import Revision

log = logging.getLogger("k.llm")

# Raise this when the question changes enough that the LLM should be asked again.
QUESTION_VERSION = 1
ANSWER_VERSION = f"{QUESTION_VERSION}:{L10N_LLM_MODEL}"

PAIR = re.compile(r"T(\d+)\s*>>>>\s*E(\d+)", re.IGNORECASE)
# The line that ends the pairs in a reply. What follows is the LLM's explanation.
EXPLANATION_DELIMITER = "----"

PAIRING_INSTRUCTIONS = """\
You get a support article from support.mozilla.org (SUMO) in English, and its translation \
into {{ language }}. Both are in wiki markup. In both, the name of a menu, a button, or \
another thing on a screen is written inside {menu …}, {button …} or {pref …}, like \
{menu Settings} or {button OK}. We call each of these a label. Some labels have a number in \
front: ⟦E3⟧ in the English article, ⟦T3⟧ in the translation. The numbers on the two sides \
have nothing to do with each other.

For each numbered label in the translation, say which numbered English label it stands for: \
the same thing on screen, at the same point in the instructions.

Rules:
- Pair labels even when the translator used other words, an older name, or left the label \
in English. Pair them too when the translator moved the label within its sentence, split or \
merged steps, or wrote {for} conditions differently.
- Answer "none" for a label with nothing to match in English, like a step the translator \
added.
- Don't judge the translation, and don't decide how a label should be translated. Only pair.

Answer with one line for each numbered label in the translation, like this:
T1>>>>E4
T2>>>>none

Then write a line with only ---- and, after it, a short explanation of the pairs that \
weren't plain from the text, and of each "none"."""

ARTICLE_AND_TRANSLATION = """\
English article:
{{ english }}

Translation into {{ language }}:
{{ translation }}"""

pairing_prompt = ChatPromptTemplate(
    (("system", PAIRING_INSTRUCTIONS), ("human", ARTICLE_AND_TRANSLATION)),
    template_format="jinja2",
)


def pairing_parser(message: AIMessage) -> tuple[dict[int, int], str]:
    """
    Read the pairs in the LLM's reply, and the explanation after them.

    A label the LLM pairs with none has no line we keep.
    """
    lines, _, explanation = message.text.partition(EXPLANATION_DELIMITER)
    if ">>>>" not in lines:
        raise OutputParserException("The reply has no pairs.")
    pairs = {int(translated): int(english) for translated, english in PAIR.findall(lines)}
    return pairs, explanation.strip()


def get_pairs(translation: Revision, official_labels: OfficialLabels) -> dict[int, int]:
    """
    Return the position of the English label that each translated label stands for,
    by the translated label's position. A label that stands for none is left out.

    `official_labels` are those, in the translation's locale, for the labels
    of the English revision the translation was made from.
    """
    english_uses = {
        position: use
        for position, use in enumerate(find_label_uses(translation.based_on.content))
        if position in official_labels.owners
    }
    translated_uses = find_labels(translation.content)
    pairs = get_text_pairs(english_uses, translated_uses, official_labels)
    paired = set(pairs.values())
    if len(pairs) < len(translated_uses) and any(
        position not in paired and official_labels.of(position).labels for position in english_uses
    ):
        llm_pairs = _get_llm_pairs(translation, english_uses, translated_uses)
        # The LLM read both articles, so its pairs win. A pair by text stays only
        # where the LLM gave none and didn't use that English label.
        pairs = {
            position: english_position
            for position, english_position in pairs.items()
            if position not in llm_pairs and english_position not in llm_pairs.values()
        } | llm_pairs
    return pairs


def get_text_pairs(
    english_uses: dict[int, LabelUse],
    translated_uses: dict[int, LabelUse],
    official_labels: OfficialLabels,
) -> dict[int, int]:
    """Pair labels by text, in the order they appear when several share a text."""
    waiting = defaultdict(list)
    for position, use in english_uses.items():
        official = (
            *official_labels.of(position).labels,
            *official_labels.variant_labels(position),
        )
        for text in {loosen(text) for text in (use.text, *official)}:
            waiting[text].append(position)
    pairs: dict[int, int] = {}
    paired: set[int] = set()
    for position, use in translated_uses.items():
        for english_position in waiting.get(loosen(use.text), ()):
            if english_position not in paired:
                pairs[position] = english_position
                paired.add(english_position)
                break
    return pairs


def _get_llm_pairs(
    translation: Revision, english_uses: dict[int, LabelUse], translated_uses: dict[int, LabelUse]
) -> dict[int, int]:
    """Return the LLM's pairs for a translation, asking only if they aren't saved yet."""
    record = UILabelPairs.objects.filter(
        revision=translation, answer_version=ANSWER_VERSION
    ).first()
    if record:
        said = {
            int(position): english_position for position, english_position in record.pairs.items()
        }
    else:
        chain = build_chain_with_retry(
            pairing_prompt,
            get_llm(model_name=L10N_LLM_MODEL, temperature=0.0),
            pairing_parser,
        )
        reply = chain.invoke(
            {
                "language": settings.LOCALES[translation.document.locale].english,
                "english": number_labels(translation.based_on.content, english_uses, "E"),
                "translation": number_labels(translation.content, translated_uses, "T"),
            }
        )
        if reply is None:
            log.warning(f"The LLM gave no pairs we could read for revision {translation.id}.")
            return {}
        said, explanation = reply
        UILabelPairs.objects.update_or_create(
            revision=translation,
            defaults={"pairs": said, "explanation": explanation, "answer_version": ANSWER_VERSION},
        )
    return {
        position: english_position
        for position, english_position in said.items()
        if position in translated_uses and english_position in english_uses
    }
