import random

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from gevent import Greenlet
import jingo
from redis import Redis

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
    return ''.join(random.choice('abcdefghijklmnopqrstuvwxyz234567')
                   for _ in xrange(10))


def socketio(request):
    io = request.environ['socketio']

    # Do some setup the first time:
    if io.on_connect():  # TODO: Always true? if it isn't, these symbols will be undefined.
        redis_in = redis_client('chat')  # non-blocking due to gevent monkeypatch of Python socket lib
        redis_in.subscribe('world')
        redis_in_generator = redis_in.listen()
        redis_out = redis_client('chat')
        redis_out.publish('world', io.session.session_id + ' connected')

    def subscriber(io, redis_in_generator):
        while True:
            for from_redis in redis_in_generator:
                print 'Incoming: %s' % from_redis
                if from_redis['type'] == 'message':  # There are also subscription notices.
                    io.send(from_redis['data'])
    in_greenlet = Greenlet.spawn(subscriber, io, redis_in_generator)  # TODO: Need to hang onto a ref to keep it from the GC?

    # Now run forever and service this long-term request?
    while True:
        message = io.recv()
        if message:  # Always a list of 0 or 1 strings, I deduce from the source code
            print 'Received nonzero message. Spawning publisher.'
            def publisher(to_redis):
                print 'Outgoing: %s' % to_redis
                redis_out.publish('world', to_redis)
            g = Greenlet.spawn(publisher, message[0])

    return HttpResponse()
