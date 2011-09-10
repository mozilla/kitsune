# Make blocking calls in socket lib non-blocking before anybody else grabs the
# socket lib:
from gevent import monkey
monkey.patch_all()

from django.conf import settings
from django.core.handlers.wsgi import WSGIHandler
from django.core.cache import cache
from django.core.management.base import NoArgsCommand

from socketio import SocketIOServer

from chat import log
from chat.views import socketio as chat_socketio


def application(environ, start_response):
    path = environ['PATH_INFO'].strip('/')
    if path.startswith('socket.io'):
        django_response = chat_socketio(environ['socketio'])

        # TODO: Do something rather than this stubbed-in 200:
        start_response('200 ok', [])  # What about cookies? Need 'em?
        return []
    else:
        start_response('404 Not Found', [])
        return ['<h1>Not Found</h1>']


class Command(NoArgsCommand):
    help = 'Start the chat server.'

    def handle_noargs(self, *args, **kwargs):
        """Turn this process into the chat server."""
        log.info('Listening on http://127.0.0.1:%s' % settings.CHAT_PORT)
        SocketIOServer(('', settings.CHAT_PORT),
                       application,
                       resource='socket.io',
                       policy_server=False).serve_forever()
