from textwrap import dedent

from nose.tools import eq_
from pyquery import PyQuery as pq

from kitsune.search import es_utils, synonym_utils
from kitsune.search.tasks import update_synonyms_task
from kitsune.search.tests import ElasticTestCase, SynonymFactory
from kitsune.sumo.tests import LocalizingClient, TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.wiki.tests import DocumentFactory, RevisionFactory


class TestSynonymModel(TestCase):
    def test_serialize(self):
        syn = SynonymFactory(from_words="foo", to_words="bar")
        eq_("foo => bar", str(syn))


class TestFilterGenerator(TestCase):
    def test_name(self):
        """Test that the right name is returned."""
        name, _ = es_utils.es_get_synonym_filter("en-US")
        eq_(name, "synonyms-en-US")

    def test_no_synonyms(self):
        """Test that when there are no synonyms an alternate filter is made."""
        _, body = es_utils.es_get_synonym_filter("en-US")
        eq_(body, {"type": "synonym", "synonyms": ["firefox => firefox"],})

    def test_with_some_synonyms(self):
        SynonymFactory(from_words="foo", to_words="bar")
        SynonymFactory(from_words="baz", to_words="qux")

        _, body = es_utils.es_get_synonym_filter("en-US")

        expected = {
            "type": "synonym",
            "synonyms": ["foo => bar", "baz => qux",],
        }
        eq_(body, expected)


class TestSynonymParser(TestCase):
    def testItWorks(self):
        synonym_text = dedent(
            """
            one, two => apple, banana
            three => orange, grape
            four, five => jellybean
            """
        )
        synonyms = {
            [
                ("one, two", "apple, banana"),
                ("three", "orange, grape"),
                ("four, five", "jellybean"),
            ]
        }
        eq_(synonyms, synonym_utils.parse_synonyms(synonym_text))

    def testTooManyArrows(self):
        try:
            synonym_utils.parse_synonyms("foo => bar => baz")
        except synonym_utils.SynonymParseError as e:
            eq_(len(e.errors), 1)
        else:
            assert False, "Parser did not catch error as expected."

    def testTooFewArrows(self):
        try:
            synonym_utils.parse_synonyms("foo, bar, baz")
        except synonym_utils.SynonymParseError as e:
            eq_(len(e.errors), 1)
        else:
            assert False, "Parser did not catch error as expected."


class SearchViewWithSynonyms(ElasticTestCase):
    client_class = LocalizingClient

    def test_synonyms_work_in_search_view(self):
        d1 = DocumentFactory(title="frob")
        d2 = DocumentFactory(title="glork")
        RevisionFactory(document=d1, is_approved=True)
        RevisionFactory(document=d2, is_approved=True)

        self.refresh()

        # First search without synonyms
        response = self.client.get(reverse("search"), {"q": "frob"})
        doc = pq(response.content)
        header = doc.find("#search-results h2").text().strip()
        eq_(header, "Found 1 result for frob for All Products")

        # Now add a synonym.
        SynonymFactory(from_words="frob", to_words="frob, glork")
        update_synonyms_task()
        self.refresh()

        # Forward search
        response = self.client.get(reverse("search"), {"q": "frob"})
        doc = pq(response.content)
        header = doc.find("#search-results h2").text().strip()
        eq_(header, "Found 2 results for frob for All Products")

        # Reverse search
        response = self.client.get(reverse("search"), {"q": "glork"})
        doc = pq(response.content)
        header = doc.find("#search-results h2").text().strip()
        eq_(header, "Found 1 result for glork for All Products")
