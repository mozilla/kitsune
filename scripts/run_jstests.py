"""
A wrapper around nosetests to run JavaScript tests in a CI environment.

Example::

    python run_jstests.py --with-xunit \
                           --with-django-serv --django-host hudson.mozilla.org \
                           --with-jstests \
                           --jstests-server http://jstestnet.farmdev.com/ \
                           --jstests-suite kitsune --jstests-browsers firefox

"""
import os
import site
import subprocess

ROOT = os.path.join(os.path.dirname(__file__), '..')

site.addsitedir(os.path.join(ROOT, 'vendor'))

from jstestnetlib.noseplugins import JSTests, DjangoServPlugin
import nose


def main():
    nose.main(addplugins=[DjangoServPlugin(ROOT), JSTests()])


if __name__ == '__main__':
    main()
