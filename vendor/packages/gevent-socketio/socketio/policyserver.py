from gevent.server import StreamServer

__all__ = ['FlashPolicyServer']


class FlashPolicyServer(StreamServer):
    policy = """<?xml version="1.0"?><!DOCTYPE cross-domain-policy SYSTEM "http://www.macromedia.com/xml/dtds/cross-domain-policy.dtd">
<cross-domain-policy><allow-access-from domain="*" to-ports="*"/></cross-domain-policy>"""

    def __init__(self, listener=None, backlog=None):
        if listener is None:
            listener = ('0.0.0.0', 843)
        StreamServer.__init__(self, listener=listener, backlog=backlog)

    def handle(self, socket, address):
        socket.sendall(self.policy)
