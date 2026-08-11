from django.test import SimpleTestCase

from kitsune.retrieval.query import build_lexical_clauses


def _contains(value, expected):
    if value == expected:
        return True
    if isinstance(value, dict):
        return any(_contains(item, expected) for item in value.values())
    if isinstance(value, list):
        return any(_contains(item, expected) for item in value)
    return False


def _simple_query(clause):
    return clause.to_dict()["bool"]["must"][0]["simple_query_string"]


class LexicalClauseTests(SimpleTestCase):
    def test_builds_requested_and_fallback_clauses_for_both_sources(self):
        clauses = build_lexical_clauses(
            "firefox startup",
            locale="de",
            sources={"kb", "aaq"},
            viewer_group_ids=(9, 7),
            product_id=3,
            default_operator="OR",
            minimum_should_match="2<75%",
        )

        kb = clauses.kb_requested.to_dict()
        self.assertEqual(
            _simple_query(clauses.kb_requested),
            {
                "query": "firefox startup",
                "default_operator": "OR",
                "fields": [
                    "keywords.de^8",
                    "title.de^6",
                    "summary.de^4",
                    "content_text.de^2",
                ],
                "flags": "PHRASE",
                "minimum_should_match": "2<75%",
            },
        )
        self.assertTrue(_contains(kb, {"prefix": {"family_id": "kb:"}}))
        self.assertTrue(_contains(kb, {"terms": {"access_group_ids": [7, 9]}}))
        self.assertTrue(_contains(kb, {"term": {"product_ids": "3"}}))

        self.assertEqual(
            _simple_query(clauses.kb_english)["fields"],
            [
                "keywords.en-US^8",
                "title.en-US^6",
                "summary.en-US^4",
                "content_text.en-US^2",
            ],
        )

        aaq = clauses.aaq_requested.to_dict()
        aaq_query = aaq["bool"]["must"][0]["bool"]
        self.assertEqual(
            aaq_query["must"][0]["simple_query_string"]["fields"],
            ["question_title.de^2", "question_content.de", "answer_content.de"],
        )
        self.assertEqual(aaq_query["must_not"], [{"exists": {"field": "updated"}}])
        self.assertTrue(_contains(aaq, {"prefix": {"family_id": "aaq:"}}))
        self.assertTrue(_contains(aaq, {"term": {"question_product_id": 3}}))
        self.assertFalse(_contains(kb, {"exists": {"field": "updated"}}))

    def test_source_selection_does_not_create_unused_or_duplicate_clauses(self):
        aaq = build_lexical_clauses("firefox", locale="de", sources={"aaq"}, viewer_group_ids=())
        self.assertIsNone(aaq.kb_requested)
        self.assertIsNone(aaq.kb_english)
        self.assertIsNotNone(aaq.aaq_requested)

        kb = build_lexical_clauses("firefox", locale="en-US", sources={"kb"}, viewer_group_ids=())
        self.assertIsNotNone(kb.kb_requested)
        self.assertIsNone(kb.kb_english)
        self.assertIsNone(kb.aaq_requested)

    def test_rejects_invalid_viewer_group_ids(self):
        for group_ids in ("12", (True,), (0,), (1.5,)):
            with self.subTest(group_ids=group_ids), self.assertRaises(ValueError):
                build_lexical_clauses(
                    "firefox",
                    locale="en-US",
                    sources={"kb"},
                    viewer_group_ids=group_ids,  # type: ignore[arg-type]
                )

    def test_advanced_fields_are_rendered_for_each_source(self):
        clauses = build_lexical_clauses(
            'field:content:"startup crash" OR field:title:firefox',
            locale="en-US",
            sources={"kb", "aaq"},
            viewer_group_ids=(),
            default_operator="OR",
            minimum_should_match="2<75%",
        )

        kb = clauses.kb_requested.to_dict()
        self.assertTrue(
            _contains(
                kb,
                {
                    "simple_query_string": {
                        "query": '"startup crash"',
                        "default_operator": "OR",
                        "fields": ["content_text.en-US"],
                        "flags": "PHRASE",
                        "minimum_should_match": "2<75%",
                    }
                },
            )
        )

        aaq = clauses.aaq_requested.to_dict()
        self.assertTrue(
            _contains(
                aaq,
                {
                    "simple_query_string": {
                        "query": '"startup crash"',
                        "default_operator": "OR",
                        "fields": ["question_content.en-US", "answer_content.en-US"],
                        "flags": "PHRASE",
                        "minimum_should_match": "2<75%",
                    }
                },
            )
        )
