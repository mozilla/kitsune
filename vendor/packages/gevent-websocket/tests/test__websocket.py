# Websocket tests by Jeffrey Gelens, Copyright 2010, Noppo.pro
# Socket related functions by:
#
# @author Donovan Preston
#
# Copyright (c) 2007, Linden Research, Inc.
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
from gevent import monkey
monkey.patch_all(thread=False)

import sys
import greentest
import gevent
from gevent import socket
from geventwebsocket.handler import WebSocketHandler


CONTENT_LENGTH = 'Content-Length'
CONN_ABORTED_ERRORS = []
DEBUG = '-v' in sys.argv

try:
    from errno import WSAECONNABORTED
    CONN_ABORTED_ERRORS.append(WSAECONNABORTED)
except ImportError:
    pass


class ConnectionClosed(Exception):
    pass


def read_headers(fd):
    response_line = fd.readline()
    if not response_line:
        raise ConnectionClosed
    headers = {}
    while True:
        line = fd.readline().strip()
        if not line:
            break
        try:
            key, value = line.split(': ', 1)
        except:
            print 'Failed to split: %r' % (line, )
            raise
        assert key.lower() not in [x.lower() for x in headers.keys()], 'Header %r:%r sent more than once: %r' % (key, value, headers)
        headers[key] = value
    return response_line, headers


def iread_chunks(fd):
    while True:
        line = fd.readline()
        chunk_size = line.strip()
        try:
            chunk_size = int(chunk_size, 16)
        except:
            print 'Failed to parse chunk size: %r' % line
            raise
        if chunk_size == 0:
            crlf = fd.read(2)
            assert crlf == '\r\n', repr(crlf)
            break
        data = fd.read(chunk_size)
        yield data
        crlf = fd.read(2)
        assert crlf == '\r\n', repr(crlf)


class Response(object):

    def __init__(self, status_line, headers, body=None, chunks=None):
        self.status_line = status_line
        self.headers = headers
        self.body = body
        self.chunks = chunks
        try:
            version, code, self.reason = status_line[:-2].split(' ', 2)
        except Exception:
            print 'Error: %r' % status_line
            raise
        self.code = int(code)
        HTTP, self.version = version.split('/')
        assert HTTP == 'HTTP', repr(HTTP)
        assert self.version in ('1.0', '1.1'), repr(self.version)

    def __iter__(self):
        yield self.status_line
        yield self.headers
        yield self.body

    def __str__(self):
        args = (self.__class__.__name__, self.status_line, self.headers, self.body, self.chunks)
        return '<%s status_line=%r headers=%r body=%r chunks=%r>' % args

    def assertCode(self, code):
        if hasattr(code, '__contains__'):
            assert self.code in code, 'Unexpected code: %r (expected %r)\n%s' % (self.code, code, self)
        else:
            assert self.code == code, 'Unexpected code: %r (expected %r)\n%s' % (self.code, code, self)

    def assertReason(self, reason):
        assert self.reason == reason, 'Unexpected reason: %r (expected %r)\n%s' % (self.reason, reason, self)

    def assertVersion(self, version):
        assert self.version == version, 'Unexpected version: %r (expected %r)\n%s' % (self.version, version, self)

    def assertHeader(self, header, value):
        real_value = self.headers.get(header)
        assert real_value == value, \
               'Unexpected header %r: %r (expected %r)\n%s' % (header, real_value, value, self)

    def assertBody(self, body):
        assert self.body == body, \
               'Unexpected body: %r (expected %r)\n%s' % (self.body, body, self)

    @classmethod
    def read(cls, fd, code=200, reason='default', version='1.1', body=None):
        _status_line, headers = read_headers(fd)
        self = cls(_status_line, headers)
        if code is not None:
            self.assertCode(code)
        if reason == 'default':
            reason = {200: 'OK'}.get(code)
        if reason is not None:
            self.assertReason(reason)
        if version is not None:
            self.assertVersion(version)
        if self.code == 100:
            return self
        try:
            if 'chunked' in headers.get('Transfer-Encoding', ''):
                if CONTENT_LENGTH in headers:
                    print "WARNING: server used chunked transfer-encoding despite having Content-Length header (libevent 1.x's bug)"
                self.chunks = list(iread_chunks(fd))
                self.body = ''.join(self.chunks)
            elif CONTENT_LENGTH in headers:
                num = int(headers[CONTENT_LENGTH])
                self.body = fd.read(num)
            #else:
            #    self.body = fd.read(16)
        except:
            print 'Response.read failed to read the body:\n%s' % self
            raise
        if body is not None:
            self.assertBody(body)
        return self

read_http = Response.read


class DebugFileObject(object):

    def __init__(self, obj):
        self.obj = obj

    def read(self, *args):
        result = self.obj.read(*args)
        if DEBUG:
            print repr(result)
        return result

    def readline(self, *args):
        result = self.obj.readline(*args)
        if DEBUG:
            print repr(result)
        return result

    def __getattr__(self, item):
        assert item != 'obj'
        return getattr(self.obj, item)


def makefile(self, mode='r', bufsize=-1):
    return DebugFileObject(socket._fileobject(self.dup(), mode, bufsize))

socket.socket.makefile = makefile

class TestCase(greentest.TestCase):
    __timeout__ = 5

    def get_wsgi_module(self):
        from gevent import pywsgi
        return pywsgi

    def init_server(self, application):
        self.server = self.get_wsgi_module().WSGIServer(('127.0.0.1', 0),
            application, handler_class=WebSocketHandler)

    def setUp(self):
        application = self.application
        self.init_server(application)
        self.server.start()
        self.port = self.server.server_port
        greentest.TestCase.setUp(self)


    def tearDown(self):
        greentest.TestCase.tearDown(self)
        timeout = gevent.Timeout.start_new(0.5)
        try:
            self.server.stop()
        finally:
            timeout.cancel()

    def connect(self):
        return socket.create_connection(('127.0.0.1', self.port))


class TestWebSocket(TestCase):
    message = "\x00Hello world\xff"

    def application(self, environ, start_response):
        if environ['PATH_INFO'] == "/echo":
            try:
                ws = environ['wsgi.websocket']
            except KeyError:
                start_response("400 Bad Request", [])
                return []

            while True:
                message = ws.wait()
                if message is None:
                    break
                ws.send(message)

            return []

    def test_basic(self):
        fd = self.connect().makefile(bufsize=1)
        headers = "" \
        "GET /echo HTTP/1.1\r\n" \
        "Host: localhost\r\n" \
        "Connection: Upgrade\r\n" \
        "Sec-WebSocket-Key2: 12998 5 Y3 1  .P00\r\n" \
        "Sec-WebSocket-Protocol: test\r\n" \
        "Upgrade: WebSocket\r\n" \
        "Sec-WebSocket-Key1: 4 @1  46546xW%0l 1 5\r\n" \
        "Origin: http://localhost\r\n\r\n" \
        "^n:ds[4U"

        fd.write(headers)

        response = read_http(fd, code=101, reason="Web Socket Protocol Handshake")
        response.assertHeader("Upgrade", "WebSocket")
        response.assertHeader("Connection", "Upgrade")
        response.assertHeader("Sec-WebSocket-Origin", "http://localhost")
        response.assertHeader("Sec-WebSocket-Location", "ws://localhost/echo")
        response.assertHeader("Sec-WebSocket-Protocol", "test")
        assert fd.read(16) == "8jKS'y:G*Co,Wxa-"

        fd.write(self.message)
        message = fd.read(len(self.message))
        assert message == self.message, \
               'Unexpected message: %r (expected %r)\n%s' % (message, self.message, self)

        fd.close()

    def test_10000_messages(self):
        fd = self.connect().makefile(bufsize=1)
        headers = "" \
        "GET /echo HTTP/1.1\r\n" \
        "Host: localhost\r\n" \
        "Connection: Upgrade\r\n" \
        "Sec-WebSocket-Key2: 12998 5 Y3 1  .P00\r\n" \
        "Sec-WebSocket-Protocol: test\r\n" \
        "Upgrade: WebSocket\r\n" \
        "Sec-WebSocket-Key1: 4 @1  46546xW%0l 1 5\r\n" \
        "Origin: http://localhost\r\n\r\n" \
        "^n:ds[4U"

        fd.write(headers)

        response = read_http(fd, code=101, reason="Web Socket Protocol Handshake")
        response.assertHeader("Upgrade", "WebSocket")
        response.assertHeader("Connection", "Upgrade")
        response.assertHeader("Sec-WebSocket-Origin", "http://localhost")
        response.assertHeader("Sec-WebSocket-Location", "ws://localhost/echo")
        response.assertHeader("Sec-WebSocket-Protocol", "test")
        assert fd.read(16) == "8jKS'y:G*Co,Wxa-"

        for i in xrange(10000):
            fd.write(self.message)
            message = fd.read(len(self.message))

            assert message == self.message, \
                   'Unexpected message: %r (expected %r)\n%s' % (message, self.message, self)


        fd.close()

    def test_badrequest(self):
        fd = self.connect().makefile(bufsize=1)
        fd.write('GET /echo HTTP/1.1\r\nHost: localhost\r\n\r\n')
        read_http(fd, code=400, reason='Bad Request')
        fd.close()

    def test_oldprotocol_version(self):
        fd = self.connect().makefile(bufsize=1)
        headers = "" \
        "GET /echo HTTP/1.1\r\n" \
        "Host: localhost\r\n" \
        "Connection: Upgrade\r\n" \
        "Sec-WebSocket-Protocol: test\r\n" \
        "Upgrade: WebSocket\r\n" \
        "Sec-WebSocket-Key1: 4 @1  46546xW%0l 1 5\r\n" \
        "Origin: http://localhost\r\n\r\n" \
        "^n:ds[4U"

        fd.write(headers)
        read_http(fd, code=400, reason='Bad Request',
            body='Client using old/invalid protocol implementation')

        fd.close()

    def test_protocol_version75(self):
        fd = self.connect().makefile(bufsize=1)
        headers = "" \
        "GET /echo HTTP/1.1\r\n" \
        "Host: localhost\r\n" \
        "Connection: Upgrade\r\n" \
        "WebSocket-Protocol: sample\r\n" \
        "Upgrade: WebSocket\r\n" \
        "Origin: http://example.com\r\n\r\n"

        fd.write(headers)
        response = read_http(fd, code=101, reason="Web Socket Protocol Handshake")

        fd.write(self.message)
        message = fd.read(len(self.message))
        assert message == self.message, \
               'Unexpected message: %r (expected %r)\n%s' % (message, self.message, self)

        fd.close()

if __name__ == '__main__':
    greentest.main()
