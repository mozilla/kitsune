#!/usr/bin/env python

# Use setuptools if we can
try:
    from setuptools.core import setup
except ImportError:
    from distutils.core import setup
from south import __version__

setup(
    name='South',
    version=__version__,
    description='South: Migrations for Django',
    long_description='South is an intelligent database migrations library for the Django web framework. It is database-independent and DVCS-friendly, as well as a whole host of other features.',
    author='Andrew Godwin & Andy McCurdy',
    author_email='south@aeracode.org',
    url='http://south.aeracode.org/',
    download_url='http://south.aeracode.org/wiki/Download',
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Software Development",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
    ],
    packages=[
        'south',
        'south.creator',
        'south.db',
        'south.management',
        'south.introspection_plugins',
        'south.hacks',
        'south.migration',
        'south.tests',
        'south.db.sql_server',
        'south.management.commands',
        'south.tests.circular_a',
        'south.tests.emptyapp',
        'south.tests.deps_a',
        'south.tests.fakeapp',
        'south.tests.brokenapp',
        'south.tests.circular_b',
        'south.tests.otherfakeapp',
        'south.tests.deps_c',
        'south.tests.deps_b',
        'south.tests.non_managed',
        'south.tests.circular_a.migrations',
        'south.tests.emptyapp.migrations',
        'south.tests.deps_a.migrations',
        'south.tests.fakeapp.migrations',
        'south.tests.brokenapp.migrations',
        'south.tests.circular_b.migrations',
        'south.tests.otherfakeapp.migrations',
        'south.tests.deps_c.migrations',
        'south.tests.deps_b.migrations',
        'south.tests.non_managed.migrations',
        'south.utils',
    ],
)
