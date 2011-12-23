import json

from nose.tools import eq_

from sumo.tests import TestCase, LocalizingClient, ElasticTestMixin
from sumo.urlresolvers import reverse

from questions.tests import question, answer, answer_vote

from waffle.models import Flag


class ESTestCase(TestCase, ElasticTestMixin):
    def setUp(self):
        super(ESTestCase, self).setUp()
        self.setup_indexes()

    def tearDown(self):
        super(ESTestCase, self).tearDown()
        self.teardown_indexes()


class ElasticSearchViewTests(ESTestCase):
    localizing_client = LocalizingClient()

    def test_excerpting_doesnt_crash(self):
        """This tests to make sure search view works.

        Amongst other things, this tests to make sure excerpting
        doesn't crash when elasticsearch flag is set to True.  This
        means that we're calling excerpt on the S that the results
        came out of.

        """
        Flag.objects.create(name='elasticsearch', everyone=True)

        # Create a question with an answer with an answervote that
        # marks the answer as helpful.  The question should have the
        # "desktop" tag.
        ques = question(
            title=u'audio fails',
            content=u'my audio dont work.')
        ques.save()

        ques.tags.add(u'desktop')

        response = self.localizing_client.get(reverse('search'), {
            'format': 'json', 'q': 'audio', 'a': 1
        })
        eq_(200, response.status_code)

        # Make sure there are more than 0 results.  Otherwise we don't
        # really know if it slid through the excerpting code.
        content = json.loads(response.content)
        eq_(content['total'], 1)

    def test_front_page_search_for_questions(self):
        """This tests whether doing a search from the front page returns
        question results.

        Bug #709202.

        """
        Flag.objects.create(name='elasticsearch', everyone=True)

        # Create a question with an answer with an answervote that
        # marks the answer as helpful.  The question should have the
        # "desktop" tag.
        ques = question(
            title=u'audio fails',
            content=u'my audio dont work.')
        ques.save()

        ques.tags.add(u'desktop')

        ans = answer(
            question=ques,
            content=u'You need to turn your volume up.')
        ans.save()

        ansvote = answer_vote(
            answer=ans,
            helpful=True)
        ansvote.save()

        # This is the search that you get when you start on the sumo
        # homepage and do a search from the box with two differences:
        # first, we do it in json since it's easier to deal with
        # testing-wise and second, we search for 'audio' since we have
        # data for that.
        response = self.localizing_client.get(reverse('search'), {
            'q_tags': 'desktop', 'product': 'desktop', 'q': 'audio',
            'format': 'json'
        })

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 1)

        # This is another search that picks up results based on the
        # answer_content.  answer_content is in a string array, so
        # this makes sure that works.
        response = self.localizing_client.get(reverse('search'), {
            'q_tags': 'desktop', 'product': 'desktop', 'q': 'volume',
            'format': 'json'
        })

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 1)
