========
IRC Bots
========

Kitsune developers hang out in the ``#sumodev`` channel of Mozilla's IRC
network. We use a number of IRC bots to help disperse information via this
channel. Here are the important ones.


``firebot``
===========

``firebot`` (sometimes ``firewolfbot``) is a common fixture of Mozilla IRC
channels. He spits out information about bugs in Bugzilla. Just include the
word ``bug`` followed by a space and a number (e.g. ``bug 12345``, ``bug
624323``) and ``firebot`` will post some info about the bug and a link to
Bugzilla in the channel.

``firebot`` is also an InfoBot and does a lot of generic MozBot-type stuff.


``travis-ci``
=============

``travis-ci`` is the IRC notifier from `Travis <https://travis-ci.org/>`_.
He tells us about the status of our CI builds.


``kitsunebot``
==============

``kitsunebot`` is a `jig <https://github.com/jsocol/jig>`_ bot that acts as a
bridge between Github and Jenkins. (Yes, Github can trigger Jenkins builds
itself. No, it doesn't do it very well.) So far, she is very quiet, but we'd
like to make her more useful.

``kitsunebot`` filters commits by branch and triggers the correct Jenkins
build. She also announces changes in IRC, but only shows the full list of
changes committed for certain branches.


``qatestbot``
=============

``qatestbot`` tells us when the QA test suite fails and also allows us to
kick off QA test suite runs.

See :ref:`tests-chapter-qa-test-suite` for details.
