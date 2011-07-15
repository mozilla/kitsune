# Copyright (C) 2007-2011 Michael Foord & the mock team
# E-mail: fuzzyman AT voidspace DOT org DOT uk
# http://www.voidspace.org.uk/python/mock/

import os
import sys
import warnings

from tests import support
from tests.support import unittest2, apply, inPy3k, SomeClass, with_available

if with_available:
    from tests.support_with import examine_warnings

from mock import Mock, patch, patch_object, sentinel

if not inPy3k:
    builtin_string = '__builtin__'
else:
    builtin_string = 'builtins'

PTModule = sys.modules[__name__]

def _getProxy(obj, get_only=True):
    class Proxy(object):
        def __getattr__(self, name):
            return getattr(obj, name)
    if not get_only:
        def __setattr__(self, name, value):
            setattr(obj, name, value)
        def __delattr__(self, name):
            delattr(obj, name)
        Proxy.__setattr__ = __setattr__
        Proxy.__delattr__ = __delattr__
    return Proxy()

# for use in the test
something  = sentinel.Something
something_else  = sentinel.SomethingElse


class Container(object):
    def __init__(self):
        self.values = {}

    def __getitem__(self, name):
        return self.values[name]

    def __setitem__(self, name, value):
        self.values[name] = value

    def __delitem__(self, name):
        del self.values[name]

    def __iter__(self):
        return iter(self.values)


class PatchTest(unittest2.TestCase):

    def testSinglePatchObject(self):
        class Something(object):
            attribute = sentinel.Original

        @apply
        @patch.object(Something, 'attribute', sentinel.Patched)
        def test():
            self.assertEqual(Something.attribute, sentinel.Patched, "unpatched")

        self.assertEqual(Something.attribute, sentinel.Original, "patch not restored")


    def testPatchObjectWithNone(self):
        class Something(object):
            attribute = sentinel.Original

        @apply
        @patch.object(Something, 'attribute', None)
        def test():
            self.assertIsNone(Something.attribute, "unpatched")

        self.assertEqual(Something.attribute, sentinel.Original, "patch not restored")


    def testMultiplePatchObject(self):
        class Something(object):
            attribute = sentinel.Original
            next_attribute = sentinel.Original2

        @apply
        @patch.object(Something, 'attribute', sentinel.Patched)
        @patch.object(Something, 'next_attribute', sentinel.Patched2)
        def test():
            self.assertEqual(Something.attribute, sentinel.Patched, "unpatched")
            self.assertEqual(Something.next_attribute, sentinel.Patched2, "unpatched")

        self.assertEqual(Something.attribute, sentinel.Original, "patch not restored")
        self.assertEqual(Something.next_attribute, sentinel.Original2, "patch not restored")


    def testObjectLookupIsQuiteLazy(self):
        global something
        original = something
        @patch('tests.testpatch.something', sentinel.Something2)
        def test():
            pass

        try:
            something = sentinel.replacement_value
            test()
            self.assertEqual(something, sentinel.replacement_value)
        finally:
            something = original


    def testPatch(self):
        @apply
        @patch('%s.something' % __name__, sentinel.Something2)
        def test():
            self.assertEqual(PTModule.something, sentinel.Something2, "unpatched")

        self.assertEqual(PTModule.something, sentinel.Something, "patch not restored")

        @patch('tests.testpatch.something', sentinel.Something2)
        @patch('tests.testpatch.something_else', sentinel.SomethingElse)
        def test():
            self.assertEqual(PTModule.something, sentinel.Something2, "unpatched")
            self.assertEqual(PTModule.something_else, sentinel.SomethingElse, "unpatched")

        self.assertEqual(PTModule.something, sentinel.Something, "patch not restored")
        self.assertEqual(PTModule.something_else, sentinel.SomethingElse, "patch not restored")

        # Test the patching and restoring works a second time
        test()

        self.assertEqual(PTModule.something, sentinel.Something, "patch not restored")
        self.assertEqual(PTModule.something_else, sentinel.SomethingElse, "patch not restored")

        mock = Mock()
        mock.return_value = sentinel.Handle
        @patch('%s.open' % builtin_string, mock)
        def test():
            self.assertEqual(open('filename', 'r'), sentinel.Handle, "open not patched")
        test()
        test()

        self.assertNotEqual(open, mock, "patch not restored")


    def testPatchClassAttribute(self):
        import tests.testpatch as PTModule

        @patch('tests.testpatch.SomeClass.class_attribute', sentinel.ClassAttribute)
        def test():
            self.assertEqual(PTModule.SomeClass.class_attribute, sentinel.ClassAttribute, "unpatched")
        test()

        self.assertIsNone(PTModule.SomeClass.class_attribute, "patch not restored")


    def testPatchObjectWithDefaultMock(self):
        class Test(object):
            something = sentinel.Original
            something2 = sentinel.Original2

        @apply
        @patch.object(Test, 'something')
        def test(mock):
            self.assertEqual(mock, Test.something, "Mock not passed into test function")
            self.assertTrue(isinstance(mock, Mock),
                            "patch with two arguments did not create a mock")

        @patch.object(Test, 'something')
        @patch.object(Test, 'something2')
        def test(this1, this2, mock1, mock2):
            self.assertEqual(this1, sentinel.this1, "Patched function didn't receive initial argument")
            self.assertEqual(this2, sentinel.this2, "Patched function didn't receive second argument")
            self.assertEqual(mock1, Test.something2, "Mock not passed into test function")
            self.assertEqual(mock2, Test.something, "Second Mock not passed into test function")
            self.assertTrue(isinstance(mock2, Mock),
                            "patch with two arguments did not create a mock")
            self.assertTrue(isinstance(mock2, Mock),
                            "patch with two arguments did not create a mock")


            # A hack to test that new mocks are passed the second time
            self.assertNotEqual(outerMock1, mock1, "unexpected value for mock1")
            self.assertNotEqual(outerMock2, mock2, "unexpected value for mock1")
            return mock1, mock2

        outerMock1 = None
        outerMock2 = None
        outerMock1, outerMock2 = test(sentinel.this1, sentinel.this2)

        # Test that executing a second time creates new mocks
        test(sentinel.this1, sentinel.this2)


    def testPatchWithSpec(self):
        @patch('tests.testpatch.SomeClass', spec=SomeClass)
        def test(MockSomeClass):
            self.assertEqual(SomeClass, MockSomeClass)
            self.assertTrue(isinstance(SomeClass.wibble, Mock))
            self.assertRaises(AttributeError, lambda: SomeClass.not_wibble)

        test()


    def testPatchObjectWithSpec(self):
        @patch.object(SomeClass, 'class_attribute', spec=SomeClass)
        def test(MockAttribute):
            self.assertEqual(SomeClass.class_attribute, MockAttribute)
            self.assertTrue(isinstance(SomeClass.class_attribute.wibble, Mock))
            self.assertRaises(AttributeError, lambda: SomeClass.class_attribute.not_wibble)

        test()


    def testPatchWithSpecAsList(self):
        @patch('tests.testpatch.SomeClass', spec=['wibble'])
        def test(MockSomeClass):
            self.assertEqual(SomeClass, MockSomeClass)
            self.assertTrue(isinstance(SomeClass.wibble, Mock))
            self.assertRaises(AttributeError, lambda: SomeClass.not_wibble)

        test()


    def testPatchObjectWithSpecAsList(self):
        @patch.object(SomeClass, 'class_attribute', spec=['wibble'])
        def test(MockAttribute):
            self.assertEqual(SomeClass.class_attribute, MockAttribute)
            self.assertTrue(isinstance(SomeClass.class_attribute.wibble, Mock))
            self.assertRaises(AttributeError, lambda: SomeClass.class_attribute.not_wibble)

        test()


    def testNestedPatchWithSpecAsList(self):
        # regression test for nested decorators
        @patch('%s.open' % builtin_string)
        @patch('tests.testpatch.SomeClass', spec=['wibble'])
        def test(MockSomeClass, MockOpen):
            self.assertEqual(SomeClass, MockSomeClass)
            self.assertTrue(isinstance(SomeClass.wibble, Mock))
            self.assertRaises(AttributeError, lambda: SomeClass.not_wibble)


    def testPatchWithSpecAsBoolean(self):
        @apply
        @patch('tests.testpatch.SomeClass', spec=True)
        def test(MockSomeClass):
            self.assertEqual(SomeClass, MockSomeClass)
            # Should not raise attribute error
            MockSomeClass.wibble

            self.assertRaises(AttributeError, lambda: MockSomeClass.not_wibble)


    def testPatchObjectWithSpecAsBoolean(self):
        from tests import testpatch
        @apply
        @patch.object(testpatch, 'SomeClass', spec=True)
        def test(MockSomeClass):
            self.assertEqual(SomeClass, MockSomeClass)
            # Should not raise attribute error
            MockSomeClass.wibble

            self.assertRaises(AttributeError, lambda: MockSomeClass.not_wibble)


    def testPatchClassActsWithSpecIsInherited(self):
        @apply
        @patch('tests.testpatch.SomeClass', spec=True)
        def test(MockSomeClass):
            instance = MockSomeClass()
            # Should not raise attribute error
            instance.wibble

            self.assertRaises(AttributeError, lambda: instance.not_wibble)


    def testPatchWithCreateMocksNonExistentAttributes(self):
        @patch('%s.frooble' % builtin_string, sentinel.Frooble, create=True)
        def test():
            self.assertEqual(frooble, sentinel.Frooble)

        test()
        self.assertRaises(NameError, lambda: frooble)


    def testPatchObjectWithCreateMocksNonExistentAttributes(self):
        @patch.object(SomeClass, 'frooble', sentinel.Frooble, create=True)
        def test():
            self.assertEqual(SomeClass.frooble, sentinel.Frooble)

        test()
        self.assertFalse(hasattr(SomeClass, 'frooble'))


    def testPatchWontCreateByDefault(self):
        try:
            @patch('%s.frooble' % builtin_string, sentinel.Frooble)
            def test():
                self.assertEqual(frooble, sentinel.Frooble)

            test()
        except AttributeError:
            pass
        else:
            self.fail('Patching non existent attributes should fail')

        self.assertRaises(NameError, lambda: frooble)


    def testPatchObjecWontCreateByDefault(self):
        try:
            @patch.object(SomeClass, 'frooble', sentinel.Frooble)
            def test():
                self.assertEqual(SomeClass.frooble, sentinel.Frooble)

            test()
        except AttributeError:
            pass
        else:
            self.fail('Patching non existent attributes should fail')
        self.assertFalse(hasattr(SomeClass, 'frooble'))


    def testPathWithStaticMethods(self):
        class Foo(object):
            @staticmethod
            def woot():
                return sentinel.Static

        @patch.object(Foo, 'woot', staticmethod(lambda: sentinel.Patched))
        def anonymous():
            self.assertEqual(Foo.woot(), sentinel.Patched)
        anonymous()

        self.assertEqual(Foo.woot(), sentinel.Static)


    def testPatchLocal(self):
        foo = sentinel.Foo
        @patch.object(sentinel, 'Foo', 'Foo')
        def anonymous():
            self.assertEqual(sentinel.Foo, 'Foo')
        anonymous()

        self.assertEqual(sentinel.Foo, foo)


    def testPatchSlots(self):
        class Foo(object):
            __slots__ = ('Foo',)

        foo = Foo()
        foo.Foo = sentinel.Foo

        @patch.object(foo, 'Foo', 'Foo')
        def anonymous():
            self.assertEqual(foo.Foo, 'Foo')
        anonymous()

        self.assertEqual(foo.Foo, sentinel.Foo)

    def testPatchObjectClassDecorator(self):
        class Something(object):
            attribute = sentinel.Original

        class Foo(object):
            def test_method(other_self):
                self.assertEqual(Something.attribute, sentinel.Patched, "unpatched")
            def not_test_method(other_self):
                self.assertEqual(Something.attribute, sentinel.Original, "non-test method patched")
        Foo = patch.object(Something, 'attribute', sentinel.Patched)(Foo)

        f = Foo()
        f.test_method()
        f.not_test_method()

        self.assertEqual(Something.attribute, sentinel.Original, "patch not restored")


    def testPatchClassDecorator(self):
        class Something(object):
            attribute = sentinel.Original

        class Foo(object):
            def test_method(other_self, mock_something):
                self.assertEqual(PTModule.something, mock_something, "unpatched")
            def not_test_method(other_self):
                self.assertEqual(PTModule.something, sentinel.Something, "non-test method patched")
        Foo = patch('%s.something' % __name__)(Foo)

        f = Foo()
        f.test_method()
        f.not_test_method()

        self.assertEqual(Something.attribute, sentinel.Original, "patch not restored")
        self.assertEqual(PTModule.something, sentinel.Something, "patch not restored")

    @unittest2.skipUnless(with_available, "test requires Python >= 2.5")
    def testPatchObjectDeprecation(self):
        # needed to enable the deprecation warnings
        warnings.simplefilter('default')

        @apply
        @examine_warnings
        def _examine_warnings(ws):
            patch_object(SomeClass, 'class_attribute', spec=SomeClass)
            warning = ws[0]
            self.assertIs(warning.category, DeprecationWarning)

    def testPatchObjectTwice(self):
        class Something(object):
            attribute = sentinel.Original
            next_attribute = sentinel.Original2

        @apply
        @patch.object(Something, 'attribute', sentinel.Patched)
        @patch.object(Something, 'attribute', sentinel.Patched)
        def test():
            self.assertEqual(Something.attribute, sentinel.Patched, "unpatched")

        self.assertEqual(Something.attribute, sentinel.Original, "patch not restored")

    def testPatchDict(self):
        foo = {'initial': object(), 'other': 'something'}
        original = foo.copy()

        @apply
        @patch.dict(foo)
        def test():
            foo['a'] = 3
            del foo['initial']
            foo['other'] = 'something else'

        self.assertEqual(foo, original)

        @apply
        @patch.dict(foo, {'a': 'b'})
        def test():
            self.assertEqual(len(foo), 3)
            self.assertEqual(foo['a'], 'b')

        self.assertEqual(foo, original)

        @apply
        @patch.dict(foo, [('a', 'b')])
        def test():
            self.assertEqual(len(foo), 3)
            self.assertEqual(foo['a'], 'b')

        self.assertEqual(foo, original)

    def testPatchDictWithContainerObject(self):
        foo = Container()
        foo['initial'] = object()
        foo['other'] =  'something'

        original = foo.values.copy()

        @apply
        @patch.dict(foo)
        def test():
            foo['a'] = 3
            del foo['initial']
            foo['other'] = 'something else'

        self.assertEqual(foo.values, original)

        @apply
        @patch.dict(foo, {'a': 'b'})
        def test():
            self.assertEqual(len(foo.values), 3)
            self.assertEqual(foo['a'], 'b')

        self.assertEqual(foo.values, original)

    def testPatchDictWithClear(self):
        foo = {'initial': object(), 'other': 'something'}
        original = foo.copy()

        @apply
        @patch.dict(foo, clear=True)
        def test():
            self.assertEqual(foo, {})
            foo['a'] = 3
            foo['other'] = 'something else'

        self.assertEqual(foo, original)

        @apply
        @patch.dict(foo, {'a': 'b'}, clear=True)
        def test():
            self.assertEqual(foo, {'a': 'b'})

        self.assertEqual(foo, original)

        @apply
        @patch.dict(foo, [('a', 'b')], clear=True)
        def test():
            self.assertEqual(foo, {'a': 'b'})

        self.assertEqual(foo, original)


    def testPatchDictWithContainerObjectAndClear(self):
        foo = Container()
        foo['initial'] = object()
        foo['other'] =  'something'

        original = foo.values.copy()

        @apply
        @patch.dict(foo, clear=True)
        def test():
            self.assertEqual(foo.values, {})
            foo['a'] = 3
            foo['other'] = 'something else'

        self.assertEqual(foo.values, original)

        @apply
        @patch.dict(foo, {'a': 'b'}, clear=True)
        def test():
            self.assertEqual(foo.values, {'a': 'b'})

        self.assertEqual(foo.values, original)

    def testNamePreserved(self):
        foo = {}

        @patch('tests.testpatch.SomeClass', object())
        @patch('tests.testpatch.SomeClass', object(), mocksignature=True)
        @patch.object(SomeClass, object())
        @patch.dict(foo)
        def some_name():
            pass

        self.assertEqual(some_name.__name__, 'some_name')

    def testPatchWithException(self):
        foo = {}

        @patch.dict(foo, {'a': 'b'})
        def test():
            raise NameError('Konrad')
        try:
            test()
        except NameError:
            pass
        else:
            self.fail('NameError not raised by test')

        self.assertEqual(foo, {})

    def testPatchDictWithString(self):
        @apply
        @patch.dict('os.environ', {'konrad_delong': 'some value'})
        def test():
            self.assertIn('konrad_delong', os.environ)

    def DONTtestPatchDescriptor(self):
        # would be some effort to fix this - we could special case the
        # builtin descriptors: classmethod, property, staticmethod
        class Nothing(object):
            foo = None

        class Something(object):
            foo = {}

            @patch.object(Nothing, 'foo', 2)
            @classmethod
            def klass(cls):
                self.assertIs(cls, Something)

            @patch.object(Nothing, 'foo', 2)
            @staticmethod
            def static(arg):
                return arg

            @patch.dict(foo)
            @classmethod
            def klass_dict(cls):
                self.assertIs(cls, Something)

            @patch.dict(foo)
            @staticmethod
            def static_dict(arg):
                return arg

        # these will raise exceptions if patching descriptors is broken
        self.assertEqual(Something.static('f00'), 'f00')
        Something.klass()
        self.assertEqual(Something.static_dict('f00'), 'f00')
        Something.klass_dict()

        something = Something()
        self.assertEqual(something.static('f00'), 'f00')
        something.klass()
        self.assertEqual(something.static_dict('f00'), 'f00')
        something.klass_dict()


    def testPatchSpecSet(self):
        @patch('tests.testpatch.SomeClass', spec=SomeClass, spec_set=True)
        def test(MockClass):
            MockClass.z = 'foo'

        self.assertRaises(AttributeError, test)

        @patch.object(support, 'SomeClass', spec=SomeClass, spec_set=True)
        def test(MockClass):
            MockClass.z = 'foo'

        self.assertRaises(AttributeError, test)
        @patch('tests.testpatch.SomeClass', spec_set=True)
        def test(MockClass):
            MockClass.z = 'foo'

        self.assertRaises(AttributeError, test)

        @patch.object(support, 'SomeClass', spec_set=True)
        def test(MockClass):
            MockClass.z = 'foo'

        self.assertRaises(AttributeError, test)


    def testSpecSetInherit(self):
        @patch('tests.testpatch.SomeClass', spec_set=True)
        def test(MockClass):
            instance = MockClass()
            instance.z = 'foo'

        self.assertRaises(AttributeError, test)


    def testPatchStartStop(self):
        original = something
        patcher = patch('%s.something' % __name__)
        self.assertIs(something, original)
        mock = patcher.start()
        self.assertIsNot(mock, original)
        try:
            self.assertIs(something, mock)
        finally:
            patcher.stop()
        self.assertIs(something, original)


    def testPatchObjectStartStop(self):
        original = something
        patcher = patch.object(PTModule, 'something', 'foo')
        self.assertIs(something, original)
        replaced = patcher.start()
        self.assertEqual(replaced, 'foo')
        try:
            self.assertIs(something, replaced)
        finally:
            patcher.stop()
        self.assertIs(something, original)


    def testPatchDictStartStop(self):
        d = {'foo': 'bar'}
        original = d.copy()
        patcher = patch.dict(d, [('spam', 'eggs')], clear=True)
        self.assertEqual(d, original)

        patcher.start()
        self.assertEqual(d, {'spam': 'eggs'})

        patcher.stop()
        self.assertEqual(d, original)


    def testPatchDictClassDecorator(self):
        this = self
        d = {'spam': 'eggs'}
        original = d.copy()

        class Test(object):
            def test_first(self):
                this.assertEqual(d, {'foo': 'bar'})
            def test_second(self):
                this.assertEqual(d, {'foo': 'bar'})

        Test = patch.dict(d, {'foo': 'bar'}, clear=True)(Test)
        self.assertEqual(d, original)

        test = Test()

        test.test_first()
        self.assertEqual(d, original)

        test.test_second()
        self.assertEqual(d, original)

        test = Test()

        test.test_first()
        self.assertEqual(d, original)

        test.test_second()
        self.assertEqual(d, original)


    def testGetOnlyProxy(self):
        class Something(object):
            foo = 'foo'
        class SomethingElse:
            foo = 'foo'

        for thing in Something, SomethingElse, Something(), SomethingElse:
            proxy = _getProxy(thing)

            @patch.object(proxy, 'foo', 'bar')
            def test():
                self.assertEqual(proxy.foo, 'bar')
            test()
            self.assertEqual(proxy.foo, 'foo')
            self.assertEqual(thing.foo, 'foo')
            self.assertNotIn('foo', proxy.__dict__)


    def testGetSetDeleteProxy(self):
        class Something(object):
            foo = 'foo'
        class SomethingElse:
            foo = 'foo'

        for thing in Something, SomethingElse, Something(), SomethingElse:
            proxy = _getProxy(Something, get_only=False)

            @patch.object(proxy, 'foo', 'bar')
            def test():
                self.assertEqual(proxy.foo, 'bar')
            test()
            self.assertEqual(proxy.foo, 'foo')
            self.assertEqual(thing.foo, 'foo')
            self.assertNotIn('foo', proxy.__dict__)



if __name__ == '__main__':
    unittest2.main()

