"""Find the labels in an article's wiki markup."""

import re
from typing import NamedTuple

LABEL = re.compile(r"\{(?P<kind>menu|button|pref) (?P<text>.*?)\}")
COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
# A pref name like "browser.tabs.warnOnClose", a prefix of one like "devtools.", "true" or
# "false", or a number.
CONFIG_TEXT = re.compile(
    r"[\w\-@*\[\]{}&#;]+(?:\.[\w\-@*\[\]{}&#;']+)+\.?"
    r"|[a-z][\w-]*\.|(?i:true|false)|-?\d+"
)
MARKUP = re.compile(r"\[\[|\{|<|''")
LETTER = re.compile(r"[^\W\d_]")
PATH = re.compile(r"\s(?:>|→|->|\|)\s")
KEYS = {"ctrl", "shift", "alt", "command", "cmd", "option", "enter", "return", "tab", "esc", "fn"}
BOLD = "'''"
HIDDEN = chr(0)


class LabelUse(NamedTuple):
    """
    One {menu}, {button} or {pref} in an article.

    `start` and `end` are where its text sits in the article, so a rewrite can
    change the text and nothing else.
    """

    kind: str
    text: str
    start: int
    end: int

    @property
    def markup(self) -> str:
        """Return the use as an article has it, like {menu View}."""
        return f"{{{self.kind} {self.text}}}"

    @property
    def category(self) -> str:
        """
        Say what the text is: a "label", or something a product never translates.

        A {pref} holds a label or config text. The test here only catches what is
        plainly config. The LLM that reads the whole article for owners settles the rest.
        """
        if self.kind == "pref" and CONFIG_TEXT.fullmatch(self.text.replace(BOLD, "").strip()):
            return "config"
        if MARKUP.search(self.text):
            return "markup"
        if not LETTER.search(self.text):
            return "icon"
        if (len(self.text) == 1 and self.text.isascii()) or self.text.casefold() in KEYS:
            return "key"
        if PATH.search(self.text):
            return "path"
        return "label"


def find_label_uses(content: str) -> list[LabelUse]:
    """
    Find the label uses a reader can see, in the order they appear.

    Readers never see what's inside an HTML comment, so a label in one doesn't count.
    """
    # Blank the comments out but keep every position, so a use's place is its place
    # in the article.
    shown = COMMENT.sub(lambda match: re.sub(r"[^\n]", HIDDEN, match.group()), content)
    uses = []
    for match in LABEL.finditer(shown):
        start, end = match.span("text")
        text = content[start:end]
        start += len(text) - len(text.lstrip())
        text = text.strip()
        uses.append(LabelUse(match.group("kind"), text, start, start + len(text)))
    return uses


def find_labels(content: str) -> dict[int, LabelUse]:
    """Return the uses that are labels, each by its position among all the uses."""
    return {
        position: use
        for position, use in enumerate(find_label_uses(content))
        if use.category == "label"
    }


def number_labels(content: str, uses: dict[int, LabelUse], prefix: str = "") -> str:
    """
    Return an article for an LLM to read: without its comments, and with a number in
    front of each of the given labels, like ⟦3⟧{menu View}.
    """
    for number, use in sorted(uses.items(), key=lambda item: item[1].start, reverse=True):
        brace = content.rindex("{", 0, use.start)
        content = f"{content[:brace]}⟦{prefix}{number}⟧{content[brace:]}"
    return COMMENT.sub("", content)
