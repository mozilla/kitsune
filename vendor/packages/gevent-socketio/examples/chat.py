import traceback
from gevent import monkey; monkey.patch_all()
from socketio import SocketIOServer


class Application(object):
    def __init__(self):
        self.buffer = []

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO'].strip('/')
        print path, start_response

        if not path:
            start_response('200 OK', [('Content-Type', 'text/html')])
            return ['<h1>Welcome. Try the <a href="/chat.html">chat</a> example.</h1>']

        if path in ['json.js', 'chat.html']:
            try:
                data = open(path).read()
            except Exception:
                traceback.print_exc()
                return not_found(start_response)
            start_response('200 OK', [('Content-Type', 'text/javascript' if path.endswith('.js') else 'text/html')])
            return [data]

        if path.startswith("socket.io"):
            socketio = environ['socketio']
            if socketio.on_connect():
                socketio.send({'buffer': self.buffer})
                socketio.broadcast({'announcement': socketio.session.session_id + ' connected'})

            while True:
                message = socketio.recv()

                if len(message) == 1:
                    message = message[0]
                    message = {'message': [socketio.session.session_id, message]}
                    self.buffer.append(message)
                    if len(self.buffer) > 15:
                        del self.buffer[0]
                    socketio.broadcast(message)
                else:
                    if not socketio.connected():
                        socketio.broadcast({'announcement': socketio.session.session_id + ' disconnected'})

            return []

        else:
            return not_found(start_response)


def not_found(start_response):
    start_response('404 Not Found', [])
    return ['<h1>Not Found</h1>']


if __name__ == '__main__':
    print 'Listening on port 8080 and on port 843 (flash policy server)'
    SocketIOServer(('', 8080), Application(), resource="socket.io").serve_forever()
