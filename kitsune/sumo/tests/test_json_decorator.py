import json

from django import http
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase

from nose.tools import eq_

from kitsune.sumo.decorators import json_view


rf = RequestFactory()
JSON = 'application/json'


class JsonViewTests(TestCase):
    def test_object(self):
        data = {
            'foo': 'bar',
            'baz': 'qux',
            'quz': [{'foo': 'bar'}],
        }
        expect = json.dumps(data)

        @json_view
        def temp(req):
            return data

        res = temp(rf.get('/'))
        eq_(200, res.status_code)
        eq_(expect, res.content)
        eq_(JSON, res['content-type'])

    def test_list(self):
        data = ['foo', 'bar', 'baz']
        expect = json.dumps(data)

        @json_view
        def temp(req):
            return data

        res = temp(rf.get('/'))
        eq_(200, res.status_code)
        eq_(expect, res.content)
        eq_(JSON, res['content-type'])

    def test_404(self):
        @json_view
        def temp(req):
            raise http.Http404, 'foo'

        res = temp(rf.get('/'))
        eq_(404, res.status_code)
        eq_(JSON, res['content-type'])
        data = json.loads(res.content)
        eq_(404, data['error'])
        eq_('foo', data['message'])

    def test_permission(self):
        @json_view
        def temp(req):
            raise PermissionDenied('bar')

        res = temp(rf.get('/'))
        eq_(403, res.status_code)
        eq_(JSON, res['content-type'])
        data = json.loads(res.content)
        eq_(403, data['error'])
        eq_('bar', data['message'])

    def test_server_error(self):
        @json_view
        def temp(req):
            raise TypeError('fail')

        res = temp(rf.get('/'))
        eq_(500, res.status_code)
        eq_(JSON, res['content-type'])
        data = json.loads(res.content)
        eq_(500, data['error'])
        eq_('fail', data['message'])
