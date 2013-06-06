from nose.tools import eq_

from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.tests import TestCase, LocalizingClient


class JSONTest(ElasticTestCase):
    client_class = LocalizingClient

    def test_json_format(self):
        """JSON without callback should return application/json"""
        response = self.client.get(reverse('search'), {
            'q': 'bookmarks',
            'format': 'json',
        })
        eq_(response['Content-Type'], 'application/json')

    def test_json_callback_validation(self):
        """Various json callbacks -- validation"""
        q = 'bookmarks'
        format = 'json'

        callbacks = (
            ('callback', 200),
            ('validCallback', 200),
            ('obj.method', 200),
            ('obj.someMethod', 200),
            ('arr[1]', 200),
            ('arr[12]', 200),
            ("alert('xss');foo", 400),
            ("eval('nastycode')", 400),
            ("someFunc()", 400),
            ('x', 200),
            ('x123', 200),
            ('$', 200),
            ('_func', 200),
            ('"></script><script>alert(\'xss\')</script>', 400),
            ('">', 400),
            ('var x=something;foo', 400),
            ('var x=', 400),
        )

        for callback, status in callbacks:
            response = self.client.get(reverse('search'), {
                'q': q,
                'format': format,
                'callback': callback,
            })
            eq_(response['Content-Type'], 'application/x-javascript')
            eq_(response.status_code, status)

    def test_json_empty_query(self):
        """Empty query returns JSON format"""
        # Test with flags for advanced search or not
        a_types = (0, 1, 2)
        for a in a_types:
            response = self.client.get(reverse('search'), {
                'format': 'json', 'a': a,
            })
            eq_(response['Content-Type'], 'application/json')
