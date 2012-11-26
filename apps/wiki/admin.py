from django.contrib import admin

from wiki.models import Document, ImportantDate, Locale


class DocumentAdmin(admin.ModelAdmin):
    exclude = ('tags',)
    list_display = ('locale', 'title', 'category', 'is_localizable',
                    'is_archived', 'allow_discussion')
    list_display_links = ('title',)
    list_filter = ('is_template', 'is_localizable', 'category', 'locale',
                   'is_archived', 'allow_discussion')
    raw_id_fields = ('parent', 'contributors')
    readonly_fields = ('id', 'current_revision', 'latest_localizable_revision')
    search_fields = ('title',)

    def has_add_permission(self, request):
        return False

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

    def allow_discussion(self, request, queryset):
        """Allow discussion on several documents."""
        queryset.update(allow_discussion=True)
        self.message_user(request, u'Document(s) now allow discussion.')

    def disallow_discussion(self, request, queryset):
        """Disallow discussion on several documents."""
        queryset.update(allow_discussion=False)
        self.message_user(request, u'Document(s) no longer allow discussion.')

    actions = [archive, unarchive, allow_discussion, disallow_discussion]


admin.site.register(Document, DocumentAdmin)


class ImportantDateAdmin(admin.ModelAdmin):
    list_display = ('text', 'date')
    list_display_links = ('text', 'date')
    list_filter = ('text', 'date')
    raw_id_fields = ()
    readonly_fields = ('id',)
    search_fields = ('text', 'date')


admin.site.register(ImportantDate, ImportantDateAdmin)


class LocaleAdmin(admin.ModelAdmin):
    list_display = ('locale',)
    list_display_links = ('locale',)
    raw_id_fields = ('leaders', 'reviewers', 'editors')
    readonly_fields = ('locale',)
    search_fields = ('locale',)

    # Disable adding and deleting new locales from the admin.
    # Use migrations instead.

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, *args, **kwargs):
        return False


admin.site.register(Locale, LocaleAdmin)
