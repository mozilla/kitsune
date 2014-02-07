#!/usr/bin/env python
"""
Test AMQP library.

Repeatedly receive messages from the demo_send.py
script, until it receives a message with 'quit' as the body.

2007-11-11 Barry Pederson <bp@barryp.org>

"""
from optparse import OptionParser
from functools import partial

import amqp


def callback(channel, msg):
    for key, val in msg.properties.items():
        print('%s: %s' % (key, str(val)))
    for key, val in msg.delivery_info.items():
        print('> %s: %s' % (key, str(val)))

    print('')
    print(msg.body)
    print('-------')
    print(msg.delivery_tag)
    channel.basic_ack(msg.delivery_tag)

    #
    # Cancel this callback
    #
    if msg.body == 'quit':
        channel.basic_cancel(msg.consumer_tag)


def main():
    parser = OptionParser()
    parser.add_option(
        '--host', dest='host',
        help='AMQP server to connect to (default: %default)',
        default='localhost',
    )
    parser.add_option(
        '-u', '--userid', dest='userid',
        help='userid to authenticate as (default: %default)',
        default='guest',
    )
    parser.add_option(
        '-p', '--password', dest='password',
        help='password to authenticate with (default: %default)',
        default='guest',
    )
    parser.add_option(
        '--ssl', dest='ssl', action='store_true',
        help='Enable SSL (default: not enabled)',
        default=False,
    )

    options, args = parser.parse_args()

    conn = amqp.Connection(options.host, userid=options.userid,
                           password=options.password, ssl=options.ssl)

    ch = conn.channel()

    ch.exchange_declare('myfan', 'fanout')
    qname, _, _ = ch.queue_declare()
    ch.queue_bind(qname, 'myfan')
    ch.basic_consume(qname, callback=partial(callback, ch))

    #pyamqp://

    #
    # Loop as long as the channel has callbacks registered
    #
    while ch.callbacks:
        ch.wait()

    ch.close()
    conn.close()

if __name__ == '__main__':
    main()
