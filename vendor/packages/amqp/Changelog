Changes
=======

py-amqp is fork of amqplib used by Kombu containing additional features and improvements.
The previous amqplib changelog is here:
http://code.google.com/p/py-amqplib/source/browse/CHANGES

.. _version-1.4.2:

1.4.2
=====
:release-date: 2014-01-23 05:00 P.M UTC

- Heartbeat negotiation would use heartbeat value from server even
  if heartbeat disabled (Issue #31).

.. _version-1.4.1:

1.4.1
=====
:release-date: 2014-01-14 09:30 P.M UTC

- Fixed error occurring when heartbeats disabled.

.. _version-1.4.0:

1.4.0
=====
:release-date: 2014-01-13 03:00 P.M UTC

- Heartbeat implementation improved (Issue #6).

    The new heartbeat behavior is the same approach as taken by the
    RabbitMQ java library.

    This also means that clients should preferably call the ``heartbeat_tick``
    method more frequently (like every second) instead of using the old
    ``rate`` argument (which is now ignored).

    - Heartbeat interval is negotiated with the server.
    - Some delay is allowed if the heartbeat is late.
    - Monotonic time is used to keep track of the heartbeat
      instead of relying on the caller to call the checking function
      at the right time.

    Contributed by Dustin J. Mitchell.

- NoneType is now supported in tables and arrays.

    Contributed by Dominik Fässler.

- SSLTransport: Now handles ``ENOENT``.

    Fix contributed by Adrien Guinet.

.. _version-1.3.3:

1.3.3
=====
:release-date: 2013-11-11 03:30 P.M UTC

- SSLTransport: Now keeps read buffer if an exception is raised
  (Issue #26).

    Fix contributed by Tommie Gannert.

.. _version-1.3.2:

1.3.2
=====
:release-date: 2013-10-29 02:00 P.M UTC

- Message.channel is now a channel object (not the channel id).

- Bug in previous version caused the socket to be flagged as disconnected
  at EAGAIN/EINTR.

.. _version-1.3.1:

1.3.1
=====
:release-date: 2013-10-24 04:00 P.M UTC

- Now implements Connection.connected (Issue #22).

- Fixed bug where ``str(AMQPError)`` did not return string.

.. _version-1.3.0:

1.3.0
=====
:release-date: 2013-09-04 02:39 P.M UTC

- Now sets ``Message.channel`` on delivery (Issue #12)

    amqplib used to make the channel object available
    as ``Message.delivery_info['channel']``, but this was removed
    in py-amqp.  librabbitmq sets ``Message.channel``,
    which is a more reasonable solution in our opinion as that
    keeps the delivery info intact.

- New option to wait for publish confirmations (Issue #3)

    There is now a new Connection ``confirm_publish`` that will
    force any ``basic_publish`` call to wait for confirmation.

    Enabling publisher confirms like this degrades performance
    considerably, but can be suitable for some applications
    and now it's possible by configuration.

- ``queue_declare`` now returns named tuple of type
  :class:`~amqp.protocol.basic_declare_ok_t`.

    Supporting fields: ``queue``, ``message_count``, and
    ``consumer_count``.

- Contents of ``Channel.returned_messages`` is now named tuples.

    Supporting fields: ``reply_code``, ``reply_text``, ``exchange``,
    ``routing_key``, and ``message``.

- Sockets now set to close on exec using the ``FD_CLOEXEC`` flag.

    Currently only supported on platforms supporting this flag,
    which does not include Windows.

    Contributed by Tommie Gannert.

.. _version-1.2.1:

1.2.1
=====
:release-date: 2013-08-16 05:30 P.M UTC

- Adds promise type: :meth:`amqp.utils.promise`

- Merges fixes from 1.0.x

.. _version-1.2.0:

1.2.0
=====
:release-date: 2012-11-12 04:00 P.M UTC

- New exception hierarchy:

    - :class:`~amqp.AMQPError`
        - :class:`~amqp.ConnectionError`
            - :class:`~amqp.RecoverableConnectionError`
                - :class:`~amqp.ConsumerCancelled`
                - :class:`~amqp.ConnectionForced`
                - :class:`~amqp.ResourceError`
            - :class:`~IrrecoverableConnectionError`
                - :class:`~amqp.ChannelNotOpen`
                - :class:`~amqp.FrameError`
                - :class:`~amqp.FrameSyntaxError`
                - :class:`~amqp.InvalidCommand`
                - :class:`~amqp.InvalidPath`
                - :class:`~amqp.NotAllowed`
                - :class:`~amqp.UnexpectedFrame`
                - :class:`~amqp.AMQPNotImplementedError`
                - :class:`~amqp.InternalError`
        - :class:`~amqp.ChannelError`
            - :class:`~RecoverableChannelError`
                - :class:`~amqp.ContentTooLarge`
                - :class:`~amqp.NoConsumers`
                - :class:`~amqp.ResourceLocked`
            - :class:`~IrrecoverableChannelError`
                - :class:`~amqp.AccessRefused`
                - :class:`~amqp.NotFound`
                - :class:`~amqp.PreconditionFailed`


.. _version-1.1.0:

1.1.0
=====
:release-date: 2012-11-08 10:36 P.M UTC

- No longer supports Python 2.5

- Fixed receiving of float table values.

- Now Supports Python 3 and Python 2.6+ in the same source code.

- Python 3 related fixes.

.. _version-1.0.13:

1.0.13
======
:release-date: 2013-07-31 04:00 P.M BST

- Fixed problems with the SSL transport (Issue #15).

    Fix contributed by Adrien Guinet.

- Small optimizations

.. _version-1.0.12:

1.0.12
======
:release-date: 2013-06-25 02:00 P.M BST

- Fixed another Python 3 compatibility problem.

.. _version-1.0.11:

1.0.11
======
:release-date: 2013-04-11 06:00 P.M BST

- Fixed Python 3 incompatibility in ``amqp/transport.py``.

.. _version-1.0.10:

1.0.10
======
:release-date: 2013-03-21 03:30 P.M UTC

- Fixed Python 3 incompatibility in ``amqp/serialization.py``.
  (Issue #11).

.. _version-1.0.9:

1.0.9
=====
:release-date: 2013-03-08 10:40 A.M UTC

- Publisher ack callbacks should now work after typo fix (Issue #9).

- ``channel(explicit_id)`` will now claim that id from the array
  of unused channel ids.

- Fixes Jython compatibility.

.. _version-1.0.8:

1.0.8
=====
:release-date: 2013-02-08 01:00 P.M UTC

- Fixed SyntaxError on Python 2.5

.. _version-1.0.7:

1.0.7
=====
:release-date: 2013-02-08 01:00 P.M UTC

- Workaround for bug on some Python 2.5 installations where (2**32) is 0.

- Can now serialize the ARRAY type.

    Contributed by Adam Wentz.

- Fixed tuple format bug in exception (Issue #4).

.. _version-1.0.6:

1.0.6
=====
:release-date: 2012-11-29 01:14 P.M UTC

- ``Channel.close`` is now ignored if the connection attribute is None.

.. _version-1.0.5:

1.0.5
=====
:release-date: 2012-11-21 04:00 P.M UTC

- ``Channel.basic_cancel`` is now ignored if the channel was already closed.

- ``Channel.events`` is now a dict of sets::

    >>> channel.events['basic_return'].add(on_basic_return)
    >>> channel.events['basic_return'].discard(on_basic_return)

.. _version-1.0.4:

1.0.4
=====
:release-date: 2012-11-13 04:00 P.M UTC

- Fixes Python 2.5 support

.. _version-1.0.3:

1.0.3
=====
:release-date: 2012-11-12 04:00 P.M UTC

- Now can also handle float in headers/tables when receiving messages.

- Now uses :class:`array.array` to keep track of unused channel ids.

- The :data:`~amqp.exceptions.METHOD_NAME_MAP` has been updated for
  amqp/0.9.1 and Rabbit extensions.

- Removed a bunch of accidentally included images.

.. _version-1.0.2:

1.0.2
=====
:release-date: 2012-11-06 05:00 P.M UTC

- Now supports float values in headers/tables.

.. _version-1.0.1:

1.0.1
=====
:release-date: 2012-11-05 01:00 P.M UTC

- Connection errors no longer includes :exc:`AttributeError`.

- Fixed problem with using the SSL transport in a non-blocking context.

    Fix contributed by Mher Movsisyan.


.. _version-1.0.0:

1.0.0
=====
:release-date: 2012-11-05 01:00 P.M UTC

- Channels are now restored on channel error, so that the connection does not
  have to closed.

.. _version-0.9.4:

Version 0.9.4
=============

- Adds support for ``exchange_bind`` and ``exchange_unbind``.

    Contributed by Rumyana Neykova

- Fixed bugs in funtests and demo scripts.

    Contributed by Rumyana Neykova

.. _version-0.9.3:

Version 0.9.3
=============

- Fixed bug that could cause the consumer to crash when reading
  large message payloads asynchronously.

- Serialization error messages now include the invalid value.

.. _version-0.9.2:

Version 0.9.2
=============

- Consumer cancel notification support was broken (Issue #1)

    Fix contributed by Andrew Grangaard

.. _version-0.9.1:

Version 0.9.1
=============

- Supports draining events from multiple channels (``Connection.drain_events``)
- Support for timeouts
- Support for heartbeats
    - ``Connection.heartbeat_tick(rate=2)`` must called at regular intervals
      (half of the heartbeat value if rate is 2).
    - Or some other scheme by using ``Connection.send_heartbeat``.
- Supports RabbitMQ extensions:
    - Consumer Cancel Notifications
        - by default a cancel results in ``ChannelError`` being raised
        - but not if a ``on_cancel`` callback is passed to ``basic_consume``.
    - Publisher confirms
        - ``Channel.confirm_select()`` enables publisher confirms.
        - ``Channel.events['basic_ack'].append(my_callback)`` adds a callback
          to be called when a message is confirmed. This callback is then
          called with the signature ``(delivery_tag, multiple)``.
- Support for ``basic_return``
- Uses AMQP 0-9-1 instead of 0-8.
    - ``Channel.access_request`` and ``ticket`` arguments to methods
      **removed**.
    - Supports the ``arguments`` argument to ``basic_consume``.
    - ``internal`` argument to ``exchange_declare`` removed.
    - ``auto_delete`` argument to ``exchange_declare`` deprecated
    - ``insist`` argument to ``Connection`` removed.
    - ``Channel.alerts`` has been removed.
    - Support for ``Channel.basic_recover_async``.
    - ``Channel.basic_recover`` deprecated.
- Exceptions renamed to have idiomatic names:
    - ``AMQPException`` -> ``AMQPError``
    - ``AMQPConnectionException`` -> ConnectionError``
    - ``AMQPChannelException`` -> ChannelError``
    - ``Connection.known_hosts`` removed.
    - ``Connection`` no longer supports redirects.
    - ``exchange`` argument to ``queue_bind`` can now be empty
      to use the "default exchange".
- Adds ``Connection.is_alive`` that tries to detect
  whether the connection can still be used.
- Adds ``Connection.connection_errors`` and ``.channel_errors``,
  a list of recoverable errors.
- Exposes the underlying socket as ``Connection.sock``.
- Adds ``Channel.no_ack_consumers`` to keep track of consumer tags
  that set the no_ack flag.
- Slightly better at error recovery
