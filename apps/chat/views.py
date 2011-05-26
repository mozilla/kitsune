import random

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

import jingo


@require_GET
def chat(request):
    """Display the current state of the chat queue."""
    nonce = None
    if request.user.is_authenticated():
        nonce = make_nonce()
        cache.set('chatnonce:{n}'.format(n=nonce), request.user, 5 * 60)
    return jingo.render(request, 'chat/chat.html', {'nonce': nonce})


@never_cache
@require_GET
def queue_status(request):
    """Dump the queue status out of the cache.

    See chat.crons.get_queue_status.

    """

    xml = cache.get(settings.CHAT_CACHE_KEY)
    status = 200
    if not xml:
        xml = ''
        status = 503
    return HttpResponse(xml, mimetype='application/xml', status=status)


def make_nonce():
    return ''.join(random.choice('abcdefghijklmnopqrstuvwxyz234567')
                   for _ in xrange(10))
