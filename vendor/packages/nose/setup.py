from nose import __version__ as VERSION
import sys

py_vers_tag = '-%s.%s' % sys.version_info[:2]

try:
    from setuptools import setup, find_packages
    addl_args = dict(
        zip_safe = False,
        packages = find_packages(),
        entry_points = {
        'console_scripts': [
            'nosetests = nose:run_exit',
            'nosetests%s = nose:run_exit' % py_vers_tag,
            ],
        'distutils.commands': [
            ' nosetests = nose.commands:nosetests',
            ],
        },
        test_suite = 'nose.collector',
        )
except ImportError:
    from distutils.core import setup
    addl_args = dict(
        packages = ['nose', 'nose.ext', 'nose.plugins'],
        scripts = ['bin/nosetests'],
        )

setup(
    name = 'nose',
    version = VERSION,
    author = 'Jason Pellerin',
    author_email = 'jpellerin+nose@gmail.com',
    description = ('nose extends unittest to make testing easier'),
    long_description = \
    """nose extends the test loading and running features of unittest, making
    it easier to write, find and run tests.

    By default, nose will run tests in files or directories under the current
    working directory whose names include "test" or "Test" at a word boundary
    (like "test_this" or "functional_test" or "TestClass" but not
    "libtest"). Test output is similar to that of unittest, but also includes
    captured stdout output from failing tests, for easy print-style debugging.

    These features, and many more, are customizable through the use of
    plugins. Plugins included with nose provide support for doctest, code
    coverage and profiling, flexible attribute-based test selection,
    output capture and more. More information about writing plugins may be
    found on in the nose API documentation, here:
    http://somethingaboutorange.com/mrl/projects/nose/

    If you have recently reported a bug marked as fixed, or have a craving for
    the very latest, you may want the unstable development version instead:
    http://bitbucket.org/jpellerin/nose/get/tip.gz#egg=nose-dev
    """,
    license = 'GNU LGPL',
    keywords = 'test unittest doctest automatic discovery',
    url = 'http://somethingaboutorange.com/mrl/projects/nose/',
    download_url = \
    'http://somethingaboutorange.com/mrl/projects/nose/nose-%s.tar.gz' \
    % VERSION,
    data_files = [('man/man1', ['nosetests.1'])],
    package_data = {'': ['*.txt',
                         'examples/*.py',
                         'examples/*/*.py']},
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Testing'
        ],
    **addl_args
    )
