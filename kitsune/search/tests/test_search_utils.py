from nose.tools import ok_

from kitsune.search.forms import SimpleSearchForm
from kitsune.search.search_utils import generate_simple_search
from kitsune.sumo.tests import TestCase


class SimpleSearchTests(TestCase):
    def test_language_en_us(self):
        form = SimpleSearchForm({"q": "foo"})
        ok_(form.is_valid())

        s = generate_simple_search(form, "en-US", with_highlights=False)

        # NB: Comparing bits of big trees is hard, so we serialize it
        # and look for strings.
        s_string = str(s.build_search())
        # Verify locale
        ok_("{'term': {'document_locale': 'en-US'}}" in s_string)
        # Verify en-US has the right synonym-enhanced analyzer
        ok_("'analyzer': 'snowball-english-synonyms'" in s_string)

    def test_language_fr(self):
        form = SimpleSearchForm({"q": "foo"})
        ok_(form.is_valid())

        s = generate_simple_search(form, "fr", with_highlights=False)

        s_string = str(s.build_search())
        # Verify locale
        ok_("{'term': {'document_locale': 'fr'}}" in s_string)
        # Verify fr has right synonym-less analyzer
        ok_("'analyzer': 'snowball-french'" in s_string)

    def test_language_zh_cn(self):
        form = SimpleSearchForm({"q": "foo"})
        ok_(form.is_valid())

        s = generate_simple_search(form, "zh-CN", with_highlights=False)

        s_string = str(s.build_search())
        # Verify locale
        ok_("{'term': {'document_locale': 'zh-CN'}}" in s_string)
        # Verify standard analyzer is used
        ok_("'analyzer': 'chinese'" in s_string)

    def test_with_highlights(self):
        form = SimpleSearchForm({"q": "foo"})
        ok_(form.is_valid())

        s = generate_simple_search(form, "en-US", with_highlights=True)
        ok_("highlight" in s.build_search())

        s = generate_simple_search(form, "en-US", with_highlights=False)
        ok_("highlight" not in s.build_search())
