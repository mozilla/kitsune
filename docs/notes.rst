.. _notes-chapter:

===========
Other Notes
===========

Questions
=========

Troubleshooter Add-on
---------------------

When asking a question, users are prompted to install an addon that will return
extra information to SUMO from about:support. This is opt-in, and considered
generally non-sensitive data, but is not revelaed to all sites because of
fingerprinting concerns.

This add-on only provides data to white listed domains. The built in whitelist
is:

- https://support.mozilla.org/
- https://support.allizom.org/
- https://support-dev.allizom.org/
- http://localhost:8000/

Note that the protocol and port are significant. If you try and run the site on
http://localhost:8900/, the add-on will not provide any data.

The source of the addon is `on GitHub`_, and it is hosted `on
AMO`_. The add-on is hosted on AMO instead of SUMO so that AMO will do
the heavy lifting of providing automatic updates.

.. _on Github: https://github.com/0c0w3/troubleshooter
.. _on AMO: https://addons.mozilla.org/en-US/firefox/addon/troubleshooter/
