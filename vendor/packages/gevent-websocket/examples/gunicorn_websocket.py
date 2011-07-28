# -*- coding: utf-8 -
#
# gunicorn -k "geventwebsocket.gunicorn.workers.GeventWebSocketWorker" gunicorn_websocket:app

import gevent

# demo app
import os
import random
def app(environ, start_response):
    if environ['PATH_INFO'] == '/test':
        start_response("200 OK", [('Content-Type', 'text/plain')])
        return ["blaat"]
    elif environ['PATH_INFO'] == "/data":
        ws = environ['wsgi.websocket']
        for i in xrange(10000):
            ws.send("0 %s %s\n" % (i, random.random()))
            gevent.sleep(1)
    else:
        start_response("404 Not Found", [])
        return []

