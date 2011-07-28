
import sys
import os
import optparse
import unittest
from nose.tools import eq_
from nose.plugins.xunit import Xunit
from nose.exc import SkipTest
from nose.config import Config

def mktest():    
    class TC(unittest.TestCase):
        def runTest(self):
            pass
    test = TC()
    return test

mktest.__test__ = False

class TestEscaping(unittest.TestCase):
    
    def setUp(self):
        self.x = Xunit()
    
    def test_all(self):
        eq_(self.x._xmlsafe(
            '''<baz src="http://foo?f=1&b=2" quote="inix hubris 'maximus'?" />'''),
            ('&lt;baz src=&quot;http://foo?f=1&amp;b=2&quot; '
                'quote=&quot;inix hubris &#39;maximus&#39;?&quot; /&gt;'))

    
    def test_unicode_is_utf8_by_default(self):
        eq_(self.x._xmlsafe(u'Ivan Krsti\u0107'),
            'Ivan Krsti\xc4\x87')

    
    def test_unicode_custom_utf16_madness(self):
        self.x.encoding = 'utf-16'
        utf16 = self.x._xmlsafe(u'Ivan Krsti\u0107')
        
        # to avoid big/little endian bytes, assert that we can put it back:
        eq_(utf16.decode('utf16'), u'Ivan Krsti\u0107')

class TestOptions(unittest.TestCase):
    
    def test_defaults(self):
        parser = optparse.OptionParser()
        x = Xunit()
        x.add_options(parser, env={})
        (options, args) = parser.parse_args([])
        eq_(options.xunit_file, "nosetests.xml")
    
    def test_file_from_environ(self):
        parser = optparse.OptionParser()
        x = Xunit()
        x.add_options(parser, env={'NOSE_XUNIT_FILE': "kangaroo.xml"})
        (options, args) = parser.parse_args([])
        eq_(options.xunit_file, "kangaroo.xml")
    
    def test_file_from_opt(self):
        parser = optparse.OptionParser()
        x = Xunit()
        x.add_options(parser, env={})
        (options, args) = parser.parse_args(["--xunit-file=blagojevich.xml"])
        eq_(options.xunit_file, "blagojevich.xml")
    
class TestXMLOutputWithXML(unittest.TestCase):
    
    def setUp(self):
        self.xmlfile = os.path.abspath(
            os.path.join(os.path.dirname(__file__), 
                            'support', 'xunit.xml'))
        parser = optparse.OptionParser()
        self.x = Xunit()
        self.x.add_options(parser, env={})
        (options, args) = parser.parse_args([
            "--with-xunit",
            "--xunit-file=%s" % self.xmlfile
        ])
        self.x.configure(options, Config())
        
        try:
            import xml.etree.ElementTree
        except ImportError:
            self.ET = False
        else:
            self.ET = xml.etree.ElementTree
    
    def tearDown(self):
        os.unlink(self.xmlfile)
    
    def get_xml_report(self):
        class DummyStream:
            pass
        self.x.report(DummyStream())
        f = open(self.xmlfile, 'r')
        return f.read()
        f.close()
            
    def test_addFailure(self):
        test = mktest()
        self.x.startTest(test)
        try:
            raise AssertionError("one is not 'equal' to two")
        except AssertionError:
            some_err = sys.exc_info()
            
        self.x.addFailure(test, some_err)
        
        result = self.get_xml_report()
        print result
        
        if self.ET:
            tree = self.ET.fromstring(result)
            eq_(tree.attrib['name'], "nosetests")
            eq_(tree.attrib['tests'], "1")
            eq_(tree.attrib['errors'], "0")
            eq_(tree.attrib['failures'], "1")
            eq_(tree.attrib['skip'], "0")
        
            tc = tree.find("testcase")
            eq_(tc.attrib['classname'], "test_xunit.TC")
            eq_(tc.attrib['name'], "test_xunit.TC.runTest")
            assert int(tc.attrib['time']) >= 0
        
            err = tc.find("failure")
            eq_(err.attrib['type'], "exceptions.AssertionError")
            err_lines = err.text.strip().split("\n")
            eq_(err_lines[0], 'Traceback (most recent call last):')
            eq_(err_lines[-1], 'AssertionError: one is not \'equal\' to two')
            eq_(err_lines[-2], '    raise AssertionError("one is not \'equal\' to two")')
        else:            
            # this is a dumb test for 2.4-
            assert '<?xml version="1.0" encoding="UTF-8"?>' in result
            assert '<testsuite name="nosetests" tests="1" errors="0" failures="1" skip="0">' in result
            assert '<testcase classname="test_xunit.TC" name="test_xunit.TC.runTest"' in result
            assert '<failure type="exceptions.AssertionError">' in result
            assert 'AssertionError: one is not &#39;equal&#39; to two' in result
            assert 'AssertionError(&quot;one is not &#39;equal&#39; to two&quot;)' in result
            assert '</failure></testcase></testsuite>' in result
            
    def test_addFailure_early(self):
        test = mktest()
        try:
            raise AssertionError("one is not equal to two")
        except AssertionError:
            some_err = sys.exc_info()
        
        # add failure without startTest, due to custom TestResult munging?
        self.x.addFailure(test, some_err)
        
        result = self.get_xml_report()
        print result
        
        if self.ET:
            tree = self.ET.fromstring(result)
            tc = tree.find("testcase")
            eq_(tc.attrib['time'], "0")
        else:
            # this is a dumb test for 2.4-
            assert '<?xml version="1.0" encoding="UTF-8"?>' in result
            assert ('<testcase classname="test_xunit.TC" '
                    'name="test_xunit.TC.runTest" time="0">') in result
    
    def test_addError(self):
        test = mktest()
        self.x.startTest(test)
        try:
            raise RuntimeError("some error happened")
        except RuntimeError:
            some_err = sys.exc_info()
            
        self.x.addError(test, some_err)
        
        result = self.get_xml_report()
        print result
        
        if self.ET:
            tree = self.ET.fromstring(result)
            eq_(tree.attrib['name'], "nosetests")
            eq_(tree.attrib['tests'], "1")
            eq_(tree.attrib['errors'], "1")
            eq_(tree.attrib['failures'], "0")
            eq_(tree.attrib['skip'], "0")
        
            tc = tree.find("testcase")
            eq_(tc.attrib['classname'], "test_xunit.TC")
            eq_(tc.attrib['name'], "test_xunit.TC.runTest")
            assert int(tc.attrib['time']) >= 0
        
            err = tc.find("error")
            eq_(err.attrib['type'], "exceptions.RuntimeError")
            err_lines = err.text.strip().split("\n")
            eq_(err_lines[0], 'Traceback (most recent call last):')
            eq_(err_lines[-1], 'RuntimeError: some error happened')
            eq_(err_lines[-2], '    raise RuntimeError("some error happened")')
        else:
            # this is a dumb test for 2.4-
            assert '<?xml version="1.0" encoding="UTF-8"?>' in result
            assert '<testsuite name="nosetests" tests="1" errors="1" failures="0" skip="0">' in result
            assert '<testcase classname="test_xunit.TC" name="test_xunit.TC.runTest"' in result
            assert '<error type="exceptions.RuntimeError">' in result
            assert 'RuntimeError: some error happened' in result
            assert '</error></testcase></testsuite>' in result
    
    def test_addError_early(self):
        test = mktest()
        try:
            raise RuntimeError("some error happened")
        except RuntimeError:
            some_err = sys.exc_info()
        
        # call addError without startTest
        # which can happen if setup() raises an error
        self.x.addError(test, some_err)
        
        result = self.get_xml_report()
        print result
        
        if self.ET:
            tree = self.ET.fromstring(result)
            tc = tree.find("testcase")
            eq_(tc.attrib['time'], "0")
        else:
            # this is a dumb test for 2.4-
            assert '<?xml version="1.0" encoding="UTF-8"?>' in result
            assert ('<testcase classname="test_xunit.TC" '
                    'name="test_xunit.TC.runTest" time="0">') in result
        
    def test_addSuccess(self):
        test = mktest()
        self.x.startTest(test)
        self.x.addSuccess(test, (None,None,None))
        
        result = self.get_xml_report()
        print result
        
        if self.ET:
            tree = self.ET.fromstring(result)
            eq_(tree.attrib['name'], "nosetests")
            eq_(tree.attrib['tests'], "1")
            eq_(tree.attrib['errors'], "0")
            eq_(tree.attrib['failures'], "0")
            eq_(tree.attrib['skip'], "0")
        
            tc = tree.find("testcase")
            eq_(tc.attrib['classname'], "test_xunit.TC")
            eq_(tc.attrib['name'], "test_xunit.TC.runTest")
            assert int(tc.attrib['time']) >= 0
        else:
            # this is a dumb test for 2.4-
            assert '<?xml version="1.0" encoding="UTF-8"?>' in result
            assert '<testsuite name="nosetests" tests="1" errors="0" failures="0" skip="0">' in result
            assert '<testcase classname="test_xunit.TC" name="test_xunit.TC.runTest"' in result
            assert '</testsuite>' in result
    
    def test_addSuccess_early(self):
        test = mktest()
        # call addSuccess without startTest
        # which can happen (?) -- did happen with JsLint plugin
        self.x.addSuccess(test, (None,None,None))
        
        result = self.get_xml_report()
        print result
        
        if self.ET:
            tree = self.ET.fromstring(result)
            tc = tree.find("testcase")
            eq_(tc.attrib['time'], "0")
        else:
            # this is a dumb test for 2.4-
            assert '<?xml version="1.0" encoding="UTF-8"?>' in result
            assert ('<testcase classname="test_xunit.TC" '
                    'name="test_xunit.TC.runTest" time="0" />') in result
        
