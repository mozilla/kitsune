from nose.tools import eq_
from textwrap import dedent

from kitsune.search import es_utils, synonym_utils
from kitsune.search.tests import synonym
from kitsune.sumo.tests import TestCase


class TestSynonymModel(TestCase):

    def test_serialize(self):
        syn = synonym(from_words="foo", to_words="bar", save=True)
        eq_("foo => bar", unicode(syn))


class TestFilterGenerator(TestCase):

    def test_name(self):
        """Test that the right name is returned."""
        name, _ = es_utils.es_get_synonym_filter('en-US')
        eq_(name, 'synonyms-en-US')

    def test_no_synonyms(self):
        """Test that when there are no synonyms an alternate filter is made."""
        _, body = es_utils.es_get_synonym_filter('en-US')
        eq_(body, {
            'type': 'synonym',
            'synonyms': ['firefox => firefox'],
            })

    def test_with_some_synonyms(self):
        synonym(from_words='foo', to_words='bar', save=True)
        synonym(from_words='baz', to_words='qux', save=True)

        _, body = es_utils.es_get_synonym_filter('en-US')

        expected = {
            'type': 'synonym',
            'synonyms': [
                'foo => bar',
                'baz => qux',
            ],
        }

        eq_(body, expected)


class TestSynonymParser(TestCase):

    def testItWorks(self):
        synonym_text = dedent("""
            one, two => apple, banana
            three => orange, grape
            four, five => jellybean
            """)
        synonyms = set([
            ('one, two', 'apple, banana'),
            ('three', 'orange, grape'),
            ('four, five', 'jellybean'),
        ])
        eq_(synonyms, synonym_utils.parse_synonyms(synonym_text))

    def testTooManyArrows(self):
        try:
            synonym_utils.parse_synonyms('foo => bar => baz')
        except synonym_utils.SynonymParseError as e:
            eq_(len(e.errors), 1)
        else:
            assert False, "Parser did not catch error as expected."

    def testTooFewArrows(self):
        try:
            synonym_utils.parse_synonyms('foo, bar, baz')
        except synonym_utils.SynonymParseError as e:
            eq_(len(e.errors), 1)
        else:
            assert False, "Parser did not catch error as expected."
