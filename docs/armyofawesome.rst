.. _armyofawesome-chapter:

===============
Army of Awesome
===============


Setting up the Army of Awesome Twitter Application
==================================================


Create the Twitter application
------------------------------

Go to https://dev.twitter.com/apps/new and fill in the required fields.
Also be sure to fill in a Callback URL, it can be any dummy URL as we
override this value by passing in an oauth_callback URL. Set up the
application for read-write access.

You will need to enter the consumer key and consumer secret in
settings_local.py below.


Update settings_local.py
------------------------

Set the following settings in ``kitsune/settings_local.py``::

    TWITTER_CONSUMER_KEY = <consumer key>
    TWITTER_CONSUMER_SECRET = <consumer secret>
    TWITTER_COOKIE_SECURE = False


Fetch tweets
============

To fetch tweets, run::

    $ ./manage.py cron collect_tweets


You should now see tweets at /army-of-awesome.


Common replies
==============

Common replies should be defined in a wiki article with slug
'army-of-awesome-common-replies'. The format for the article
content is::

    =Category 1=

    ==Reply 1==
    Reply goes here http://example.com/kb-article

    ==Reply 2==
    Another reply here

    =Category 2=
    ==Reply 3==
    And another reply


Note that replies can't be over 140 characters long, including the
@username and #fxhelp hash tag. Therefore, each reply defined here
should not go over 125 characters. The reply must be plain text
without any HTML or wiki syntax.
