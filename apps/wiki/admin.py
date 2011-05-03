from django.contrib import admin

from wiki.models import Document


class DocumentAdmin(admin.ModelAdmin):
    exclude = ('tags',)
    list_display = ('locale', 'title', 'category', 'is_localizable',
                    'is_archived')
    list_display_links = ('title',)
    list_filter = ('is_template', 'is_localizable', 'category', 'locale')
    raw_id_fields = ('parent',)
    readonly_fields = ('id', 'current_revision')
    search_fields = ('title',)

    @staticmethod
    def _set_archival(queryset, should_be_archived):
        """Set archival bit of documents, percolating up to parents as well."""
        for doc in queryset:
            # If this is a child, change its parent instead, and saving the
            # parent will change all the children to match.
            doc_to_change = doc.parent or doc
            doc_to_change.is_archived = should_be_archived
            doc_to_change.save()

    def _show_archival_message(self, request, queryset, verb):
        count = len(queryset)
        phrase = (
            'document, along with its English version or translations, was '
            'marked as '
            if count == 1 else
            'documents, along with their English versions or translations, '
            'were marked as ')
        self.message_user(request, '%s %s %s.' % (count, phrase, verb))

    def archive(self, request, queryset):
        """Mark several documents as obsolete."""
        self._set_archival(queryset, True)
        self._show_archival_message(request, queryset, 'obsolete')
    archive.short_description = 'Mark as obsolete'

    def unarchive(self, request, queryset):
        """Mark several documents as not obsolete."""
        self._set_archival(queryset, False)
        self._show_archival_message(request, queryset, 'no longer obsolete')
    unarchive.short_description = 'Mark as not obsolete'

    actions = [archive, unarchive]


admin.site.register(Document, DocumentAdmin)
