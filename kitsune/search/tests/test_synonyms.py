from nose.tools import eq_

from kitsune.search import es_utils
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
