import json
import time

from nose.tools import eq_
from rest_framework.test import APIClient

from django.conf import settings

from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.questions.tests import QuestionFactory, AnswerFactory
from kitsune.products.tests import ProductFactory
from kitsune.wiki.tests import DocumentFactory, RevisionFactory


class SuggestViewTests(ElasticTestCase):
    client_class = APIClient

    # TODO: This should probably be a subclass of QuestionFactory
    def _make_question(self, solved=True, **kwargs):
        defaults = {
            "title": "Login to website comments disabled " + str(time.time()),
            "content": """
                readersupportednews.org, sends me emails with a list of
                articles to read.

                The links to the articles work as normal, except that I
                cannot login from the linked article - as required - to
                send my comments.

                I see a javascript activity statement at the bottom left
                corner of my screen while the left button is depressed
                on the Login button. it is gone when I release the left
                button, but no results.

                I have the latest (7) version of java enabled, on an XP
                box.

                Why this inability to login to this website commentary?
                """,
        }
        defaults.update(kwargs)
        q = QuestionFactory(**defaults)
        if solved:
            a = AnswerFactory(question=q)
            q.solution = a
        # Trigger a reindex for the question.
        q.save()
        return q

    # TODO: This should probably be a subclass of DocumentFactory
    def _make_document(self, **kwargs):
        defaults = {
            "title": "How to make a pie from scratch with email " + str(time.time()),
            "category": 10,
        }

        defaults.update(kwargs)
        d = DocumentFactory(**defaults)
        RevisionFactory(document=d, is_approved=True)
        d.save()
        return d

    def test_invalid_product(self):
        res = self.client.get(
            reverse("search.suggest"), {"product": "nonexistant", "q": "search"}
        )
        eq_(res.status_code, 400)
        eq_(res.data, {"product": [u'Could not find product with slug "nonexistant".']})

    def test_invalid_locale(self):
        res = self.client.get(
            reverse("search.suggest"), {"locale": "bad-medicine", "q": "search"}
        )
        eq_(res.status_code, 400)
        eq_(res.data, {"locale": [u'Could not find locale "bad-medicine".']})

    def test_invalid_fallback_locale_none_case(self):
        # Test the locale -> locale case.
        non_none_locale_fallback_pairs = [
            (key, val)
            for key, val in sorted(settings.NON_SUPPORTED_LOCALES.items())
            if val is not None
        ]
        locale, fallback = non_none_locale_fallback_pairs[0]

        res = self.client.get(
            reverse("search.suggest"), {"locale": locale, "q": "search"}
        )
        eq_(res.status_code, 400)
        error_message = u'"{0}" is not supported, but has fallback locale "{1}".'.format(
            locale, fallback
        )
        eq_(res.data, {"locale": [error_message]})

    def test_invalid_fallback_locale_non_none_case(self):
        # Test the locale -> None case which falls back to WIKI_DEFAULT_LANGUAGE.
        has_none_locale_fallback_pairs = [
            (key, val)
            for key, val in sorted(settings.NON_SUPPORTED_LOCALES.items())
            if val is None
        ]
        locale, fallback = has_none_locale_fallback_pairs[0]

        res = self.client.get(
            reverse("search.suggest"), {"locale": locale, "q": "search"}
        )
        eq_(res.status_code, 400)
        error_message = u'"{0}" is not supported, but has fallback locale "{1}".'.format(
            locale, settings.WIKI_DEFAULT_LANGUAGE
        )
        eq_(res.data, {"locale": [error_message]})

    def test_invalid_numbers(self):
        res = self.client.get(
            reverse("search.suggest"),
            {"max_questions": "a", "max_documents": "b", "q": "search",},
        )
        eq_(res.status_code, 400)
        eq_(
            res.data,
            {
                "max_questions": [u"A valid integer is required."],
                "max_documents": [u"A valid integer is required."],
            },
        )

    def test_q_required(self):
        res = self.client.get(reverse("search.suggest"))
        eq_(res.status_code, 400)
        eq_(res.data, {"q": [u"This field is required."]})

    def test_it_works(self):
        q1 = self._make_question()
        d1 = self._make_document()
        self.refresh()

        req = self.client.get(reverse("search.suggest"), {"q": "emails"})
        eq_([q["id"] for q in req.data["questions"]], [q1.id])
        eq_([d["title"] for d in req.data["documents"]], [d1.title])

    def test_filters_in_postdata(self):
        q1 = self._make_question()
        d1 = self._make_document()
        self.refresh()

        data = json.dumps({"q": "emails"})
        # Note: Have to use .generic() because .get() will convert the
        # data into querystring params and then it's clownshoes all
        # the way down.
        req = self.client.generic(
            "GET", reverse("search.suggest"), data=data, content_type="application/json"
        )
        eq_(req.status_code, 200)
        eq_([q["id"] for q in req.data["questions"]], [q1.id])
        eq_([d["title"] for d in req.data["documents"]], [d1.title])

    def test_both_querystring_and_body_raises_error(self):
        self._make_question()
        self._make_document()
        self.refresh()

        data = json.dumps({"q": "emails"})
        # Note: Have to use .generic() because .get() will convert the
        # data into querystring params and then it's clownshoes all
        # the way down.
        req = self.client.generic(
            "GET",
            reverse("search.suggest") + "?max_documents=3",
            data=data,
            content_type="application/json",
        )
        eq_(req.status_code, 400)
        eq_(
            req.data,
            {
                u"detail": "Put all parameters either in the querystring or the HTTP request body."
            },
        )

    def test_questions_max_results_0(self):
        self._make_question()
        self.refresh()

        # Make sure something matches the query first.
        req = self.client.get(reverse("search.suggest"), {"q": "emails"})
        eq_(len(req.data["questions"]), 1)

        # If we specify "don't give me any" make sure we don't get any.
        req = self.client.get(
            reverse("search.suggest"), {"q": "emails", "max_questions": "0"}
        )
        eq_(len(req.data["questions"]), 0)

    def test_questions_max_results_non_0(self):
        self._make_question()
        self._make_question()
        self._make_question()
        self._make_question()
        self._make_question()
        self.refresh()

        # Make sure something matches the query first.
        req = self.client.get(reverse("search.suggest"), {"q": "emails"})
        eq_(len(req.data["questions"]), 5)

        # Make sure we get only 3.
        req = self.client.get(
            reverse("search.suggest"), {"q": "emails", "max_questions": "3"}
        )
        eq_(len(req.data["questions"]), 3)

    def test_documents_max_results_0(self):
        self._make_document()
        self.refresh()

        # Make sure something matches the query first.
        req = self.client.get(reverse("search.suggest"), {"q": "emails"})
        eq_(len(req.data["documents"]), 1)

        # If we specify "don't give me any" make sure we don't get any.
        req = self.client.get(
            reverse("search.suggest"), {"q": "emails", "max_documents": "0"}
        )
        eq_(len(req.data["documents"]), 0)

    def test_documents_max_results_non_0(self):
        self._make_document()
        self._make_document()
        self._make_document()
        self._make_document()
        self._make_document()
        self.refresh()

        # Make sure something matches the query first.
        req = self.client.get(reverse("search.suggest"), {"q": "emails"})
        eq_(len(req.data["documents"]), 5)

        # Make sure we get only 3.
        req = self.client.get(
            reverse("search.suggest"), {"q": "emails", "max_documents": "3"}
        )
        eq_(len(req.data["documents"]), 3)

    def test_product_filter_works(self):
        p1 = ProductFactory()
        p2 = ProductFactory()
        q1 = self._make_question(product=p1)
        self._make_question(product=p2)
        self.refresh()

        req = self.client.get(
            reverse("search.suggest"), {"q": "emails", "product": p1.slug}
        )
        eq_([q["id"] for q in req.data["questions"]], [q1.id])

    def test_locale_filter_works_for_questions(self):
        q1 = self._make_question(locale="fr")
        self._make_question(locale="en-US")
        self.refresh()

        req = self.client.get(
            reverse("search.suggest"), {"q": "emails", "locale": "fr"}
        )
        eq_([q["id"] for q in req.data["questions"]], [q1.id])

    def test_locale_filter_works_for_documents(self):
        d1 = self._make_document(slug="right-doc", locale="fr")
        self._make_document(slug="wrong-doc", locale="en-US")
        self.refresh()

        req = self.client.get(
            reverse("search.suggest"), {"q": "emails", "locale": "fr"}
        )
        eq_([d["slug"] for d in req.data["documents"]], [d1.slug])

    def test_serializer_fields(self):
        """Test that fields from the serializer are included."""
        self._make_question()
        self.refresh()

        req = self.client.get(reverse("search.suggest"), {"q": "emails"})
        # Check that a field that is only available from the DB is in the response.
        assert "metadata" in req.data["questions"][0]

    def test_only_solved(self):
        """Test that only solved questions are suggested."""
        q1 = self._make_question(solved=True)
        q2 = self._make_question(solved=False)
        self.refresh()

        req = self.client.get(reverse("search.suggest"), {"q": "emails"})
        ids = [q["id"] for q in req.data["questions"]]
        assert q1.id in ids
        assert q2.id not in ids
        eq_(len(ids), 1)
