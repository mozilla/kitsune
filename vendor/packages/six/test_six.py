import operator
import sys
import types

import py

import six


def test_add_doc():
    def f():
        """Icky doc"""
        pass
    six._add_doc(f, """New doc""")
    assert f.__doc__ == "New doc"


def test_import_module():
    from logging import handlers
    m = six._import_module("logging.handlers")
    assert m is handlers


def test_integer_types():
    assert isinstance(1, six.integer_types)
    assert isinstance(-1, six.integer_types)
    assert isinstance(six.MAXSIZE + 23, six.integer_types)
    assert not isinstance(.1, six.integer_types)


def test_string_types():
    assert isinstance("hi", six.string_types)
    assert isinstance(six.u("hi"), six.string_types)
    assert issubclass(six.text_type, six.string_types)


def test_class_types():
    class X:
        pass
    class Y(object):
        pass
    assert isinstance(X, six.class_types)
    assert isinstance(Y, six.class_types)
    assert not isinstance(X(), six.class_types)


def test_text_type():
    assert type(six.u("hi")) is six.text_type


def test_binary_type():
    assert type(six.b("hi")) is six.binary_type


def test_MAXSIZE():
    try:
        # This shouldn't raise an overflow error.
        six.MAXSIZE.__index__()
    except AttributeError:
        # Before Python 2.6.
        pass
    if sys.version_info[:2] == (2, 4):
        exc = ValueError
    else:
        exc = OverflowError
    py.test.raises(exc, operator.mul, [None], six.MAXSIZE + 1)


def test_lazy():
    if six.PY3:
        html_name = "html.parser"
    else:
        html_name = "HTMLParser"
    assert html_name not in sys.modules
    mod = six.moves.html_parser
    assert sys.modules[html_name] is mod
    assert "htmlparser" not in six._MovedItems.__dict__


try:
    import _tkinter
except ImportError:
    have_tkinter = False
else:
    have_tkinter = True

@py.test.mark.parametrize("item_name",
                          [item.name for item in six._moved_attributes])
def test_move_items(item_name):
    """Ensure that everything loads correctly."""
    try:
        getattr(six.moves, item_name)
    except AttributeError:
        if item_name == "zip_longest" and sys.version_info < (2, 6):
            py.test.skip("zip_longest only available on 2.6+")
    except ImportError:
        if item_name == "winreg" and not sys.platform.startswith("win"):
            py.test.skip("Windows only module")
        if item_name.startswith("tkinter") and not have_tkinter:
            py.test.skip("requires tkinter")
        raise


@py.test.mark.parametrize("item_name",
                          [item.name for item in six._urllib_parse_moved_attributes])
def test_move_items_urllib_parse(item_name):
    """Ensure that everything loads correctly."""
    if item_name == "ParseResult" and sys.version_info < (2, 5):
        py.test.skip("ParseResult is only found on 2.5+")
    if item_name in ("parse_qs", "parse_qsl") and sys.version_info < (2, 6):
        py.test.skip("parse_qs[l] is new in 2.6")
    getattr(six.moves.urllib.parse, item_name)


@py.test.mark.parametrize("item_name",
                          [item.name for item in six._urllib_error_moved_attributes])
def test_move_items_urllib_error(item_name):
    """Ensure that everything loads correctly."""
    getattr(six.moves.urllib.error, item_name)


@py.test.mark.parametrize("item_name",
                          [item.name for item in six._urllib_request_moved_attributes])
def test_move_items_urllib_request(item_name):
    """Ensure that everything loads correctly."""
    getattr(six.moves.urllib.request, item_name)


@py.test.mark.parametrize("item_name",
                          [item.name for item in six._urllib_response_moved_attributes])
def test_move_items_urllib_response(item_name):
    """Ensure that everything loads correctly."""
    getattr(six.moves.urllib.response, item_name)


@py.test.mark.parametrize("item_name",
                          [item.name for item in six._urllib_robotparser_moved_attributes])
def test_move_items_urllib_robotparser(item_name):
    """Ensure that everything loads correctly."""
    getattr(six.moves.urllib.robotparser, item_name)


def test_filter():
    from six.moves import filter
    f = filter(lambda x: x % 2, range(10))
    assert six.advance_iterator(f) == 1


def test_filter_false():
    from six.moves import filterfalse
    f = filterfalse(lambda x: x % 3, range(10))
    assert six.advance_iterator(f) == 0
    assert six.advance_iterator(f) == 3
    assert six.advance_iterator(f) == 6

def test_map():
    from six.moves import map
    assert six.advance_iterator(map(lambda x: x + 1, range(2))) == 1


def test_zip():
    from six.moves import zip
    assert six.advance_iterator(zip(range(2), range(2))) == (0, 0)


@py.test.mark.skipif("sys.version_info < (2, 6)")
def test_zip_longest():
    from six.moves import zip_longest
    it = zip_longest(range(2), range(1))

    assert six.advance_iterator(it) == (0, 0)
    assert six.advance_iterator(it) == (1, None)


class TestCustomizedMoves:

    def teardown_method(self, meth):
        try:
            del six._MovedItems.spam
        except AttributeError:
            pass
        try:
            del six.moves.__dict__["spam"]
        except KeyError:
            pass


    def test_moved_attribute(self):
        attr = six.MovedAttribute("spam", "foo", "bar")
        if six.PY3:
            assert attr.mod == "bar"
        else:
            assert attr.mod == "foo"
        assert attr.attr == "spam"
        attr = six.MovedAttribute("spam", "foo", "bar", "lemma")
        assert attr.attr == "lemma"
        attr = six.MovedAttribute("spam", "foo", "bar", "lemma", "theorm")
        if six.PY3:
            assert attr.attr == "theorm"
        else:
            assert attr.attr == "lemma"


    def test_moved_module(self):
        attr = six.MovedModule("spam", "foo")
        if six.PY3:
            assert attr.mod == "spam"
        else:
            assert attr.mod == "foo"
        attr = six.MovedModule("spam", "foo", "bar")
        if six.PY3:
            assert attr.mod == "bar"
        else:
            assert attr.mod == "foo"


    def test_custom_move_module(self):
        attr = six.MovedModule("spam", "six", "six")
        six.add_move(attr)
        six.remove_move("spam")
        assert not hasattr(six.moves, "spam")
        attr = six.MovedModule("spam", "six", "six")
        six.add_move(attr)
        from six.moves import spam
        assert spam is six
        six.remove_move("spam")
        assert not hasattr(six.moves, "spam")


    def test_custom_move_attribute(self):
        attr = six.MovedAttribute("spam", "six", "six", "u", "u")
        six.add_move(attr)
        six.remove_move("spam")
        assert not hasattr(six.moves, "spam")
        attr = six.MovedAttribute("spam", "six", "six", "u", "u")
        six.add_move(attr)
        from six.moves import spam
        assert spam is six.u
        six.remove_move("spam")
        assert not hasattr(six.moves, "spam")


    def test_empty_remove(self):
        py.test.raises(AttributeError, six.remove_move, "eggs")


def test_get_unbound_function():
    class X(object):
        def m(self):
            pass
    assert six.get_unbound_function(X.m) is X.__dict__["m"]


def test_get_method_self():
    class X(object):
        def m(self):
            pass
    x = X()
    assert six.get_method_self(x.m) is x
    py.test.raises(AttributeError, six.get_method_self, 42)


def test_get_method_function():
    class X(object):
        def m(self):
            pass
    x = X()
    assert six.get_method_function(x.m) is X.__dict__["m"]
    py.test.raises(AttributeError, six.get_method_function, hasattr)


def test_get_function_closure():
    def f():
        x = 42
        def g():
            return x
        return g
    cell = six.get_function_closure(f())[0]
    assert type(cell).__name__ == "cell"


def test_get_function_code():
    def f():
        pass
    assert isinstance(six.get_function_code(f), types.CodeType)
    if not hasattr(sys, "pypy_version_info"):
        py.test.raises(AttributeError, six.get_function_code, hasattr)


def test_get_function_defaults():
    def f(x, y=3, b=4):
        pass
    assert six.get_function_defaults(f) == (3, 4)


def test_get_function_globals():
    def f():
        pass
    assert six.get_function_globals(f) is globals()


def test_dictionary_iterators(monkeypatch):
    class MyDict(dict):
        if not six.PY3:
            def lists(self, **kw):
                return [1, 2, 3]
        def iterlists(self, **kw):
            return iter([1, 2, 3])
    f = MyDict.iterlists
    del MyDict.iterlists
    setattr(MyDict, six._iterlists, f)
    d = MyDict(zip(range(10), reversed(range(10))))
    for name in "keys", "values", "items", "lists":
        meth = getattr(six, "iter" + name)
        it = meth(d)
        assert not isinstance(it, list)
        assert list(it) == list(getattr(d, name)())
        py.test.raises(StopIteration, six.advance_iterator, it)
        record = []
        def with_kw(*args, **kw):
            record.append(kw["kw"])
            return old(*args)
        old = getattr(MyDict, getattr(six, "_iter" + name))
        monkeypatch.setattr(MyDict, getattr(six, "_iter" + name), with_kw)
        meth(d, kw=42)
        assert record == [42]
        monkeypatch.undo()


def test_advance_iterator():
    assert six.next is six.advance_iterator
    l = [1, 2]
    it = iter(l)
    assert six.next(it) == 1
    assert six.next(it) == 2
    py.test.raises(StopIteration, six.next, it)
    py.test.raises(StopIteration, six.next, it)


def test_iterator():
    class myiter(six.Iterator):
        def __next__(self):
            return 13
    assert six.advance_iterator(myiter()) == 13
    class myitersub(myiter):
        def __next__(self):
            return 14
    assert six.advance_iterator(myitersub()) == 14


def test_callable():
    class X:
        def __call__(self):
            pass
        def method(self):
            pass
    assert six.callable(X)
    assert six.callable(X())
    assert six.callable(test_callable)
    assert six.callable(hasattr)
    assert six.callable(X.method)
    assert six.callable(X().method)
    assert not six.callable(4)
    assert not six.callable("string")


def test_create_bound_method():
    class X(object):
        pass
    def f(self):
        return self
    x = X()
    b = six.create_bound_method(f, x)
    assert isinstance(b, types.MethodType)
    assert b() is x


if six.PY3:

    def test_b():
        data = six.b("\xff")
        assert isinstance(data, bytes)
        assert len(data) == 1
        assert data == bytes([255])


    def test_u():
        s = six.u("hi")
        assert isinstance(s, str)
        assert s == "hi"

else:

    def test_b():
        data = six.b("\xff")
        assert isinstance(data, str)
        assert len(data) == 1
        assert data == "\xff"


    def test_u():
        s = six.u("hi")
        assert isinstance(s, unicode)
        assert s == "hi"


def test_u_escapes():
    s = six.u("\u1234")
    assert len(s) == 1


def test_unichr():
    assert six.u("\u1234") == six.unichr(0x1234)
    assert type(six.u("\u1234")) is type(six.unichr(0x1234))


def test_int2byte():
    assert six.int2byte(3) == six.b("\x03")
    py.test.raises((OverflowError, ValueError), six.int2byte, 256)


def test_byte2int():
    assert six.byte2int(six.b("\x03")) == 3
    assert six.byte2int(six.b("\x03\x04")) == 3
    py.test.raises(IndexError, six.byte2int, six.b(""))


def test_bytesindex():
    assert six.indexbytes(six.b("hello"), 3) == ord("l")


def test_bytesiter():
    it = six.iterbytes(six.b("hi"))
    assert six.next(it) == ord("h")
    assert six.next(it) == ord("i")
    py.test.raises(StopIteration, six.next, it)


def test_StringIO():
    fp = six.StringIO()
    fp.write(six.u("hello"))
    assert fp.getvalue() == six.u("hello")


def test_BytesIO():
    fp = six.BytesIO()
    fp.write(six.b("hello"))
    assert fp.getvalue() == six.b("hello")


def test_exec_():
    def f():
        l = []
        six.exec_("l.append(1)")
        assert l == [1]
    f()
    ns = {}
    six.exec_("x = 42", ns)
    assert ns["x"] == 42
    glob = {}
    loc = {}
    six.exec_("global y; y = 42; x = 12", glob, loc)
    assert glob["y"] == 42
    assert "x" not in glob
    assert loc["x"] == 12
    assert "y" not in loc


def test_reraise():
    def get_next(tb):
        if six.PY3:
            return tb.tb_next.tb_next
        else:
            return tb.tb_next
    e = Exception("blah")
    try:
        raise e
    except Exception:
        tp, val, tb = sys.exc_info()
    try:
        six.reraise(tp, val, tb)
    except Exception:
        tp2, value2, tb2 = sys.exc_info()
        assert tp2 is Exception
        assert value2 is e
        assert tb is get_next(tb2)
    try:
        six.reraise(tp, val)
    except Exception:
        tp2, value2, tb2 = sys.exc_info()
        assert tp2 is Exception
        assert value2 is e
        assert tb2 is not tb
    try:
        six.reraise(tp, val, tb2)
    except Exception:
        tp2, value2, tb3 = sys.exc_info()
        assert tp2 is Exception
        assert value2 is e
        assert get_next(tb3) is tb2


def test_print_():
    save = sys.stdout
    out = sys.stdout = six.moves.StringIO()
    try:
        six.print_("Hello,", "person!")
    finally:
        sys.stdout = save
    assert out.getvalue() == "Hello, person!\n"
    out = six.StringIO()
    six.print_("Hello,", "person!", file=out)
    assert out.getvalue() == "Hello, person!\n"
    out = six.StringIO()
    six.print_("Hello,", "person!", file=out, end="")
    assert out.getvalue() == "Hello, person!"
    out = six.StringIO()
    six.print_("Hello,", "person!", file=out, sep="X")
    assert out.getvalue() == "Hello,Xperson!\n"
    out = six.StringIO()
    six.print_(six.u("Hello,"), six.u("person!"), file=out)
    result = out.getvalue()
    assert isinstance(result, six.text_type)
    assert result == six.u("Hello, person!\n")
    six.print_("Hello", file=None) # This works.
    out = six.StringIO()
    six.print_(None, file=out)
    assert out.getvalue() == "None\n"


def test_print_exceptions():
    py.test.raises(TypeError, six.print_, x=3)
    py.test.raises(TypeError, six.print_, end=3)
    py.test.raises(TypeError, six.print_, sep=42)


def test_with_metaclass():
    class Meta(type):
        pass
    class X(six.with_metaclass(Meta)):
        pass
    assert type(X) is Meta
    assert issubclass(X, object)
    class Base(object):
        pass
    class X(six.with_metaclass(Meta, Base)):
        pass
    assert type(X) is Meta
    assert issubclass(X, Base)
    class Base2(object):
        pass
    class X(six.with_metaclass(Meta, Base, Base2)):
        pass
    assert type(X) is Meta
    assert issubclass(X, Base)
    assert issubclass(X, Base2)


def test_add_metaclass():
    class Meta(type):
        pass
    class X:
        "success"
    X = six.add_metaclass(Meta)(X)
    assert type(X) is Meta
    assert issubclass(X, object)
    assert X.__module__ == __name__
    assert X.__doc__ == "success"
    class Base(object):
        pass
    class X(Base):
        pass
    X = six.add_metaclass(Meta)(X)
    assert type(X) is Meta
    assert issubclass(X, Base)
    class Base2(object):
        pass
    class X(Base, Base2):
        pass
    X = six.add_metaclass(Meta)(X)
    assert type(X) is Meta
    assert issubclass(X, Base)
    assert issubclass(X, Base2)

    # Test a second-generation subclass of a type.
    class Meta1(type):
        m1 = "m1"
    class Meta2(Meta1):
        m2 = "m2"
    class Base:
        b = "b"
    Base = six.add_metaclass(Meta1)(Base)
    class X(Base):
        x = "x"
    X = six.add_metaclass(Meta2)(X)
    assert type(X) is Meta2
    assert issubclass(X, Base)
    assert type(Base) is Meta1
    assert "__dict__" not in vars(X)
    instance = X()
    instance.attr = "test"
    assert vars(instance) == {"attr": "test"}
    assert instance.b == Base.b
    assert instance.x == X.x

    # test a class with slots
    class MySlots(object):
        __slots__ = ["a", "b"]
    MySlots = six.add_metaclass(Meta1)(MySlots)

    assert MySlots.__slots__ == ["a", "b"]
    instance = MySlots()
    instance.a = "foo"
    py.test.raises(AttributeError, setattr, instance, "c", "baz")
