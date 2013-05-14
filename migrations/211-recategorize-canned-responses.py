"""
All the forum canned responses are stored in KB articles. There is a
category for them now. Luckily they follow a simple pattern of slugs, so
they are easy to find.
"""

from django.conf import settings
from django.db.models import F

from wiki.models import Document
from wiki.config import CANNED_RESPONSES_CATEGORY

canned = F(slug__startswith='forum-response-',
                     locale=settings.WIKI_DEFAULT_LANGUAGE)
canned |= F(slug='common-forum-responses',
                      locale=settings.WIKI_DEFAULT_LANGUAGE)

Document.object.filter(canned).update(category=CANNED_RESPONSES_CATEGORY)
