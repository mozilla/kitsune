.. _notes-chapter:

===========
Other Notes
===========

.. warning::
    This section of documentation may be outdated.

Questions
=========

about:support API
-----------------

The about:support API replaces the Troubleshooter Add-on and is available
starting in Firefox 35. To test this locally during development, you need
to run an ssl server and change some permissions in your browser.

To run the ssl server, first add sslserver to INSTALLED_APPS in
settings_local.py::

    INSTALLED_APPS = list(INSTALLED_APPS) + ['sslserver']

Run the ssl server::

    $ ./manage.py runsslserver

Then you need to run the following in the Browser Console::

    Services.perms.add(Services.io.newURI("https://localhost:8000", null, null), "remote-troubleshooting", Services.perms.ALLOW_ACTION);


.. Note::

	You need to Enable chrome debugging in developer console settings,
	so that you can access the browser console.

	See also https://developer.mozilla.org/en-US/docs/Tools/Browser_Console

memcached
---------

.. Note::

   This should probably be somewhere else, but the easy way to flush
   your cache is something like this::

       echo "flush_all" | nc localhost 11211


   Assuming you have memcache configured to listen to 11211.
