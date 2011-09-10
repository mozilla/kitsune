================
gevent-websocket
================

`gevent-websocket`_ is a websocket library for the gevent_ networking library
written written and maintained by `Jeffrey Gelens`_ It is licensed under the BSD license.

Installation
------------------------

Install Python 2.4 or newer and gevent and its dependencies. The latest release
can be download from PyPi_ or by cloning the repository_.

Usage
-----

Native Gevent
^^^^^^^^^^^^^

At the moment gevent-websocket has one handler based on the Pywsgi gevent
server. Set the `handler_class` when creating a pywsgi server instance to make
use of the Websocket functionality:

::

    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler

    server = pywsgi.WSGIServer(('127.0.0.1', 8000), websocket_app,
        handler_class=WebSocketHandler)
    server.serve_forever()

Afterwards write a WSGI application with a 3rd parameter, namely a websocket instance:

::

    def websocket_app(environ, start_response):
        if environ["PATH_INFO"] == '/echo':
            ws = environ["wsgi.websocket"]
            message = ws.wait()
            ws.send(message)

Gunicorn
^^^^^^^^

Using Gunicorn it is even more easy to start a server. Only the
websocket_app from the previous example is required to start the server.
Start Gunicorn using the following command and worker class:

::

    gunicorn -k "geventwebsocket.gunicorn.workers.GeventWebSocketWorker" gunicorn_websocket:websocket_app

.. _gevent-websocket: http://www.bitbucket.org/Jeffrey/gevent-websocket/
.. _gevent: http://www.gevent.org/
.. _Jeffrey Gelens: http://www.gelens.org/
.. _PyPi: http://pypi.python.org/pypi/gevent-websocket/
.. _repository: http://www.bitbucket.org/Jeffrey/gevent-websocket/
