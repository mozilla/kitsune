.. _installation:

Installation guide
==================

Requirements
------------

polib requires python 2.5 or higher.


Installing polib
----------------

There are several ways to install polib:

* Automatically, via a package manager.
* Manually, by downloading a copy of the release package and
  installing it yourself.
* Manually, by performing a Mercurial checkout of the latest code.


Automatic installation via a package manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Several automatic package-installation tools are available for Python;
the most popular are `pip <http://pip.openplans.org/>`_ and `easy_install
<http://peak.telecommunity.com/DevCenter/EasyInstall>`_  .
Either can be used to install polib.

Using ``pip``, type::

    pip install polib

Using ``easy_install``, type::

    easy_install polib

It is also possible that your operating system distributor provides a
packaged version of polib. Consult your operating system's package list for
details, but be aware that third-party distributions may be providing older
versions of polib, and so you should consult the documentation which comes
with your operating system's package.


Manual installation from a downloaded package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you prefer not to use an automated package installer, you can download a
copy of polib and install it manually. The latest release package can be
downloaded from `polib's page on the Python Package Index
<http://pypi.python.org/pypi/polib/>`_.

Once you've downloaded the package, unpack it, this will create the directory
``polib-X-Y-Z``, which contains the ``setup.py`` installation script.
From a command line in that directory, type::

    python setup.py install

.. note::
    On some systems you may need to execute this with administrative 
    privileges (e.g., ``sudo python setup.py install``).


Manual installation from a Mercurial checkout
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you'd like to try out the latest in-development code, you can obtain it
from the polib repository, which is hosted at
`Bitbucket <http://bitbucket.org/>`_ and uses `Mercurial
<http://www.selenic.com/mercurial/wiki/>`_ for version control.

To obtain the latest code and documentation, you'll need to have Mercurial
installed, at which point you can type::

    hg clone http://bitbucket.org/izi/polib/

This will create a copy of the polib Mercurial repository on your computer;
you can then add the ``polib.py`` file to your Python import path, or use the
``setup.py`` script to install as a package.

