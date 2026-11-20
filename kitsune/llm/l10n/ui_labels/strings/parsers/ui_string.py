"""What every reader of a product's translation files hands back, and what they all skip."""

import re
from typing import NamedTuple

ACCESS_KEY = re.compile(r"(?:accesskey|commandkey)[^.]*$|\.key$", re.IGNORECASE)


class UIString(NamedTuple):
    """
    One string from a product's translation files.

    `id` is the path of the string's file, then its name in that file,
    as in "browser/browser/menubar.ftl:menu-view.label". `text` is what a user
    sees. `comment` is the note the source file has about the string, if any.
    """

    id: str
    text: str
    comment: str = ""
