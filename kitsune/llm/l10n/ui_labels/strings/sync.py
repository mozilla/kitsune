"""
Copy products' strings from their sources into our database.

A sync looks at one source. If anything about it changed, it reads the download
as it arrives, without saving it to disk, and saves a catalog for English and for
each locale an owner ships.
"""

import hashlib
import json
import logging
import tarfile
from collections import defaultdict
from itertools import takewhile
from typing import IO, cast

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from lxml import etree

from kitsune.llm.l10n.ui_labels.strings import github
from kitsune.llm.l10n.ui_labels.strings.locales import get_product_codes
from kitsune.llm.l10n.ui_labels.strings.parsers.fluent import FluentFiles
from kitsune.llm.l10n.ui_labels.strings.parsers.standalone import parse
from kitsune.llm.l10n.ui_labels.strings.parsers.ui_string import UIString
from kitsune.llm.l10n.ui_labels.strings.shipped_locales import get_shipped_codes
from kitsune.llm.l10n.ui_labels.strings.sources import SOURCES, OwnerFiles, Source
from kitsune.llm.models import UIStringCatalog, UIStringSource

log = logging.getLogger("k.llm")

PARSER_VERSION = 1
MAX_FILE_SIZE = 5 * 1024**2
MAX_DOWNLOAD_SIZE = 1024**3
# An owner with no list of shipped locales ships a locale when this share of one
# file's strings is translated. The product itself decides that way.
MIN_TRANSLATED = 0.7
NUL = chr(0)
# A product can put this invisible mark inside a word, to say where it may break
# across lines. It isn't part of the text a user reads.
SOFT_HYPHEN = chr(0xAD)

# The files read from a download: for each owner, by locale code, then by path.
type Files = dict[OwnerFiles, dict[str, dict[str, bytes]]]


def sync(source: Source) -> bool:
    """
    Read a source's strings again if anything about them changed, and say whether it did.

    What goes wrong is saved on the source. A sync that fails keeps every string of
    the last one that worked. An owner whose strings are missing where we expect
    some keeps the ones it had there, while the rest of the source is saved.
    """
    record, _ = UIStringSource.objects.get_or_create(name=source.name)
    try:
        commit = github.get_latest_commit(source.repo, source.ref)
        shipped = {
            owner_files.owner: set(get_product_codes(get_shipped_codes(owner_files.owner)))
            for owner_files in source.owner_files
            if owner_files.translated and not owner_files.measured_by
        }
        # An owner's brand names can come from an earlier source, so a change there
        # changes what this sync saves.
        earlier = takewhile(lambda other: other.name != source.name, SOURCES.values())
        providers = [other.name for other in earlier if other.owners & source.owners]
        state = [
            PARSER_VERSION,
            repr(source),
            commit,
            {owner: sorted(locales) for owner, locales in shipped.items()},
            sorted(
                UIStringSource.objects.filter(name__in=providers).values_list("name", "commit")
            ),
        ]
        fingerprint = hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()
        if fingerprint == record.fingerprint:
            return False
        with github.get_tarball(source.repo, commit) as download, transaction.atomic():
            missing = _Reading(source, record, shipped).read(cast(IO[bytes], download.raw))
            record.update(
                commit=commit,
                fingerprint=fingerprint,
                synced_at=timezone.now(),
                error=" ".join(missing),
            )
        for problem in missing:
            log.error(problem)
    except Exception as error:
        # Without a fingerprint the next sync reads the source again, which replaces
        # this error with whatever is still wrong then.
        record.update(error=f"{type(error).__name__}: {error}", fingerprint="")
        raise
    return True


class _Reading:
    """One pass over a source's download."""

    def __init__(self, source: Source, record: UIStringSource, shipped: dict[str, set[str]]):
        self.source = source
        self.record = record
        self.shipped = shipped
        self.saved: dict[OwnerFiles, set[str]] = defaultdict(set)

    def read(self, download: IO[bytes]) -> list[str]:
        """
        Save the download's strings, and return a sentence for each owner missing some.

        A source whose top folders are locales is saved one locale at a time, as
        the download passes each. Any other source is saved at the end.
        """
        files: Files = defaultdict(lambda: defaultdict(dict))
        folder, size = None, 0
        with tarfile.open(fileobj=download, mode="r|gz") as archive:
            for member in archive:
                # Every path in a GitHub tarball starts with a folder named after the commit.
                path = member.name.partition("/")[2]
                found = [
                    (owner_files, match)
                    for owner_files in self.source.owner_files
                    if (match := owner_files.match(path))
                ]
                if not member.isfile() or not found:
                    continue
                if member.size > MAX_FILE_SIZE:
                    log.warning(f"Skipped {path} in {self.source.repo}: it's too big.")
                    continue
                size += member.size
                if size > MAX_DOWNLOAD_SIZE:
                    raise ValueError(f"{self.source.repo} holds more than we expect to read.")
                top = path.partition("/")[0]
                if self.source.by_locale and top != folder:
                    self._save_catalogs(files)
                    files.clear()
                    folder = top
                data = cast(IO[bytes], archive.extractfile(member)).read()
                for owner_files, (code, string_path) in found:
                    files[owner_files][code][string_path] = data
        self._save_catalogs(files)
        return [
            problem
            for owner_files in self.source.owner_files
            if (problem := self._check(owner_files))
        ]

    def _save_catalogs(self, files: Files) -> None:
        """Save English and each locale that ships, from the files read so far."""
        for owner_files, by_code in files.items():
            if "" in by_code:
                self._save_catalog(owner_files, settings.WIKI_DEFAULT_LANGUAGE, by_code.pop(""))
            for locale, code in get_product_codes(by_code).items():
                if owner_files.measured_by:
                    xliff = by_code[code].get(owner_files.measured_by, b"")
                    strings, translated = xliff.count(b"<source"), xliff.count(b"<target")
                    ships = strings > 0 and translated >= MIN_TRANSLATED * strings
                else:
                    ships = locale in self.shipped[owner_files.owner]
                if ships:
                    self._save_catalog(owner_files, locale, by_code[code])

    def _save_catalog(self, owner_files: OwnerFiles, locale: str, files: dict[str, bytes]) -> None:
        """Read one locale's files, and save its catalog if it has strings and they changed."""
        english = locale == settings.WIKI_DEFAULT_LANGUAGE
        fluent = FluentFiles()
        entries: list[UIString] = []
        for path, data in sorted(files.items()):
            try:
                if path.endswith(".ftl"):
                    fluent.add(path, data.decode("utf-8", "replace"))
                else:
                    entries += parse(path, data, owner_files.app_name, english)
            except (etree.XMLSyntaxError, UnicodeDecodeError, RecursionError) as error:
                log.warning(f"Skipped {path} [{locale}] in {self.source.repo}: {error}")
        terms = fluent.terms_text()
        # A string can use a brand name that is kept in another source. A product shows
        # the English name where a locale has none of its own.
        borrowed = (
            UIStringCatalog.objects.filter(
                owner=owner_files.owner, locale__in=(locale, settings.WIKI_DEFAULT_LANGUAGE)
            )
            .exclude(source=self.record)
            .exclude(terms="")
            .order_by("source__name")
            .values_list("locale", "terms")
        )
        for _, text in sorted(borrowed, key=lambda row: row[0] != locale):
            fluent.add("", text)
        entries += fluent.strings()
        if not entries:
            return
        row = {"owner": owner_files.owner, "source": self.record, "locale": locale}
        fields = {
            "strings": {
                _storable(entry.id): _storable(entry.text).replace(SOFT_HYPHEN, "")
                for entry in entries
            },
            "comments": {
                _storable(entry.id): _storable(entry.comment)
                for entry in entries
                if english and entry.comment
            },
            "terms": terms,
        }
        # Most locales are the same as the last time, and a catalog is a big row to rewrite.
        if not UIStringCatalog.objects.filter(**row, **fields).exists():
            UIStringCatalog.objects.update_or_create(**row, defaults=fields)
        self.saved[owner_files].add(locale)

    def _check(self, owner_files: OwnerFiles) -> str | None:
        """
        Drop the locales the owner no longer ships, and say where the repository
        has no strings but we expect some.

        Missing strings usually mean a moved folder or a wrong locale code. Those
        locales keep the rows they had, so their labels don't quietly go back to
        English.
        """
        saved = self.saved[owner_files]
        expected: set[str] = set()
        if owner_files.translates_every_locale:
            expected |= self.shipped.get(owner_files.owner, set())
        if not self.source.by_locale:
            expected.add(settings.WIKI_DEFAULT_LANGUAGE)
        missing = expected - saved
        dropped = UIStringCatalog.objects.filter(
            source=self.record, owner=owner_files.owner
        ).exclude(locale__in=saved | missing)
        if locales := sorted(dropped.values_list("locale", flat=True)):
            log.info(f"{owner_files.owner} no longer ships {locales} from {self.source.repo}.")
            dropped.delete()
        if not missing:
            return None
        return f"{self.source.repo} has no strings for {owner_files.owner} in {sorted(missing)}."


def _storable(text: str) -> str:
    """Remove what Postgres can't keep: NUL characters and halves of a surrogate pair."""
    return text.replace(NUL, "").encode("utf-8", "ignore").decode("utf-8")
