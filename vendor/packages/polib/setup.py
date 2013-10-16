#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# License: MIT (see LICENSE file provided)
# vim600: fdm=marker tabstop=4 shiftwidth=4 expandtab ai

"""
polib setup script.
"""

__author__ = 'David Jean Louis <izimobil@gmail.com>'

from distutils.core import setup
import codecs

import polib

author_data = __author__.split(' ')
maintainer = ' '.join(author_data[0:-1])
maintainer_email = author_data[-1]
desc = 'A library to manipulate gettext files (po and mo files).'

if polib.PY3:
    mode = 'rb'
else:
    mode = 'r'

long_desc = r'''
.. contents:: Table of Contents

%s

%s

''' % (open('README.rst', mode).read(), open('CHANGELOG', mode).read())

if __name__ == '__main__':
    setup(
        name='polib',
        description=desc,
        long_description=long_desc,
        version=polib.__version__,
        author=maintainer,
        author_email=maintainer_email,
        maintainer=maintainer,
        maintainer_email=maintainer_email,
        url='http://bitbucket.org/izi/polib/',
        download_url='http://bitbucket.org/izi/polib/downloads/polib-%s.tar.gz' % polib.__version__,
        license='MIT',
        platforms=['posix'],
        classifiers = [
            'Development Status :: 5 - Production/Stable',
            'Environment :: Console',
            'Intended Audience :: System Administrators',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Natural Language :: French',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Programming Language :: Python :: 3',
            'Topic :: Software Development :: Libraries :: Python Modules',
            'Topic :: Software Development :: Internationalization',
            'Topic :: Software Development :: Localization',
            'Topic :: Text Processing :: Linguistic'
        ],
        py_modules=['polib']
    )

