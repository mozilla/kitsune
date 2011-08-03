import json
from string import ascii_letters
import random

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

import jingo
import waffle

from chat import log, redis, nonce_key
from chat.models import RoomsUserIsIn


@require_GET
def chat(request):
    """Display the current state of the chat queue."""
    if waffle.flag_is_active(request, 'new-chat'):
        nonce = None
        if request.user.is_authenticated():
            nonce = ''.join(random.choice(ascii_letters) for _ in xrange(10))
            redis().setex(nonce_key(nonce), request.user.id, 60)
        return jingo.render(request, 'chat/chat.html', {'nonce': nonce})
    else:
        return jingo.render(request, 'chat/old_chat.html')


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


def socketio(io):
    """View that serves the /socket.io madness used by socketio

    Directly handles traffic from the user to the server.

    """
    if io.on_connect():
        log.debug('CONNECT %s' % io.session)
    else:
        # I haven't nailed down when this happens yet. It might happen when
        # websockets are enabled and we hit the server with FF 7.
        log.debug('SOMETHING OTHER THAN CONNECT!')

    rooms = RoomsUserIsIn()

    # Until the client disconnects, listen for input from the user:
    for from_client in _messages_while_connected(io):
        kind = from_client.get('kind')
        if kind == 'say':
            room, message = from_client.get('room'), from_client.get('message')
            if room and message:  # else drop it on the floor
                rooms.say(room, message)
        elif kind == 'nonce':
            nonce = from_client.get('nonce')
            if nonce:
                rooms.identify(nonce)
                # TODO: Think about reloading the page or prompting to if the
                # nonce doesn't resolve.
        elif kind == 'join':
            room = from_client.get('room')
            if room:
                rooms.join(room, io)
        elif kind == 'leave':
            room = from_client.get('room')
            if room:
                rooms.leave(room)

    log.debug('EXIT %s' % io.session)
    rooms.leave_all()
    return HttpResponse()


def _messages_while_connected(io):
    """Return an iterator over decoded JSON blobs from a socketio socket.

    Stop when the socket disconnects.

    """
    while io.connected():
        message = io.recv()
        # message is always a list of 0 or 1 strings, I deduce from the source.
        if message:
            json_data = message[0]
            log.debug('Outgoing: %s' % json_data)
            try:
                data = json.loads(json_data)
            except ValueError:
                log.warning('Invalid JSON from chat client: %s' % json_data)
            else:
                yield data
