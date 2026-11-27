"""Read what an owner's strings say in one locale."""

from collections.abc import Iterable

from django.db import connection

from kitsune.llm.models import UIStringCatalog

# Unpacks each catalog once, however many strings we ask for. Looking them up one
# by one would unpack it once per string.
TRANSLATIONS = """
    SELECT string.key, string.value
    FROM llm_uistringcatalog AS catalog, jsonb_each_text(catalog.strings) AS string
    WHERE catalog.owner = %s AND catalog.locale = %s AND string.key = ANY(%s)
"""


def get_translations(owner: str, locale: str, string_ids: Iterable[str]) -> dict[str, str]:
    """Return what each of the owner's strings says in a locale, for those it has there."""
    with connection.cursor() as cursor:
        cursor.execute(TRANSLATIONS, [owner, locale, sorted(set(string_ids))])
        return dict(cursor.fetchall())


def get_owners_shipping(locale: str) -> set[str]:
    """Return the owners that ship a locale. Those are the ones with a catalog in it."""
    return set(UIStringCatalog.objects.filter(locale=locale).values_list("owner", flat=True))
