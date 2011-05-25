from os import path as op

from django.core.management.base import NoArgsCommand

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

    def on_open(self, *args, **kwargs):
        self.participants.add(self)
        self.send("Welcome!")

    def on_message(self, message):
        for p in self.participants:
            p.send(message)

    def on_close(self):
        self.participants.remove(self)
        for p in self.participants:
            p.send("A user has left.")


#use the routes classmethod to build the correct resource
ChatRouter = tornadio.get_router(ChatConnection)


#configure the Tornado application
application = tornado.web.Application(
    [ChatRouter.route()],
    enabled_protocols = ['websocket',
                         'xhr-multipart',
                         'xhr-polling'],
    socket_io_port = 3000
)
