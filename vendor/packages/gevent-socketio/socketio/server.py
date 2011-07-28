import sys
import random
import traceback
import gevent
from socket import error

from gevent.pywsgi import WSGIServer
from gevent.queue import Queue
from gevent.event import Event
from socketio.protocol import SocketIOProtocol
from socketio.handler import SocketIOHandler
from socketio.policyserver import FlashPolicyServer


__all__ = ['SocketIOServer']

class SocketIOServer(WSGIServer):
    """A WSGI Server with a resource that acts like an SocketIO."""

    def __init__(self, *args, **kwargs):
        self.sessions = {}
        self.resource = kwargs.pop('resource')
        if kwargs.pop('policy_server', True):
            self.policy_server = FlashPolicyServer()
        else:
            self.policy_server = None
        kwargs['handler_class'] = SocketIOHandler
        super(SocketIOServer, self).__init__(*args, **kwargs)

    def start_accepting(self):
        if self.policy_server is not None:
            try:
                self.policy_server.start()
            except error, ex:
                sys.stderr.write('FAILED to start flash policy server: %s\n' % (ex, ))
            except Exception:
                traceback.print_exc()
                sys.stderr.write('FAILED to start flash policy server.\n\n')
        super(SocketIOServer, self).start_accepting()

    def kill(self):
        if self.policy_server is not None:
            self.policy_server.kill()
        super(SocketIOServer, self).kill()

    def handle(self, socket, address):
        handler = self.handler_class(socket, address, self)
        self.set_environ({'socketio': SocketIOProtocol(handler)})
        handler.handle()

    def get_session(self, session_id=''):
        """Return an existing or new client Session."""

        session = self.sessions.get(session_id)

        if session is None:
            session = Session()
            self.sessions[session.session_id] = session
        else:
            session.incr_hits()

        return session


class Session(object):
    """
    Client session which checks the connection health and the queues for
    message passing.
    """

    def __init__(self):
        self.session_id = str(random.random())[2:]
        self.client_queue = Queue() # queue for messages to client
        self.server_queue = Queue() # queue for messages to server
        self.hits = 0
        self.heartbeats = 0
        self.connected = False
        self.timeout = Event()
        self.wsgi_app_greenlet = None

        def disconnect_timeout():
            self.timeout.clear()
            if self.timeout.wait(10.0):
                gevent.spawn(disconnect_timeout)
            else:
                self.kill()
        gevent.spawn(disconnect_timeout)

    def __str__(self):
        result = ['session_id=%r' % self.session_id]
        if self.connected:
            result.append('connected')
        if self.client_queue.qsize():
            result.append('client_queue[%s]' % self.client_queue.qsize())
        if self.server_queue.qsize():
            result.append('server_queue[%s]' % self.server_queue.qsize())
        if self.hits:
            result.append('hits=%s' % self.hits)
        if self.heartbeats:
            result.append('heartbeats=%s' % self.heartbeats)

        return ' '.join(result)

    def incr_hits(self):
        self.hits += 1

    def clear_disconnect_timeout(self):
        self.timeout.set()

    def heartbeat(self):
        self.heartbeats += 1
        return self.heartbeats

    def valid_heartbeat(self, counter):
        self.clear_disconnect_timeout()
        return self.heartbeats == counter

    def is_new(self):
        return self.hits == 0

    def kill(self):
        if self.connected:
            self.connected = False
            self.server_queue.put_nowait(None)
            self.client_queue.put_nowait(None)
        else:
            pass # Fail silently

    def put_server_msg(self, msg):
        self.clear_disconnect_timeout()
        self.server_queue.put_nowait(msg)

    def put_client_msg(self, msg):
        self.clear_disconnect_timeout()
        self.client_queue.put_nowait(msg)

    def get_client_msg(self, **kwargs):
        return self.client_queue.get(**kwargs)

    def get_server_msg(self, **kwargs):
        return self.server_queue.get(**kwargs)
