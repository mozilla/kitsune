"""
Turn a product's locale codes into SUMO's.

Products spell locales their own way. Firefox says "es-ES" and Android says "iw"
where SUMO says "es" and "he".
"""

import re
from collections.abc import Iterable

from django.conf import settings

# SUMO has one Spanish locale and writes new labels in Spain's Spanish. The other
# variants are kept under their own codes, to recognize a translator's official label.
SPANISH_VARIANTS = ("es-AR", "es-CL", "es-MX")

# Product codes that name the same language as a SUMO locale with another code.
# Tamil has two SUMO locales, and products ship one.
OTHER_SPELLINGS = {
    "es-ES": ("es",),
    "fy": ("fy-NL",),
    "ga": ("ga-IE",),
    "gu": ("gu-IN",),
    "hi": ("hi-IN",),
    "in": ("id",),
    "iw": ("he",),
    "nb": ("no",),
    "nb-NO": ("no",),
    "ne": ("ne-NP",),
    "sv-SE": ("sv",),
    "ta": ("ta", "ta-LK"),
}

ANDROID_REGION = re.compile(r"-r(?=[A-Z]{2}$)")


def get_catalog_locales(code: str) -> tuple[str, ...]:
    """
    Return the locales under which the strings of a product's locale code are saved.

    Those are the SUMO locales the code stands for: "iw" stands for "he". A Spanish variant
    is not a SUMO locale, and is saved under its own code. A code is never matched to
    a sibling: Brazilian Portuguese is not Portugal's.
    """
    code = ANDROID_REGION.sub("-", code.replace("_", "-"))
    if code in SPANISH_VARIANTS:
        return (code,)
    if code in OTHER_SPELLINGS:
        return OTHER_SPELLINGS[code]
    return (
        (code,)
        if code in settings.SUMO_LANGUAGES and code != settings.WIKI_DEFAULT_LANGUAGE
        else ()
    )


def get_product_codes(codes: Iterable[str]) -> dict[str, str]:
    """
    Map each locale we save strings under to the product's own code for it, from the
    codes a product has.

    When a product has two codes for one locale, like "sv" and "sv_SE", the longer
    one wins. The short one is often a copy, and not always a fresh one.
    """
    return {
        locale: code
        for code in sorted(codes, key=lambda code: (len(code), code))
        for locale in get_catalog_locales(code)
    }
