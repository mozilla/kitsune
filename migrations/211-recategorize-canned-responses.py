"""
All the forum canned responses are stored in KB articles. There is a
category for them now. Luckily they follow a simple pattern of slugs, so
they are easy to find.

This could have been an SQL migration, but I'm lazy and prefer Python.
"""
from django.conf import settings

from wiki.models import Document
from wiki.config import CANNED_RESPONSES_CATEGORY

to_move = list(Document.objects.filter(slug__startswith='forum-response-',
                                       locale=settings.WIKI_DEFAULT_LANGUAGE))
try:
    to_move.append(Document.objects.get(slug='common-forum-responses',
                                        locale=settings.WIKI_DEFAULT_LANGUAGE))
except Document.DoesNotExist:
    pass

print 'Recategorizing %d common response articles.' % len(to_move)

for doc in to_move:
    doc.category = CANNED_RESPONSES_CATEGORY
    doc.is_localizable = True
    doc.save()
