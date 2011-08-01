"""
About our little nonce dance
----------------------------

We don't want anybody to be able to impersonate anybody else in a chat. Thus,
we have to map a socketio SID to a user. To do that, we have to map a socketio
SID to a session ID, which in turn can show the server that we are who we claim
(since session ID is secret). So, when we draw the chat page, we make up a
nonce and stick it in there, while simultaneously mapping it to the session ID
in redis for a short time. The JS yanks the nonce out of the page and sends it
back to the server on join, along with the socketio SID (implicitly), thus
completing the SID-to-session-ID mapping. And, because we avoid sticking the
session ID in the page, we avoid the possibility of session hijacking by any JS
that gets injected by an XSS attack; cookies are protected from evil JS better
(through HttpOnly, for example).


About the protocol
------------------

There are several kinds of message which go flitting between the clients and
server. Each message is a JSON dict with one or more of the fields `kind` and
`message`.

    Join. Sent from the client to the server.
        kind: join
        room: ID of the room to join

    Leave. Sent from the client to the server to unsubscribe from a room.
        kind: leave
        room: ID of the room

    Say. Sent in both directions.
        kind: say
        room: ID of the room
        message: What was said

There's no facility for private messages yet, but it can be added if needed. At
the moment, the plan is to implement private help sessions by first creating a
public room behind the scenes. That will allow additional moderators to steal
into the room undetected.

"""
import json
from string import ascii_letters
import random

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from gevent import Greenlet
import jingo

from chat import log
from sumo.utils import redis_client


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
    return ''.join(random.choice(ascii_letters) for _ in xrange(10))


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


def chat_socketio(io):
    def subscriber(io, channel):
        """Event loop which listens on a redis channel and sends anything
        received to the client JS."""
        try:
            redis_in = redis_client('chat')
            redis_in.subscribe(channel)
            redis_in_generator = redis_in.listen()

            # io.connected() never becomes false for some reason.
            while io.connected():
                for from_redis in redis_in_generator:
                    log.debug('Incoming: %s' % from_redis)

                    # This check for 'message' is for redis's idea of a
                    # message, not our chat 'message':
                    if from_redis['type'] == 'message':
                        # Incoming data should always be valid JSON, as it is
                        # checked before being put into redis.
                        out = json.loads(from_redis['data'])
                        out['room'] = channel
                        io.send(json.dumps(out))  # Just send it verbatim.
                    # Else it's a subscription notice.
        finally:
            log.debug('EXIT SUBSCRIBER %s' % io.session)

    if io.on_connect():
        log.debug('CONNECT %s' % io.session)
    else:
        # I haven't nailed down when this happens yet. It might happen when
        # websockets are enabled and we hit the server with FF 7.
        log.debug('SOMETHING OTHER THAN CONNECT!')

    # Hanging onto these greenlets might keep them from the GC:
    subscribers = []

    # Until the client disconnects, listen for input from the user:
    for from_client in _messages_while_connected(io):
        # TODO: Think about how to dissuade people from sending messages to
        # rooms they're not in, whether by keeping a redis hash of what rooms
        # they're in, doing capability-based access control, or something else.
        kind = from_client.get('kind')
        if kind == 'say':
            room = from_client.get('room')
            message = from_client.get('message')
            if room and message:  # else drop it on the floor
                redis_client('chat').publish(room, json.dumps(
                    {'kind': 'say',
                     'message': message}))
        elif kind == 'join':
            # Start a new subscriber. At least as a starting point, we start a
            # new subscriber for each room you're in, because otherwise there
            # would be a mess of de-duping as we fight with the race of killing
            # the old subscriber and starting a new one that listens to all
            # joined rooms.
            room = from_client.get('room')
            if room:
                subscribers.append(Greenlet.spawn(subscriber, io, room))

    log.debug('EXIT %s' % io.session)

    # Each time I close the 2nd chat window, wait for the old socketio() view
    # to exit, and then reopen the chat page, the number of Incomings increases
    # by one. The subscribers are never exiting. This fixes that behavior:
    for s in subscribers:
        s.kill()

    return HttpResponse()
