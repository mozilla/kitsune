from django.core.management.base import NoArgsCommand
from django.core.cache import cache

import tornado.web
import tornadio
import tornadio.router
import tornadio.server


class Command(NoArgsCommand):
    help = 'Start the chat server.'

    def handle_noargs(self, *args, **kwargs):
        """Turn this process into the chat server."""
        tornadio.server.SocketServer(application)


class ChatConnection(tornadio.SocketConnection):
    # Class level variable
    participants = set()

    def on_open(self, request, *args, **kwargs):
        nonce = kwargs['extra']
        key = 'chatnonce:{n}'.format(n=nonce)
        self.user = cache.get(key)
        cache.delete(key)
        self.participants.add(self)
        self.send('Welcome to the room, {u}!'.format(u=self.user.username))
        for p in self.participants:
            p.send('<strong>{u}</strong> has joined the chatroom.'.format(
                u=self.user.username))

    def on_message(self, message):
        for p in self.participants:
            p.send('<strong>{u}</strong>: {m}'.format(
                u=self.user.username, m=message))

    def on_close(self):
        self.participants.remove(self)
        for p in self.participants:
            p.send('<strong>{u}</strong> has left.'.format(
                u=self.user.username))


#use the routes classmethod to build the correct resource
ChatRouter = tornadio.get_router(ChatConnection, resource='chat',
                                 extra_re='\w+', extra_sep='/')
print ChatRouter.route()

#configure the Tornado application
application = tornado.web.Application(
    [ChatRouter.route()],
    enabled_protocols=[# 'websocket',
                       'xhr-multipart',
                       'xhr-polling'],
    socket_io_port=3000
)
