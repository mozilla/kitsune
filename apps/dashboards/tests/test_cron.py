# -*- coding: utf-8 -*-
from datetime import timedelta

from django.conf import settings

from nose import SkipTest
from nose.tools import eq_

from dashboards.cron import (cache_most_unhelpful_kb_articles,
                             _get_old_unhelpful, _get_current_unhelpful)
from sumo.tests import TestCase
from sumo.utils import redis_client
from wiki.models import HelpfulVote
from wiki.tests import revision


def _add_vote_in_past(rev, vote, days_back):
    v = HelpfulVote(revision=rev, helpful=vote)
    v.created = v.created - timedelta(days=days_back)
    v.save()


def _make_backdated_revision(backdate):
    r = revision(save=True)
    r.created = r.created - timedelta(days=backdate)
    r.save()
    return r


class TopUnhelpfulArticlesTests(TestCase):
    def test_no_old_articles(self):
        """Make sure _get_old_articles() returns nothing with no votes."""
        result = _get_old_unhelpful()
        eq_(0, len(result))

    def test_no_current_articles(self):
        """Make sure _get_current_articles() returns nothing with no votes."""
        result = _get_current_unhelpful({})
        eq_(0, len(result))

    def test_old_articles(self):
        """
        Make sure _get_old_unhelpful() returns an unhelpful (no > yes) with
        votes within time range.
        """
        r = _make_backdated_revision(90)

        # Add 4 no votes 1.5 months ago
        for x in range(0, 4):
            _add_vote_in_past(r, 0, 45)

        # Add 1 yes vote 1.5 months ago
        _add_vote_in_past(r, 1, 45)

        result = _get_old_unhelpful()
        eq_(1, len(result))
        self.assertAlmostEqual(0.2, result[r.id]['percentage'])
        eq_(5, result[r.id]['total'])

    def test_old_articles_helpful(self):
        """
        Make sure _get_old_unhelpful() doesn't return a helpful (no < yes)
        with votes within time range.
        """
        r = _make_backdated_revision(90)

        for x in range(0, 4):
            _add_vote_in_past(r, 1, 45)

        _add_vote_in_past(r, 0, 45)

        result = _get_old_unhelpful()
        eq_(0, len(result))

    def test_current_articles(self):
        """
        Make sure _get_current_unhelpful() returns an unhelpful (no > yes) with
        votes within time range.
        """
        r = _make_backdated_revision(90)

        for x in range(0, 3):
            _add_vote_in_past(r, 0, 15)

        for x in range(0, 2):
            _add_vote_in_past(r, 1, 15)

        old_data = {r.id: {'percentage': 0.2, 'total': 5.0}}

        result = _get_current_unhelpful(old_data)
        eq_(1, len(result))
        self.assertAlmostEqual(0.4, result[r.id]['currperc'])
        self.assertAlmostEqual(0.4 - old_data[r.id]['percentage'],
                               result[r.id]['diffperc'])
        eq_(5, result[r.id]['total'])

    def test_current_articles_helpful(self):
        """
        Make sure _get_current_unhelpful() doesn't return a helpful (no < yes)
        with votes within time range.
        """
        r = _make_backdated_revision(90)

        for x in range(0, 3):
            _add_vote_in_past(r, 1, 15)

        for x in range(0, 2):
            _add_vote_in_past(r, 0, 15)

        old_data = {r.id: {'percentage': 0.2, 'total': 5.0}}

        result = _get_current_unhelpful(old_data)
        eq_(0, len(result))

    def test_current_articles_not_in_old(self):
        """
        Unhelpful articles in current but not in old shouldn't break stuff.
        """
        r = _make_backdated_revision(90)

        for x in range(0, 3):
            _add_vote_in_past(r, 0, 15)

        for x in range(0, 2):
            _add_vote_in_past(r, 1, 15)

        old_data = {}

        result = _get_current_unhelpful(old_data)
        eq_(1, len(result))
        self.assertAlmostEqual(0.4, result[r.id]['currperc'])
        self.assertAlmostEqual(0, result[r.id]['diffperc'])
        eq_(5, result[r.id]['total'])


class TopUnhelpfulArticlesCronTests(TestCase):
    def setUp(self):
        super(TopUnhelpfulArticlesCronTests, self).setUp()
        try:
            self.redis = redis_client('helpfulvotes')
            if self.redis is None:
                raise SkipTest
            self.redis.flushdb()
            self.REDIS_KEY = settings.HELPFULVOTES_UNHELPFUL_KEY
        except (KeyError, AttributeError):
            raise SkipTest

    def tearDown(self):
        try:
            self.redis.flushdb()
        except (KeyError, AttributeError):
            raise SkipTest
        super(TopUnhelpfulArticlesCronTests, self).tearDown()

    def test_no_articles(self):
        """Full cron with no articles returns no unhelpful articles."""
        cache_most_unhelpful_kb_articles()
        eq_(0, self.redis.llen(self.REDIS_KEY))

    def test_caching_unhelpful(self):
        """Cron should get the unhelpful articles."""
        r = _make_backdated_revision(90)

        for x in range(0, 3):
            _add_vote_in_past(r, 0, 15)

        for x in range(0, 2):
            _add_vote_in_past(r, 1, 15)

        cache_most_unhelpful_kb_articles()

        eq_(1, self.redis.llen(self.REDIS_KEY))
        result = self.redis.lrange(self.REDIS_KEY, 0, 1)
        eq_(u'%d::%.1f::%.1f::%.1f::%.1f::%s::%s' %
             (r.id, 5.0, 0.4, 0.0, 0.0, r.document.slug, r.document.title),
            result[0].decode('utf-8'))

    def test_caching_helpful(self):
        """Cron should ignore the helpful articles."""
        r = _make_backdated_revision(90)

        for x in range(0, 3):
            _add_vote_in_past(r, 1, 15)

        for x in range(0, 2):
            _add_vote_in_past(r, 0, 15)

        cache_most_unhelpful_kb_articles()

        eq_(0, self.redis.llen(self.REDIS_KEY))

    def test_caching_changed_helpfulness(self):
        """Changed helpfulness should be calculated correctly."""
        r = _make_backdated_revision(90)

        for x in range(0, 4):
            _add_vote_in_past(r, 0, 45)

        for x in range(0, 1):
            _add_vote_in_past(r, 1, 45)

        for x in range(0, 3):
            _add_vote_in_past(r, 0, 15)

        for x in range(0, 2):
            _add_vote_in_past(r, 1, 15)

        cache_most_unhelpful_kb_articles()

        eq_(1, self.redis.llen(self.REDIS_KEY))
        result = self.redis.lrange(self.REDIS_KEY, 0, 1)
        eq_(u'%d::%.1f::%.1f::%.1f::%.1f::%s::%s' %
             (r.id, 5.0, 0.4, 0.2, 0.0, r.document.slug, r.document.title),
            result[0].decode('utf-8'))

    def test_caching_sorting(self):
        """Tests if Bayesian Average sorting works correctly."""
        # This should be at the bottom.
        r = _make_backdated_revision(90)

        for x in range(0, 26):
            _add_vote_in_past(r, 1, 15)

        for x in range(0, 76):
            _add_vote_in_past(r, 0, 15)

        # This should be at the top.
        r2 = _make_backdated_revision(90)

        for x in range(0, 61):
            _add_vote_in_past(r2, 1, 15)

        for x in range(0, 181):
            _add_vote_in_past(r2, 0, 15)

        # This should be in the middle.
        r3 = _make_backdated_revision(90)

        for x in range(0, 31):
            _add_vote_in_past(r3, 1, 15)

        for x in range(0, 91):
            _add_vote_in_past(r3, 0, 15)

        cache_most_unhelpful_kb_articles()

        eq_(3, self.redis.llen(self.REDIS_KEY))
        result = self.redis.lrange(self.REDIS_KEY, 0, 3)
        assert '%d::%.1f:' % (r2.id, 242.0) in result[0]
        assert '%d::%.1f:' % (r3.id, 122.0) in result[1]
        assert '%d::%.1f:' % (r.id, 102.0) in result[2]
