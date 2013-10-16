.. _contributing:

Contributing to polib
=====================

You are very welcome to contribute to the project!
The bugtracker, wiki and mercurial repository can be found at the 
`project's page <http://bitbucket.org/izi/polib/>`_.

New releases are also published at the 
`cheeseshop <http://cheeseshop.python.org/pypi/polib/>`_.

How to contribute
~~~~~~~~~~~~~~~~~

There are various possibilities to get involved, for example you can:

* `Report bugs <http://www.bitbucket.org/izi/polib/issues/new/>`_
  preferably with patches if you can;
* Enhance this `documentation <http://www.bitbucket.org/izi/polib/src/tip/docs/>`_
* `Fork the code <http://www.bitbucket.org/izi/polib/>`_, implement new
  features, test and send a pull request

Running the test suite
~~~~~~~~~~~~~~~~~~~~~~

To run the tests, just type the following on a terminal::

    $ cd /path/to/polib/
    $ ./runtests.sh

If you want to generate coverage information::

    $ pip install coverage
    $ ./runtests.sh
    $ coverage html
