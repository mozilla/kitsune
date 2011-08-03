"""No actual Django models, but some generic ones"""

import json
import random

from django.contrib.auth.models import AnonymousUser, User

from gevent import Greenlet

from chat import log, redis, nonce_key


class NamedAnonymousUser(AnonymousUser):
    """A user not mapped to a known persistent user but having a name for
    display purposes"""
    def __init__(self, username):
        self.username = username


class RoomsUserIsIn(object):
    """A collection of rooms a user is listening to (and able to talk to).

    This is the model, and the socketio view is the controller.

    About the protocol:

        There are several kinds of message which go flitting between the
        clients and server. Each message is a JSON dict having the keys listed
        below:

        Join. Sent from the client to the server.
            kind: join
            room: ID of the room to join
            user: Username of user joining (sent toward client only)

        Leave. Sent in both directions.
            kind: leave
            room: ID of the room
            user: Username of user leaving (sent toward client only)

        Say. Sent in both directions.
            kind: say
            room: ID of the room
            message: What was said
            user: Username of user speaking (sent toward client only)

        Nonce. Identify the user to the server by sending a nonce value.
            kind: nonce
            nonce: the nonce

    There's no facility for private messages yet, but it can be added if
    needed. At the moment, the plan is to implement private help sessions by
    first creating a public room behind the scenes. That will allow additional
    moderators to steal into the room undetected.

    """
    def __init__(self):
        # Hanging onto these greenlets might keep them from the GC:
        self._subscribers = {}  # room -> subscriber greenlet

        # Start anonymous. JS will immediately authenticate and fix that if the
        # user is logged in.
        self._user = NamedAnonymousUser(self._random_nick())

    def __contains__(self, room):
        return room in self._subscribers

    def _random_nick(self):
        """Return a fun random name to distinguish anonymous users memorably.

        This will go away once we get UI for entering a name.

        """
        syllables = ['nox', 'frot', 'gos', 'ler', 'jam', 'rip', 'kap']
        return ''.join(random.choice(syllables) for _ in xrange(3))

    def _send(self, room, **kwargs):
        """Throw a JSON-coded message (from kwargs) at a room.

        ...regardless of whether you're in the room.

        """
        redis().publish(room, json.dumps(kwargs))

    def join(self, room, io):
        """Start listening to a room."""
        if room not in self:  # No joining a room twice.
            # Start a new subscriber. At least as a starting point, we start a
            # new subscriber for each room you're in, because otherwise there
            # would be a mess of de-duping as we fight with the race of killing
            # the old subscriber and starting a new one that listens to all
            # joined rooms.
            self._subscribers[room] = Greenlet.spawn(
                self._subscriber, io, room)
            self._send(room, kind='join', user=self._user.username)

    def leave(self, room):
        """Announce the user is leaving a room, and stop subscribing to it."""
        if room in self:  # No leaving rooms you're not in.
            # Each time I close the 2nd chat window, wait for the old
            # socketio() view to exit, and then reopen the chat page, the
            # number of Incomings increases by one. The subscribers are never
            # exiting. kill() fixes that behavior:
            self._subscribers[room].kill()
            del self._subscribers[room]
            self._send(room, kind='leave', user=self._user.username)

    def leave_all(self):
        """Leave all rooms."""
        # Can't use iterkeys(): _leave_rooms() mutates subscribers.
        for room in self._subscribers.keys():
            self.leave(room)

    def identify(self, nonce):
        """Identify the person on the client end as a specific Django user.

        We don't want anybody to be able to impersonate anybody else in a chat.
        Thus, we have to map a socketio SID to a user. To do that, we have to
        map a socketio SID to a user. So, when we draw the chat page, we make
        up a nonce and stick it in there, while simultaneously mapping it to
        the user ID in redis for a short time. The JS yanks the nonce out of
        the page and sends it back to the server on join, along with the
        socketio SID (implicitly), thus completing the SID-to-user mapping.
        And, because we avoid sticking the session ID in the page, we avoid the
        possibility of session hijacking by any JS that gets injected by an XSS
        attack; cookies are protected from evil JS better (through HttpOnly,
        for example).

        """
        user_id = redis().get(nonce_key(nonce))
        if user_id:
            try:
                self._user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                # Just stay anonymous.
                log.warning('Got an expired or bogus nonce: %s' % nonce)
            else:
                log.debug('Mapped nonce to %s.' % self._user.username)

    def say(self, room, message):
        """Say something in a room you're in."""
        if room in self:
            self._send(room, kind='say',
                             message=message,
                             user=self._user.username)
        else:
            log.warning("%s said something in a room he wasn't in." %
                        self._user.username)

    @staticmethod
    def _subscriber(io, channel):
        """Event loop which listens on a redis channel and sends anything
        received to the client JS."""
        try:
            redis_in = redis()
            redis_in.subscribe(channel)
            redis_in_generator = redis_in.listen()

            # io.connected() never becomes false for some reason.
            while io.connected():
                for from_redis in redis_in_generator:
                    log.debug('Incoming: %s' % from_redis)

                    # This check for 'message' is for redis's idea of a
                    # message, not our chat 'message':
                    if from_redis['type'] == 'message':
                        # Incoming data should always be valid, as it is checked
                        # before being put into redis. It also happens to be in the
                        # same format the JS expects. Just add the room to it, and
                        # ship it out:
                        out = json.loads(from_redis['data'])
                        out['room'] = channel
                        io.send(json.dumps(out))
        finally:
            log.debug('EXIT SUBSCRIBER %s' % io.session)
