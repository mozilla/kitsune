import json

from django.conf import settings
from django.core.cache import cache

from nose.tools import eq_
from pyquery import PyQuery as pq

from kitsune.customercare.replies import REPLIES_DOCUMENT_SLUG
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.wiki.tests import DocumentFactory, RevisionFactory


CANNED_RESPONSES_WIKI = """
Any initial text above the first H1 should be ignored.

=Category 1=

==Reply 1==
Reply goes here http://example.com/kb-article

==Reply 2==
Another reply here

=Category 2=
==Reply 3==
And another reply
"""

MESSED_UP_CANNED_RESPONSES_WIKI = """
Lal al ala la  alaa lala la
==Bogus Reply will be ignored==
==Another bogus one==
Any initial text above the first H1 should be ignored.

=Category 1=

==Reply 1==
Reply goes here http://example.com/kb-article

==Reply 2==
Another reply here [[Bad link]]

==A reply without text==
=Category 2=
==Another reply without text==
==Reply 3==
And another reply
==Another Reply without text==
"""


class CannedResponsesTestCase(TestCase):
    """Canned responses tests."""

    def _create_doc(self, content):
        # Create the canned responses article.
        doc = DocumentFactory(slug=REPLIES_DOCUMENT_SLUG)
        rev = RevisionFactory(document=doc, content=content, is_approved=True)
        doc.current_revision = rev
        doc.save()

    def test_list_canned_responses(self):
        """Listing canned responses works as expected."""

        # Create the canned responses article.
        self._create_doc(CANNED_RESPONSES_WIKI)

        r = self.client.get(reverse('customercare.landing'), follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        responses_plain = doc('#accordion').text()

        # Verify categories and replies
        assert 'Category 1' in responses_plain
        assert 'Reply 1' in responses_plain
        assert 'Reply goes here' in responses_plain
        assert 'Category 2' in responses_plain
        assert 'Reply 3' in responses_plain
        assert 'And another reply' in responses_plain

        # Listing all responses
        eq_(3, len(doc('#accordion a.reply-topic')))

    def test_list_canned_responses_nondefault_locale(self):
        """Listing canned responses gives all snippets regardless of locale.
        """
        # Create the canned responses article.
        self._create_doc(CANNED_RESPONSES_WIKI)

        r = self.client.get(reverse('customercare.landing', locale='es'),
                            follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)

        # Listing all responses, l10n-agnostic (English if not in Pontoon).
        eq_(3, len(doc('#accordion a.reply-topic')))

    def test_messed_up_canned_responses(self):
        """Make sure we don't blow up if the article is malformed."""
        # Create the canned responses article.
        self._create_doc(MESSED_UP_CANNED_RESPONSES_WIKI)

        r = self.client.get(reverse('customercare.landing'), follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        responses_plain = doc('#accordion').text()

        assert 'Category 1' in responses_plain
        assert 'Category 2' in responses_plain


class TweetListTestCase(TestCase):
    """Tests for the list of tweets."""

    def test_fallback_message(self):
        """Fallback message when there are no tweets."""
        r = self.client.get(reverse('customercare.landing'), follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        assert doc('#tweets-wrap .warning-box'), (
            'Fallback message is not showing up.')


class StatsTests(TestCase):
    """Tests for the activity and contributors stats."""

    def test_contributors(self):
        """Only contributors stats are set."""
        with open('kitsune/customercare/tests/stats.json') as f:
            json_data = json.load(f)

        cache.set(settings.CC_TOP_CONTRIB_CACHE_KEY,
                  json_data['contributors'],
                  settings.CC_STATS_CACHE_TIMEOUT)
        r = self.client.get(reverse('customercare.landing'), follow=True)
        eq_(200, r.status_code)

        cache.delete(settings.CC_TOP_CONTRIB_CACHE_KEY)
