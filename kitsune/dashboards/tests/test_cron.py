# -*- coding: utf-8 -*-
from datetime import timedelta

from django.conf import settings

from nose import SkipTest
from nose.tools import eq_

from kitsune.dashboards.cron import (
    cache_most_unhelpful_kb_articles, _get_old_unhelpful,
    _get_current_unhelpful, update_l10n_coverage_metrics)
from kitsune.dashboards.models import (
    WikiMetric, L10N_TOP20_CODE, L10N_ALL_CODE)
from kitsune.products.tests import product
from kitsune.sumo.redis_utils import redis_client, RedisError
from kitsune.sumo.tests import TestCase
from kitsune.wiki.models import HelpfulVote, Revision
from kitsune.wiki.tests import revision, document


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
        """Make sure _get_current_articles() returns nothing with no votes.
        """
        result = _get_current_unhelpful({})
        eq_(0, len(result))

    def test_old_articles(self):
        """Returns unhelpful votes within time range"""
        r = _make_backdated_revision(90)

        # Add 4 no votes 1.5 months ago
        for x in range(0, 4):
            _add_vote_in_past(r, 0, 10)

        # Add 1 yes vote 1.5 months ago
        _add_vote_in_past(r, 1, 10)

        result = _get_old_unhelpful()
        eq_(1, len(result))
        self.assertAlmostEqual(0.2, result[r.id]['percentage'])
        eq_(5, result[r.id]['total'])

    def test_old_articles_helpful(self):
        """Doesn't return helpful votes within range"""
        r = _make_backdated_revision(90)

        for x in range(0, 4):
            _add_vote_in_past(r, 1, 10)

        _add_vote_in_past(r, 0, 10)

        result = _get_old_unhelpful()
        eq_(0, len(result))

    def test_current_articles(self):
        """Returns unhelpful votes within time range"""
        r = _make_backdated_revision(90)

        for x in range(0, 3):
            _add_vote_in_past(r, 0, 3)

        for x in range(0, 2):
            _add_vote_in_past(r, 1, 3)

        old_data = {r.id: {'percentage': 0.2, 'total': 5.0}}

        result = _get_current_unhelpful(old_data)
        eq_(1, len(result))
        self.assertAlmostEqual(0.4, result[r.id]['currperc'])
        self.assertAlmostEqual(0.4 - old_data[r.id]['percentage'],
                               result[r.id]['diffperc'])
        eq_(5, result[r.id]['total'])

    def test_current_articles_helpful(self):
        """Doesn't return helpful votes within time range"""
        r = _make_backdated_revision(90)

        for x in range(0, 3):
            _add_vote_in_past(r, 1, 3)

        for x in range(0, 2):
            _add_vote_in_past(r, 0, 3)

        old_data = {r.id: {'percentage': 0.2, 'total': 5.0}}

        result = _get_current_unhelpful(old_data)
        eq_(0, len(result))

    def test_current_articles_not_in_old(self):
        """Unhelpful articles in current but not in old works"""
        r = _make_backdated_revision(90)

        for x in range(0, 3):
            _add_vote_in_past(r, 0, 3)

        for x in range(0, 2):
            _add_vote_in_past(r, 1, 3)

        old_data = {}

        result = _get_current_unhelpful(old_data)
        eq_(1, len(result))
        self.assertAlmostEqual(0.4, result[r.id]['currperc'])
        self.assertAlmostEqual(0, result[r.id]['diffperc'])
        eq_(5, result[r.id]['total'])


class TopUnhelpfulArticlesCronTests(TestCase):
    def setUp(self):
        super(TopUnhelpfulArticlesCronTests, self).setUp()
        self.REDIS_KEY = settings.HELPFULVOTES_UNHELPFUL_KEY
        try:
            self.redis = redis_client('helpfulvotes')
            self.redis.flushdb()
        except RedisError:
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
            _add_vote_in_past(r, 0, 3)

        for x in range(0, 2):
            _add_vote_in_past(r, 1, 3)

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
            _add_vote_in_past(r, 1, 3)

        for x in range(0, 2):
            _add_vote_in_past(r, 0, 3)

        cache_most_unhelpful_kb_articles()

        eq_(0, self.redis.llen(self.REDIS_KEY))

    def test_caching_changed_helpfulness(self):
        """Changed helpfulness should be calculated correctly."""
        r = _make_backdated_revision(90)

        for x in range(0, 4):
            _add_vote_in_past(r, 0, 10)

        for x in range(0, 1):
            _add_vote_in_past(r, 1, 10)

        for x in range(0, 3):
            _add_vote_in_past(r, 0, 3)

        for x in range(0, 2):
            _add_vote_in_past(r, 1, 3)

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
            _add_vote_in_past(r, 1, 3)

        for x in range(0, 76):
            _add_vote_in_past(r, 0, 3)

        # This should be at the top.
        r2 = _make_backdated_revision(90)

        for x in range(0, 61):
            _add_vote_in_past(r2, 1, 3)

        for x in range(0, 181):
            _add_vote_in_past(r2, 0, 3)

        # This should be in the middle.
        r3 = _make_backdated_revision(90)

        for x in range(0, 31):
            _add_vote_in_past(r3, 1, 3)

        for x in range(0, 91):
            _add_vote_in_past(r3, 0, 3)

        cache_most_unhelpful_kb_articles()

        eq_(3, self.redis.llen(self.REDIS_KEY))
        result = self.redis.lrange(self.REDIS_KEY, 0, 3)
        assert '%d::%.1f:' % (r2.id, 242.0) in result[0]
        assert '%d::%.1f:' % (r3.id, 122.0) in result[1]
        assert '%d::%.1f:' % (r.id, 102.0) in result[2]


class L10nCoverageMetricsTests(TestCase):

    def test_update_l10n_coverage_metrics(self):
        """Test the cron job that updates l10n coverage metrics."""
        p = product(save=True)

        # Create en-US documents.
        for i in range(20):
            r = revision(
                is_approved=True, is_ready_for_localization=True, save=True)
            r.document.products.add(p)

        r1 = Revision.objects.all()[0]
        r2 = Revision.objects.all()[1]

        # Translate one to es.
        d = document(parent=r1.document, locale='es', save=True)
        revision(document=d, based_on=r1, is_approved=True, save=True)

        # Translate two to de.
        d = document(parent=r1.document, locale='de', save=True)
        revision(document=d, based_on=r1, is_approved=True, save=True)
        d = document(parent=r2.document, locale='de', save=True)
        revision(document=d, based_on=r2, is_approved=True, save=True)

        # Translate all to ak.
        for r in Revision.objects.filter(document__locale='en-US'):
            d = document(parent=r.document, locale='ak', save=True)
            revision(document=d, based_on=r, is_approved=True, save=True)

        # Call the cronjob
        update_l10n_coverage_metrics()

        # Verify es metrics.
        eq_(4, WikiMetric.objects.filter(locale='es').count())
        eq_(5.0, WikiMetric.objects.get(
            locale='es', product=p, code=L10N_TOP20_CODE).value)
        eq_(5.0, WikiMetric.objects.get(
            locale='es', product=p, code=L10N_ALL_CODE).value)
        eq_(5.0, WikiMetric.objects.get(
            locale='es', product=None, code=L10N_TOP20_CODE).value)
        eq_(5.0, WikiMetric.objects.get(
            locale='es', product=None, code=L10N_ALL_CODE).value)

        # Verify de metrics.
        eq_(4, WikiMetric.objects.filter(locale='de').count())
        eq_(10.0, WikiMetric.objects.get(
            locale='de', product=p, code=L10N_TOP20_CODE).value)
        eq_(10.0, WikiMetric.objects.get(
            locale='de', product=p, code=L10N_ALL_CODE).value)
        eq_(10.0, WikiMetric.objects.get(
            locale='de', product=None, code=L10N_TOP20_CODE).value)
        eq_(10.0, WikiMetric.objects.get(
            locale='de', product=None, code=L10N_ALL_CODE).value)

        # Verify ak metrics.
        eq_(4, WikiMetric.objects.filter(locale='de').count())
        eq_(100.0, WikiMetric.objects.get(
            locale='ak', product=p, code=L10N_TOP20_CODE).value)
        eq_(100.0, WikiMetric.objects.get(
            locale='ak', product=p, code=L10N_ALL_CODE).value)
        eq_(100.0, WikiMetric.objects.get(
            locale='ak', product=None, code=L10N_TOP20_CODE).value)
        eq_(100.0, WikiMetric.objects.get(
            locale='ak', product=None, code=L10N_ALL_CODE).value)

        # Verify it metrics.
        eq_(4, WikiMetric.objects.filter(locale='it').count())
        eq_(0.0, WikiMetric.objects.get(
            locale='it', product=p, code=L10N_TOP20_CODE).value)
        eq_(0.0, WikiMetric.objects.get(
            locale='it', product=p, code=L10N_ALL_CODE).value)
        eq_(0.0, WikiMetric.objects.get(
            locale='it', product=None, code=L10N_TOP20_CODE).value)
        eq_(0.0, WikiMetric.objects.get(
            locale='it', product=None, code=L10N_ALL_CODE).value)
