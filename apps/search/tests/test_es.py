import json

from nose.tools import eq_

from sumo.tests import TestCase, LocalizingClient, ElasticTestMixin
from sumo.urlresolvers import reverse

from waffle.models import Flag


class ESTestCase(TestCase, ElasticTestMixin):
    fixtures = ['users.json', 'search/documents.json',
                'posts.json', 'questions.json']

    def setUp(self):
        super(ESTestCase, self).setUp()
        self.setup_indexes()

    def tearDown(self):
        super(ESTestCase, self).tearDown()
        self.teardown_indexes()


class ElasticSearchViewTests(ESTestCase):
    def test_excerpting_doesnt_crash(self):
        """This tests to make sure search view works.

        Amongst other things, this tests to make sure excerpting
        doesn't crash when elasticsearch flag is set to True.  This
        means that we're calling excerpt on the S that the results
        came out of.

        """
        Flag.objects.create(name='elasticsearch', everyone=True)

        c = LocalizingClient()

        response = c.get(reverse('search'), {
            'format': 'json', 'q': 'audio', 'a': 1
        })
        eq_(200, response.status_code)

        # Make sure there are more than 0 results.  Otherwise we don't
        # really know if it slid through the excerpting code.
        content = json.loads(response.content)
        self.assertGreater(content['total'], 0)
