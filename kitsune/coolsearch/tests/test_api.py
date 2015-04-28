from kitsune.products.tests import product
from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.sumo.tests import LocalizingClient
from kitsune.sumo.urlresolvers import reverse
from kitsune.wiki.tests import document, revision


class SearchApiTests(ElasticTestCase):
    client_class = LocalizingClient

    def test_search_products(self):
        p = product(title=u'Product One', slug='product', save=True)
        doc1 = document(title=u'cookies', locale='en-US', category=10,
                        save=True)
        revision(document=doc1, is_approved=True, save=True)
        doc1.products.add(p)
        doc1.save()

        self.refresh()

        response = self.client.get(
            reverse('coolsearch.search_wiki'),
            {}
        )

        assert "We couldn't find any results for" not in response.content
        # eq_(200, response.status_code)
        # assert 'Product One' in response.content
