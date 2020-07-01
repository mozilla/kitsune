from django.http import HttpResponse
from django.test import RequestFactory
from django.test.utils import override_settings
from nose.tools import eq_

from kitsune.sumo.tests import TestCase
from kitsune.wiki.decorators import check_simple_wiki_locale


rf = RequestFactory()


@override_settings(SIMPLE_WIKI_LANGUAGES=["es"])
class SimpleWikiDecoratorTests(TestCase):
    def test_faq_locale_redirects(self):
        @check_simple_wiki_locale
        def temp(request):
            return HttpResponse("OK")

        req = rf.get("/es/products/firefox")
        req.LANGUAGE_CODE = "es"
        res = temp(req)
        eq_(302, res.status_code)
        eq_("/kb/frequently-asked-questions", res["location"])

    def test_non_faq_locale_doesnt_redirect(self):
        @check_simple_wiki_locale
        def temp(request):
            return HttpResponse("OK")

        req = rf.get("/de/products/firefox")
        req.LANGUAGE_CODE = "de"
        res = temp(req)
        eq_(200, res.status_code)
