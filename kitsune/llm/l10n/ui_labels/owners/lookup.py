"""
Find the owner of each label of an English revision, and its spot when the
owner has several.

A label's text can't tell who owns it. "Settings" is in Firefox, in Thunderbird
and in Windows. So an LLM reads the whole article, with a number in front of
each label we ask about, and answers for each number. What it says is saved.
Everything that needs to know a label's owner asks `get_owners()`.
"""

import logging
from contextlib import suppress
from dataclasses import asdict

from django.conf import settings
from redis.exceptions import LockNotOwnedError

from kitsune.llm.l10n.config import L10N_LLM_MODEL
from kitsune.llm.l10n.ui_labels.labels import LabelUse, find_labels, number_labels
from kitsune.llm.l10n.ui_labels.owners import (
    CONFIG,
    OWNERS,
    UNKNOWN,
    UNKNOWN_REASONS,
    LabelOwner,
)
from kitsune.llm.l10n.ui_labels.owners.prompt import (
    QUESTION_VERSION,
    LabelAnswer,
    owner_parser,
    owner_prompt,
)
from kitsune.llm.l10n.ui_labels.strings.spots import get_spots, get_strings_with_text, is_one_spot
from kitsune.llm.models import UILabelOwners, UIStringCatalog
from kitsune.llm.utils import build_chain_with_retry, get_llm
from kitsune.sumo.redis_utils import redis_client
from kitsune.wiki.models import Revision

log = logging.getLogger("k.llm")

ANSWER_VERSION = f"{QUESTION_VERSION}:{L10N_LLM_MODEL}"

# How long one task may take to ask about a revision, and how long another waits
# for it. The wait is the longer one, so that when the task that asks has died, a
# waiting task outlasts its lock and asks instead.
LOCK_SECONDS = 180
WAIT_SECONDS = 300

# How much of each of a label's spots the LLM is shown.
MAX_EXAMPLES = 4
MAX_COMMENT_LENGTH = 200


def get_owners(revision: Revision) -> dict[int, LabelOwner]:
    """
    Return the owner of each label of an English revision, by the label's position.

    The LLM is asked about each label that has no owner saved yet. A label it
    doesn't answer is left out, and is asked about again the next time. Each
    revision has its own answers, because a change anywhere in an article can
    change what a label means.
    """
    lookup = _OwnerLookup(revision)
    if (owners := lookup.saved()).keys() == lookup.uses.keys():
        return owners
    # Only one task asks about a revision. The others wait for what it saves.
    lock = redis_client("default").lock(
        f"ui-labels:owners:{revision.id}",
        timeout=LOCK_SECONDS,
        blocking_timeout=WAIT_SECONDS,
    )
    if lock.acquire():
        try:
            lookup.ask()
        finally:
            # A call that outlasted the lock has still saved its answers.
            with suppress(LockNotOwnedError):
                lock.release()
    else:
        log.warning(f"Gave up waiting for the label owners of revision {revision.id}.")
    return lookup.saved()


class _OwnerLookup:
    """One revision's labels, and what it takes to find their owners."""

    def __init__(self, revision: Revision):
        self.revision = revision
        self.uses = find_labels(revision.content)
        self.products = sorted(revision.document.products.values_list("slug", flat=True))
        # Spots are only shown for the owners that the article's products usually point to.
        self.spot_owners = {
            owner.name for owner in OWNERS.values() if set(owner.products) & set(self.products)
        }
        self.found = get_strings_with_text(use.text for use in self.uses.values())
        self.comments: dict[str, dict[str, str]] = {}

    def saved(self) -> dict[int, LabelOwner]:
        """Return the saved label owners that still hold, by position."""
        record = UILabelOwners.objects.filter(
            revision=self.revision, answer_version=ANSWER_VERSION
        ).first()
        saved = {}
        for position, said in (record.owners if record else {}).items():
            use, label_owner = self.uses.get(int(position)), LabelOwner(**said)
            if (
                use
                and (label_owner.kind, label_owner.text) == (use.kind, use.text)
                and self._holds(label_owner)
            ):
                saved[int(position)] = label_owner
        return saved

    def _holds(self, label_owner: LabelOwner) -> bool:
        """
        Say whether a saved label owner is still enough to settle its label.

        It isn't when a sync split or removed the spot it names, or when its owner
        now has several spots and the LLM was never asked to choose one.
        """
        strings = self.found.get(label_owner.owner, {}).get(label_owner.text, [])
        if label_owner.spot is None:
            return label_owner.owner not in self.spot_owners or len(get_spots(strings)) < 2
        return not label_owner.spot or is_one_spot(set(label_owner.spot), strings)

    def ask(self) -> None:
        """Ask the LLM about the labels with no saved owner, and save what it says."""
        saved = self.saved()
        asking = sorted(self.uses.keys() - saved.keys())
        if not asking:
            return
        chain = build_chain_with_retry(
            owner_prompt, get_llm(model_name=L10N_LLM_MODEL, temperature=0.0), owner_parser
        )
        reply = chain.invoke(
            {
                "title": self.revision.document.title,
                "products": self.products,
                "labels": [self._label(position) for position in asking],
                "article": number_labels(
                    self.revision.content, {position: self.uses[position] for position in asking}
                ),
            }
        )
        if reply is None:
            log.warning(f"The LLM gave no answer we could read for revision {self.revision.id}.")
            return
        answered = {
            said.label: self._label_owner(said) for said in reply.answers if said.label in asking
        }
        if answered:
            UILabelOwners.objects.update_or_create(
                revision=self.revision,
                defaults={
                    "owners": {
                        position: asdict(label_owner)
                        for position, label_owner in (saved | answered).items()
                    },
                    "answer_version": ANSWER_VERSION,
                },
            )

    def _label(self, position: int) -> dict:
        """Return what the prompt says about one label: the owners with its text, and its spots."""
        use = self.uses[position]
        return {
            "number": position,
            "markup": use.markup,
            "found_in": sorted(owner for owner, texts in self.found.items() if use.text in texts),
            "spots": {
                owner: {name: self._shown(owner, ids) for name, ids in spots.items()}
                for owner, spots in self._shown_spots(use).items()
            },
        }

    def _shown_spots(self, use: LabelUse) -> dict[str, dict[str, list[str]]]:
        """
        Return the spots the LLM chooses from for a label: for each owner that has
        several, the string IDs of each spot by the name the LLM knows it by.
        """
        spots = {}
        for owner in sorted(self.spot_owners & self.found.keys()):
            members = get_spots(self.found[owner].get(use.text, []))
            if len(members) > 1:
                spots[owner] = {
                    f"s{number}": string_ids for number, string_ids in enumerate(members, 1)
                }
        return spots

    def _shown(self, owner: str, string_ids: list[str]) -> dict:
        """Return a few of a spot's strings as the LLM sees them, and how many more it has."""
        examples = [self._example(owner, string_id) for string_id in string_ids[:MAX_EXAMPLES]]
        return {"examples": examples, "more": len(string_ids) - len(examples)}

    def _example(self, owner: str, string_id: str) -> str:
        comment = " ".join(self._comments(owner).get(string_id, "").split())[:MAX_COMMENT_LENGTH]
        return f"{string_id} ({comment})" if comment else string_id

    def _comments(self, owner: str) -> dict[str, str]:
        if owner not in self.comments:
            self.comments[owner] = {}
            catalogs = UIStringCatalog.objects.filter(
                owner=owner, locale=settings.WIKI_DEFAULT_LANGUAGE
            )
            for comments in catalogs.values_list("comments", flat=True):
                self.comments[owner] |= comments
        return self.comments[owner]

    def _label_owner(self, said: LabelAnswer) -> LabelOwner:
        """
        Turn one answer of the LLM into a label owner, keeping only what we asked
        for: an owner we know, a reason we know, a spot we showed.
        """
        use = self.uses[said.label]
        owner, reason = said.owner, ""
        spot: list[str] | None = None
        if owner in OWNERS:
            if shown := self._shown_spots(use).get(owner):
                spot = shown[said.spot] if said.spot in shown else []
        elif not (owner == CONFIG and use.kind == "pref"):
            owner = UNKNOWN
            reason = said.unknown_reason if said.unknown_reason in UNKNOWN_REASONS else "unclear"
        return LabelOwner(use.kind, use.text, owner, reason, spot)
