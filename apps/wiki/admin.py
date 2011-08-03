from django.contrib import admin, messages
from django.shortcuts import render_to_response
from django.template import RequestContext

from wiki.models import Document, ImportantDate
from wiki.tasks import migrate_helpfulvotes


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


def helpfulvotes(request):
    chunk_size = 2000

    if request.POST.get('firetext'):
        try:
            chunk_size = int(request.POST.get('chunksize'))
        except:
            messages.add_message(request, messages.ERROR,
               'migrate_helpfulvotes task failed! Specify a valid chunk size')
            return render_to_response('wiki/admin/helpfulvotes.html',
                                  {'title': 'HelpfulVotes',
                                   'chunksize': chunk_size},
                                  RequestContext(request, {}))

        chunk_list = request.POST.get('textlist').split()

        try:
            chunk_split = [i.split('-') for i in chunk_list]
            chunks = []
            for chunk_range in chunk_split:
                chunks += filter(lambda x: not(x % chunk_size),
                                [i for i in range(int(chunk_range[0]),
                                    int(chunk_range[1]))])

            for start_id in chunks:
                migrate_helpfulvotes.delay(start_id, start_id + chunk_size)

            messages.add_message(request, messages.SUCCESS,
                '%s migrate_helpfulvotes task queued!' % len(chunks))
        except:
            messages.add_message(request, messages.ERROR,
                'migrate_helpfulvotes task failed! Follow entry format.')

    return render_to_response('wiki/admin/helpfulvotes.html',
                              {'title': 'HelpfulVotes',
                               'chunksize': chunk_size},
                              RequestContext(request, {}))


admin.site.register_view('helpfulvotes', helpfulvotes, 'HelpfulVotes')


class ImportantDateAdmin(admin.ModelAdmin):
    list_display = ('text', 'date')
    list_display_links = ('text', 'date')
    list_filter = ('text', 'date')
    raw_id_fields = ()
    readonly_fields = ('id',)
    search_fields = ('text', 'date')


admin.site.register(ImportantDate, ImportantDateAdmin)
