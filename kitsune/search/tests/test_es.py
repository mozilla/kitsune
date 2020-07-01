# -*- coding: utf-8 -*-
import json
import unittest
from unittest import mock

from django.contrib.sites.models import Site
from nose.tools import eq_

from kitsune.questions.models import QuestionMappingType
from kitsune.questions.tests import AnswerFactory
from kitsune.questions.tests import AnswerVoteFactory
from kitsune.questions.tests import QuestionFactory
from kitsune.search import es_utils
from kitsune.search.models import generate_tasks
from kitsune.search.tests import ElasticTestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.wiki.models import DocumentMappingType
from kitsune.wiki.tests import ApprovedRevisionFactory
from kitsune.wiki.tests import DocumentFactory


class ElasticSearchSuggestionsTests(ElasticTestCase):
    @mock.patch.object(Site.objects, "get_current")
    def test_invalid_suggestions(self, get_current):
        """The suggestions API needs a query term."""
        get_current.return_value.domain = "testserver"
        response = self.client.get(reverse("search.suggestions", locale="en-US"))
        eq_(400, response.status_code)
        assert not response.content

    @mock.patch.object(Site.objects, "get_current")
    def test_suggestions(self, get_current):
        """Suggestions API is well-formatted."""
        get_current.return_value.domain = "testserver"

        doc = DocumentFactory(title="doc1 audio", locale="en-US", is_archived=False)
        ApprovedRevisionFactory(document=doc, summary="audio", content="audio")

        ques = QuestionFactory(title="q1 audio", tags=["desktop"])
        # ques.tags.add(u'desktop')
        ans = AnswerFactory(question=ques)
        AnswerVoteFactory(answer=ans, helpful=True)

        self.refresh()

        response = self.client.get(reverse("search.suggestions", locale="en-US"), {"q": "audio"})
        eq_(200, response.status_code)
        eq_("application/x-suggestions+json", response["content-type"])
        results = json.loads(response.content)

        eq_("audio", results[0])
        eq_(2, len(results[1]))
        eq_(0, len(results[2]))
        eq_(2, len(results[3]))


class TestUtils(ElasticTestCase):
    def test_get_documents(self):
        q = QuestionFactory()
        self.refresh()

        docs = es_utils.get_documents(QuestionMappingType, [q.id])
        eq_(docs[0]["id"], q.id)


class TestTasks(ElasticTestCase):
    @mock.patch.object(QuestionMappingType, "index")
    def test_tasks(self, index_fun):
        """Tests to make sure tasks are added and run"""
        q = QuestionFactory()
        # Don't call self.refresh here since that calls generate_tasks().

        eq_(index_fun.call_count, 0)

        q.save()
        generate_tasks()

        eq_(index_fun.call_count, 1)

    @mock.patch.object(QuestionMappingType, "index")
    def test_tasks_squashed(self, index_fun):
        """Tests to make sure tasks are squashed"""
        q = QuestionFactory()
        # Don't call self.refresh here since that calls generate_tasks().

        eq_(index_fun.call_count, 0)

        q.save()
        q.save()
        q.save()
        q.save()

        eq_(index_fun.call_count, 0)

        generate_tasks()

        eq_(index_fun.call_count, 1)


class TestMappings(unittest.TestCase):
    def test_mappings(self):
        # This is more of a linter than a test. If it passes, then
        # everything is fine. If it fails, then it means things are
        # not fine. Not fine? Yeah, it means that there are two fields
        # with the same name, but different types in the
        # mappings that share an index. That doesn't work in ES.

        # Doing it as a test seemed like a good idea since
        # it's likely to catch epic problems, but isn't in the runtime
        # code.

        # Verify mappings that share the same index don't conflict
        for index in es_utils.all_read_indexes():
            merged_mapping = {}

            for cls_name, mapping in list(es_utils.get_mappings(index).items()):
                mapping = mapping["properties"]

                for key, val in list(mapping.items()):
                    if key not in merged_mapping:
                        merged_mapping[key] = (val, [cls_name])
                        continue

                    # FIXME - We're comparing two dicts here. This might
                    # not work for non-trivial dicts.
                    if merged_mapping[key][0] != val:
                        raise es_utils.MappingMergeError(
                            "%s key different for %s and %s"
                            % (key, cls_name, merged_mapping[key][1])
                        )

                    merged_mapping[key][1].append(cls_name)

        # If we get here, then we're fine.


class TestAnalyzers(ElasticTestCase):
    def setUp(self):
        super(TestAnalyzers, self).setUp()

        self.locale_data = {
            "en-US": {"analyzer": "snowball-english", "content": "I have a cat.",},
            "es": {"analyzer": "snowball-spanish", "content": "Tieno un gato.",},
            "ar": {"analyzer": "arabic", "content": "لدي اثنين من القطط",},
            "he": {"analyzer": "standard", "content": "גאולוגיה היא אחד",},
        }

        self.docs = {}
        for locale, data in list(self.locale_data.items()):
            d = DocumentFactory(locale=locale)
            ApprovedRevisionFactory(document=d, content=data["content"])
            self.locale_data[locale]["doc"] = d

        self.refresh()

    def test_analyzer_choices(self):
        """Check that the indexer picked the right analyzer."""

        ids = [d.id for d in list(self.docs.values())]
        docs = es_utils.get_documents(DocumentMappingType, ids)
        for doc in docs:
            locale = doc["locale"]
            eq_(doc["_analyzer"], self.locale_data[locale]["analyzer"])

    def test_query_analyzer_upgrader(self):
        analyzer = "snowball-english-synonyms"
        before = {
            "document_title__match": "foo",
            "document_locale__match": "bar",
            "document_title__match_phrase": "baz",
            "document_locale__match_phrase": "qux",
        }
        expected = {
            "document_title__match_analyzer": ("foo", analyzer),
            "document_locale__match": "bar",
            "document_title__match_phrase_analyzer": ("baz", analyzer),
            "document_locale__match_phrase": "qux",
        }
        actual = es_utils.es_query_with_analyzer(before, "en-US")
        eq_(actual, expected)

    def _check_locale_tokenization(self, locale, expected_tokens, p_tag=True):
        """
        Check that a given locale's document was tokenized correctly.

        * `locale` - The locale to check.
        * `expected_tokens` - An iterable of the tokens that should be
            found. If any tokens from this list are missing, or if any
            tokens not in this list are found, the check will fail.
        * `p_tag` - Default True. If True, an extra token will be added
            to `expected_tokens`: "p".

            This is because our wiki parser wraps it's content in <p>
            tags and many analyzers will tokenize a string like
            '<p>Foo</p>' as ['p', 'foo'] (the HTML tag is included in
            the tokenization). So this will show up in the tokenization
            during this test. Not all the analyzers do this, which is
            why it can be turned off.

        Why can't we fix the analyzers to strip out that HTML, and not
        generate spurious tokens? That could probably be done, but it
        probably isn't worth while because:

        * ES will weight common words lower, thanks to it's TF-IDF
          algorithms, which judges words based on how often they
          appear in the entire corpus and in the document, so the p
          tokens will be largely ignored.
        * The pre-l10n search code did it this way, so it doesn't
          break search.
        * When implementing l10n search, I wanted to minimize the
          number of changes needed, and this seemed like an unneeded
          change.
        """

        search = es_utils.Sphilastic(DocumentMappingType)
        search = search.filter(document_locale=locale)
        facet_filter = search._process_filters([("document_locale", locale)])
        search = search.facet_raw(
            tokens={"terms": {"field": "document_content"}, "facet_filter": facet_filter}
        )
        facets = search.facet_counts()

        expected = set(expected_tokens)
        if p_tag:
            # Since `expected` is a set, there is no problem adding this
            # twice, since duplicates will be ignored.
            expected.add("p")
        actual = set(t["term"] for t in facets["tokens"])
        eq_(actual, expected)

    # These 4 languages were chosen for tokenization testing because
    # they represent the 4 kinds of languages we have: English, Snowball
    # supported languages, ES supported languages and languages with no
    # analyzer, which use the standard analyzer. There is another
    # possible case, which is a custom analyzer, but we don't have any
    # of those right now.

    def test_english_tokenization(self):
        """Test that English stemming and stop words work."""
        self._check_locale_tokenization("en-US", ["i", "have", "cat"])

    def test_spanish_tokenization(self):
        """Test that Spanish stemming and stop words work."""
        self._check_locale_tokenization("es", ["tien", "un", "gat"])

    def test_arabic_tokenization(self):
        """Test that Arabic stemming works.

        I don't read Arabic, this is just what ES gave me when I asked
        it to analyze an Arabic text as Arabic. If someone who reads
        Arabic can improve this test, go for it!
        """
        self._check_locale_tokenization("ar", ["لد", "اثن", "قطط"])

    def test_herbrew_tokenization(self):
        """Test that Hebrew uses the standard analyzer."""
        tokens = ["גאולוגיה", "היא", "אחד"]
        self._check_locale_tokenization("he", tokens)


class TestGetAnalyzerForLocale(ElasticTestCase):
    def test_default(self):
        actual = es_utils.es_analyzer_for_locale("en-US")
        eq_("snowball-english", actual)

    def test_without_synonyms(self):
        actual = es_utils.es_analyzer_for_locale("en-US", synonyms=False)
        eq_("snowball-english", actual)

    def test_with_synonyms_right_locale(self):
        actual = es_utils.es_analyzer_for_locale("en-US", synonyms=True)
        eq_("snowball-english-synonyms", actual)

    def test_with_synonyms_wrong_locale(self):
        actual = es_utils.es_analyzer_for_locale("es", synonyms=True)
        eq_("snowball-spanish", actual)
