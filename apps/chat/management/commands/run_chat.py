from django.conf import settings
from django.core.handlers.wsgi import WSGIHandler
from django.core.cache import cache
from django.core.management.base import NoArgsCommand

from gevent import monkey
from socketio import SocketIOServer

class Command(NoArgsCommand):
    help = 'Start the chat server.'

    def handle_noargs(self, *args, **kwargs):
        """Turn this process into the chat server."""
        # Make blocking calls in socket lib non-blocking:
        monkey.patch_all()

        # Start up socketio stuff
        application = WSGIHandler()  # TODO: Probably overkill. We don't want to expose all kitsune's views, just the socketio-serving one.
        print 'Listening on http://127.0.0.1:%s and on port 843 (flash policy server)' % settings.CHAT_PORT
        SocketIOServer(('', settings.CHAT_PORT), application, resource='socket.io').serve_forever()


# class ChatConnection(tornadio.SocketConnection):
#     # Class level variable
#     participants = set()
# 
#     def on_open(self, request, *args, **kwargs):
#         nonce = kwargs['extra']
#         key = 'chatnonce:{n}'.format(n=nonce)
#         self.user = cache.get(key)
#         cache.delete(key)
#         self.participants.add(self)
#         self.send('Welcome to the room, {u}!'.format(u=self.user.username))
#         for p in self.participants:
#             p.send('<strong>{u}</strong> has joined the chatroom.'.format(
#                 u=self.user.username))
# 
#     def on_message(self, message):
#         for p in self.participants:
#             p.send('<strong>{u}</strong>: {m}'.format(
#                 u=self.user.username, m=message))
# 
#     def on_close(self):
#         self.participants.remove(self)
#         for p in self.participants:
#             p.send('<strong>{u}</strong> has left.'.format(
#                 u=self.user.username))
# 
