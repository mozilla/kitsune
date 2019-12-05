import re
from datetime import datetime

from django.forms.widgets import Widget, Select, URLInput
from django.utils.dates import MONTHS
from django.utils.safestring import mark_safe

RE_DATE = re.compile(r'(\d{4})-(\d\d?)-(\d\d?)$')


class MonthYearWidget(Widget):
    """
    A Widget that splits date input into two <select> boxes for month and year,
    with 'day' defaulting to the first of the month ( 01 ).
    Based on SelectDateWidget, in
    http://djangosnippets.org/snippets/1688/
    """
    none_value = (0, '---')
    month_field = '%s_month'
    year_field = '%s_year'

    def __init__(self, attrs=None, years=None, required=True):
        # years is an optional list/tuple of years to use in the "year" select box.
        self.attrs = attrs or {}
        self.required = required
        if years:
            self.years = years
        else:
            this_year = datetime.date.today().year
            self.years = list(range(this_year, this_year + 10))

    def render(self, name, value, attrs=None):
        try:
            year_val, month_val = value.year, value.month
        except AttributeError:
            year_val = month_val = None
            if isinstance(value, basestring):
                match = RE_DATE.match(value)
                if match:
                    year_val, month_val, day_val = [int(v) for v in match.groups()]

        output = []

        if 'id' in self.attrs:
            id_ = self.attrs['id']
        else:
            id_ = 'id_%s' % name

        month_choices = list(MONTHS.items())
        if not (self.required and value):
            month_choices.append(self.none_value)
        month_choices.sort()
        local_attrs = self.build_attrs(dict(id=self.month_field % id_))
        s = Select(choices=month_choices)
        select_html = s.render(self.month_field % name, month_val, local_attrs)
        output.append(select_html)

        year_choices = [(i, i) for i in self.years]
        if not (self.required and value):
            year_choices.insert(0, self.none_value)
        local_attrs['id'] = self.year_field % id_
        s = Select(choices=year_choices)
        select_html = s.render(self.year_field % name, year_val, local_attrs)
        output.append(select_html)

        return mark_safe(u'\n'.join(output))

    def id_for_label(self, id_):
        return '%s_month' % id_
    id_for_label = classmethod(id_for_label)

    def value_from_datadict(self, data, files, name):
        y = data.get(self.year_field % name)
        m = data.get(self.month_field % name)

        if not y or not m or y == m == '0':
            return None

        try:
            return datetime.date(int(y), int(m), 1)
        except (TypeError, ValueError):
            return '%s-%s-%s' % (y, m, 1)


class PatternURLWidget(URLInput):
    """A URLWidget with a pattern attribute, set by self.pattern."""

    def render(self, *args, **kwargs):
        self.attrs['pattern'] = self.pattern
        return super(PatternURLWidget, self).render(*args, **kwargs)


class FacebookURLWidget(PatternURLWidget):
    """A URLWidget that requires a Facebook URL."""
    pattern = r'https?://(?:www\.)?facebook\.com/.+'
