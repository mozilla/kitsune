# -*- coding: utf-8 -*-
from collections import namedtuple
from datetime import datetime

import jinja2
from babel.dates import format_date, format_datetime, format_time
from django.forms.fields import CharField
from django.test.client import RequestFactory
from pyquery import PyQuery as pq
from pytz import timezone

from kitsune.sumo.templatetags.jinja_helpers import (
    DateTimeFormatError,
    class_selected,
    collapse_linebreaks,
    datetimeformat,
    f,
    fe,
    json,
    label_with_help,
    number,
    remove,
    static,
    timesince,
    url,
    urlparams,
    yesno,
)
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse


class TestHelpers(TestCase):
    def test_urlparams_unicode(self):
        context = {"q": "Français"}
        self.assertEqual("/foo?q=Fran%C3%A7ais", urlparams("/foo", **context))
        context["q"] = "\u0125help"
        self.assertEqual("/foo?q=%C4%A5help", urlparams("/foo", **context))

    def test_urlparams_valid(self):
        context = {"a": "foo", "b": "bar"}
        self.assertEqual("/foo?a=foo&b=bar", urlparams("/foo", **context))

    def test_urlparams_query_string(self):
        self.assertEqual("/foo?a=foo&b=bar", urlparams("/foo?a=foo", b="bar"))

    def test_urlparams_multivalue(self):
        self.assertEqual("/foo?a=foo&a=bar", urlparams("/foo?a=foo&a=bar"))
        self.assertEqual("/foo?a=bar", urlparams("/foo?a=foo", a="bar"))

    def test_urlparams_none(self):
        """Assert a value of None doesn't make it into the query string."""
        self.assertEqual("/foo", urlparams("/foo", bar=None))

    def test_collapse_linebreaks(self):
        """Make sure collapse_linebreaks works on some tricky cases."""
        self.assertEqual(
            collapse_linebreaks("\r\n \t  \n\r  Trouble\r\n\r\nshooting \r\n"),
            "\r\n  Trouble\r\nshooting\r\n",
        )
        self.assertEqual(
            collapse_linebreaks(
                "Application Basics\n      \n\n      \n      "
                "\n\n\n        \n          \n            \n   "
                "           Name"
            ),
            "Application Basics\r\n              Name",
        )

    def test_label_with_help(self):
        field = CharField(label="Foo", help_text="Foo bar")
        field.auto_id = "foo"
        expect = '<label for="foo" title="Foo bar">Foo</label>'
        self.assertEqual(expect, label_with_help(field))

    def test_yesno(self):
        self.assertEqual("Yes", yesno(True))
        self.assertEqual("No", yesno(False))
        self.assertEqual("Yes", yesno(1))
        self.assertEqual("No", yesno(0))

    def test_number(self):
        context = {"request": namedtuple("R", "LANGUAGE_CODE")("en-US")}
        self.assertEqual("5,000", number(context, 5000))
        self.assertEqual("", number(context, None))

    def test_remove_in_list(self):
        tags = ["tag1", "tag2"]
        tag = "tag3"
        tags.append(tag)
        tags = remove(tags, tag)
        self.assertEqual(2, len(tags))
        assert tag not in tags

    def test_remove_not_in_list(self):
        tags = ["tag1", "tag2"]
        tag = "tag3"
        tags = remove(tags, tag)
        # Nothing was removed and we didn't crash.
        self.assertEqual(2, len(tags))

    def test_static_failure(self):
        """Should not raise an error if the static file is missing."""
        static("does/not/exist.js")


class TestDateTimeFormat(TestCase):
    def setUp(self):
        self.timezone = timezone("US/Pacific")
        self.locale = "en_US"
        url_ = reverse("forums.threads", args=["testslug"])
        self.context = {"request": RequestFactory().get(url_)}
        self.context["request"].LANGUAGE_CODE = self.locale
        self.context["request"].session = {"timezone": self.timezone}

    def _get_datetime_result(
        self, locale, timezone, format="short", return_format="shortdatetime"
    ):
        value = datetime.fromordinal(733900)
        value = self.timezone.localize(value)
        value_test = value.astimezone(self.timezone)

        value_localize = value_test.astimezone(timezone)
        value_expected = format_datetime(
            value_localize, format=format, locale=locale, tzinfo=timezone
        )
        value_returned = datetimeformat(self.context, value_test, format=return_format)
        self.assertEqual(pq(value_returned)("time").text(), value_expected)

    def test_today(self):
        """Expects shortdatetime, format: Today at {time}."""
        date_today = datetime.today()
        date_localize = self.timezone.localize(date_today)
        value_returned = str(datetimeformat(self.context, date_today))
        value_expected = "Today at %s" % format_time(
            date_localize, format="short", locale=self.locale, tzinfo=self.timezone
        )
        self.assertEqual(pq(value_returned)("time").text(), value_expected)

    def test_locale(self):
        """Expects shortdatetime in French."""
        self.context["request"].LANGUAGE_CODE = "fr"
        self._get_datetime_result("fr", self.timezone)

    def test_default(self):
        """Expects shortdatetime."""
        self._get_datetime_result(self.locale, self.timezone)

    def test_longdatetime(self):
        """Expects long format."""
        self._get_datetime_result(self.locale, self.timezone, "long", "longdatetime")

    def test_date(self):
        """Expects date format."""
        value_test = datetime.fromordinal(733900)
        value_expected = format_date(value_test, locale=self.locale)
        value_returned = datetimeformat(self.context, value_test, format="date")
        self.assertEqual(pq(value_returned)("time").text(), value_expected)

    def test_time(self):
        """Expects time format."""
        value_test = datetime.fromordinal(733900)
        value_localize = self.timezone.localize(value_test)
        value_expected = format_time(value_localize, locale=self.locale, tzinfo=self.timezone)
        value_returned = datetimeformat(self.context, value_test, format="time")
        self.assertEqual(pq(value_returned)("time").text(), value_expected)

    def test_datetime(self):
        """Expects datetime format."""
        self._get_datetime_result(self.locale, self.timezone, "medium", "datetime")

    def test_year(self):
        """Expects year format."""
        self._get_datetime_result(self.locale, self.timezone, "yyyy", "year")

    def test_unknown_format(self):
        """Unknown format raises DateTimeFormatError."""
        date_today = datetime.today()
        with self.assertRaises(DateTimeFormatError):
            datetimeformat(self.context, date_today, format="unknown")

    def test_timezone(self):
        """Expects Europe/Paris timezone."""
        fr_timezone = timezone("Europe/Paris")
        self.context["request"].LANGUAGE_CODE = "fr"
        self.context["request"].session = {"timezone": fr_timezone}
        self._get_datetime_result("fr", fr_timezone, "medium", "datetime")

    def test_timezone_different_locale(self):
        """Expects Europe/Paris timezone with different locale."""
        fr_timezone = timezone("Europe/Paris")
        self.context["request"].LANGUAGE_CODE = "tr"
        self.context["request"].session = {"timezone": fr_timezone}
        self._get_datetime_result("tr", fr_timezone, "medium", "datetime")

    def test_invalid_value(self):
        """Passing invalid value raises ValueError."""
        with self.assertRaises(ValueError):
            datetimeformat(self.context, "invalid")

    def test_json_helper(self):
        self.assertEqual("false", json(False))
        self.assertEqual('{"foo": "bar"}', json({"foo": "bar"}))


class TestUrlHelper(TestCase):
    """Tests for the url helper."""

    def test_with_locale(self):
        """Passing a locale to url creates a URL for that locale."""
        u = url("home", locale="es")
        self.assertEqual("/es/", u)


class TimesinceTests(TestCase):
    """Tests for the timesince filter"""

    def test_none(self):
        """If None is passed in, timesince returns ''."""
        self.assertEqual("", timesince(None))

    def test_trunc(self):
        """Assert it returns only the most significant time division."""
        self.assertEqual("1 year ago", timesince(datetime(2000, 1, 2), now=datetime(2001, 2, 3)))

    def test_future(self):
        """Test behavior when date is in the future and also when omitting the
        `now` kwarg."""
        self.assertEqual("", timesince(datetime(9999, 1, 2)))


class TestFormat(TestCase):
    """Test the |f and |fe filters"""

    def test_f_handles_unicode_in_ascii_strings(self):
        var = "Pśetergnuś"
        # Note that the format string is not a unicode string.
        self.assertEqual(f("{0}", var), var)

    def test_fe_handles_unicode_in_ascii_strings(self):
        var = "Pśetergnuś"
        # Note that the format string is not a unicode string.
        self.assertEqual(fe("{0}", var), var)


class TestClassSelected(TestCase):
    """Test class_selected"""

    def test_is_escaped(self):
        value_returned = class_selected(1, 1)
        type_expected = jinja2.Markup
        self.assertEqual(type(value_returned), type_expected)

    def test_is_selected(self):
        value_returned = class_selected(1, 1)
        value_expected = 'class="selected"'
        self.assertEqual(value_returned, value_expected)

    def test_is_not_selected(self):
        value_returned = class_selected(0, 1)
        value_expected = ""
        self.assertEqual(value_returned, value_expected)
