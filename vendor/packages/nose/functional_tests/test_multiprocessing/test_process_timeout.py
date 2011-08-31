import os
import unittest

from nose.plugins import PluginTester
from nose.plugins.skip import SkipTest
from nose.plugins.multiprocess import MultiProcess

support = os.path.join(os.path.dirname(__file__), 'support')


def setup():
    try:
        import multiprocessing
        if 'active' in MultiProcess.status:
            raise SkipTest("Multiprocess plugin is active. Skipping tests of "
                           "plugin itself.")
    except ImportError:
        raise SkipTest("multiprocessing module not available")



class TestMPTimeout(PluginTester, unittest.TestCase):
    activate = '--processes=2'
    args = ['--process-timeout=1']
    plugins = [MultiProcess()]
    suitepath = os.path.join(support, 'timeout.py')

    def runTest(self):
        assert "TimedOutException: 'timeout.test_timeout'" in self.output


class TestMPTimeoutPass(TestMPTimeout):
    args = ['--process-timeout=3']

    def runTest(self):
        assert "TimedOutException: 'timeout.test_timeout'" not in self.output
        assert str(self.output).strip().endswith('OK')
