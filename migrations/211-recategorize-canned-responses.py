"""
All the forum canned responses are stored in KB articles. There is a
category for them now. Luckily they follow a simple pattern of slugs, so
they are easy to find.
"""

from django.conf import settings
from django.db.models import Q

from kitsune.wiki.models import Document
from kitsune.wiki.config import CANNED_RESPONSES_CATEGORY

canned = Q(slug__startswith='forum-response-')
canned |= Q(slug='common-forum-responses')
canned &= Q(locale=settings.WIKI_DEFAULT_LANGUAGE)

Document.objects.filter(canned).update(category=CANNED_RESPONSES_CATEGORY)
