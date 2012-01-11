# -*- coding: utf-8 -*-

#old way 
from distutils.core import setup

#new way
#from setuptools import setup, find_packages

setup(name='mimeparse',
      version='0.1.3',
      description='A module provides basic functions for parsing mime-type names and matching them against a list of media-ranges.',
      long_description="""
This module provides basic functions for handling mime-types. It can handle
matching mime-types against a list of media-ranges. See section 14.1 of 
the HTTP specification [RFC 2616] for a complete explanation.

   http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.1

Contents:
    - parse_mime_type():   Parses a mime-type into its component parts.
    - parse_media_range(): Media-ranges are mime-types with wild-cards and a 'q' quality parameter.
    - quality():           Determines the quality ('q') of a mime-type when compared against a list of media-ranges.
    - quality_parsed():    Just like quality() except the second parameter must be pre-parsed.
    - best_match():        Choose the mime-type with the highest quality ('q') from a list of candidates.
      """,
      classifiers=[
          # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python',
          'Topic :: Internet :: WWW/HTTP',
          'Topic :: Software Development :: Libraries :: Python Modules',
          ],
      keywords='mime-type',
      author='Joe Gregorio',
      author_email='joe@bitworking.org',
      maintainer='Joe Gregorio',
      maintainer_email='joe@bitworking.org',
      url='http://code.google.com/p/mimeparse/',
      license='MIT',
      py_modules=['mimeparse'],
      zip_safe=True,
      )

