import sys
import unittest
from cStringIO import StringIO
from optparse import OptionParser
import nose.core
from nose.config import Config
from nose.tools import set_trace
from mock import Bucket, MockOptParser


class NullLoader:
    def loadTestsFromNames(self, names):
        return unittest.TestSuite()

class TestAPI_run(unittest.TestCase):

    def test_restore_stdout(self):
        print "AHOY"
        s = StringIO()
        print s
        stdout = sys.stdout
        conf = Config(stream=s)
        # set_trace()
        print "About to run"
        res = nose.core.run(
            testLoader=NullLoader(), argv=['test_run'], env={}, config=conf)
        print "Done running"
        stdout_after = sys.stdout
        self.assertEqual(stdout, stdout_after)
        
if __name__ == '__main__':
    unittest.main()
