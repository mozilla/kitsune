# Copyright (C) 2007-2011 Michael Foord & the mock team
# E-mail: fuzzyman AT voidspace DOT org DOT uk
# http://www.voidspace.org.uk/python/mock/

from __future__ import with_statement

from tests.support import unittest2

from mock import MagicMock, Mock, patch, sentinel

from tests.support_with import catch_warnings, nested

something  = sentinel.Something
something_else  = sentinel.SomethingElse


class WithTest(unittest2.TestCase):

    def testWithStatement(self):
        with patch('tests._testwith.something', sentinel.Something2):
            self.assertEqual(something, sentinel.Something2, "unpatched")
        self.assertEqual(something, sentinel.Something)

    def testWithStatementException(self):
        try:
            with patch('tests._testwith.something', sentinel.Something2):
                self.assertEqual(something, sentinel.Something2, "unpatched")
                raise Exception('pow')
        except Exception:
            pass
        else:
            self.fail("patch swallowed exception")
        self.assertEqual(something, sentinel.Something)


    def testWithStatementAs(self):
        with patch('tests._testwith.something') as mock_something:
            self.assertEqual(something, mock_something, "unpatched")
            self.assertTrue(isinstance(mock_something, Mock), "patching wrong type")
        self.assertEqual(something, sentinel.Something)


    def testPatchObjectWithStatementAs(self):
        mock = Mock()
        original = mock.something
        with patch.object(mock, 'something'):
            self.assertNotEqual(mock.something, original, "unpatched")
        self.assertEqual(mock.something, original)


    def testWithStatementNested(self):
        with catch_warnings(record=True):
            # nested is deprecated in Python 2.7
            with nested(patch('tests._testwith.something'),
                    patch('tests._testwith.something_else')) as (mock_something, mock_something_else):
                self.assertEqual(something, mock_something, "unpatched")
                self.assertEqual(something_else, mock_something_else, "unpatched")
        self.assertEqual(something, sentinel.Something)
        self.assertEqual(something_else, sentinel.SomethingElse)


    def testWithStatementSpecified(self):
        with patch('tests._testwith.something', sentinel.Patched) as mock_something:
            self.assertEqual(something, mock_something, "unpatched")
            self.assertEqual(mock_something, sentinel.Patched, "wrong patch")
        self.assertEqual(something, sentinel.Something)


    def testContextManagerMocking(self):
        mock = Mock()
        mock.__enter__ = Mock()
        mock.__exit__ = Mock()
        mock.__exit__.return_value = False

        with mock as m:
            self.assertEqual(m, mock.__enter__.return_value)
        mock.__enter__.assert_called_with()
        mock.__exit__.assert_called_with(None, None, None)


    def testContextManagerWithMagicMock(self):
        mock = MagicMock()

        with self.assertRaises(TypeError):
            with mock:
                'foo' + 3
        mock.__enter__.assert_called_with()
        self.assertTrue(mock.__exit__.called)


    def testWithStatementSameAttribute(self):
        with patch('tests._testwith.something', sentinel.Patched) as mock_something:
            self.assertEqual(something, mock_something, "unpatched")

            with patch('tests._testwith.something') as mock_again:
                self.assertEqual(something, mock_again, "unpatched")

            self.assertEqual(something, mock_something, "restored with wrong instance")

        self.assertEqual(something, sentinel.Something, "not restored")

    def testWithStatementImbricated(self):
        with patch('tests._testwith.something') as mock_something:
            self.assertEqual(something, mock_something, "unpatched")

            with patch('tests._testwith.something_else') as mock_something_else:
                self.assertEqual(something_else, mock_something_else, "unpatched")

        self.assertEqual(something, sentinel.Something)
        self.assertEqual(something_else, sentinel.SomethingElse)

    def testDictContextManager(self):
        foo = {}
        with patch.dict(foo, {'a': 'b'}):
            self.assertEqual(foo, {'a': 'b'})
        self.assertEqual(foo, {})

        with self.assertRaises(NameError):
            with patch.dict(foo, {'a': 'b'}):
                self.assertEqual(foo, {'a': 'b'})
                raise NameError('Konrad')

        self.assertEqual(foo, {})


if __name__ == '__main__':
    unittest2.main()
