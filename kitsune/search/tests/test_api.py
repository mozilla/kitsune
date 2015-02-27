from nose.tools import eq_

from rest_framework.test import APIClient

from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.questions.tests import question, answer
from kitsune.products.tests import product
from kitsune.wiki.tests import document, revision


class SuggestViewTests(ElasticTestCase):
    client_class = APIClient

    def _make_question(self, solved=True, **kwargs):
        defaults = {
            'title': 'Login to website comments disabled',
            'content': """
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
            'save': True,
        }
        defaults.update(kwargs)
        q = question(**defaults)
        if solved:
            a = answer(question=q, save=True)
            q.solution = a
        # Trigger a reindex for the question.
        q.save()
        return q

    def _make_document(self, **kwargs):
        defaults = {
            'title': 'How to make a pie from scratch with email',
            'category': 10,
            'save': True
        }

        defaults.update(kwargs)
        d = document(**defaults)
        revision(document=d, is_approved=True, save=True)
        d.save()
        return d

    def test_invalid_product(self):
        res = self.client.get(reverse('search.suggest'), {
            'product': 'nonexistant',
            'q': 'search',
        })
        eq_(res.status_code, 400)
        eq_(res.data['detail'], {'product': 'Could not find product with slug "nonexistant".'})

    def test_invalid_numbers(self):
        res = self.client.get(reverse('search.suggest'), {
            'max_questions': 'a',
            'max_documents': 'b',
            'q': 'search',
        })
        eq_(res.status_code, 400)
        eq_(res.data['detail'], {
            'max_questions': 'This field must be an integer.',
            'max_documents': 'This field must be an integer.',
        })

    def test_q_required(self):
        res = self.client.get(reverse('search.suggest'))
        eq_(res.status_code, 400)
        eq_(res.data['detail'], {'q': 'This field is required.'})

    def test_it_works(self):
        q1 = self._make_question()
        d1 = self._make_document()
        self.refresh()

        req = self.client.get(reverse('search.suggest'), {'q': 'emails'})
        eq_([q['id'] for q in req.data['questions']], [q1.id])
        eq_([d['title'] for d in req.data['documents']], [d1.title])

    def test_questions_max_results_0(self):
        self._make_question()
        self.refresh()

        # Make sure something matches the query first.
        req = self.client.get(reverse('search.suggest'), {'q': 'emails'})
        eq_(len(req.data['questions']), 1)

        # If we specify "don't give me any" make sure we don't get any.
        req = self.client.get(reverse('search.suggest'), {'q': 'emails', 'max_questions': '0'})
        eq_(len(req.data['questions']), 0)

    def test_documents_max_results_0(self):
        self._make_document()
        self.refresh()

        # Make sure something matches the query first.
        req = self.client.get(reverse('search.suggest'), {'q': 'emails'})
        eq_(len(req.data['documents']), 1)

        # If we specify "don't give me any" make sure we don't get any.
        req = self.client.get(reverse('search.suggest'), {'q': 'emails', 'max_documents': '0'})
        eq_(len(req.data['documents']), 0)

    def test_product_filter_works(self):
        p1 = product(save=True)
        p2 = product(save=True)
        q1 = self._make_question(product=p1)
        self._make_question(product=p2)
        self.refresh()

        req = self.client.get(reverse('search.suggest'), {'q': 'emails', 'product': p1.slug})
        eq_([q['id'] for q in req.data['questions']], [q1.id])

    def test_serializer_fields(self):
        """Test that fields from the serializer are included."""
        self._make_question()
        self.refresh()

        req = self.client.get(reverse('search.suggest'), {'q': 'emails'})
        # Check that a field that is only available from the DB is in the response.
        assert 'metadata' in req.data['questions'][0]

    def test_only_solved(self):
        """Test that only solved questions are suggested."""
        q1 = self._make_question(solved=True)
        q2 = self._make_question(solved=False)
        self.refresh()

        req = self.client.get(reverse('search.suggest'), {'q': 'emails'})
        ids = [q['id'] for q in req.data['questions']]
        assert q1.id in ids
        assert q2.id not in ids
        eq_(len(ids), 1)
