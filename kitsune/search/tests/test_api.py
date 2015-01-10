from nose.tools import eq_

from rest_framework.test import APIClient

from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.questions.tests import question, answer, answervote
from kitsune.products.tests import product


class SuggestViewTests(ElasticTestCase):
    client_class = APIClient

    def _make_question(self, **kwargs):
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
        a = answer(question=q, save=True)
        answervote(answer=a, helpful=True, save=True)
        # Trigger a reindex for the question.
        q.save()
        return q

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
        self.refresh()

        req = self.client.get(reverse('search.suggest'), {'q': 'emails'})
        eq_([q['id'] for q in req.data['questions']], [q1.id])

    def test_product_filter_works(self):
        p1 = product(save=True)
        p2 = product(save=True)
        q1 = self._make_question(product=p1)
        self._make_question(product=p2)
        self.refresh()

        req = self.client.get(reverse('search.suggest'), {'q': 'emails', 'product': p1.slug})
        eq_([q['id'] for q in req.data['questions']], [q1.id])
