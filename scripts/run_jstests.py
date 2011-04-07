"""
A wrapper around nosetests to run JavaScript tests in a CI environment.

Example::

    python run_jstests.py --with-xunit \
                           --with-kitsune --kitsune-host hudson.mozilla.org \
                           --with-jstests \
                           --jstests-server http://jstestnet.farmdev.com/ \
                           --jstests-suite kitsune --jstests-browsers firefox

"""
import os
import site
import subprocess

ROOT = os.path.join(os.path.dirname(__file__), '..')
assert 'manage.py' in os.listdir(ROOT), (
    'Expected this to be the root dir containing manage.py: %s' % ROOT)

site.addsitedir(os.path.join(ROOT, 'vendor'))

from jstestnetlib import webapp
from jstestnetlib.noseplugin import JSTests
import nose
from nose.plugins import Plugin


class Kitsune(Plugin):
    """Starts/stops Django runserver for tests."""
    name = 'kitsune'

    def options(self, parser, env=os.environ):
        super(Kitsune, self).options(parser, env=env)
        parser.add_option('--kitsune-host', default='0.0.0.0',
                          help='Hostname or IP address to bind manage.py '
                               'runserver to. This must match the host/ip '
                               'configured in your --jstests-suite URL. '
                               'Default: %default')
        parser.add_option('--kitsune-port', default=9878,
                          help='Port to bind manage.py runserver to. '
                               'This must match the port '
                               'configured in your --jstests-suite URL. '
                               'Default: %default')
        parser.add_option('--kitsune-log', default=None,
                          help='Log filename for the manage.py runserver '
                               'command. Logs to a temp file by default.')
        self.parser = parser

    def configure(self, options, conf):
        super(Kitsune, self).configure(options, conf)
        self.options = options

    def begin(self):
        bind = '%s:%s' % (self.options.kitsune_host,
                          self.options.kitsune_port)
        startup_url = 'http://%s/' % bind
        self.kitsune = webapp.WebappServerCmd(
                                ['python', 'manage.py', 'runserver', bind],
                                startup_url, logfile=self.options.kitsune_log,
                                cwd=ROOT)
        self.kitsune.startup()

    def finalize(self, result):
        self.kitsune.shutdown()


def main():
    nose.main(addplugins=[Kitsune(), JSTests()])


if __name__ == '__main__':
    main()
