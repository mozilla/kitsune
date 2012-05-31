#!/usr/bin/env python
"""
Python Distutils setup for for amqp.  Build and install with

    python setup.py install

2007-11-10 Barry Pederson <bp@barryp.org>

"""

import sys

try:
    from setuptools import setup
except:
    from distutils.core import setup


try:
    from distutils.command.build_py import build_py_2to3 as build_py
except ImportError:
    # 2.x
    from distutils.command.build_py import build_py

setup(name = "amqplib",
      description = "AMQP Client Library",
      version = "1.0.2",
      classifiers=[
          'Programming Language :: Python',
	  'Programming Language :: Python :: 2',
	  'Programming Language :: Python :: 2.4',
	  'Programming Language :: Python :: 2.5',
	  'Programming Language :: Python :: 2.6',
	  'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.0',
          'Programming Language :: Python :: 3.1',
          'Programming Language :: Python :: 3.2',
	  'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
	  'Intended Audience :: Developers',
          ],
      license = "LGPL",
      author = "Barry Pederson",
      author_email = "bp@barryp.org",
      url = "http://code.google.com/p/py-amqplib/",
      packages = ['amqplib', 'amqplib.client_0_8'],
      cmdclass = {'build_py':build_py},
     )
