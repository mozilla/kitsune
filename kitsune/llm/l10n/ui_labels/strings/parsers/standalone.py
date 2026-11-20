"""
Read the formats whose files stand alone: .properties, .dtd, Android XML, XLIFF
and gettext.

Unlike Fluent, a string in these never points into another file, so each file is
read by itself.
"""

import io
import re
from collections.abc import Iterator
from pathlib import PurePosixPath

from babel.messages.pofile import read_po
from lxml import etree

from kitsune.llm.l10n.ui_labels.strings.parsers.ui_string import ACCESS_KEY, UIString

PLACEHOLDER = re.compile(r"%%|%(?:\d+\$)?[-#0+]*[\d.]*[a-zA-Z@]|%\d+")
APP_NAME_PLACEHOLDER = re.compile(r"%(?:\d+\$)?[sS@]|%\d+")
PROPERTY = re.compile(r"([^=:\s]+)\s*[=:]\s*(.*)")
DTD_COMMENT = re.compile(r"<!--.*?(?:-->|\Z)", re.DOTALL)
DTD_ENTITY = re.compile(r"""<!ENTITY\s+(\S+)\s+(?:"([^"]*)"|'([^']*)')\s*>""")
DTD_BRAND = re.compile(r"&brand\w+;")
ANDROID_ESCAPE = re.compile(r"\\(u[0-9a-fA-F]{4}|.)")
# Android shows a line break or a run of spaces in a string as one space.
SPACES = re.compile(r"[ \t\r\n]+")
UNICODE_ESCAPE = re.compile(r"\\u([0-9a-fA-F]{4})")


def parse(path: str, data: bytes, app_name: str, english: bool) -> Iterator[UIString]:
    """
    Yield the strings of one file, with `path` in each ID.

    XLIFF and gettext files hold English and a translation side by side, and
    `english` says which one to read.
    """
    # A gettext template gets the IDs of its translations.
    prefix = path.removesuffix("t") if path.endswith(".pot") else path
    for entry in PARSERS[PurePosixPath(path).suffix](data, app_name, english):
        yield entry._replace(id=f"{prefix}:{entry.id}")


def fill_app_name(text: str, app_name: str) -> str | None:
    """
    Put the app's name where the text has one placeholder for a name, like "About %1$s".

    Return None when the text has more placeholders, or one for a number: those
    stand for things only known when the product runs.
    """
    placeholders = [found for found in PLACEHOLDER.findall(text) if found != "%%"]
    if len(placeholders) > 1 or any(not APP_NAME_PLACEHOLDER.fullmatch(p) for p in placeholders):
        return None
    return PLACEHOLDER.sub(lambda match: "%" if match.group() == "%%" else app_name, text)


def parse_properties(data: bytes, app_name: str, english: bool) -> Iterator[UIString]:
    comment = []
    for line in re.sub(r"\\\r?\n\s*", "", data.decode("utf-8", "replace")).splitlines():
        line = line.strip()
        if line.startswith(("#", "!")):
            comment.append(line.lstrip("#! "))
            continue
        if match := PROPERTY.match(line):
            key, text = match.groups()
            text = UNICODE_ESCAPE.sub(lambda match: chr(int(match.group(1), 16)), text)
            # A placeholder here is rarely the app's name, which comes from brand.properties.
            if text and not ACCESS_KEY.search(key) and not PLACEHOLDER.search(text):
                yield UIString(key, text, " ".join(comment))
        comment = []


def parse_dtd(data: bytes, app_name: str, english: bool) -> Iterator[UIString]:
    entities = DTD_COMMENT.sub("", data.decode("utf-8", "replace"))
    for key, double_quoted, single_quoted in DTD_ENTITY.findall(entities):
        if (text := double_quoted or single_quoted) and not ACCESS_KEY.search(key):
            yield UIString(key, DTD_BRAND.sub(app_name, text))


def parse_android(data: bytes, app_name: str, english: bool) -> Iterator[UIString]:
    comment = ""
    for element in _xml(data):
        if element.tag is etree.Comment:
            comment = " ".join((element.text or "").split())
            continue
        if element.tag == "string" and element.get("name"):
            text = SPACES.sub(" ", "".join(element.itertext())).strip()
            if len(text) > 1 and text[0] == text[-1] == '"':
                text = text[1:-1]
            filled = fill_app_name(ANDROID_ESCAPE.sub(_android_escape, text), app_name)
            if filled:
                yield UIString(element.get("name"), filled, comment)
        comment = ""


def parse_xliff(data: bytes, app_name: str, english: bool) -> Iterator[UIString]:
    for file in _xml(data).iter("{*}file"):
        for unit in file.iter("{*}trans-unit"):
            element = unit.find("{*}source" if english else "{*}target")
            text = (
                fill_app_name("".join(element.itertext()), app_name)
                if element is not None
                else None
            )
            if text and unit.get("id"):
                yield UIString(
                    f"{file.get('original')}:{unit.get('id')}",
                    text,
                    unit.findtext("{*}note") or "",
                )


def parse_po(data: bytes, app_name: str, english: bool) -> Iterator[UIString]:
    # A template's header has a word where a translation has its number of plural forms.
    data = data.replace(b"nplurals=INTEGER", b"nplurals=2")
    for message in read_po(io.BytesIO(data)):
        text = message.id if english else message.string
        if message.id and isinstance(text, str) and text and not message.fuzzy:
            key = f"{message.context}\x04{message.id}" if message.context else message.id
            yield UIString(key, text, " ".join(message.auto_comments))


def _xml(data: bytes) -> etree._Element:
    """Parse a download as outside data: no entity expansion and no network access."""
    return etree.fromstring(data, etree.XMLParser(resolve_entities=False, no_network=True))


def _android_escape(match: re.Match) -> str:
    escape = match.group(1)
    if len(escape) == 5:
        return chr(int(escape[1:], 16))
    return {"n": " ", "t": " "}.get(escape, escape)


PARSERS = {
    ".properties": parse_properties,
    ".dtd": parse_dtd,
    ".xml": parse_android,
    ".xliff": parse_xliff,
    ".po": parse_po,
    ".pot": parse_po,
}
