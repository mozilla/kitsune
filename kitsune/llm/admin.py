"""
Show in the admin the sources of product UI strings, with how each one's last sync
went, and what an LLM said about the labels of a revision: their owners, or their pairs.
"""

from django.contrib import admin
from django.utils.html import format_html

from kitsune.llm.l10n.ui_labels.labels import find_label_uses
from kitsune.llm.l10n.ui_labels.owners import LabelOwner
from kitsune.llm.models import UILabelOwners, UILabelPairs, UIStringSource


@admin.register(UIStringSource)
class UIStringSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "commit", "synced_at", "error")
    readonly_fields = ("name", "commit", "fingerprint", "synced_at", "error")

    def has_add_permission(self, request):
        return False


class LabelAnswersAdmin(admin.ModelAdmin):
    """What an LLM said about the labels of a revision, found by the revision or its article."""

    list_display = ("revision_id", "article", "answer_version")
    list_select_related = ("revision__document",)
    search_fields = ("revision__id", "revision__document__title", "revision__document__slug")

    def has_add_permission(self, request):
        return False

    @admin.display(description="Article")
    def article(self, record):
        return str(record.revision.document)


@admin.register(UILabelOwners)
class UILabelOwnersAdmin(LabelAnswersAdmin):
    fields = readonly_fields = ("revision", "labels", "answer_version")

    @admin.display(description="Labels")
    def labels(self, record):
        """Show a line for each label: its position, the label, its owner, and its spot."""
        lines = []
        for position, said in sorted(record.owners.items(), key=lambda item: int(item[0])):
            label_owner = LabelOwner(**said)
            line = f"{position}  {{{label_owner.kind} {label_owner.text}}} → {label_owner.owner}"
            if label_owner.unknown_reason:
                line += f": {label_owner.unknown_reason}"
            if label_owner.spot is not None:
                line += f", spot: {', '.join(label_owner.spot) or 'none'}"
            lines.append(line)
        return format_html("<pre>{}</pre>", "\n".join(lines))


@admin.register(UILabelPairs)
class UILabelPairsAdmin(LabelAnswersAdmin):
    fields = readonly_fields = ("revision", "labels", "explanation", "answer_version")

    @admin.display(description="Pairs")
    def labels(self, record):
        """
        Show a line for each pair: the translated label, and the English label it
        stands for. They are numbered as the LLM's explanation names them.
        """
        translated = find_label_uses(record.revision.content)
        english = find_label_uses(record.revision.based_on.content)

        def shown(prefix, uses, position):
            # The LLM can name a label that doesn't exist.
            markup = uses[position].markup if position < len(uses) else "?"
            return f"{prefix}{position}  {markup}"

        lines = [
            f"{shown('T', translated, int(position))} → {shown('E', english, english_position)}"
            for position, english_position in sorted(
                record.pairs.items(), key=lambda pair: int(pair[0])
            )
        ]
        return format_html("<pre>{}</pre>", "\n".join(lines))
