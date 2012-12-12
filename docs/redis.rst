.. _redis-chapter:

=====
Redis
=====

This covers installing `Redis <http://redis.io/>`_.


Installation
============

Install Redis on your machine.

There are three ``.conf`` files in ``configs/redis/``.  One is for
testing and is used in ``settings_test.py``.  The other two are used
for the sections in ``REDIS_BACKEND``.

There are two ways to set this up. First is to set it up using the
configuration below and run three separate Redis servers. The second
is to set it up differently, tweak the settings in
``settings_local.py`` accordingly, and run Redis using just the test
configuration.


Configuration
=============

If you want to run three separate Redis servers, add this to
``settings_local.py``::

    REDIS_BACKENDS = {
            'default': 'redis://localhost:6379?socket_timeout=0.5&db=0',
            'karma': 'redis://localhost:6381?socket_timeout=0.5&db=0',
            'helpfulvotes': 'redis://localhost:6379?socket_timeout=0.\
                5&db=1',
        }

    REDIS_BACKEND = REDIS_BACKENDS['default']


Otherwise adjust the above accordingly.


Running redis
=============

Running redis
-------------

This script runs all three servers---one for each configuration.

I (Will) put that in a script that creates the needed directories in
``/var/redis/`` and kicks off the three redis servers::

    #!/bin/bash

    set -e

    # Adjust these according to your setup!
    REDISBIN=/usr/bin/redis-server
    CONFFILE=/path/to/conf/files/

    if test ! -e /var/redis/sumo/
    then
        echo "creating /var/redis/sumo/"
        mkdir -p /var/redis/sumo/
    fi

    if test ! -e /var/redis/sumo-test/
    then
        echo "creating /var/redis/sumo-test/"
        mkdir -p /var/redis/sumo-test/
    fi

    if test ! -e /var/redis/sumo-persistent/
    then
        echo "creating /var/redis/sumo-persistent/"
        mkdir -p /var/redis/sumo-persistent/
    fi

    $REDISBIN $CONFFILE/redis-persistent.conf
    $REDISBIN $CONFFILE/redis-test.conf
    $REDISBIN $CONFFILE/redis-volatile.conf
