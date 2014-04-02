.. _vendor-chapter:

==============
Vendor Library
==============

To help make setup faster and deployment easier, we pull all of our
pure-Python dependencies into a "vendor library" (``kitsune/vendor``)
in the kitsune repository and add them to the path in ``manage.py``.

The vendor library used to be optional, with a virtualenv option
available, as well. While it's still possible to install the compiled
requirements in a virtualenv, we've decided to simplify
docs/setup/tooling and encourage environments to be as similar to
production as possible, by settling on the vendor library as the only
method for managing dependencies.


Getting the Vendor Library and Keeping Up-to-Date
=================================================

If you cloned Kitsune with ``--recursive``, you already have the
vendor library in ``vendor/``.

If you didn't clone with ``--recursive``, or need to update the vendor
library (or other submodules), just run::

    $ git submodule update --init --recursive

Aliasing that to something short (e.g. ``gsu``) is recommended.


Updating the Vendor Library
===========================

From time to time we need to update libraries, either for new versions
of libraries or to add a new library. There are two ways to do
that. The easiest and prefered way is pure git.


Using Git Submodules
--------------------

Using git submodules is prefered because it is much easier to
maintain, and it keeps the repository size small. Upgrading is as
simple as updating a submodule.


Updating a Library with Git Submodules
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If the library is in ``vendor/src``, it was pulled directly from
version control, and if that version control was git, updating the
submodule is as easy as::

    $ cd vendor/src/$LIBRARY
    $ git fetch origin
    $ git checkout <REFSPEC>
    $ cd ../..
    $ git add vendor/src/$LIBRARY
    $ git ci -m "Updating $LIBRARY"

Easy! Just like updating any other git submodule.


Adding a New Library with Git Submodules
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Technically this can be done with ``pip install --no-install`` but
there's an even easier method when installing a new library from a git
repo::

    $ cd vendor/src
    $ git clone https://<repo>
    $ cd ../..
    $ vendor/addsubmodules.sh
    $ vim vendor/kitsune.pth  # Add the new library's path
    $ git add vendor/kitsune.pth
    $ git ci -m "Adding $LIBRARY"


.. Note::

   Use the ``git://`` url for a repository and not the ``http://``
   one. The git protocol is more resilient and faster to clone over.

   Don't use the ``git@`` url. It will only bring you pain.


Removing a Library from ``vendor/src``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Removing an existing submodule is easy if you follow these steps in the
right order::

    $ rm -rf vendor/src/<submodule>
    $ git submodule deinit vendor/src/<submodule>
    $ git rm vendor/src/<submodule>
    $ vim vendor/kitsune.pth  # Remove the line with ``src/<submodule>``
    $ git ci -am "Removing <submodule> from vendor."


Using PyPI
----------

Sometimes a library isn't in a git repository. It, sadly,
happens. Maybe you can find a git mirror? If not, it might as well be
installed from PyPI.


Updating a Library from PyPI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The easiest way to update a library from PyPI is to remove it
completely and then install the new version.

::

    $ cd vendor/packages
    $ git rm -r $LIBRARY
    $ cd ..
    $ git ci -m "Removing version $VERSION of $LIBRARY"
    $ cd ..

After removing the old version, go ahead and install the new one::

    $ pip install --no-install --build=vendor/packages --src=vendor/src -I $LIBRARY

Finally, add the new library to git::

    $ cd vendor
    $ git add packages
    $ git ci -m "Adding version $VERSION of $LIBRARY"


.. warning::

   **Caveat developer!** Sometimes a library has dependencies that are
   already installed in the vendor repo. You may need to remove
   several of them to make everything work easily.


Adding a Library from PyPI
^^^^^^^^^^^^^^^^^^^^^^^^^^

Adding a new library from PyPI is easy using pip::

    $ pip install --no-install --build=vendor/packages --src=vendor/src -I $LIBRARY
    $ cd vendor
    $ git add packages
    $ vim kitsune.pth  # Add any new libraries' paths.
    $ git ci -m "Adding $LIBRARY"

Make sure you add any dependencies from the new library, as well.


Requirements Files
==================

There are a few requirements that are not included in the vendor
library because they need to be (or can be, for performance benefits)
compiled (or have compiled dependencies themselves).

You can :ref:`install <hacking-howto-chapter>` these in a virtualenv
or at the system level by running::

    $ pip install -r requirements/compiled.txt

If you want to run coverage builds or are having issues with tests,
you can run::

    $ pip install -r requirements/tests-compiled.txt
