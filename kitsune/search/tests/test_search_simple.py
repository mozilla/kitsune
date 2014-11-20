import json

from django.conf import settings
from django.utils.http import urlquote

import jingo
from nose.tools import eq_
from pyquery import PyQuery as pq

from kitsune.forums.tests import post, thread
from kitsune.products.tests import product
from kitsune.questions.tests import question, answer, answervote
from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.sumo.tests import LocalizingClient
from kitsune.sumo.urlresolvers import reverse
from kitsune.wiki.tests import document, revision


def render(s, context):
    t = jingo.env.from_string(s)
    return t.render(context)


class SimpleSearchTests(ElasticTestCase):
    client_class = LocalizingClient

    def test_content(self):
        """Ensure template is rendered with no errors for a common search"""
        response = self.client.get(reverse('search'), {'q': 'audio'})
        eq_('text/html; charset=utf-8', response['Content-Type'])
        eq_(200, response.status_code)

    def test_content_mobile(self):
        """Ensure mobile template is rendered."""
        self.client.cookies[settings.MOBILE_COOKIE] = 'on'
        response = self.client.get(reverse('search'), {'q': 'audio'})
        eq_('text/html; charset=utf-8', response['Content-Type'])
        eq_(200, response.status_code)

    def test_search_type_param(self):
        """Ensure that invalid values for search type (a=)
        does not cause errors"""
        response = self.client.get(reverse('search'), {'a': 'dontdie'})
        eq_('text/html; charset=utf-8', response['Content-Type'])
        eq_(200, response.status_code)

    def test_headers(self):
        """Verify caching headers of search forms and search results"""
        response = self.client.get(reverse('search'), {'q': 'audio'})
        eq_('max-age=%s' % (settings.SEARCH_CACHE_PERIOD * 60),
            response['Cache-Control'])
        assert 'Expires' in response
        response = self.client.get(reverse('search'))
        eq_('max-age=%s' % (settings.SEARCH_CACHE_PERIOD * 60),
            response['Cache-Control'])
        assert 'Expires' in response

    def test_page_invalid(self):
        """Ensure non-integer param doesn't throw exception."""
        doc = document(
            title=u'How to fix your audio',
            locale=u'en-US',
            category=10,
            save=True)
        doc.tags.add(u'desktop')
        revision(document=doc, is_approved=True, save=True)

        self.refresh()

        response = self.client.get(reverse('search'), {
            'q': 'audio',
            'format': 'json',
            'page': 'invalid'
        })
        eq_(200, response.status_code)
        eq_(1, json.loads(response.content)['total'])

    def test_clean_excerpt(self):
        """Ensure we clean html out of excerpts."""
        q = question(title='audio',
                     content='<script>alert("hacked");</script>', save=True)
        a = answer(question=q, save=True)
        answervote(answer=a, helpful=True, save=True)

        self.refresh()

        response = self.client.get(reverse('search'), {'q': 'audio'})
        eq_(200, response.status_code)

        doc = pq(response.content)
        assert 'script' not in doc('div.result').text()

    def test_ga_zero_results_event(self):
        """If there are no results, verify ga-push data attr on body."""
        doc = document(title=u'audio', locale=u'en-US', category=10, save=True)
        doc.products.add(product(title=u'firefox', slug=u'desktop', save=True))
        revision(document=doc, is_approved=True, save=True)

        self.refresh()

        # If there are results, data-ga-push should be an empty list.
        response = self.client.get(reverse('search'), {'q': 'audio'})
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_('[]', doc('body').attr('data-ga-push'))

        # If there are no results, then Zero Search Results event is there.
        response = self.client.get(reverse('search'), {'q': 'piranha'})
        eq_(200, response.status_code)
        doc = pq(response.content)
        assert '"Zero Search Results"' in doc('body').attr('data-ga-push')

    def test_fallback_for_zero_results(self):
        """If there are no results, fallback to a list of top articles."""
        firefox = product(title=u'firefox', slug=u'desktop', save=True)
        doc = document(title=u'audio1', locale=u'en-US', category=10,
                       save=True)
        doc.products.add(firefox)
        revision(document=doc, is_approved=True, save=True)
        doc = document(title=u'audio2', locale=u'en-US', category=10,
                       save=True)
        doc.products.add(firefox)
        revision(document=doc, is_approved=True, save=True)

        self.refresh()

        # Verify there are no real results but 2 fallback results are rendered
        response = self.client.get(reverse('search'), {'q': 'piranha'})
        eq_(200, response.status_code)

        assert "We couldn't find any results for" in response.content
        doc = pq(response.content)
        eq_(2, len(doc('#search-results .result')))

    def test_meta_tags(self):
        """Tests that the search results page has the right meta tags"""
        url_ = reverse('search')
        response = self.client.get(url_, {'q': 'contribute'})

        doc = pq(response.content)
        eq_(doc('meta[name="WT.oss"]')[0].attrib['content'], 'contribute')
        eq_(doc('meta[name="WT.oss_r"]')[0].attrib['content'], '0')
        eq_(doc('meta[name="robots"]')[0].attrib['content'], 'noindex')

    def test_search_cookie(self):
        """Set a cookie with the latest search term."""
        data = {'q': u'pagap\xf3 banco'}
        cookie = settings.LAST_SEARCH_COOKIE
        response = self.client.get(reverse('search', locale='fr'), data)
        assert cookie in response.cookies
        eq_(urlquote(data['q']), response.cookies[cookie].value)

    def test_empty_pages(self):
        """Tests requesting a page that has no results"""
        ques = question(title=u'audio', save=True)
        ques.tags.add(u'desktop')
        ans = answer(question=ques, content=u'volume', save=True)
        answervote(answer=ans, helpful=True, save=True)

        self.refresh()

        qs = {'q': 'audio', 'page': 81}
        response = self.client.get(reverse('search'), qs)
        eq_(200, response.status_code)

    def test_include_questions(self):
        """This tests whether doing a simple search returns
        question results.

        Bug #709202.

        """
        # Create a question with an answer with an answervote that
        # marks the answer as helpful.  The question should have the
        # "desktop" tag.
        p = product(title=u'firefox', slug=u'desktop', save=True)
        ques = question(title=u'audio', product=p, save=True)
        ans = answer(question=ques, content=u'volume', save=True)
        answervote(answer=ans, helpful=True, save=True)

        self.refresh()

        # This is the search that you get when you start on the sumo
        # homepage and do a search from the box with two differences:
        # first, we do it in json since it's easier to deal with
        # testing-wise and second, we search for 'audio' since we have
        # data for that.
        response = self.client.get(reverse('search'), {
            'q': 'audio', 'format': 'json'})

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 1)

        # This is another search that picks up results based on the
        # answer_content.  answer_content is in a string array, so
        # this makes sure that works.
        response = self.client.get(reverse('search'), {
            'q': 'volume', 'format': 'json'})

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 1)

    def test_include_wiki(self):
        """This tests whether doing a simple search returns wiki document
        results.

        Bug #709202.

        """
        doc = document(title=u'audio', locale=u'en-US', category=10, save=True)
        doc.products.add(product(title=u'firefox', slug=u'desktop', save=True))
        revision(document=doc, is_approved=True, save=True)

        self.refresh()

        # This is the search that you get when you start on the sumo
        # homepage and do a search from the box with two differences:
        # first, we do it in json since it's easier to deal with
        # testing-wise and second, we search for 'audio' since we have
        # data for that.
        response = self.client.get(reverse('search'), {
            'q': 'audio', 'format': 'json'})

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 1)

    def test_only_show_wiki_and_questions(self):
        """Tests that the simple search doesn't show forums

        This verifies that we're only showing documents of the type
        that should be shown and that the filters on model are working
        correctly.

        Bug #767394

        """
        p = product(slug=u'desktop', save=True)
        ques = question(title=u'audio', product=p, save=True)
        ans = answer(question=ques, content=u'volume', save=True)
        answervote(answer=ans, helpful=True, save=True)

        doc = document(title=u'audio', locale=u'en-US', category=10, save=True)
        doc.products.add(p)
        revision(document=doc, is_approved=True, save=True)

        thread1 = thread(title=u'audio', save=True)
        post(thread=thread1, save=True)

        self.refresh()

        response = self.client.get(reverse('search'), {
            'q': 'audio', 'format': 'json'})

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 2)

        # Archive the article and question. They should no longer appear
        # in simple search results.
        ques.is_archived = True
        ques.save()
        doc.is_archived = True
        doc.save()

        self.refresh()

        response = self.client.get(reverse('search'), {
            'q': 'audio', 'format': 'json'})

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 0)

    def test_filter_by_product(self):
        desktop = product(slug=u'desktop', save=True)
        mobile = product(slug=u'mobile', save=True)
        ques = question(title=u'audio', product=desktop, save=True)
        ans = answer(question=ques, content=u'volume', save=True)
        answervote(answer=ans, helpful=True, save=True)

        doc = document(title=u'audio', locale=u'en-US', category=10, save=True)
        doc.products.add(desktop)
        doc.products.add(mobile)
        revision(document=doc, is_approved=True, save=True)

        self.refresh()

        # There should be 2 results for desktop and 1 for mobile.
        response = self.client.get(reverse('search'), {
            'q': 'audio', 'format': 'json', 'product': 'desktop'})
        eq_(200, response.status_code)
        content = json.loads(response.content)
        eq_(content['total'], 2)

        response = self.client.get(reverse('search'), {
            'q': 'audio', 'format': 'json', 'product': 'mobile'})
        eq_(200, response.status_code)
        content = json.loads(response.content)
        eq_(content['total'], 1)

    def test_filter_by_doctype(self):
        desktop = product(slug=u'desktop', save=True)
        ques = question(title=u'audio', product=desktop, save=True)
        ans = answer(question=ques, content=u'volume', save=True)
        answervote(answer=ans, helpful=True, save=True)

        doc = document(title=u'audio', locale=u'en-US', category=10, save=True)
        doc.products.add(desktop)
        revision(document=doc, is_approved=True, save=True)

        doc = document(
            title=u'audio too', locale=u'en-US', category=10, save=True)
        doc.products.add(desktop)
        revision(document=doc, is_approved=True, save=True)

        self.refresh()

        # There should be 2 results for kb (w=1) and 1 for questions (w=2).
        response = self.client.get(reverse('search'), {
            'q': 'audio', 'format': 'json', 'w': '1'})
        eq_(200, response.status_code)
        content = json.loads(response.content)
        eq_(content['total'], 2)

        response = self.client.get(reverse('search'), {
            'q': 'audio', 'format': 'json', 'w': '2'})
        eq_(200, response.status_code)
        content = json.loads(response.content)
        eq_(content['total'], 1)
