import json

from nose.tools import eq_

from sumo.tests import LocalizingClient, ElasticTestCase
from sumo.urlresolvers import reverse

from search.models import generate_tasks
from questions.tests import question, answer, answer_vote
from questions.models import Question
from wiki.tests import document, revision
from forums.tests import thread, post
import mock


class ElasticSearchTasksTests(ElasticTestCase):
    @mock.patch.object(Question, 'index')
    def test_tasks(self, index_fun):
        """Tests to make sure tasks are added and run"""

        q = question()
        # Don't call self.refresh here since that calls generate_tasks().

        eq_(index_fun.call_count, 0)

        q.save()
        generate_tasks()

        eq_(index_fun.call_count, 1)

    @mock.patch.object(Question, 'index')
    def test_tasks_squashed(self, index_fun):
        """Tests to make sure tasks are squashed"""

        q = question()
        # Don't call self.refresh here since that calls generate_tasks().

        eq_(index_fun.call_count, 0)

        q.save()
        q.save()
        q.save()
        q.save()

        eq_(index_fun.call_count, 0)

        generate_tasks()

        eq_(index_fun.call_count, 1)


class ElasticSearchViewTests(ElasticTestCase):
    client_class = LocalizingClient

    def test_excerpting_doesnt_crash(self):
        """This tests to make sure search view works.

        Amongst other things, this tests to make sure excerpting
        doesn't crash when elasticsearch flag is set to True.  This
        means that we're calling excerpt on the S that the results
        came out of.

        """
        # Create a question with an answer with an answervote that
        # marks the answer as helpful.  The question should have the
        # "desktop" tag.
        ques = question(
            title=u'audio fails',
            content=u'my audio dont work.')
        ques.save()

        ques.tags.add(u'desktop')
        self.refresh()

        response = self.client.get(reverse('search'), {
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

        self.refresh()

        # This is the search that you get when you start on the sumo
        # homepage and do a search from the box with two differences:
        # first, we do it in json since it's easier to deal with
        # testing-wise and second, we search for 'audio' since we have
        # data for that.
        response = self.client.get(reverse('search'), {
            'q_tags': 'desktop', 'product': 'desktop', 'q': 'audio',
            'format': 'json'
        })

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 1)

        # This is another search that picks up results based on the
        # answer_content.  answer_content is in a string array, so
        # this makes sure that works.
        response = self.client.get(reverse('search'), {
            'q_tags': 'desktop', 'product': 'desktop', 'q': 'volume',
            'format': 'json'
        })

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 1)

    def test_front_page_search_for_wiki(self):
        """This tests whether doing a search from the front page returns
        wiki document results.

        Bug #709202.

        """
        doc = document(
            title=u'How to fix your audio',
            locale=u'en-US',
            category=10)
        doc.save()

        doc.tags.add(u'desktop')

        rev = revision(
            document=doc,
            summary=u'Volume.',
            content=u'Turn up the volume.',
            is_approved=True)
        rev.save()

        self.refresh()

        # This is the search that you get when you start on the sumo
        # homepage and do a search from the box with two differences:
        # first, we do it in json since it's easier to deal with
        # testing-wise and second, we search for 'audio' since we have
        # data for that.
        response = self.client.get(reverse('search'), {
            'q_tags': 'desktop', 'product': 'desktop', 'q': 'audio',
            'format': 'json'
        })

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 1)

    def test_forums_search(self):
        """This tests whether forum posts show up in searches."""
        thread1 = thread(
            title=u'Why don\'t we spell crash backwards?')
        thread1.save()

        post1 = post(
            thread=thread1,
            content=u'What, like hsarc?  That\'s silly.')
        post1.save()

        self.refresh()

        response = self.client.get(reverse('search'), {
            'author': '', 'created': '0', 'created_date': '',
            'updated': '0', 'updated_date': '', 'sortby': '0',
            'a': '1', 'w': '4', 'q': 'hsarc',
            'format': 'json'
        })

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 1)


class ElasticSearchHtmlTests(ElasticTestCase):
    """Tests for whether we're indexing and excerpting HTML properly"""
    client_class = LocalizingClient

    def test_html_filtered_out_of_question_excerpts(self):
        """HTML should get filtered out of question excerpts."""
        answer_vote(
            answer=answer(
                question=question(
                    content='My<br />printer is on fire.',
                    save=True),
                content='Put it out.',
                save=True),
            helpful=True,
            save=True)
        self.refresh()

        response = self.client.get(reverse('search'),
                                   {'q': 'printer',
                                    'format': 'json'
                                   })
        self.assertNotContains(response, '&lt;br')
        # We leave off the rest of the <br> tag because bleach atm returns
        # <br/>, but it could have a space or no slash someday.

    def test_html_filtered_out_of_indexed_questions(self):
        """HTML should be filtered out of question content before indexing."""
        answer_vote(
            answer=answer(
                question=question(
                    content='My<br />printer is on [[FirePage|fire]].',
                    save=True),
                content='Put it out.',
                save=True),
            helpful=True,
            save=True)
        self.refresh()

        response = self.client.get(reverse('search'),
                                   {'q': 'br',
                                    'format': 'json'
                                   })
        # It shouldn't find the "br" from the <br> tag:
        eq_(json.loads(response.content)['total'], 0)

        response = self.client.get(reverse('search'),
                                   {'q': 'FirePage',
                                    'format': 'json'
                                   })
        # ...or the <a> tag, which bleach usually allows:
        eq_(json.loads(response.content)['total'], 0)
