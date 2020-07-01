from django import forms
from nose.tools import eq_
from pyquery import PyQuery as pq

from kitsune.sumo.tests import TestCase


class ExampleForm(forms.Form):
    """
    Example form to test some monkey patched Django fields.
    """

    date = forms.DateField()
    time = forms.TimeField()


class TestFields(TestCase):
    """
    We're not breaking fields when monkey patching in ``sumo/monkeypatch.py``.
    """

    def setUp(self):
        self.f = ExampleForm()

    def _attr_eq(self, field, attr, value):
        doc = pq(str(self.f[field]))
        eq_(value, doc.attr(attr))

    def test_date_field(self):
        self._attr_eq("date", "type", "date")

    def test_time_field(self):
        self._attr_eq("time", "type", "time")
