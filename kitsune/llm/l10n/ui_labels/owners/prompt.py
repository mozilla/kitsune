"""The prompt for the question we ask an LLM about the owner of each label of an article."""

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from kitsune.llm.l10n.ui_labels.owners import OWNERS, UNKNOWN_REASONS


class LabelAnswer(BaseModel):
    label: int = Field(description="The label's number.")
    owner: str = Field(
        description="One owner from the list, 'unknown', or 'config' for a {pref} that holds "
        "a preference's name or value."
    )
    unknown_reason: str | None = Field(
        default=None, description="os, website, app or unclear. Only when the owner is 'unknown'."
    )
    spot: str | None = Field(
        default=None,
        description="s1, s2, … or 'none'. Only when spots are listed for the owner you chose.",
    )


class LabelAnswers(BaseModel):
    answers: list[LabelAnswer]


owner_parser = PydanticOutputParser(pydantic_object=LabelAnswers)

# Raise this when the question changes enough that the LLM should be asked again:
# the prompt, the list of owners, or the reasons.
QUESTION_VERSION = 1

OWNER_INSTRUCTIONS = """\
You read a support article from support.mozilla.org (SUMO), written in wiki markup. In it, \
the name of a menu, a button, or another thing on a screen is written inside {menu …}, \
{button …} or {pref …}, like {menu Settings} or {button OK}. We call each of these a label. \
Some labels in the article have a number in front, like ⟦3⟧{menu View}. For each numbered \
label, decide which app, website or operating system shows it on its screen at that point \
in the article. We call that app, website or operating system the label's owner.

You get the article's title, its products, the list of numbered labels with hints about \
each, and then the article.

Owners you can choose:
{{ owners }}
- config: not a label, but the name or the value of a preference in about:config. Only a \
{pref} can be this.
- unknown: anything else. Give a reason.

When the owner is "unknown", also give one of these reasons:
{{ reasons }}

Rules:
- Read the whole article. The clue is often a few steps above the label, like "Open Windows \
Settings". Markup like {for win} and {for mac} says which readers see a part.
- The article's products are only a hint. A Firefox article often has steps in Windows or \
macOS, and a Thunderbird article can have steps in Thunderbird for Android.
- "Owners with this text" names the owners that have a string with this text, or with the \
same text apart from capital letters and a last …, : or . mark. It's a hint, not a limit. An \
old article can use a text that no owner has any more.
- Some labels list spots for an owner: s1, s2, …. Each spot is a place in that owner's \
screens where this text appears, shown by a few of its strings: the file, the string's name, \
and the translators' note if there is one. Spots differ because some language translates them \
differently. If you choose an owner that has spots listed, also say which spot this label \
means, or "none" if none fits or you can't tell. If the owner you choose has no spots \
listed, leave the spot empty.
- Answer every numbered label, by its number.

{{ format_instructions }}"""

LABELS_AND_ARTICLE = """\
Title: {{ title }}
Products: {{ products|join(", ") or "none" }}

Labels:
{%- for label in labels %}

⟦{{ label.number }}⟧{{ label.markup }}
  owners with this text: {{ label.found_in|join(", ") or "none" }}
{%- for owner, spots in label.spots.items() %}
  spots if the owner is {{ owner }}:
{%- for name, spot in spots.items() %}
    {{ name }}: {{ spot.examples|join("; ") }}{% if spot.more %} … and {{ spot.more }} more{% endif %}
{%- endfor %}
{%- endfor %}
{%- endfor %}

Article:
{{ article }}"""

owner_prompt = ChatPromptTemplate(
    (("system", OWNER_INSTRUCTIONS), ("human", LABELS_AND_ARTICLE)), template_format="jinja2"
).partial(
    owners="\n".join(f"- {owner.name}: {owner.description}" for owner in OWNERS.values()),
    reasons="\n".join(f"- {name}: {meaning}" for name, meaning in UNKNOWN_REASONS.items()),
    format_instructions=owner_parser.get_format_instructions(),
)
