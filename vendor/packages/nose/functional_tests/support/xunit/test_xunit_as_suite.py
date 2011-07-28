import sys
from nose.exc import SkipTest
import unittest

class TestForXunit(unittest.TestCase):

    def test_success(self):
        pass

    def test_fail(self):
        self.assertEqual("this","that")

    def test_error(self):
        raise TypeError("oops, wrong type")
    
    def test_output(self):
        sys.stdout.write("test-generated output\n")

    def test_skip(self):
        raise SkipTest("skipit")
