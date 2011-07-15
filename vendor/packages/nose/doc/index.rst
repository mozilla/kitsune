.. nose documentation master file, created by sphinx-quickstart on Thu Mar 26 16:49:00 2009.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


Installation and quick start
============================

*On most UNIX-like systems, you'll probably need to run these commands as root
or using sudo.*

Install nose using setuptools::

  easy_install nose

Or, if you don't have setuptools installed, use the download link at right to
download the source package, and install it in the normal fashion: Ungzip and
untar the source package, cd to the new directory, and::

  python setup.py install

However, **please note** that without setuptools installed, you will not be
able to use third-party nose plugins.

This will install the nose libraries, as well as the :doc:`nosetests <usage>`
script, which you can use to automatically discover and run tests.

Now you can run tests for your project::

  cd path/to/project
  nosetests

You should see output something like this::

  ..................................
  ----------------------------------------------------------------------
  Ran 34 tests in 1.440s

  OK

Indicating that nose found and ran your tests.  
  
For help with nosetests' many command-line options, try::

  nosetests -h

or visit the :doc:`usage documentation <usage>`.

.. toctree::
   :hidden:

   testing
   developing
   news      
   further_reading
