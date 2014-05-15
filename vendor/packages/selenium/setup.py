#!/usr/bin/env python
# Copyright 2008-2009 WebDriver committers
# Copyright 2008-2009 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from setuptools import setup
from setuptools.command.install import install

from os.path import dirname, join, isfile, abspath
from shutil import copy
import sys

from distutils.command.install import INSTALL_SCHEMES
for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']

setup_args = {
    'cmdclass':{'install': install},
    'name':'selenium',
    'version':"2.41.0",
    'description':'Python bindings for Selenium',
    'long_description':open(join(abspath(dirname(__file__)), "py", "README")).read(),
    'url':'http://code.google.com/p/selenium/',
    'classifiers':['Development Status :: 5 - Production/Stable',
                     'Intended Audience :: Developers',
                     'License :: OSI Approved :: Apache Software License',
                     'Operating System :: POSIX',
                     'Operating System :: Microsoft :: Windows',
                     'Operating System :: MacOS :: MacOS X',
                     'Topic :: Software Development :: Testing',
                     'Topic :: Software Development :: Libraries',
                     'Programming Language :: Python',
                     'Programming Language :: Python :: 2.6',
                     'Programming Language :: Python :: 2.7',
                     'Programming Language :: Python :: 3.2',
                     'Programming Language :: Python :: 3.3'],
    'package_dir':{
        'selenium': 'py/selenium',
        'selenium.common': 'py/selenium/common',
        'selenium.webdriver': 'py/selenium/webdriver',
    },
    'packages':['selenium',
              'selenium.common',
              'selenium.webdriver',
              'selenium.webdriver.chrome',
              'selenium.webdriver.common',
 	          'selenium.webdriver.common.html5',
              'selenium.webdriver.support',
              'selenium.webdriver.firefox',
              'selenium.webdriver.ie',
              'selenium.webdriver.opera',
              'selenium.webdriver.phantomjs',
              'selenium.webdriver.remote',
              'selenium.webdriver.support', ],
    'package_data':{
        'selenium.webdriver.firefox': ['*.xpi', 'webdriver_prefs.json'],
    },
    'data_files':[('selenium/webdriver/firefox/x86', ['py/selenium/webdriver/firefox/x86/x_ignore_nofocus.so']),
            ('selenium/webdriver/firefox/amd64', ['py/selenium/webdriver/firefox/amd64/x_ignore_nofocus.so'])],
    'include_package_data':True,
    'zip_safe':False
}

setup(**setup_args)
