from django.contrib.contenttypes.models import ContentType

from taggit.models import TaggedItem

from wiki.models import Document


def run():
    # Get content_type_id for Document.
    content_type = ContentType.objects.get_for_model(Document)
    # Get all instances of tags that point at a Document
    tags = TaggedItem.objects.filter(content_type=content_type)

    print 'Deleting %d tags.' % tags.count()
    tags.delete()
    print 'Done!'
