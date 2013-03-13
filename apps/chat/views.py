from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET


@require_GET
def chat(request):
    """Display the current state of the chat queue."""
    return render(request, 'chat/chat.html')


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
