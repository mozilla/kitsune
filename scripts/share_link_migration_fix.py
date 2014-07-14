# Reverts the data migration for bug #766394 that broke localization
# and review for some KB articles.
#
# Run this with ./manage.py runscript share_link_migration_fix


from kitsune.wiki.models import Document, Revision


def run():
    migration_revisions = (Revision.objects.select_related('document')
                           .filter(creator__username='migrations'))
    affected_docs = [(rev.document, rev) for rev in migration_revisions]

    # Remove all links between migration revisions and replace with
    # correct ones.
    for doc, rev in affected_docs:
        Revision.objects.filter(based_on=rev).update(based_on=rev.based_on)
        (Document.objects.filter(current_revision=rev)
                         .update(current_revision=rev.based_on))
        rev.delete()


if __name__ == '__main__':
    print 'Run with "./manage.py runscript share_link_migration_fix"'
