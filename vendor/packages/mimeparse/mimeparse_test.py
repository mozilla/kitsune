"""
Python tests for Mime-Type Parser.

This module loads a json file and converts the tests specified therein to a set
of PyUnitTestCases. Then it uses PyUnit to run them and report their status.
"""
__version__ = "0.1"
__author__ = 'Ade Oshineye'
__email__ = "ade@oshineye.com"
__credits__ = ""

import mimeparse
import unittest
from functools import partial
# Conditional import to support Python 2.5
try:
    import json
except ImportError:
    import simplejson as json

def test_parse_media_range(args, expected):
    expected = tuple(expected)
    result = mimeparse.parse_media_range(args)
    message = "Expected: '%s' but got %s" % (expected, result)
    assert expected == result, message

def test_quality(args, expected):
    result = mimeparse.quality(args[0], args[1])
    message = "Expected: '%s' but got %s" % (expected, result)
    assert expected == result, message

def test_best_match(args, expected):
    result = mimeparse.best_match(args[0], args[1])
    message = "Expected: '%s' but got %s" % (expected, result)
    assert expected == result, message

def test_parse_mime_type(args, expected):
    expected = tuple(expected)
    result = mimeparse.parse_mime_type(args)
    message = "Expected: '%s' but got %s" % (expected, result)
    assert expected == result, message

def add_tests(suite, json_object, func_name, test_func):
    test_data = json_object[func_name]
    for test_datum in test_data:
        args, expected = test_datum[0], test_datum[1]
        desc = "%s(%s) with expected result: %s" % (func_name, str(args), str(expected))
        if len(test_datum) == 3:
            desc = test_datum[2] + " : " + desc
        func =  partial(test_func, *(args, expected))
        testcase = unittest.FunctionTestCase(func, description=desc)
        suite.addTest(testcase)

def run_tests():
    json_object = json.load(open("testdata.json"))

    suite = unittest.TestSuite()
    add_tests(suite, json_object, "parse_media_range", test_parse_media_range)
    add_tests(suite, json_object, "quality", test_quality)
    add_tests(suite, json_object, "best_match", test_best_match)
    add_tests(suite, json_object, "parse_mime_type", test_parse_mime_type)

    test_runner = unittest.TextTestRunner(verbosity=1)
    test_runner.run(suite)

if __name__ == "__main__":
    run_tests()
