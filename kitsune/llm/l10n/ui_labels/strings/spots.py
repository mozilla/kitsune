"""
Work out the spots of each owner's strings.

Several strings of one product can have the same English text, like "View" in
the menu bar and "View" on a button. If every locale translates them the same
way, it doesn't matter which one a label means, and they make one spot. If some
locale translates them differently, they are different spots, and someone has to
read the article to tell which one a label means.

An owner's spot list holds every English text it has, with the strings that have
that text and the spot each string is in.
"""

from collections import defaultdict
from collections.abc import Iterable

from django.conf import settings
from django.db.models import F, Func, JSONField, Max, TextField, Value
from django.db.models.functions import Cast

from kitsune.llm.l10n.ui_labels.text import loosen, normalize
from kitsune.llm.models import UISpotList, UIStringCatalog


def get_strings_with_text(texts: Iterable[str]) -> dict[str, dict[str, list[dict]]]:
    """
    Find the strings that have a label's text, for each owner that has any.

    The answer is {owner: {text: strings}}, each string as it is in the spot list.
    A string matches when its text is the label's, letter for letter. Only when an
    owner has none like that do its strings that differ in case or in their last
    punctuation mark match.
    """
    texts = sorted(set(texts))
    # One lookup by key for each text. Naming the key as text keeps Postgres from
    # reading a label like "2" as a position in a list.
    lookups = {
        f"text{number}": Func(
            F("strings_by_text"),
            Cast(Value(loosen(text)), TextField()),
            template="(%(expressions)s)",
            arg_joiner=" -> ",
            output_field=JSONField(),
        )
        for number, text in enumerate(texts)
    }
    found: dict[str, dict[str, list[dict]]] = defaultdict(dict)
    for owner, *values in UISpotList.objects.annotate(**lookups).values_list("owner", *lookups):
        for text, strings in zip(texts, values, strict=True):
            exact = [s for s in strings or () if normalize(s["text"]) == normalize(text)]
            if strings:
                found[owner][text] = exact or strings
    return found


def get_spots(strings: list[dict]) -> list[list[str]]:
    """Return the string IDs of each spot among the strings, in the order of the spots' numbers."""
    members = defaultdict(list)
    for string in strings:
        members[string["spot"]].append(string["id"])
    return [members[number] for number in sorted(members)]


def is_one_spot(string_ids: set[str], strings: list[dict]) -> bool:
    """
    Say whether strings that once made a spot still do.

    They don't when a translation changed and split them, or when the product
    removed them all.
    """
    return len({string["spot"] for string in strings if string["id"] in string_ids}) == 1


def build_spot_lists() -> None:
    """Build the spot list of each owner whose strings were synced since its last one."""
    built = dict(UISpotList.objects.values_list("owner", "built_at"))
    synced = UIStringCatalog.objects.values_list("owner").annotate(Max("source__synced_at"))
    for owner, synced_at in synced.order_by("owner"):
        if synced_at and not (owner in built and built[owner] > synced_at):
            build_spot_list(owner)


def build_spot_list(owner: str) -> None:
    """
    Group an owner's strings into spots, and save the list.

    This is the one place that reads every locale of an owner, one at a time.
    Everything else looks a label up in the list it leaves behind.
    """
    catalogs = UIStringCatalog.objects.filter(owner=owner)
    english: dict[str, str] = {}
    for strings in catalogs.filter(locale=settings.WIKI_DEFAULT_LANGUAGE).values_list(
        "strings", flat=True
    ):
        english |= strings

    same_text = defaultdict(list)
    for string_id in sorted(english):
        same_text[loosen(english[string_id])].append(string_id)

    # Only strings that share their text with another can land in different spots.
    shared = {string_id for ids in same_text.values() if len(ids) > 1 for string_id in ids}
    shown = {string_id: {"": normalize(english[string_id])} for string_id in shared}
    locales = set(settings.SUMO_LANGUAGES) - {settings.WIKI_DEFAULT_LANGUAGE}
    for locale in sorted(locales & set(catalogs.values_list("locale", flat=True))):
        for strings in catalogs.filter(locale=locale).values_list("strings", flat=True):
            for string_id in shared & strings.keys():
                shown[string_id][locale] = normalize(strings[string_id])

    strings_by_text = {
        text: [
            {"id": string_id, "text": english[string_id], "spot": spot}
            for string_id, spot in zip(
                ids, _spot_numbers([shown.get(i, {}) for i in ids]), strict=True
            )
        ]
        for text, ids in same_text.items()
    }
    UISpotList.objects.update_or_create(owner=owner, defaults={"strings_by_text": strings_by_text})


def _spot_numbers(shown: list[dict[str, str]]) -> list[int]:
    """
    Number the spot of each string, given what each shows per locale.

    A string joins the first spot it never disagrees with. A locale where it has
    no translation yet can't disagree, so a new string doesn't split a spot.
    """
    spots: list[dict[str, str]] = []
    numbers = []
    for texts in shown:
        for number, spot in enumerate(spots):
            if all(spot.get(locale, text) == text for locale, text in texts.items()):
                break
        else:
            number = len(spots)
            spots.append({})
        spots[number] |= texts
        numbers.append(number)
    return numbers
